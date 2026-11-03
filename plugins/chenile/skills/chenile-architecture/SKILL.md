---
name: "chenile-architecture"
description: "How the Chenile framework is built: the 11 repositories and their layers, module map, and the runtime internals (ChenileExchange, the chenile-highway interceptor chain, interpolations, body typing, service selection via ServiceSelector, ServiceInvoker binding, JSON service definitions, events), plus polymorphism by configuration and its late-binding failure modes. Use when explaining Chenile architecture or internals, onboarding someone, debugging the request pipeline, or reasoning about where a change belongs."
---

# Chenile architecture and runtime internals

## Layers (11 repositories under chenile-parent)

1. **Build baseline**
   - `chenile-parent`: Maven super-parent and dependency BOM. It defines the Java and Spring Boot versions and every Chenile artifact version.
2. **Core runtime**
   - `chenile-core`. Modules: stm, chenile-base, owiz, chenile-core, chenile-http, cucumber-utils, utils, jpa-utils, multi-datasource-utils, chenile-mcp, chenile-admin-ui.
3. **Application blueprints**
   - `chenile-query-workflow-blueprints`. Modules: query-api, chenile-query-service, chenile-query-controller, query-mcp, workflow-api, workflow-service, workflow-info, workflow-mcp, workflow-utils, cucumber-workflow-utils, stm-generate-puml.
   - `chenile-process-management`. Modules: process-api, chenile-outbox, trigger-api, trigger-service, crontab-api, crontab-service, process-service, process-delegate, the jdbc/q-based/invm starters, process-admin-server, process-ui (see the chenile-process-management skill).
4. **Integration**
   - `chenile-service-registry`
   - `chenile-proxies`
   - `chenile-security`: legacy Keycloak model, plus auth-framework (auth-server / gateway / resource-server starters).
   - `chenile-messaging`: pub-sub, mqtt, kafka, azure, jvm-pub-sub, cloud-edge-switch.
5. **Support**
   - `chenile-bdd`: it-cucumber-utils, it-cucumber-sec-utils.
   - `chenile-others`: filewatch, scheduler, cache, config-maven-plugin.
   - `cconfig`: chenile-config, cconfig-db.

Size (2026-10-03): about 33.1K lines of production Java and 20.8K lines of tests, in 74 Maven modules. chenile-core holds about 39% of the production code. There are 791 framework tests.

Query and workflow blueprints build **on** the core; they don't duplicate it. Integration repos are small because they plug into the same pipeline.

## Runtime: one pipeline for every entry point

HTTP, events, proxies, scheduler, file-watch and MCP all create a **`ChenileExchange`** and run it through `ChenileEntryPoint`, which executes the Owiz flow `chenile-highway`. That flow is defined in `chenile-core/src/main/resources/org/chenile/core/chenile-core.xml` and loaded via `chenile.interceptors.path`.

**The exchange** is bidirectional:
- Incoming: `headers`, `multiPartMap`, `locale`, `body`.
- Routing: `serviceDefinition`, `operationDefinition`, `bodyType`.
- Invocation: `serviceReference`, `method`, `apiInvocation`.
- Outgoing: `response`, `exception`, `httpResponseStatusCode`, `responseMessages`.

Exchanges are created by `HttpEntryPoint` (path variables go into headers) or by `ChenileExchangeBuilder` (programmatic, with a `HeaderCopier`).

**Chain order:**

1. `logOutput`
2. `genericResponseBuilder`
3. `exceptionHandlerInterpolation`
4. `validateCopyHeaders`
5. `preProcessorsInterpolation`
6. `transformationClassSelector`
7. `transformer`
8. `constructServiceReference`
9. `postProcessorsInterpolation`
10. `operationSpecificProcessorsInterpolation`
11. `serviceSpecificProcessorsInterpolation`
12. `serviceInvoker`

How the chain is built and behaves:
- Owiz maps a kebab-case tag to a camelCase Spring bean, falling back to instantiating a class of that name. Nesting means attachment; in a `Chain`, the attachment order is the execution order.
- **Interpolations** expand at runtime into commands taken from:
  - `chenile.exception.handler`
  - `chenile.pre.processors` / `chenile.post.processors` (deployable-wide)
  - the operation's or service's `interceptorComponentNames` / `@InterceptedBy`
- Interceptors extend `BaseChenileInterceptor`: `doPreProcessing`, then continue the chain, capture exceptions, and `doPostProcessing` in `finally`. So the XML is a **nested call stack**; the response builder sits near the top so it can wrap everything.
- `validateCopyHeaders` ensures a request id exists, copies `x-…` headers into `ContextContainer`, and **rejects incoming `x-p-…`** (protected internal headers).
- `constructServiceReference` picks the implementation bean, in this precedence: **mock** mode (`x-chenile-mock-mode: true` or a mock exchange) › **trajectory** override (`x-chenile-trajectory-id`) › the service's optional **`ServiceSelector`** › the default `serviceName` bean. See *Service selection* below.

**Body typing:**
- The default body type is the operation's `input` class.
- Selectors are configured with `bodyTypeSelectorComponentNames` (JSON) or `@BodyTypeSelector` (annotation); both end up in `OperationDefinition.bodyTypeSelector`.
- `SubclassBodyTypeSelector` + `SubclassRegistry` pick a subclass using a top-level `"type"` discriminator (bad discriminator → 400 `PAYLOAD_CANNOT_BE_PARSED`).
- `Transformer` deserializes string bodies; failure is a bad request.

**ServiceInvoker binding:** each `ParamDefinition` has a type:
- `BODY`: the typed body.
- `HEADER`: one header.
- `HEADERS`: the whole header map.
- `MULTI_PART`: one uploaded file.

`paramType` is the public, possibly generic type (MCP reads it); `paramClass` is the legacy raw class used for method matching. This keeps services domain-shaped.

**Response:** `GenericResponse` JSON has these top-level fields: `success`, `code` (a string), `subErrorCode`, `description`, `severity`, `errors[]`, `payload`. Warnings are `@JsonIgnore`.

**JSON service definitions:**
- Found through `chenile.service.json.package`.
- Top-level fields: `name` (implementation bean), `id` (logical id), `serviceSelector` (optional, 2.1.35), `mockName`, `healthCheckerName`, `interceptorComponentNames`, `operations[]`.
- Operation fields: `name`, `url` and/or `urls` (ordered aliases; `getUrl()` stays the canonical one), `httpMethod`, `produces`/`consumes`, `input`, `output`, `interceptorComponentNames`, `bodyTypeSelectorComponentNames`, `eventSubscribedTo`, `params`.
- Each operation is validated against a real Java method at startup.

**Events:**
- Definitions come from `chenile.event.json.package` (`{"id","topic","type"}`).
- Subscriptions use `eventSubscribedTo` or `@EventsSubscribedTo`.
- `ChenileEventSubscribersInitializer` fails startup on a payload-type mismatch.
- `EventProcessor.handleEvent(id, payload, headers)` creates an exchange per subscriber and runs the same chain. So messaging, the scheduler, process triggers and so on inherit every policy.

**Annotation services (2.1.31):**
- `@ChenileController` (now in chenile-core) plus `@ChenileOperation` and `@ChenileBody` create transport-neutral services that need no chenile-http.
- `HttpAnnotationChenileServiceInitializer` adds the MVC routes.
- `SpringMvcMappingProducer` requires exactly one HTTP verb per operation but accepts several paths: every alias is registered against the same handler and `OperationDefinition`, so interceptors, invocation and event subscriptions are shared.
- `registerInServiceRegistry=false` skips registry publication for one service; `chenile.service.registry.read-only=true` makes a whole deployable a consumer only.
- `CANNOT_INVOKE_TARGET` (E509) now names the operation and the exception type.

**Service selection (2.1.35, chenile-core):**
- `@ChenileController(serviceSelector = "<bean>")` or JSON `"serviceSelector": "<bean>"` names a Spring bean implementing `org.chenile.core.service.ServiceSelector`:
  `String selectServiceReferenceName(ChenileExchange exchange, ChenileServiceDefinition sd)`.
- It runs per invocation inside `constructServiceReference`. A returned bean name replaces the default implementation for that call (`exchange.serviceReferenceId` becomes that name); `null` keeps the configured `serviceName` bean.
- Precedence: mock › trajectory › selector › default. A trajectory override therefore still wins over a selector.
- The selector bean is resolved at startup (`AbstractServiceInitializer.configureServiceSelector`); a bean that is not a `ServiceSelector` fails startup with `NOT_INSTANCE_SERVICE_SELECTOR` (E525). Stored on `ChenileServiceDefinition` as `serviceSelector` (name) and `serviceSelectorComponent` (`@JsonIgnore`).
- The *selected* bean is looked up and its method resolved **per request** (`MethodUtils.computeMethod` by operation name and params) — unlike the default bean, it is not validated at startup. A missing bean fails with `NOT_CONFIGURED_IN_SPRING`, a missing method with `UNKNOWN_METHOD`, on that request.
- Pair it with a `@BodyTypeSelector` when the selected implementations take different body types.
- First consumer: process management's typed work listener (`processWorkServiceSelector` routes to `<processType>Executor|Splitter|Aggregator`).
- Docs: `chenile-core/docs/chenile-annotations.md`, `service-definition-json.md`, `trajectories.md`.

## Polymorphism by configuration (concept: chenile.org/concepts/16-polymorphism/)

Chenile decides *which code runs* per request, from data. The mechanisms, by what varies:
- **Implementation:** mock › trajectory (`@ConditionalOnTrajectory(id, service)` overrides a *Chenile service* bean only — registered at startup by `TrajectoryPostprocessor` / `AnnotationTrajectoryInitializer`) › `ServiceSelector` › default.
- **Location:** `ProxyTypeRouter` — `LOCAL`, `REMOTE`, or `COMPUTE_DYNAMICALLY` (local when the target's monolith name equals this one).
- **Input type:** `@BodyTypeSelector`; `SubclassBodyTypeSelector`; `StmBodyTypeSelector` (per workflow event: second param of the resolved action's `transitionTo`, else event `bodyType` metadata).
- **Workflow logic:** `STMTransitionActionResolver` (workflow-service). Bean name = `[ctx] + prefix + [EntitySimpleName] + Capitalize(eventOrState) + [Action|AutoState|PostSaveHook if useSuffix]`. Extra "other prefixes" are header keys read as `x-<key>`; their value + `Capitalize(prefix)` is tried first (multi-tenant sample passes `chenile-tenant-id` → `acmeVehicleCreate` before `vehicleCreate`). Trajectory-specific STM beans are **opt-in**: pass `chenile-trajectory-id` the same way — there is no other trajectory code in the workflow modules. Entity-qualified names are tried before plain ones.
- **Agent view:** `@ChenilePolymorph("bean")` + `ChenilePolymorphProvider.getVariants(...)` publishes one operation as several MCP tools; `ProcessIdPolymorph` (workflow-mcp) makes one tool per workflow event (`<prefix>_<event>`, event fixed, typed payload).
- **Values:** cconfig per-tenant/per-trajectory overrides; workflow enablement.

**Late-binding failure modes** (sort by when a mistake shows up):
- *Loud at startup:* default service bean + operations; the selector bean's type (E525); `@ConditionalOnTrajectory` beans registered.
- *Loud per request:* the selector's chosen bean/method (`NOT_CONFIGURED_IN_SPRING` / `UNKNOWN_METHOD`); a trajectory override's method; a bad subclass discriminator (400); a misrouted process-work message (Kafka retry → `.DLT`).
- *Silent (worst):* an unknown trajectory id falls through to selector/default; `StmBodyTypeSelector` that can't derive a type logs a warning and keeps the operation's input type (fields can be dropped); the STM resolver **swallows lookup exceptions**, a misnamed action runs the resolver's default action — the JGen-generated `DefaultSTMTransitionAction` is a **no-op**, so the transition succeeds and business logic is skipped; a missing post-save hook is skipped (`DefaultPostSaveHook`); a missing auto-state returns `""` (`DefaultAutomaticStateComputation`).

**Mitigations (documented on the concept page):** make fallbacks loud (process management's `ProcessWorkServiceFallback` throws `NO_PROCESS_WORKER_SELECTED`; give `DefaultSTMTransitionAction` a log/metric or throw for events not on an allow-list); close the selector's candidate set (map, not string concatenation); add an `ApplicationReadyEvent` wiring check using `ChenileConfiguration.getServices()`, `ServiceDefinition.getOperations()` and `MethodUtils.computeMethod(Class, OperationDefinition)` (process work: leaf → `<type>Executor`, non-leaf → `<type>Splitter` + `<type>Aggregator`, limited to the queues a worker consumes); validate trajectory/tenant headers at the edge (pre-processor); test every variant (per trajectory, tenant, processType×workerType, event; `/{svc}/info/test-cases`); log/metric `exchange.getServiceReferenceId()` and alert on default-action hits, fallback hits and DLT depth; keep DLTs provisioned for replay.

Framework enhancement ideas (not implemented as of 2026-10-25): an optional candidate-declaring selector interface so chenile-core validates candidates at startup; a strict mode for `STMTransitionActionResolver` that fails or warns when an event resolves to the default; a startup check in process-delegate for worker bean names; an allow-list for trajectory ids.

## Where the long-form docs live

- `chenile-core/docs` (github.com/ajapros/chenile-core): exchange-lifecycle, interceptor-chain, transformation, service-invoker, service-definition-json, events, stm, trajectories, chenile-annotations, chenile-mcp, codebase-overview.
- `chenile-query-workflow-blueprints/docs`: REPO_OVERVIEW, GENERATOR_BLUEPRINT_MAPPING, WORKFLOW_STMCMDS_GUIDE.
- Public versions:
  - https://chenile.org/developer/runtime-internals/
  - https://chenile.org/concepts/16-polymorphism/
  - /developer/workflow-internals/
  - /architecture/
  - /by-the-numbers/

Related skills: chenile-framework-knowledge (API contracts for clients and UIs), chenile-process-management, chenile-query-workflow-blueprints, chenile-jgen.


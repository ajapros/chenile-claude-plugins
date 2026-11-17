---
name: "chenile-framework-knowledge"
description: "Reference knowledge of the Chenile Java/Spring microservices framework (chenile.org) and the Chenile house rules for writing Chenile code (cucumber tests always, reuse existing utilities, imports not FQCNs, @Configuration/@Bean instead of @Component, -api/-service split, follow JGen blueprint patterns, no single-use helper classes, avoid static methods, ask before adding abstraction layers, org.chenile.configuration.x for configuration and org.chenile.x for core classes). Covers concepts, exact REST/response contracts, headers, workflow (Finito STM) and query APIs, security, messaging, cconfig, registry/proxies, admin endpoints, service selection, and releases through 2.1.35 (2.1.36 in development). Use when writing or reviewing Chenile code, building a UI, client or integration against Chenile services, or explaining Chenile."
---


# Chenile: working knowledge for writing Chenile code and building against it

Chenile (https://chenile.org, `org.chenile`) is an open-source Java / Spring Boot framework for "microservices done right." Business logic stays pure; cross-cutting concerns are configuration-driven interceptors ("policies"); where policies run is configuration.

- **Source:** `github.com/ajapros/*` (framework), `rajakolluru/chenile-gen` (JGen) and `ajapros/stm-cli` (stm-cli). Clone the repositories you work with; the house rules below assume you can search them.
- **Platform:** Java **25**, Spring Boot **4.1**, Jackson **3** (`tools.jackson.*` packages in chenile-core; annotations stay `com.fasterxml.jackson.annotation`).
- **Versions:**
  - **2.1.35** is tagged (framework 2026-10-27).
  - **2.1.36** is in development.
  - **JGen** (2.5.x, Maven group `org.chenile.jgen`) and **stm-cli** (1.0.x) have their own release lines, built only against released Chenile.
  - Release notes: https://chenile.org/release-notes/ and https://jgen.chenile.org/releases/.
- **Verify specifics** against a running server: `GET /info` and `GET /service-info/{service}`.

Related skills:
- chenile-architecture: internals.
- chenile-jgen: generation and blueprints.
- chenile-process-management.
- chenile-query-workflow-blueprints: workflow and query runtime code.

## 0. House rules for writing Chenile code (always follow)

1. **Always write Cucumber tests.** Every feature, fix or service gets Gherkin scenarios. Follow the blueprint layout (e.g. `bp-service`'s `service-template`):
   - **Feature files:** in `src/test/resources/features/*.feature`.
   - **Runner:** `bdd/CukesRestTest` (`@RunWith(Cucumber.class)`, `@CucumberOptions(features = "src/test/resources/features", glue = {"classpath:<your>/bdd", "classpath:org/chenile/cucumber/rest"})`; add `"classpath:org/chenile/cucumber/security/rest"` when security is on).
   - **Steps class:** `bdd/CukesSteps` with `@SpringBootTest(webEnvironment = RANDOM_PORT, classes = SpringTestConfig.class)`, `@AutoConfigureMockMvc`, `@ActiveProfiles("unittest")`, `@CucumberContextConfiguration` and a dummy `@Given("dummy")`.
   - **Reuse the existing step libraries before writing a step:**
     - `cucumber-utils` REST steps (`org.chenile.cucumber.rest.RestCukesSteps`): `Given that "x" equals "y"`, `I construct a REST request with header … and value …`, `I POST|GET|PATCH a REST request to URL … with payload`, `success is true`, `store "$.payload.id" from response to "id"`, `the REST response key … is …`, plus the collection steps added in 2.1.31.
     - non-REST steps (`org.chenile.cucumber.nonrest.CukesSteps`): `I POST a request to service … and operation …`, `an exception is thrown with message code …`, `a warning must be thrown …`.
     - `VariableHelper` for `${var}` substitution.
     - `cucumber-workflow-utils` (chenile-query-workflow-blueprints) for STM.
     - `it-cucumber-utils` / `it-cucumber-sec-utils` (chenile-bdd) for integration tests against running servers.
   - **Custom steps** only when no existing step fits, kept in the project's own `bdd` package.
   - **Plain JUnit** is fine for pure units (parsers, validators), but the behaviour of a service is proved with Cucumber.
2. **Use existing utilities instead of writing new ones.** Search the framework first (the Chenile repositories, or the sources jars of the `org.chenile` artifacts in your build). Commonly reused:
   - **chenile-base:** `GenericResponse`, `ResponseMessage`, `ErrorNumException`, `BadRequestException`, `NotFoundException`, `ServerException`, `ConfigurationException`, `WarningAware`, `ResponseHeadersAware`.
   - **chenile-core:** `BaseChenileInterceptor`, `ChenileExchange`, `ControllerSupport`, `ChenileTypeUtils`, `ChenileGenericTypeParser`, `MethodUtils`, body type selectors, `ServiceSelector`, proxies (`proxyBuilder`).
   - **utils:**
     - `IDGenerator`, `TypedIdGenerator`;
     - `EntityStore`, `ChenileEntity`, `BaseEntity`, `ExtendedStateEntity`;
     - `TenantSpecificResourceLoader`, `TenantRouter`, `HeadersAwareContext`;
     - `StrSubstitutor`;
     - `CsvReader`, `JsonReader`, `LineIterable`, `Looper`;
     - `RegionToTrajectoryConverter`;
     - `BitsUtil`.
   - **jpa-utils:** `BaseJpaEntity` (and its Long/Integer/generated-id variants), `AbstractJpaStateEntity`, `@ChenileGeneratedId`.
   - **stm / workflow:**
     - the Finito STM;
     - `workflow-service` (`StateEntityServiceImpl`, `BaseTransitionAction`, `StmBodyTypeSelector`);
     - `workflow-utils` `CLIHelper` for diagrams and test cases.
   - **Query:** `chenile-query-controller` (`POST /q/{name}`) with MyBatis mappers.
   - **Config:** `CconfigClient.value(module, key[, type])`.
   - **Messaging:** `ChenilePub` / `ChenileSub`.
   - **Process:** process-delegate's typed work listeners.
   - **Generic helpers:** Spring, Jackson and Apache Commons, already on the classpath.

   If a utility is genuinely missing and reusable, propose adding it to the right framework module rather than burying it in an application.
3. **Imports, not fully qualified names.** Never write `org.chenile.foo.Bar x = new org.chenile.foo.Bar()` in code. Import the class at the top of the file and use the simple name. The only exception is a genuine simple-name clash in one file; there, import the more frequently used one and qualify the other.
4. **No `@Component` / `@Service` / `@Repository` for wiring.** Create every bean in a `@Configuration` class with explicit `@Bean` methods, as the blueprints do:

   ```java
   @Configuration
   public class OrderConfiguration {
       @Bean public OrderService _orderService_() { return new OrderServiceImpl(); }
       @Bean OrderHealthChecker orderHealthChecker() { return new OrderHealthChecker(); }
   }
   ```

   - **Exceptions:** controllers stay `@RestController` + `@ChenileController` (a Chenile requirement), Spring Data repository interfaces, test classes, and `@Configuration` classes themselves.
   - **Bean names:** service beans are named `_<svc>Service_` and health checkers `<svc>HealthChecker`.
   - **Dependencies:** passed through `@Bean` method parameters or constructors, not field `@Autowired` where it can be avoided.
   - **Existing `@Component` classes** in the framework, e.g. in process-delegate, are legacy and not a pattern to copy.
5. **Complex services are split into `-api` and `-service`.** For any non-trivial service, create two modules under a parent pom:
   - **`<svc>-api`:** the service interface plus model/DTOs. It is the only thing consumers depend on.
   - **`<svc>-service`:** the implementation, configuration, controller, error codes, health checker, messages and Cucumber tests. Nobody depends on it.

   Prefer generating the skeleton with JGen (`jgen -g chenile-service`, `wfservice`/`wfcustom` for workflows, `mybatisQuery` for queries, `chenile-headless-service` for non-HTTP), then fill it in.
6. **Look among the blueprints for patterns first.** Before designing structure, wiring, tests, configuration, error codes, curl scripts or pom layout, check the JGen blueprint templates in `chenile-gen/jgen/bp-*/src/main/resources/*-template/` (github.com/rajakolluru/chenile-gen):

   | Need | Blueprint |
   |---|---|
   | A service | `bp-service` |
   | A workflow | `bp-wfservice`, `bp-wfcustom` |
   | A query | `bp-mybatisQuery` |
   | A deployable | `bp-minimonolith` |
   | An interceptor | `bp-interceptor` |
   | An integration test | `bp-it` |
   | Process workers and deployment | `bp-process-workers`, `bp-process-management` |
   | A non-HTTP service | `bp-headless-service` |

   Mirror their package layout (`configuration`, `configuration/controller`, `service/impl`, `service/errorcodes`, `service/healthcheck`, `bdd`) and naming. The chenile-jgen skill describes every blueprint.
7. **No single-use helper classes.** Don't create a utility class (`XxxEvents`, `XxxHelper`, `XxxUtils`) to hold a method that only one class calls. Put it in that class as a private method or a private nested class. Test it through the owning class's behaviour, not separately.
   - A shared class is justified only when two or more classes really call it **and** keeping their copies identical matters (for example tenant or header security rules). A few lines that two classes happen to repeat are not a reason on their own.
   - Rule 2 still applies: reuse what the framework already has. This rule is about not *inventing* new helper classes.
   - **Avoid static methods.** Use instance methods, and give the class that needs them an instance (a field, a constructor argument or a `@Bean`). Statics are fine only in a typical general-purpose utility class, the `trim()` / `isBlank()` kind, and for constants. Domain rules, validation and anything with behaviour worth substituting in a test are instance methods, even when the class is stateless.
8. **Ask before adding layers of abstraction.** Before you introduce an extra interface, base class, SPI, factory, registry or delegating wrapper beyond what the task needs, describe the layer and why, and ask the user first. Default to the most direct design: one interface with its implementations, logic in the class that uses it. Many layers that each just forward a call are a design smell here.
9. **Package layout for framework modules.** For a framework module `x`:
   - `org.chenile.configuration.x` holds its `@Configuration` classes (and controllers under `.controller`);
   - `org.chenile.x` holds its core classes (services, models, jobs, error codes).

   For a two-part name such as `scheduler-db`, use `org.chenile.configuration.scheduler.db` and `org.chenile.scheduler.db`. An application then needs to scan only `org.chenile.configuration` (`@SpringBootApplication(scanBasePackages = "org.chenile.configuration")`), and the core packages are never component-scanned. An auto-configuration also goes under `org.chenile.configuration.x`: list it in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`, and `@SpringBootApplication`'s scan skips it, so its conditions still run after the application's beans.

## 1. Model

- **Module split:** services are split into `xxx-api` (interface and model, which consumers depend on) and `xxx-service` (the implementation, which nobody depends on).
- **Hosting:** services are hosted by a mini-monolith deployable on port 8080.
- **One pipeline for every entry point.** HTTP, events, proxies, the scheduler, file-watch and MCP all become a `ChenileExchange`. It runs the same interceptor pipeline, then the pure implementation, and returns back out through the pipeline.
- **Everything but HTTP is an event (2.1.36).** A Chenile event is internal: an event id, a payload and x- headers. External happenings map onto it by configuration: a cron schedule (`chenile-scheduler`: one `SchedulerDefinition` from JSON via `chenile.scheduler.json.package`, code via `chenileScheduler.schedule(def)`, or the database via `chenile-scheduler-db`'s `/schedule` API), a file in a watched folder (`chenile-filewatch`, `eventId` defaults to `fileWatchId`, one event per record), a message on a topic (`chenile.kafka.consumer.topic-bindings`, default event id = topic), `POST /trigger`, or code (`TriggerService.trigger(TriggerInput)`). Operations subscribe with `@EventsSubscribedTo("x")` on the controller method or `"eventSubscribedTo": ["x"]` in JSON; payloads are converted to the body type by the transformer. Internal sources go through chenile-core's `chenile-trigger` `TriggerService`: `DirectTriggerService` by default (in memory; dedupe `chenile.trigger.dedupe.retention` PT24H, `max-entries` 100000) or process management's durable `EventTriggerService`. Standard headers (`TriggerHeaders`): `x-chenile-event-source` (CRON/FILE/API/EXTERNAL), `x-chenile-trigger-id`, `x-chenile-tenant-id`, `x-chenile-schedule-id`, `x-chenile-scheduled-fire-time`, `x-chenile-fire-time`, `x-chenile-file-watch-id`, `x-chenile-file-name`, `x-chenile-record-index`. Concept: chenile.org/concepts/17-events/; reference: /developer/entry-points/.
- **Controllers:** HTTP controllers carry `@ChenileController(value="<svc>Service", serviceName="_<svc>Service_", healthCheckerName=…)`, extend `ControllerSupport`, and call `process([op,] request, args…)`.
- **Per-request implementation choice (2.1.35):** `@ChenileController(serviceSelector="<bean>")` lets a `ServiceSelector` bean pick the implementation bean **per request**; `null` falls back to `serviceName`. Precedence: mock, then trajectory, then selector, then default. Details in the chenile-architecture skill.
- **Pipeline order** (`chenile-core.xml`):
  1. log-output
  2. generic-response-builder
  3. exception handler
  4. validate-copy-headers
  5. pre-processors
  6. transformation-class-selector
  7. transformer
  8. construct-service-reference
  9. post-processors
  10. operation-specific, then service-specific interceptors
  11. service-invoker

## 2. Response envelope: `GenericResponse<T>` (exact JSON)

```json
{ "success": true, "code": "200", "subErrorCode": 0, "description": "…", "severity": "ERROR|WARN",
  "errors": [ { "code": "400", "subErrorCode": 1234, "description": "…", "field": "email", "params": [], "severity": "ERROR" } ],
  "payload": { … } }
```

- `code` is a **string**.
- Warnings are `@JsonIgnore`, so they are never in the body.
- `description` is already localized.
- On failure, `success` is false and the HTTP status equals `code`.
- `CANNOT_INVOKE_TARGET` (E509) names the operation and the exception type.

UI: branch on `success`, show `description`, and map `errors[].field` to form fields.

## 3. Headers

| Header | Purpose |
|---|---|
| `Authorization: Bearer <JWT>` | Keycloak realm per tenant; the generated jwk-set-uri is `http://localhost:8180/realms/#tenantId#/…/certs`. The gateway validates the token and relays claims. |
| `x-chenile-tenant-id` | Tenant (required when security is on) |
| `x-chenile-eid` | User id in the samples |
| `Accept-Language` | Locale |
| `x-chenile-trajectory-id` | Variant routing (trajectories) |
| `x-chenile-region-id`, `x-chenile-gid`, `x-chenile-apt`, `x-chenile-tenanttype` | Entity-store and config selection |

Clients must never send `x-p-…` headers; they are protected and rejected.

## 4. Plain service (`chenile-service` blueprint)

- `POST /{svc}`: save.
- `GET /{svc}/{id}`: returns 404 (`NotFoundException`) if the id is missing.
- `POST /{svc}/op1`: a sample operation.

With JPA, entities extend `BaseJpaEntity`: `id`, `createdTime`, `lastModifiedTime`, `lastModifiedBy`, `createdBy`, `tenant`, `testEntity`, `version`.

## 5. Workflow service (`wfservice` / `wfcustom`): Finito STM

**Endpoints:**
- `POST /{svc}`
- `GET /{svc}/{id}`
- `PATCH /{svc}/{id}/{eventID}`: PATCH is canonical; old curl scripts use PUT.

All three return `GenericResponse<StateEntityServiceResponse<T>>`:

```json
"payload": { "mutatedEntity": { "id": "…", "currentState": {"stateId":"ASSIGNED","flowId":"IssueFlow"},
   "stateEntryTime": "…", "slaYellowDate": "…", "slaRedDate": "…", "slaTendingLate": 0, "slaLate": 0, … },
  "allowedActionsAndMetadata": [ {"allowedAction":"resolve","acls":"test.premium"}, {"allowedAction":"doRetrospective","activity":"MANDATORY"} ] }
```

- `allowedActionsAndMetadata` is already filtered by state and security. Each entry is `allowedAction` (the eventID to PATCH) plus every `meta-*` transition attribute from the states XML, with the prefix stripped.
- **Build buttons from this list; never hard-code events.**

**Event payloads:**
- `MinimalPayload{comment}` is the base. Specific events add fields, e.g. `Assign<Svc>Payload{assignee, comment}`.
- The type per event comes from `StmBodyTypeSelector`.
- With security on, events require `@SecurityConfig(authoritiesSupplier="<svc>EventAuthoritiesSupplier")`, derived from the STM acls.

**Generated example:** OPENED -assign→ ASSIGNED -resolve→ RESOLVED -close→ CLOSED. The activity option adds mandatory activities and ARCHIVED.

**Introspection** (GET or POST; params `flowId`, `stylingPropertiesText`, `state`). Each returns `GenericResponse<WorkflowInfoResponse<X>>`:

| Endpoint | X (result) |
|---|---|
| `/{svc}/info/state-diagram` | PNG `byte[]`, base64 in JSON |
| `/{svc}/info/allowed-actions?state=S` | `List<String>` |
| `/{svc}/info/json` | `Map`: states, transitions (eventId, acls, meta-data), state meta-data |
| `/{svc}/info/test-cases` | String |
| `/{svc}/info/test-visualization` | String |
| `/{svc}/info/test-state-diagrams` | `Map<String, byte[]>` |

`styling.json` holds rules like `{"expression":"highlight==true","style":{"color":"Fuchsia","thickness":2.5}}`.

**Offline:** `stm-cli` (`brew install ajapros/jgen-tap/stm-cli`) renders diagrams, allowed actions and test cases straight from a states XML.

**Health:** `GET /health-check/{svc}Service` returns `HealthCheckInfo{healthy, statusCode, message}`.

## 6. Query service (`mybatisQuery`): CQRS read side

**Endpoint:** `POST /q/{name}`. `name` is the external name, e.g. `students`, not the id `Student.getAll`. With MCP the path is `/mcp/q/{name}`.

**Request (`SearchRequest`):** `pageNum` (1), `numRowsInPage` (10), `filters` (arrays for contains-queries), `sortCriteria[{name, ascendingOrder}]`, `fields`, `systemFilters`, `customVariables`, `cannedReportName`, `saveChangesToCannedReport`, `publishCannedReportToEveryone`, `hiddenColumns`, `isOrOperation`, `countOnly`, `toDoList`.

**Response (`SearchResponse`):**
- Paging: `numRowsReturned`, `currentPage`, `maxPages`, `numRowsInPage`, `startRow`, `endRow`, `maxRows`, `pagination`.
- Rows: `list[{row, allowedActions}]`, or `data` for a single object graph.
- Also `columnMetadata`, `cannedReportName`, `availableCannedReports`, `hiddenColumns`.

**ColumnMetadata:**
- `name`, `columnName`
- `columnType`: Text | Number | Date | DateTime | DropDown | CheckBox
- Flags: `filterable`, `sortable`, `likeQuery`, `containsQuery`, `betweenQuery`
- Options and display: `dropDownValues` / `dropDownQuery`, `display`, `customRender`, `group`

**Query metadata:** `paginated`, `sortable`, `acls`, `workflowName` (gives per-row `allowedActions`), `flowColumn` / `stateColumn`, `toDoList`, `lateColumn` / `tendingLateColumn`. Queries are tenant-aware.

UI: build grids and filters from `columnMetadata`; put row actions from `allowedActions` and PATCH them to the workflow service.

## 7. Admin endpoints

| Endpoint | Returns |
|---|---|
| `GET /info` | services and the version map |
| `GET /service-info/{service}` | the full definition |
| `GET /health-check/{service}` | health |
| `GET /serviceregistry` | the catalog, when the registry is hosted |

`chenile-admin-ui` (Vite/React) is served at `/chenile/admin`; it uses only these endpoints and proxies requests in dev. MCP is at `/mcp` when enabled.

## 8. Process management: see the chenile-process-management skill

- **Workflow:** `POST /process`, `GET /process/{id}`, `PATCH /process/{id}/{event}`, `GET /processChildren/{id}`.
- **Admin API:** `/process-management/api/*`.
  - Plain DTOs, not `GenericResponse`.
  - Headers `X-Process-Management-Key` (at least 32 characters) and `x-chenile-tenant-id`.
  - Endpoints: info, schedules (2.1.36; was crontabs), triggers, executions (filter `scheduleId`), definitions (+refresh), processes, trace.
- **React dashboard:** `process-ui`, with a Schedules tab and a Quartz cron-expression builder.
- **Typed work listeners (2.1.35):** `ExecutorWorkListener` / `SplitterWorkListener` / `AggregatorWorkListener`, routed by `serviceSelector`.

## 9. Governance features

**Interceptors**
- They extend `BaseChenileInterceptor` and are attached with `interceptorComponentNames` (JSON) or `@InterceptedBy`.
- Deployable-wide interceptors use `chenile.pre.processors` / `chenile.post.processors`.
- Since 2.1.35, unknown interceptor names fail at startup (E526/E527; `chenile.interceptors.validate-on-startup`).

**Security**
- `@SecurityConfig(authorities=… | authoritiesSupplier=…)`.
- 401 at the edge, 403 at the last mile.

**cconfig**
- Module JSON configuration with path-level runtime overrides and per-tenant attributes (`customAttribute`).
- Trajectory-aware resource layering.
- Read with `CconfigClient.value(module, key[, Class|TypeReference])`.
- Sources: properties, JSON, environment, or DB (cconfig-db).

**Messaging**
- `ChenilePub` (publish, asyncPublish, publishToOperation) and `ChenileSub.messageArrived`.
- Transports: mqtt, kafka, azure, jvm, plus cloud-edge-switch.
- Kafka consumer: `chenile.kafka.consumer.topic-bindings` maps topics to Chenile event ids (default: event id = topic); failures retry with a fixed delay (`retry-interval-ms`, default 1000; `max-retries`, default 3), then go to `<topic><dead-letter-suffix>` (default `.DLT`). Auto-commit is off; provision the DLT topics.
- UIs call HTTP, not brokers.

**Registry and proxies**
- `proxyBuilder.buildProxy(Iface.class, "svc", headerCopier)`; `ProxyTypeRouter` sends calls local or remote; client processors are configurable per service and per operation.
- `registerInServiceRegistry=false` hides one service; `chenile.service.registry.read-only=true` makes a deployable a consumer only.

**Testing**
- One Gherkin feature runs over MockMvc (cucumber-utils) and REST Assured (it-cucumber-utils). See house rule 1.

## 10. Release highlights

- **2.1.31:**
  - Transport-neutral services: `@ChenileController` moved into chenile-core, and with `@ChenileOperation` and `@ChenileBody` on a plain bean a service needs no chenile-http (the headless blueprint).
  - Ecosystem and process-management blueprints, and `sinceVersion` gating.
  - Process triggers, outbox, DB definitions, admin API, UI and server.
- **2.1.33:**
  - Several URL aliases per operation (JSON `urls`, or several paths on the mapping annotation).
  - `ResponseHeadersAware` (a response DTO can set headers such as `Location`).
  - Centralized decoded-JSON transformation.
- **2.1.34:** Kafka consumer retry and dead-lettering; process deployment refinements.
- **2.1.35 (tagged):**
  - `serviceSelector` on `@ChenileController` and in JSON service definitions.
  - Typed process work listeners.
  - Interceptor names checked at startup.
  - The process console cron builder.
  - JGen 2.1.35: payload validator, generation records and `jgen -r`, `github:` blueprints, Homebrew/JBang.
- **2.1.36 (in development):**
  - stm-cli moved out of workflow-utils into `ajapros/stm-cli`; `CLIHelper`/`CLIParams` stay.
  - JGen work since 2.1.35 ships as JGen 2.5.1.
  - **Unified event model:** new `chenile-trigger` (chenile-core); `chenile-scheduler` rebuilt on `SchedulerDefinition` + `ChenileScheduler` (launchers, `SchedulerInfo`, execution store removed; clustered Spring Boot Quartz); new `chenile-scheduler-db`; `chenile-filewatch` fires through `TriggerService`; process management drops `trigger-api`, `crontab-api`, `crontab-service` (admin API `/schedules`). ADR: chenile-others `docs/adr/0001-unified-chenile-events-and-scheduling.md`.
  - A **chenile-validation** framework is proposed (chenile-core `docs/adr/0001-chenile-validation.md`):
    - Jakarta Bean Validation plus external schemas;
    - defaults;
    - copyable validators with no statics;
    - a `payload-validator` step after `transformer`;
    - cconfig tenant overlays, typed cconfig keys, field metadata and introspection;
    - `runtimeEditable` fields.

    It is not implemented yet; check the ADR before relying on it.

## 11. UI checklist

1. One API client that adds the auth, tenant and language headers, unwraps `GenericResponse`, and treats `code` as a string.
2. Handle 401 (re-authenticate) separately from 403 ("not permitted").
3. Lists: `POST /q/{name}`, driven by `columnMetadata`.
4. Detail: `GET /{svc}/{id}`, showing state and SLA badges.
5. Actions: render from `allowedActionsAndMetadata`, then PATCH, then refresh from the response.
6. Workflow view: `/{svc}/info/state-diagram` or `/json`.
7. Admin: `/info`, `/service-info`, `/health-check/{svc}Service`, `/serviceregistry`.
8. Brand: bg `#0d0d0d`, accent `#f89038`, gradient `#e0801e→#ffab52`; Sora, Josefin Sans, JetBrains Mono.
9. CORS: proxy via the dev server, or configure it on the gateway.


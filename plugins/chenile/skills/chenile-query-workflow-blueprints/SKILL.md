---
name: "chenile-query-workflow-blueprints"
description: "Working knowledge of the chenile-query-workflow-blueprints repository: module map, query runtime wiring (SearchRequest/QueryMetadata, mapper/definition files), the workflow-service stmcmds conventions (STMTransitionActionResolver, BaseTransitionAction, StmBodyTypeSelector, entry actions, post-save hooks, auto-states, secondary actions, StmAuthoritiesBuilder, ProcessIdPolymorph) and how JGen templates map onto these libraries. Use when changing, reviewing or explaining Chenile query or workflow runtime code or its generator impact."
---

# chenile-query-workflow-blueprints

Repo: github.com/ajapros/chenile-query-workflow-blueprints. The repository also carries its own version of this skill at `skills/chenile-query-workflow-blueprints/SKILL.md`.

## Read first (the smallest doc that answers the question)

- `docs/REPO_OVERVIEW.md`
- `docs/GENERATOR_BLUEPRINT_MAPPING.md`
- `docs/WORKFLOW_STMCMDS_GUIDE.md`
- `docs/AGENT_TRAVERSAL_GUIDE.md`

## Module map

| Module | Contents |
|---|---|
| `query-api` | Query contracts and common processing: `SearchRequest`, `SearchResponse`, `QueryMetadata`, `ColumnMetadata`, `AbstractSearchServiceImpl` |
| `chenile-query-service` | Spring + MyBatis runtime: `QueryConfiguration`, `NamedQueryServiceSpringMybatisImpl` |
| `chenile-query-controller` | HTTP `POST /q/{queryName}` (`QueryController`) |
| `query-mcp` | `POST /mcp/q/{queryName}` |
| `workflow-api` | `StateEntityService`, DTOs (`StateEntityServiceResponse`, `MinimalPayload`) |
| `workflow-service` | Generic STM workflow runtime; the `stmcmds` package |
| `workflow-info` | Introspection support (state diagram, allowed actions, JSON, test cases) |
| `workflow-mcp` | `ProcessIdPolymorph`, so the base runtime has no chenile-mcp dependency |
| `workflow-utils` | CLI, visualization, test-case tooling |
| `cucumber-workflow-utils` | BDD helpers for enablement and activities |
| `stm-generate-puml` | Maven plugin that generates PlantUML from workflow XML |

## Query runtime

- **Wiring:**
  - Mappers and definitions are loaded from `query.mapperFiles` and `query.definitionFiles`.
  - `QueryMetadata` drives what may be filtered and sorted.
  - Column flags are `filterable`, `sortable`, `likeQuery`, `containsQuery` and `betweenQuery`; `columnType` is Text/Number/Date/DateTime/DropDown/CheckBox; there are also `dropDownValues`/`dropDownQuery`, `display`, `customRender` and `group`.
  - Query-level fields are `paginated`, `sortable`, `acls`, `workflowName`, `flowColumn` (default flowId), `stateColumn` (default stateId), `toDoList`, `lateColumn` and `tendingLateColumn`.
- **Workflow actions on rows:** with `workflowName` set, each `ResponseRow { row, allowedActions }` is decorated with the allowed workflow actions for that row's state.
- **Pagination:** paginated queries need an `<id>-count` select and must include `${pagination}`.
- **Read in order:**
  1. `SearchRequest.java`
  2. `QueryMetadata.java`
  3. `AbstractSearchServiceImpl.java`
  4. `QueryConfiguration.java`
  5. `NamedQueryServiceSpringMybatisImpl.java`
  6. `QueryController.java`

## Workflow runtime: the `stmcmds` system

The flow of one event, `PATCH /{svc}/{id}/{eventID}`:

1. `StmBodyTypeSelector` chooses the payload type. An explicit `bodyType` in event metadata wins; otherwise it reflects on the second parameter of the resolved action's `transitionTo(...)`.
2. The STM runs the transition, starting with `BaseTransitionAction`. It dispatches, in order, to:
   1. a metadata `command` bean;
   2. an `orchExecutor` bean;
   3. `orchestratedCommandsConfiguration` XML;
   4. otherwise the bean found by `STMTransitionActionResolver`.
3. The resolved action is typically an `AbstractSTMTransitionAction<E,P>`.
4. Secondary actions run next: `SecondSTMTransitionAction` beans registered in `MultipleCommandsRegistry` with an order index.
5. `GenericEntryAction` sets state-entry time and SLA fields, stores the entity through `EntityStore`, and calls the `PostSaveHook`. `DefaultPostSaveHook` resolves a state-specific hook by convention.
6. Auto-states are computed by `DefaultAutomaticStateComputation`.
7. The response is `StateEntityServiceResponse{mutatedEntity, allowedActionsAndMetadata}`. Each entry is `{"allowedAction": …}` plus every `meta-*` attribute on the transition, with the prefix stripped (from `STMActionsInfoProvider`; the `meta-` handling is in `XmlFlowReader.META_PREFIX`).

**Naming convention** (`prefix` = the workflow prefix; with `useSuffix`):

| Bean | With suffix | Without suffix |
|---|---|---|
| Transition action | `prefix+Cap(eventId)+"Action"` (e.g. `issueAssignAction`) | `issueAssign` |
| Post-save hook | `prefix+Cap(stateId)+"PostSaveHook"` | `prefix+Cap(stateId)` |
| Auto-state | `prefix+Cap(stateId)+"AutoState"` | `prefix+Cap(stateId)` |

Context-sensitive prefixes come from `ContextContainer` headers, giving tenant/client overrides and trajectories.

**Other classes:**
- `GenericRetrievalStrategy`: loads the entity by id.
- `StmAuthoritiesBuilder`: event → authorities, from `meta-acls`, with a fallback derived from the service and event. Generated controllers reference it as `<svc>EventAuthoritiesSupplier`.
- `ProcessIdPolymorph` (in workflow-mcp): exposes per-event payload variants to MCP.

**`stmcmds` read order:**
1. `STMTransitionActionResolver`
2. `BaseTransitionAction`
3. `AbstractSTMTransitionAction`
4. `StmBodyTypeSelector`
5. `GenericEntryAction`
6. `DefaultPostSaveHook`
7. `DefaultAutomaticStateComputation`

## Conventions to preserve

- Don't break the `STMTransitionActionResolver` naming. Names are part of the contract.
- When changing `StmBodyTypeSelector`, check every `getConfigs()` consumer.
- When changing workflow wiring, check the runtime **and** `chenile-gen/jgen/bp-wfservice` / `bp-wfcustom` (github.com/rajakolluru/chenile-gen) (controllers, configuration, states XML, PlantUML setup).
- When changing query config keys, check the `bp-mybatisQuery` templates.
- Prefer explaining end-to-end flow over describing one class in isolation.

## Verification

```bash
mvn -pl workflow-service -am -DskipTests compile
rg -n "STMTransitionActionResolver|StmBodyTypeSelector|getConfigs\(|query\.mapperFiles|query\.definitionFiles" .
```

The public write-up is https://chenile.org/developer/workflow-internals/.


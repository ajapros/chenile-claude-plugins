---
name: "chenile-jgen"
description: "User guide for JGen (chenile-gen), the Chenile code generator, versioned separately from Chenile (JGen 2.5.x, org.chenile.jgen, built only on released Chenile): its 14 blueprints, template markup (Mustache, Pebble .peb, __key__, _DoT_, %%key=value%%, .filelist, %{{child}}), hooks in Java or sandboxed JavaScript, extensions (engines, language packs, path tags, requires), Git repos, composable and aggregated blueprints, input validation, records and jgen -r, GitHub blueprints, catalogs, install and release. Use when asked to generate a Chenile service, workflow, query, monolith, ecosystem or process deployment, run, install or release jgen, or author, extend or publish a blueprint."
---


# JGen: generating Chenile applications (and anything else that is text)

JGen is a pure-Java code generator driven by blueprints.

- **Source:** github.com/rajakolluru/chenile-gen. The generator lives under `chenile-gen/jgen`:
  - `jgen-base`: the engine;
  - `jgen-cli`: the command line;
  - `jgen-ext-pebble`: the Pebble template engine extension (2.5.1);
  - `bp-*`: the blueprint plugins.
  - stm-cli is **not** here any more: it is its own repo (github.com/ajapros/stm-cli, version 1.0.0, `org.chenile.stmcli.StmCli`, built on released `org.chenile:workflow-utils`), released by its own JReleaser workflow into the same tap (`brew install ajapros/jgen-tap/stm-cli`).
- **What it is not:** it generates application code; it is not the runtime.
- **Do not use app-gen / gen.sh.** It is deprecated; always use jgen.
- **Versions:** JGen has its own version line and cadence, separate from Chenile (decided 2026-11-01). JGen 2.1.35 was the last release that shared Chenile's number. `main` is **JGen 2.5.1** in development; features marked (2.5.1) are not in 2.1.35.
  - **Released Chenile only:** JGen builds against a *released* `chenile-parent` (2.1.35), the parent of `jgen/pom.xml`. `<revision>` in that pom (2.5.1) is JGen's own version, and `jgen.version` follows it. The release builds with `-Drevision=<tag>`.
  - **Target Chenile:** generated projects target `config.json` `chenileVersion`, which is the latest *released* Chenile (2.1.35). Blueprints needing a newer runtime use `sinceVersion`. Never point either at an unreleased Chenile.
  - **CI guard:** `.github/workflows/build.yml` builds from Maven Central only (`-Dmaven.repo.local=$RUNNER_TEMP/m2`) and checks that the parent isn't a SNAPSHOT and that `chenileVersion`'s `chenile-parent` exists on Central.
  - **Coordinates:** groupId `org.chenile.jgen` for every JGen module (Java packages unchanged). Only the parent pom, `jgen-base` and `jgen-ext-pebble` go to Maven Central: `make -C jgen deploy-central version=<v> passphrase=…` (`-pl jgen-base,jgen-ext-pebble -am -DperformRelease=true deploy`). Standalone blueprints depend on `org.chenile.jgen:jgen-base:${jgen.version}`, where `jgenVersion` comes from `JgenVersion.current()`.
  - **Version display:** `jgen --version` (`org.chenile.jgen.cli.VersionProvider`) prints the JGen version, the default target Chenile, and the Chenile it was built with (`cli-version.txt` / `jgen-version.properties`, filtered `@revision@` / `@chenile.version@`).
  - **Release notes and compatibility table:** https://jgen.chenile.org/releases/. chenile.org release notes only link to them.
- **Documentation:**
  - the docs site is https://jgen.chenile.org;
  - the manual page is `man jgen`, with source `jgen/jgen-cli/src/man/jgen.1.md`;
  - design notes are in `jgen/docs/`.

## Install and the safest flow

Install it without a build:

```bash
brew install ajapros/jgen-tap/jgen                  # macOS/Linux; also installs the man page and completions
jbang app install jgen@rajakolluru/chenile-gen      # any OS; JBang fetches Java if needed
```

Alternatively, download `jgen-<version>.zip` from the GitHub releases. It contains `bin/jgen`, `lib/jgen-cli.jar`, `blueprints/`, `man/` and `completions/`.

To build from source (needed only to work on JGen itself): `make clean all && source setpath.sh`. This puts `jgen.sh` on the PATH.

```bash
jgen -e myconfig                              # optional: emit config (com/company/org/chenileVersion) to ./config
jgen -g <blueprint> -o input.json             # write a sample input contract
# or: jgen -g <blueprint> -e <folder>         # input-file.json plus companion spec files
# edit input.json (and any companion spec files)
jgen -f input.json                            # generate (output defaults to ./output)
```

Prefer `-g` then `-f` over guessing fields. Running `jgen` with no mode option is interactive.

**CLI options:**

| Option | Purpose |
|---|---|
| `-c` | config file |
| `-e` | emit config; with `-g`, a folder for the input and companion files |
| `-f` | generate from an input file |
| `-g` | emit a sample input for a blueprint |
| `-o` | output file for `-g` |
| `-r <project>` | regenerate a project (with `--into <folder>` and `--blueprint <ref>`) |
| `--fetch <ref>` | fetch, verify and cache a blueprint |
| `--search [text]` | search the blueprint catalogs (2.5.1) |
| `--extensions` | list installed template engines, language packs (rules, helpers), path tags and helpers (2.5.1) |
| `--trust` | trust new blueprint sources for this run |
| `--offline` | use only installed and cached blueprints and catalogs |
| `--completion bash\|zsh\|fish` | print a completion script |
| `-h`, `-V` | help, version |

**Generated projects:** build with `mvn install` (or `make build`). Monoliths run with `make run` on port 8080.

**Shell completion:** Homebrew installs it. Otherwise:
- bash and zsh: `source <(jgen --completion bash)` (or `zsh`);
- fish: `jgen --completion fish > ~/.config/fish/completions/jgen.fish`.

Completion offers installed blueprints, names from cached catalogs, cached `github:` references, and the `github:` and `dir:` prefixes. The list is cached in `~/.cache/jgen/blueprint-names`.

## Blueprints (14)

Values are the names used with `-g` and in the `blueprint` field of an input file. Wherever a name is accepted, you can also use:
- a catalog name: `name`, `name@version` or `catalog/name`;
- a `github:owner/repo[@version]` reference;
- a `dir:<folder>` reference.

See "Blueprints from the web" and "Catalogs".

**`chenile-service`**
- Prompts: `service`, `serviceVersion`, `destFolder`, `security` (n), `jpa` (y), `cloudSwitchEnabled` (n), `enableMCP` (n).
- Generates `<svc>-api` and `<svc>-service`: controller, impl, configuration, health checker, error codes, BDD tests and `scripts/curl-scripts.sh`.
- Endpoints: `POST /<svc>`, `GET /<svc>/{id}`, `POST /<svc>/op1`.

**`chenile-headless-service`** (2.1.31)
- Prompts: `service`, `serviceVersion`, `destFolder`, `registerInServiceRegistry` (y).
- A non-HTTP service: `@ChenileController` + `@ChenileOperation` + `@ChenileBody` on a plain bean, with no chenile-http.

**`chenile-ecosystem`** (2.1.31)
- Prompts: `ecosystem`, `ecosystemVersion`, `destFolder`, `service` (`${ecosystem}Service`), `monolith` (`${ecosystem}Monolith`), `security` (n), `jpa` (y).
- Optional add-ons: `includeServiceRegistry` (+ `serviceRegistryMonolith`, `serviceRegistryUrl`), `includeCconfig`, `includeHeadlessService`, `includeQueryService`.
- Composes the service, mini-monolith, registry, cconfig, headless and query blueprints under an enclosing Maven reactor parent. It is an aggregated blueprint (see below).

**`wfservice`**
- Prompts: `service`, `serviceVersion`, `destFolder`, `activity`, `enablement`, `jpa`, `cloudSwitchEnabled`, `security`, `enableMCP`.
- A workflow service OPENED→ASSIGNED→RESOLVED→CLOSED. With `activity`, mandatory activities lead to ARCHIVED.
- Generates the states XML, actions, entity store and the `<Svc>StateEntityInfoController`.
- Endpoints: `POST /<svc>`, `GET /<svc>/{id}`, `PATCH /<svc>/{id}/{eventID}`.
- Info endpoints: `/<svc>/info/state-diagram|allowed-actions|json|test-cases|test-visualization|test-state-diagrams`.

**`wfcustom`**: the same as wfservice, but from your own states XML (`xmlFile`). This is the Finito blueprint.

**`mybatisQuery`**
- Prompts: `namespace`, `namespaceVersion`, `destFolder`, `security`.
- Generates `mapper/<ns>.xml` (with the `getAll-count` query and `${pagination}`) and `mapper/<ns>.json`.
- Served at `POST /q/<name>` by `chenile-query-controller`.

**`minimonolith`**
- Prompts: `monolith`, `monolithVersion`, `destFolder`, `jpa`, `cloudSwitchEnabled`, `security`, `enableMCP` (+ `mcpServerName`, `mcpInstructions`), `enableServiceRegistry`, `enableServiceRegistryDelegate` (+ `serviceRegistryUrl`), `dependencies[]`, `enableQueryController`, `enableH2Console`.
- `application.yml` points Keycloak at localhost:8180 (client `authz-servlet`). MCP is served at `/mcp`.
- Reused as a child by `chenile-ecosystem` and `chenile-process-management` to produce runnable hosts.

**`chenile-interceptor`**
- Prompts: `interceptorName`, `interceptorVersion`, `destFolder`.
- Scaffolds a `BaseChenileInterceptor` policy.

**`batch`**
- Prompts: `batch`, `batchVersion`, `destFolder`, `batchJson`.
- Generates a batch process against **process-delegate**, using `KafkaBaseTest`.
- Legacy-ish: prefer `chenile-process-management` for new work.

**`chenile-process-workers`** (2.1.32): **one worker JAR for one process definition.**
- Prompts: `workerModule`, `application`, `applicationVersion`, `packageName`, `processType`, `name`, `inputType`, `leaf` (y), `children[]` (RECORD_ARRAY of `name`/`inputType`), `destFolder`, `super_pom`, `dependencies`.
- A **leaf** type gets an **executor**; a **non-leaf** type gets a **splitter + aggregator** in the same JAR.
- It is a plain JAR with no Spring host. Its payload model comes from the application's API JAR.
- Generated workers (2.1.35) extend the typed listener bases from process-delegate:
  - `ExecutorWorkListener<In,Out>` and `SplitterWorkListener<In,Object>` implement `doStart(WorkListenerInput<In>)`;
  - `AggregatorWorkListener<In,Out,ChildOut>` is a per-child fold, `doStart(out, input, childOutput, child)`, building an `AggregatedResult`.
- The hooks **return defaults**; they are application code to fill in.
- Worker **bean names are routing keys**: `<processType>Executor|Splitter|Aggregator`.
- Normally invoked once per definition by `chenile-process-worker-set`, not directly.

**`chenile-process-worker-set`** (2.1.34)
- Takes a prepared process-definition set and **expands it into per-definition worker modules**, invoking `chenile-process-workers` once per process type.
- It owns the iteration and the validation of the process definitions.
- Rarely run on its own: `chenile-process-management` invokes it through `%{{chenile-process-worker-set}}`.

**`chenile-process-management`** (2.1.32+): the deployment generator.

It generates a **process server + worker mini-monolith deployment**, plus per-definition worker JARs and an optional service-registry host, from native `processMap` definitions. It composes `minimonolith` and `chenile-process-worker-set`. Guide: `bp-process-management/README.md`.

Inputs:

| Input | Meaning |
|---|---|
| `application`, `applicationVersion`, `destFolder` | the project |
| `processSpec` | FILE, native processMap |
| `cronSpec` | optional FILE of cron schedules |
| `definitionSource` | `json` or `database` |
| `registryMode` | `create` or `existing`; `existingRegistryUrl` when `existing` |
| `registryPlacement` | `server` (recommended) or `separate`; only when `create` |
| `serverDeploymentUrl`, `workerDeploymentUrl`, `registryDeploymentUrl` | ports 8000, 8001 and 8002 |
| `transport` | `kafka` (the only one) |
| `workTopic` | default `${application}-work` |
| `super_pom`, `dependencies` | added to the server-service JAR |

Generated modules:

- **`<app>-api`:** typed payloads and process-start contracts.
- **`<app>-server-config`:** native definitions and cron seeds.
- **`<app>-server-service`:** typed HTTP services, process bootstrap and runtime services. Worker dispatch goes only through the durable outbox. It acknowledges Kafka publication and has no separate publisher.
- **`<app>-<processType>-workers`:** one plain JAR per definition.
- **`<app>-worker-listener`:** a headless `ProcessWorkListener`. It is an `@ChenileController("processWork")` with `serviceSelector="processWorkServiceSelector"` and `@BodyTypeSelector("processWorkBodyTypeSelector")`, subscribed to the work topic.
  - The selector routes each message to the worker bean named by its `processType`/`workerType` headers.
  - A worker's exception becomes a `...WithErrors` event.
  - Callback and malformed-delivery failures get Kafka retries, then the `.DLT` topic.
- **`<app>Server` and `<app>Worker`:** `minimonolith` hosts. The server uses exactly one queue-based starter.
- **`<app>Registry`:** only when `registryPlacement=separate`.

Examples are in `bp-process-management/examples`. Generated tests extend `KafkaBaseTest`, so **Docker must be running** for `mvn install`. The reference implementation is `chenile-samples/p1`.

**`it`**
- Prompts: `app`, `appVersion`, `entity`, `destFolder`, `security`.
- An integration-test project using `it-cucumber-utils`.

**`jgen-blueprint`** (the meta-blueprint) writes a new blueprint. Its hook is Java; a blueprint can instead use JavaScript hooks (see "Hooks").

Prompts:

| Prompt | Notes |
|---|---|
| `blueprintName` | |
| `destFolder` | |
| `standaloneRepo` | default n (2.5.1) |
| `groupId`, `blueprintVersion`, `githubRepository` | only when `standaloneRepo` is y; `githubRepository` is optional and validated by `GITHUB_REPOSITORY` |
| `security`, `jpa`, `cloudSwitchEnabled` | |
| `super_pom`, `dependencies` | |

Output is `bp-<name>/`:

- **Always:** a working blueprint containing:
  - `META-INF/blueprint.json`, with inputs `projectName` (PROJECT_NAME), `projectVersion`, `destFolder`, `includeExtras`;
  - a starter template, `<name>-template/__projectName__/README.md.mustache` plus a `%%includeExtras=true%%/` folder;
  - an init hook;
  - a test that generates from the blueprint.
- **`standaloneRepo=n`:** a module of the chenile-gen build, with `org.chenile.jgen:jgen` as its parent.
- **`standaloneRepo=y`:** a self-contained project:
  - a parentless pom with its own groupId and `${revision}` version, Java 25, `org.chenile.jgen:jgen-base` (the generating JGen's version) as `provided`, and JUnit;
  - a README, `.gitignore` and `.github/workflows/release.yml` (on a pushed tag it builds with `-Drevision=<tag>` and attaches the jar to a GitHub release);
  - it is a **local Git repository on `main` with one commit** that includes `.jgen/`. This uses the engine's Git support: the hook sets `initGit` from `standaloneRepo`, and `blueprint.json` declares `"gitRepositoryField": "githubRepository"`, so a given repository becomes `origin`.

  JGen prints the next steps (create the GitHub repo, push), and the blueprint's `finalHook` adds the release step (tag and push the tag).

A blueprint without a Java init hook (JavaScript hooks are fine) doesn't need this module structure at all. It can be published template-only (see below).

## Template markup

Every blueprint gets this markup from the shared pipeline:

- **Template engines** (2.5.1) are picked by file extension, and the extension is removed:
  - **Mustache** renders `.mustache` (built in). Use `{{{x}}}` to avoid HTML escaping.
  - **Pebble** renders `.peb` (Twig/Jinja syntax; module `jgen-ext-pebble`, shipped with the CLI and portal). No escaping, missing values render empty, no `include`/`extends`.
  - Files with neither extension are copied as they are. One blueprint can mix engines.
- **Template helpers** (2.5.1): `capitalize`, `uncapitalize`, `camelCase`, `pascalCase`, `snakeCase`, `upperSnakeCase`, `kebabCase`, plus any language pack's. Words split at spaces, `-`, `_` and case changes (`HTTPServer` → `http_server`). Mustache: `{{#snakeCase}}{{entity}}{{/snakeCase}}`; Pebble: `{{ entity | snakeCase }}`; JS hooks: `jgen.snakeCase(x)` or `jgen.helper(name, x)`. Code: `NameCase`.
- **`.filelist`** files are split on `--START--name` / `--END--`. A `.filelist.mustache` is rendered first, then split.
- **`__key__`** in file and folder names is replaced from the map (`__service__`, `__Service__`, `__com__`, …). `__key:-default__` is supported.
- **`_DoT_`** (2.5.1) in file and folder names becomes a dot. `_DoT_gitignore` becomes `.gitignore`; `_DoT_github/workflows/ci.yml` becomes `.github/workflows/ci.yml`. It runs right after `__key__` (the `dot` path tag), so `__service___DoT_properties` becomes `orders.properties`. Use it for every dotfile, because Maven leaves dotfiles out of blueprint jars.
- **`%%key=value%%`** folders are kept, with their contents promoted, only when the input matches.
- **`%{{blueprint attr=v}}`** empty folders expand a child blueprint (see "Aggregated blueprints").

**Path tags** (2.5.1): `.filelist`, `__key__`, `_DoT_` and `%%key=value%%` are built-in `PathTag`s (`org.chenile.jgen.template.tags`), applied one pass per tag by the single `path-tag-processor` step, in `order`: `filelist` 100, `placeholder` 200, `dot` 300, `conditional` 400. Extension jars can add tags (see "Extensions"). Tags never see `%{{…}}` markers. A conditional folder's sub-folder that already exists in the parent is merged (2.5.1). The old step classes (`FileSplitter`, `FileNameReplacer`, `DotReplacer`, `ConditionalProcessor`) remain, deprecated, delegating to the tags.

**Pipeline order** (`jgen-base/.../template/processors.xml`):

1. `config-defaulter`
2. `version-validator`
3. `generic-input-validator`, then `input-snapshot`
4. `post-input-executor`
5. `folder-copier`
6. `lambda-loader` (puts the template helpers in the map for Mustache)
7. `file-template-executor` (renders with the engine each file's extension selects)
8. `path-tag-processor` (steps 8–10): tags `filelist` (8), `placeholder` (9), `dot` (9a), `conditional` (10), plus added tags by `order`
11. `blueprint-expander`
12. `post-process-executor`
13. `provenance-writer`
14. `git-initializer`
15. `final-executor`

## Hooks (optional; Java via the blueprint's `InitHook`, or JavaScript)

- **`InitHook.init(BlueprintConfig)`:** runs once, when the blueprint loads. It registers the other hooks and any sample-input emitters.
- **`postInputCaptureHook`:** runs after validation and before any file is written. It augments the input map, e.g. with derived names or a parsed input file.
- **`childBlueprintInputs`:** computes a child blueprint's input map from the parent's map and the marker's attributes.
- **`postProcessHook`:** runs after generation. It changes the generated files.
- **`finalHook`** (2.5.1): runs last, for top-level generations only, after the generation record and the Git step. It is for work outside the file tree, such as printing next steps; files it changes are not in the initial commit. It can read `gitInitialised`, `gitCommitted` and `gitRemote` from the map.

**JavaScript hooks (2.5.1).** `"scripts": {"postInputCapture": "scripts/hooks.js", "postProcess": "scripts/hooks.js"}` in `blueprint.json` maps hook names (`postInputCapture`, `childBlueprintInputs`, `postProcess`, `final`) to script resources; each file must define a function of that name:
- `postInputCapture(inputs, jgen)` returns an object merged into the inputs;
- `childBlueprintInputs(inputs, child, attributes, jgen)` returns the child's inputs (Java and script can't both define it);
- `postProcess(inputs, project, jgen)` and `final(inputs, project, jgen)`.

Inputs and results are JSON. `jgen` (`ScriptApi`) has the template helpers, `log`, and `readInput(field)` for declared FILE inputs. `project` (`ScriptProject`) has `name`, `exists`, `read`, `write`, `move`, `delete`, `list` and `copyInput`, confined to the generated folder.

Scripts run in GraalJS (polyglot + js-community 25.0.4, property `graalvm.version`) in a sandbox: only `@HostAccess.Export` methods; no Java class lookup, I/O, network, processes, threads, native code or environment; a 50M statement limit; a fresh context per call. They compile when the blueprint loads (syntax errors and missing functions fail it), and run after a Java hook of the same kind. A blueprint whose hooks are all scripts stays template-only. Code: `org.chenile.jgen.script.ScriptHooks`, installed from `Registry.load`. Docs: https://jgen.chenile.org/scripting/

Validate input formats with declared rules (below), not in hooks: hook errors come after the collect-all validation and are not visible to the portal.

## Extensions (2.5.1)

Three extension points, all registered in `org.chenile.jgen.ext.Extensions` and found with `ServiceLoader` on JGen's class path. Installing one means dropping its jar in a blueprints folder. Extensions compile against `org.chenile.jgen:jgen-base` (provided, same version as the JGen they run in).

| Kind | Interface | Built in |
|---|---|---|
| Template engine | `org.chenile.jgen.ext.TemplateEngine` (`name`, `extension`, `render`) | `mustache`; `pebble` ships in `jgen-ext-pebble` |
| Language pack | `org.chenile.jgen.ext.LanguagePack` (`name`, `rules()`, `helpers()`); rules via `ValidationRule.of(name, description, regex, extraCheck)` | `python`, `node` |
| Path tag | `org.chenile.jgen.template.tags.PathTag` (`name`, `order`, `depthFirst`, `matches`, `process`) | `filelist`, `placeholder`, `dot`, `conditional` |

Each is listed in `META-INF/services/<interface name>`.

- **Safety rules:** names are unique across all kinds, so built-ins can't be replaced; engines can't share a file extension; packs can't redefine a built-in rule (a `ValidationType` name) or an existing helper.
- **`requires`** in `blueprint.json`: `["pebble", "python", "terraform@1.2"]` (`kind:name` is accepted). It is checked in `Registry.load` before the fields are read, so a missing pack is reported as missing. Minimum versions compare with the jar's `Implementation-Version` (Maven `ComparableVersion`); an unversioned jar passes. Extension poms should set `addDefaultImplementationEntries`.
- **Records:** the generation record's `extensions` field lists the added (not built-in) extensions the project depended on, as `kind:name@version`: all added path tags, added engines that rendered files (`TemplateContext.enginesUsed`, shared with children), packs whose rules the blueprint uses, and its requires. `jgen -r` refuses without them (`Regenerator.requireRecordedExtensions`).
- **Testing:** `Extensions.register(obj)` and `Extensions.reset()`.

Docs: https://jgen.chenile.org/extensions/

## Generated Git repositories (2.5.1)

Any blueprint can have JGen make its output a local Git repository, with no code. It runs in the `git-initializer` step, for top-level generations only.

- **Turning it on:** `initGit` = `true` in the input map, either as a BOOLEAN input or set by a hook. JGen then runs `git init`, sets the branch to `main`, adds everything (including `.jgen/`) and makes one commit. `gitCommitMessage` in `blueprint.json` can set the message, with `${input}` placeholders.
- **No repository field:** without a `gitRepositoryField`, or when its input is empty, you get a local repository only, plus a hint for adding a remote.
- **Connecting to GitHub:** with `"gitRepositoryField": "<input name>"` in `blueprint.json` and a value in that input, the value becomes the `origin` remote, and JGen prints "create the repo on GitHub, then push -u origin main". The field must have validation `GITHUB_REPOSITORY`; this is checked when the blueprint loads.
- **Remote style:** `gitRemoteProtocol` in the JGen config, `ssh` (default) or `https`.
- **What it never does:** set a commit author, create the GitHub repository, or push. If Git is missing or has no identity, the project is still generated, and JGen prints the commands to finish by hand.
- **Code:** `GitInitializer` (pipeline) and `GitRepository` (`jgen-base/util`).

## Composable blueprints (super_pom + dependencies)

**Every** built-in blueprint accepts two optional inputs:

- `super_pom` (`SuperPOM`): `groupId`, `artifactId`, `version`, and `relativePath`, which defaults to `../pom.xml`;
- `dependencies` (`POM_Dependencies`): an array of `groupId`, `artifactId` and optional `version`.

The parent changes only in the **outermost** generated POM. See `jgen/docs/composable-blueprints.md`.

## Aggregated blueprints (one blueprint invokes others)

Empty marker folders in the template tree include other blueprints. An empty `.gitkeep` is allowed inside them.

```
%{{minimonolith role=server}}/
%{{chenile-process-worker-set}}/
```

How a marker is resolved:

- The first token is the registered blueprint name.
- The `key=value` attributes are passed to the parent's **`childBlueprintInputs`** callback, which computes the child's input map.
- The child then runs its own defaults, validation, hooks and pipeline.

The built-in aggregates are `chenile-process-management`, `chenile-process-worker-set` and `chenile-ecosystem`. Child blueprints are looked up among installed blueprints (or the same jar), not in catalogs. See `jgen/docs/aggregated-blueprints.md`.

## Input validation

**inputFields** declare:

- `name` and `type`. Types: `STRING`, `BOOLEAN`, `NUMBER`, `DATE`, `FILE`, `DROPDOWN` + `validValues`, `MULTI_SELECT`, `RECORD_ARRAY` + `childFields`, `SuperPOM`, `POM_Dependencies`.
- `defaultValue` (supports `${config}` substitution) and `required`.
- a `validation` rule. The rules are:
  - `JAVA_IDENTIFIER`, `JAVA_TYPE`, `JAVA_PACKAGE`, `PROJECT_NAME`, `VERSION`, `HTTP_URL`, `KAFKA_TOPIC`;
  - `GITHUB_REPOSITORY` (2.5.1): `owner/repo`; the owner is at most 39 letters, digits or single hyphens and cannot start or end with a hyphen; the repo is 1-100 of `[A-Za-z0-9._-]` and not `.` or `..`;
  - `PATTERN` (2.5.1): uses the field's own `pattern` (a Java regex that must match the **whole** value) and a mandatory `patternMessage`, which is the error text, e.g. "must look like ABC-123".
  - language pack rules (2.5.1), named the same way: `PYTHON_MODULE`, `PYTHON_PACKAGE`, `PYPI_PROJECT` (python), `NPM_PACKAGE`, `JS_IDENTIFIER` (node), or an added pack's. Internally the field gets `validation = EXTENSION` and `rule = <name>`; JSON reads and writes the rule's own name. A name that is neither built in nor an installed pack's rule fails as soon as the field is read.
- `visibleWhen`.

How the rules behave:

- `PATTERN` declarations are checked when the blueprint loads (`InputValidation.checkDeclarations`). A missing pattern or message, an invalid regex, or a `pattern` on a field whose rule isn't `PATTERN` is an error. The same check verifies that a `gitRepositoryField` names a `GITHUB_REPOSITORY` field.
- Prefer a named rule. Use `PATTERN` only for a format unique to one blueprint; promote it to a named rule in `jgen-base` if several blueprints need it.
- A new built-in rule means extending `ValidationType`, `InputValidation.validate` and `InputValidation.describe`. A rule for another language belongs in a language pack instead.
- Every rule's error message says what a valid value looks like.

**`BlueprintPayloadValidator`** (`jgen-base`, 2.1.35) is the single, collect-all validator. Every path uses it: `-f`, the portal, `buildInputMap` and composed children.

- It checks:
  - JSON syntax (including duplicate keys);
  - that required, visible fields are present;
  - types and shapes;
  - the declared rules, including nested ones;
  - the generic inputs (`com`/`company`/`org`, project name, `*Version`, registry URL).
- It returns `PayloadIssue{path, code, message}` objects. The codes are `INVALID_JSON`, `NOT_AN_OBJECT`, `REQUIRED`, `INVALID_VALUE`, `INVALID_INPUT`, and the warnings `UNKNOWN_FIELD` and `NOT_VISIBLE`.
- It never touches the filesystem. The check that the destination folder doesn't exist, and that FILE inputs exist, stays at the generation boundary.

`sinceVersion` is checked against the configured `chenileVersion` before anything is written. See `jgen/docs/input-validation.md`.

## Generation records and regeneration (2.1.35)

Every top-level generation writes `<project>/.jgen/generation.json`. It holds:

- the blueprint: name, version, jar coordinates, and the exact `github:` or `dir:` reference and sha256 if it was fetched (never a catalog short name);
- the JGen version (`JgenVersion.current()`);
- the config;
- the validated inputs, captured before hooks run, with copies of FILE inputs;
- the sha256 of every generated file;
- (2.5.1) `extensions`: the added extensions the generation depended on (see "Extensions").

Disable it with `-Djgen.record=false`.

`jgen -r <project> [--into dir] [--blueprint <ref>]` regenerates the project into a separate folder and classifies each file. The original project is never touched; merging is left to git or an agent. The classes are:

| Class | Meaning |
|---|---|
| `SAFE_UPDATE` | changed by the blueprint only |
| `KEEP_USER` | changed by the user only |
| `CONFLICT` | changed on both sides |
| `NEW_FILE` | new in the blueprint |
| `SAFE_DELETE` | dropped by the blueprint, unchanged by the user |
| `DELETE_CONFLICT` | dropped by the blueprint, changed by the user |
| `USER_DELETED` | deleted by the user, still generated |

It writes the classification to `<project>.regeneration.json`. A recorded `github:` reference is re-fetched pinned to its hash; a `dir:` reference is not pinned. See `jgen/docs/regeneration.md`.

## Blueprints from the web (2.1.35)

**References:** `github:owner/repo[/name][@version][#sha256:<hex>]`. If the release carries a blueprint jar (exactly one, or exactly one named `<repo>-*.jar`), JGen uses it. Installed blueprints always win, and a clashing name is refused.

**Template-only blueprints (2.5.1):** a blueprint with no `initHook` needs no jar.
- **Layout:** the repository is laid out like a jar's resources: `src/main/resources/META-INF/blueprint.json` plus the template folder.
- **From GitHub:** for `github:owner/repo@tag`, if the release has no jar, or the tag has no release, JGen downloads the source archive (zipball) at that tag. Without a version it uses the latest release, or else the highest version tag.
- **Trust and hashes:** the same trust prompt and lock as jars. The SHA-256 is a content hash over the resources files, so it is stable if GitHub re-packs the tag.
- **Java hooks refused:** an `initHook` in the descriptor is an error. JavaScript hooks (`scripts`) are allowed.
- **Local folders:** `dir:<folder>` (the repo or its `src/main/resources`) is for authoring. It is not cached, locked or trust-checked.
- **Code:** `TemplateOnlyBlueprints` and `Registry.loadTemplateOnly`.

**Trust:**
- `~/.jgen/settings.json` holds `trustedSources`. The default is `github:ajapros/*` and `github:rajakolluru/*`.
- Any other source is prompted (once or always). Non-interactive runs refuse unless `--trust` is given.
- `~/.jgen/blueprints.lock.json` pins each version's sha256 on first use.

**Storage and isolation:**
- The cache is `~/.jgen/cache/github/<owner>/<repo>/<version>/`: a `.jar`, or a `.zip` plus its extracted `source/`.
- Each fetched blueprint gets its own class loader (`Registry.loadJar` / `loadTemplateOnly`).
- `JGEN_HOME_DIR` relocates `~/.jgen`; `GITHUB_TOKEN` raises the rate limit.

**Local blueprint jars:** drop them into `~/.jgen/blueprints`, `$JGEN_HOME/blueprints` or `$JGEN_BLUEPRINTS`. They are picked up with no rebuild, because the jar uses Spring Boot's ZIP layout, whose launcher reads extra folders from `loader.path`. Extension jars go in the same folders.

See `jgen/docs/remote-blueprints.md`. Maven references and signature checks are planned phases.

## Catalogs (2.5.1)

Catalogs let people use blueprints by short name.

**Names.** `jgen -g terraform`, `terraform@1.2.0` or `acme/terraform`, where the prefix is a catalog's alias. A plain name without a version that matches an installed blueprint uses it. Otherwise JGen searches the catalogs in order, and the first match wins. The entry's `github:` source is then fetched as above.

**Where catalogs come from.**
- **Official catalog:** `github:ajapros/jgen-catalog`. It is searched first, and the sources it lists are **trusted** without a prompt, so entries must be reviewed.
- **Team catalogs:** listed in `~/.jgen/settings.json` as `catalogs: [{source: "github:acme/jgen-catalog", alias: "acme", trusted: false}]`. The alias defaults to the owner. Their sources go through the normal prompt unless `trusted` is true. Set `officialCatalog: false` to skip the official one.

**Format.** `catalog.json` at the root of the repo's default branch:

```json
{"schema":"jgen.catalog/1","blueprints":{"terraform":{"source":"github:acme/jgen-terraform","description":"…","tags":["iac"],"versions":{"1.2.0":"<sha256>"},"blueprint":"<name inside a multi-blueprint jar>"}}}
```

Entries without a valid `github:` source are skipped with a warning. Version pins are enforced like `#sha256:`.

**Search and caching.**
- `jgen --search [text]` matches name, description or tags.
- Catalogs are cached for an hour in `~/.jgen/cache/catalogs/`, with a fallback to the cache when GitHub can't be reached; `--offline` uses only the cache.

**Code:** `Catalog`, `Catalogs`, and `BlueprintResolver.resolveName`.

**The official catalog's repository** is github.com/ajapros/jgen-catalog. It holds `catalog.json`, a README, `scripts/validate.py`, and a pull-request validation workflow.

Docs: https://jgen.chenile.org/catalogs/

## Dependencies and cross-repo notes

- Generated query projects depend on `chenile-query-controller`. Workflow projects depend on `workflow-api`/`workflow-service` and use `stm-generate-puml` for diagrams.
- `chenile-process-management`/`chenile-process-workers` generate against the runtime in github.com/ajapros/chenile-process-management. The generated worker listener needs chenile-core's `serviceSelector` (2.1.35+).
- Template-to-library mapping is in `chenile-query-workflow-blueprints/docs/GENERATOR_BLUEPRINT_MAPPING.md`. When workflow or query runtime conventions change, check `bp-wfservice`, `bp-wfcustom` and `bp-mybatisQuery`.
- Standalone blueprints with hooks, and extension jars, depend on `org.chenile.jgen:jgen-base` from Maven Central, so it must be published (`deploy-central`) with each JGen release.
- JGen uses `org.chenile.workflow.cli.CLIHelper`/`CLIParams` from workflow-utils (bp-wfcustom). Those stay in workflow-utils; only stm-cli's `main` moved out.

Public reference: https://jgen.chenile.org (manual at /manual/, releases at /releases/), https://chenile.org/developer/jgen-blueprints/ and https://chenile.org/get-started/.


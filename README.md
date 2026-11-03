# Chenile plugins for Claude

Claude skills for building with [Chenile](https://chenile.org), the Java / Spring Boot microservices framework, and
its code generator [JGen](https://jgen.chenile.org). With the plugin installed, Claude knows Chenile's
contracts, follows its house rules, and uses JGen blueprints instead of improvising.

| Skill | Use it for |
| --- | --- |
| `chenile-framework-knowledge` | Writing or reviewing Chenile code, and building UIs or clients against Chenile services. Covers the house rules, the REST and response contracts, headers, workflow and query APIs, security, messaging, cconfig and admin endpoints. |
| `chenile-jgen` | Generating services, workflows, queries, monoliths and process deployments with JGen, and writing or publishing blueprints. |
| `chenile-architecture` | Chenile internals: `ChenileExchange`, the interceptor pipeline, interpolations, service selection, and configuration-driven polymorphism. |
| `chenile-process-management` | Splitter/aggregator processes, workers, the durable outbox, triggers, cron, and the management API and UI. |
| `chenile-query-workflow-blueprints` | The query and workflow (Finito STM) runtime libraries, and how JGen's templates map onto them. |

**The house rules** (from `chenile-framework-knowledge`):
- always write Cucumber tests;
- reuse existing Chenile utilities;
- import classes instead of writing fully qualified names;
- create beans in `@Configuration` classes with `@Bean` methods, not with `@Component`;
- split complex services into `-api` and `-service` modules;
- look at the JGen blueprints for patterns first.

## Install

### Claude Code

```text
/plugin marketplace add ajapros/chenile-claude-plugins
/plugin install chenile@chenile-plugins
```

From a shell, the same is `claude plugin marketplace add ajapros/chenile-claude-plugins` followed by
`claude plugin install chenile@chenile-plugins`. Skills are then available as `/chenile:<skill>`, and Claude uses
them on its own when your work matches.

To get updates, run `/plugin marketplace update chenile-plugins`.

### claude.ai and Claude desktop

1. Download the skill zips from the latest release, or build them with `scripts/package-skills.sh`.
2. Upload each one under **Settings → Capabilities → Skills**.

An organization owner can instead provision them to everyone under **Organization settings → Skills**.

### Suggesting the plugin automatically inside an organization

The marketplace entry declares when the plugin is relevant:
- a `pom.xml` or Gradle build that depends on `org.chenile`;
- a JGen generation record or blueprint file being read;
- running `jgen` or `stm-cli`.

Claude Code then suggests installing the plugin, but only where an administrator has allowlisted the marketplace
in managed settings:

```json
{
  "extraKnownMarketplaces": {
    "chenile-plugins": { "source": { "source": "github", "repo": "ajapros/chenile-claude-plugins" } }
  },
  "pluginSuggestionMarketplaces": ["chenile-plugins"]
}
```

## Repository layout

```text
.claude-plugin/marketplace.json           the marketplace: one plugin, "chenile", with relevance signals
plugins/chenile/.claude-plugin/plugin.json   (and icon.png, the Chenile mark)
plugins/chenile/skills/<skill>/SKILL.md   the skills
scripts/check-skills.py                   frontmatter checks; refuses local paths and maintainer-only notes
scripts/package-skills.sh                 one zip per skill, for claude.ai
.github/workflows/validate.yml            runs both checks plus `claude plugin validate`
```

## Contributing

- Change a skill under `plugins/chenile/skills/`.
- Run `python3 scripts/check-skills.py` and `claude plugin validate .`.
- Bump `version` in `plugins/chenile/.claude-plugin/plugin.json`, so that installed copies update.
- Open a pull request.

Skills must not contain machine-specific paths or maintainer-only workflows; the check script enforces this.

## License

MIT

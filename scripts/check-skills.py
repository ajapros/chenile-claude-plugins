#!/usr/bin/env python3
"""Checks the published skills: frontmatter present and valid, description within limits, and no references to a
maintainer's machine (local paths, sandbox notes) that would mean nothing to other users."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORBIDDEN = [r"~/Documents/", r"/Users/", r"/sessions/", r"\bCowork\b", r"chenile-maintainer", r"\bsandbox git"]
problems = []
skills = sorted(ROOT.glob("plugins/*/skills/*/SKILL.md"))
if not skills:
    problems.append("no skills found under plugins/*/skills/*/SKILL.md")
for path in skills:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        problems.append(f"{rel}: missing frontmatter")
        continue
    front = match.group(1)
    name = re.search(r'^name:\s*"?([^"\n]+)"?', front, re.M)
    desc = re.search(r'^description:\s*"?(.+?)"?\s*$', front, re.M)
    if not name or name.group(1) != path.parent.name:
        problems.append(f"{rel}: frontmatter name must equal the folder name ({path.parent.name})")
    if not desc:
        problems.append(f"{rel}: missing description")
    elif len(desc.group(1)) > 1024:
        problems.append(f"{rel}: description is {len(desc.group(1))} characters; the limit is 1024")
    for pattern in FORBIDDEN:
        for line_no, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                problems.append(f"{rel}:{line_no}: local reference matches {pattern!r}: {line.strip()[:100]}")

plugin_root = ROOT / "plugins/chenile"
claude_manifest = plugin_root / ".claude-plugin/plugin.json"
codex_manifest = plugin_root / ".codex-plugin/plugin.json"
codex_marketplace = ROOT / ".agents/plugins/marketplace.json"

try:
    claude = json.loads(claude_manifest.read_text(encoding="utf-8"))
    codex = json.loads(codex_manifest.read_text(encoding="utf-8"))
    marketplace = json.loads(codex_marketplace.read_text(encoding="utf-8"))

    if codex.get("name") != claude.get("name"):
        problems.append("Codex and Claude plugin names must match")
    if codex.get("version") != claude.get("version"):
        problems.append("Codex and Claude plugin versions must match")
    skills_path = codex.get("skills")
    if skills_path != "./skills/" or not (plugin_root / "skills").is_dir():
        problems.append("Codex plugin must expose the canonical ./skills/ directory")
    if not codex.get("interface", {}).get("displayName"):
        problems.append("Codex plugin manifest must define interface.displayName")

    entries = [entry for entry in marketplace.get("plugins", []) if entry.get("name") == codex.get("name")]
    if len(entries) != 1:
        problems.append("Codex marketplace must contain exactly one Chenile plugin entry")
    else:
        source = entries[0].get("source", {})
        if source.get("source") != "git-subdir" or source.get("path") != "./plugins/chenile":
            problems.append("Codex marketplace must point to the Chenile plugin subdirectory")
        if not entries[0].get("policy", {}).get("installation"):
            problems.append("Codex marketplace plugin must define an installation policy")
        if not entries[0].get("policy", {}).get("authentication"):
            problems.append("Codex marketplace plugin must define an authentication policy")
except (OSError, json.JSONDecodeError) as exc:
    problems.append(f"Codex plugin metadata is missing or invalid: {exc}")

for problem in problems:
    print(problem)
print(f"{len(skills)} skills checked, {len(problems)} problems")
sys.exit(1 if problems else 0)

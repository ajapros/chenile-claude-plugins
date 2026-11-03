#!/usr/bin/env python3
"""Checks the published skills: frontmatter present and valid, description within limits, and no references to a
maintainer's machine (local paths, sandbox notes) that would mean nothing to other users."""
import pathlib, re, sys

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
for problem in problems:
    print(problem)
print(f"{len(skills)} skills checked, {len(problems)} problems")
sys.exit(1 if problems else 0)

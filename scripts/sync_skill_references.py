"""Copy the OpenAPI spec and the API guides into the skill's references folder.

python3 scripts/sync_skill_references.py          # rewrite skills/hlthstack-api/references/
python3 scripts/sync_skill_references.py --check  # exit 1 if it is out of date

A skill installed on its own (copied into a skills folder, installed by Codex's skill
installer, or uploaded to ChatGPT) has only its own folder, so it carries copies of the
spec and guides. Links between the guides are rewritten to work inside that folder.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "skills" / "hlthstack-api" / "references"
# Guides about the API. ai-skills.md (installing this skill) and getting-started.md
# (onboarding, links outside docs/) are not.
SKIP = {"ai-skills.md", "getting-started.md"}


def sources() -> dict[str, str]:
    files = {"openapi.yaml": ROOT / "openapi" / "openapi.yaml"}
    for doc in sorted((ROOT / "docs").glob("*.md")):
        if doc.name not in SKIP:
            files[doc.name] = doc
    out = {}
    for name, path in files.items():
        text = path.read_text(encoding="utf-8")
        origin = path.relative_to(ROOT).as_posix()
        if name.endswith(".md"):
            text = re.sub(r"\]\(\.\./openapi/openapi\.yaml", "](openapi.yaml", text)
            header = f"<!-- Copied from {origin} by scripts/sync_skill_references.py. Edit the source. -->\n\n"
        else:
            header = f"# Copied from {origin} by scripts/sync_skill_references.py. Edit the source.\n"
        out[name] = header + text
    return out


def main() -> int:
    wanted = sources()
    present = {p.name: p.read_text(encoding="utf-8") for p in TARGET.glob("*")} if TARGET.exists() else {}
    if "--check" in sys.argv:
        stale = sorted(n for n in wanted if present.get(n) != wanted[n])
        extra = sorted(set(present) - set(wanted))
        for n in stale:
            print(f"out of date: {TARGET.relative_to(ROOT)}/{n}")
        for n in extra:
            print(f"not generated: {TARGET.relative_to(ROOT)}/{n}")
        if stale or extra:
            print("Run: python3 scripts/sync_skill_references.py")
            return 1
        return 0
    TARGET.mkdir(parents=True, exist_ok=True)
    for name in set(present) - set(wanted):
        (TARGET / name).unlink()
    for name, text in wanted.items():
        (TARGET / name).write_text(text, encoding="utf-8")
    print(f"wrote {len(wanted)} files to {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

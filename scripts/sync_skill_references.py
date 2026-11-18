"""Copy the OpenAPI spec and the guides into the skill's references folder.

python3 scripts/sync_skill_references.py          # rewrite skills/hlthstack-api/references/
python3 scripts/sync_skill_references.py --check  # exit 1 if it is out of date

A skill installed on its own (copied into a skills folder, installed by Codex's skill
installer, or uploaded to ChatGPT) has only its own folder, so it carries copies of the
spec and guides. Links between the guides are rewritten to work inside that folder.

The member-app (PWA) guide and the SAML guide live in hlthstack/web; they are fetched from
its main branch and bundled as pwa.md and saml.md, so this needs network access.
"""

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "skills" / "hlthstack-api" / "references"
# ai-skills.md is about installing this skill, not about hlthstack.
SKIP = {"ai-skills.md"}
REPO = "https://github.com/hlthstack/integration-guide/blob/main"
WEB = "https://github.com/hlthstack/web"
WEB_RAW = "https://raw.githubusercontent.com/hlthstack/web/main"
# Bundled name -> path in hlthstack/web.
WEB_GUIDES = {"pwa.md": "README.md", "saml.md": "docs/saml.md"}


def web_links(text: str) -> str:
    """Point links to the web repo's guides at their bundled copies."""
    text = re.sub(rf"\]\({re.escape(WEB)}/blob/main/docs/saml\.md", "](saml.md", text)
    text = re.sub(rf"\]\({re.escape(WEB)}#readme\)", "](pwa.md)", text)
    text = re.sub(rf"\]\({re.escape(WEB)}#", "](pwa.md#", text)
    return re.sub(rf"\]\({re.escape(WEB)}\)", "](pwa.md)", text)


def fetch_web(path: str) -> str:
    req = urllib.request.Request(f"{WEB_RAW}/{path}", headers={"User-Agent": "sync-skill-references"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def web_guide(name: str, path: str) -> str:
    text = fetch_web(path)
    base = path.rpartition("/")[0]

    def fix(m: re.Match) -> str:
        target = m.group(1)
        if re.match(r"[a-z]+:|#", target):
            return m.group(0)
        resolved = (Path(base) / target).as_posix() if base else target
        resolved = re.sub(r"[^/]+/\.\./", "", resolved)
        file, _, anchor = resolved.partition("#")
        bundled = next((n for n, p in WEB_GUIDES.items() if p == file), None)
        if bundled:
            return f"]({bundled}{'#' + anchor if anchor else ''})"
        return f"]({WEB}/blob/main/{resolved})"

    text = re.sub(r"\]\(([^)\s]+)\)", fix, text)
    # Links to integration-guide docs that are bundled here stay inside the folder.
    text = re.sub(rf"\]\({re.escape(REPO)}/docs/(?!{'|'.join(map(re.escape, SKIP))})([\w-]+\.md)", r"](\1", text)
    text = web_links(text)
    return f"<!-- Copied from hlthstack/web {path} by scripts/sync_skill_references.py. Edit it in hlthstack/web. -->\n\n" + text


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
            # Files outside docs/, and guides not bundled here, are linked on GitHub instead.
            text = re.sub(r"\]\(\.\./", f"]({REPO}/", text)
            for skipped in SKIP:
                text = re.sub(rf"\]\({re.escape(skipped)}", f"]({REPO}/docs/{skipped}", text)
            text = web_links(text)
            header = f"<!-- Copied from {origin} by scripts/sync_skill_references.py. Edit the source. -->\n\n"
        else:
            header = f"# Copied from {origin} by scripts/sync_skill_references.py. Edit the source.\n"
        out[name] = header + text
    for name, path in WEB_GUIDES.items():
        out[name] = web_guide(name, path)
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

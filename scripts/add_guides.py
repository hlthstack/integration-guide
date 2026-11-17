"""Put the guides in docs/ into the spec used for the docs site and the Postman collection.

python3 scripts/add_guides.py <bundled-spec.json> <out.json>

Each API area (tag) gets its guide appended to its description, so the reference at
developers.hlthstack.io and each Postman folder explain the flow, rules and statuses, not just
the endpoints. Guides that are not about one area (getting started, environments, webhooks,
errors, FAQ) become documentation-only sections (`x-traitTag`). The guides stay the single
source: edit docs/, not the generated spec.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/hlthstack/integration-guide/blob/main"

# Tag name -> guide that explains it.
AREA_GUIDES = {
    "Authentication": "authentication.md",
    "Health Checkups": "health-checkups.md",
    "Consultations": "consultations.md",
    "ePharmacy": "epharmacy.md",
    "Wallet": "wallet.md",
    "Pre-registration": "pre-registration.md",
    "Testing": "testing.md",
}
# Documentation-only sections: (name, guide, position). "start" sections come before the API
# areas, "end" sections after.
EXTRA_SECTIONS = [
    ("For business teams", "for-business-teams.md", "start"),
    ("Getting started", "getting-started.md", "start"),
    ("Environments", "environments.md", "start"),
    ("Webhooks guide", "webhooks.md", "end"),
    ("Errors", "errors.md", "end"),
    ("Common errors", "common-errors.md", "end"),
    ("Product communications", "product-communications.md", "end"),
    ("White-labelling", "white-labelling.md", "end"),
    ("FAQ", "faq.md", "end"),
    ("Glossary", "glossary.md", "end"),
]
SITE = "https://developers.hlthstack.io/"


def gh_slug(heading: str) -> str:
    """The anchor GitHub gives a heading."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower().replace("`", "")).replace(" ", "-")


def site_slug(heading: str) -> str:
    """The anchor Redoc gives a top-level (##) heading inside a section."""
    # Redoc keeps most punctuation (".", ":", "(", ")") but drops commas and quotes.
    return re.sub(r"[,`'\"?!]", "", heading.strip()).replace(" ", "-")


def site_anchors(name: str) -> dict:
    """GitHub anchors in a guide -> the Redoc anchor of the ## section that holds them."""
    anchors, current, pending = {}, "", []
    text = re.sub(r"```.*?```", "", (ROOT / "docs" / name).read_text(encoding="utf-8"), flags=re.S)
    for line in text.splitlines():
        a = re.match(r'<a id="([^"]+)"></a>', line)
        h = re.match(r"(#{2,6}) (.+)", line)
        if a:
            pending.append(a.group(1))
        elif h:
            if len(h.group(1)) == 2:
                current = site_slug(h.group(2))
            for anchor in pending + [gh_slug(h.group(2))]:
                anchors.setdefault(anchor, current)
            pending = []
    return anchors


def site_link(guide: str, anchor: str):
    """The docs-site URL for a link to a guide (and anchor), or None if it isn't on the site."""
    tag = next((t for t, g in AREA_GUIDES.items() if g == guide), None) or next(
        (n for n, g, _ in EXTRA_SECTIONS if g == guide), None)
    if not tag or not (ROOT / "docs" / guide).exists():
        return None
    url = f"{SITE}#tag/{tag.replace(' ', '-')}"
    section = site_anchors(guide).get(anchor) if anchor else None
    # Brackets would end the Markdown link early, so encode them.
    section = section.replace("(", "%28").replace(")", "%29") if section else section
    return f"{url}/{section}" if section else url


def guide_body(name: str) -> str:
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    text = re.sub(r"\A# [^\n]*\n+", "", text)  # the section already has a title

    # The site and Postman have their own navigation, so drop the guides' "On this page" lists.
    text = re.sub(r"^\*\*On this page:\*\*.*?(?:\n\n|\Z)", "", text, flags=re.M | re.S)
    text = re.sub(r"^\*\*On this page\*\*\n\n(?:\d+\. .*\n)+\n?", "", text, flags=re.M)

    def absolute(m: re.Match) -> str:
        target = m.group(2)
        if re.match(r"[a-z]+:", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        # Links between guides go to the matching section of the docs site (also from Postman).
        if path == "" or (path.endswith(".md") and "/" not in path):
            site = site_link(path or name, anchor)
            if site:
                return f"{m.group(1)}({site})"
        if path == "":
            return f"{m.group(1)}({REPO}/docs/{name}#{anchor})"
        url = f"{REPO}/{(Path('docs') / path).as_posix()}"
        url = re.sub(r"/docs/\.\./", "/", url)
        return f"{m.group(1)}({url}{'#' + anchor if anchor else ''})"

    # Relative links would point nowhere on the docs site or in Postman.
    text = re.sub(r"(\[[^\]]*\])\(([^)\s]+)\)", absolute, text)
    # GitHub alerts ("> [!NOTE]") render as boxes on GitHub only; elsewhere show a bold label.
    text = re.sub(
        r"^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\n> ",
        lambda m: f"> **{m.group(1).capitalize()}:** ",
        text,
        flags=re.M,
    )
    # Neither Redoc nor Postman draws Mermaid diagrams; the guides describe each flow in words too.
    text = re.sub(r"```mermaid\n.*?```\n?", "", text, flags=re.S)
    return text.strip()


def main() -> int:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    spec = json.loads(src.read_text(encoding="utf-8"))
    tags = spec.get("tags", [])
    for tag in tags:
        guide = AREA_GUIDES.get(tag["name"])
        if guide:
            tag["description"] = f"{tag.get('description', '').strip()}\n\n{guide_body(guide)}"
    missing = set(AREA_GUIDES) - {t["name"] for t in tags}
    if missing:
        raise SystemExit(f"tags not in the spec: {sorted(missing)}")
    extra = {pos: [{"name": n, "description": guide_body(g), "x-traitTag": True}
                   for n, g, p in EXTRA_SECTIONS if p == pos] for pos in ("start", "end")}
    spec["tags"] = extra["start"] + tags + extra["end"]
    out.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"added {len(AREA_GUIDES)} area guides and {len(EXTRA_SECTIONS)} sections to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

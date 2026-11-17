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
    ("Getting started", "getting-started.md", "start"),
    ("Environments", "environments.md", "start"),
    ("Webhooks guide", "webhooks.md", "end"),
    ("Errors", "errors.md", "end"),
    ("Common errors", "common-errors.md", "end"),
    ("Product communications", "product-communications.md", "end"),
    ("White-labelling", "white-labelling.md", "end"),
    ("FAQ", "faq.md", "end"),
]


def guide_body(name: str) -> str:
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    text = re.sub(r"\A# [^\n]*\n+", "", text)  # the section already has a title

    # The site and Postman have their own navigation, so drop the guides' "On this page" lists.
    text = re.sub(r"^\*\*On this page:\*\*.*?(?:\n\n|\Z)", "", text, flags=re.M | re.S)
    text = re.sub(r"^\*\*On this page\*\*\n\n(?:\d+\. .*\n)+\n?", "", text, flags=re.M)

    def absolute(m: re.Match) -> str:
        target = m.group(2)
        if target.startswith("#"):
            # Headings get no anchors on the site or in Postman; send in-page links to GitHub.
            return f"{m.group(1)}({REPO}/docs/{name}{target})"
        if re.match(r"[a-z]+:", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
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

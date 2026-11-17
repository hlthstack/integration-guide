"""Update the published Postman collection in place with a new build.

POSTMAN_API_KEY=... python3 scripts/update_postman.py <collection.json> [--previous <url>]

Replacing the collection through Postman's API keeps its id, so the published docs keep their
link and show the new content. With --previous, nothing is sent when the new build matches the
collection currently served there (the docs site's copy), to stay within Postman's API limits.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# The "hlthstack API" collection in hlthstack's Postman workspace, published at
# https://documenter.getpostman.com/view/32733686/2sBYHbrFjt
COLLECTION_UID = "32733686-9102ef40-ba12-49d6-8040-15c1b70f9fd3"
API = "https://api.getpostman.com"


def unchanged(new: dict, previous_url: str) -> bool:
    try:
        with urllib.request.urlopen(previous_url, timeout=30) as resp:
            old = json.load(resp)
    except (urllib.error.URLError, ValueError) as e:
        print(f"could not read the previous collection ({e}); updating anyway")
        return False
    return old == new


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("collection")
    parser.add_argument("--previous", help="URL of the collection currently published")
    args = parser.parse_args()

    key = os.environ.get("POSTMAN_API_KEY")
    if not key:
        raise SystemExit("POSTMAN_API_KEY is not set")
    with open(args.collection, encoding="utf-8") as f:
        collection = json.load(f)
    if args.previous and unchanged(collection, args.previous):
        print("collection unchanged; Postman not updated")
        return 0

    req = urllib.request.Request(
        f"{API}/collections/{COLLECTION_UID}",
        data=json.dumps({"collection": collection}).encode("utf-8"),
        method="PUT",
        headers={"X-Api-Key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        # Postman's error body names the problem; it never contains the key.
        raise SystemExit(f"Postman update failed: HTTP {e.code} {e.read().decode('utf-8', 'replace')[:500]}")
    print(f"updated Postman collection {body.get('collection', {}).get('uid', COLLECTION_UID)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

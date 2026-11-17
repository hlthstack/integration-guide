"""Finish the Postman collection converted from openapi/openapi.yaml, and write its environments.

python3 scripts/build_postman.py <converted-collection.json> <dereferenced-spec.json> <out-dir>

The OpenAPI converter (openapi-to-postmanv2) names auth variables after the security schemes
and fills parameters and bodies with random values. This renames the auth variables to the
credentials partners receive, takes values from the spec instead (required parameters get the
spec's example, optional ones are included but switched off, bodies use the spec's example),
leaves the multi-entity headers off, adds a collection script that fetches and caches the
access token (or the pre-registration token) before each call, and writes a staging and a
production environment.
"""

import json
import sys
from pathlib import Path

PRE_REQUEST = r"""
// Fetches and caches the token each call needs, so you never paste one by hand.
const path = pm.request.url.getPath();
if (path.endsWith('/api/get-access-token') || path.endsWith('/api/pre_registration/access-token')) return;

const prereg = path.startsWith('/v1/corporate/pre_registrations');
const tokenKey = prereg ? 'preregToken' : 'accessToken';
const expiresKey = tokenKey + 'ExpiresAt';
const env = pm.environment;

function apply(token) {
  env.set(tokenKey, token);
}

const cached = env.get(tokenKey);
if (cached && Number(env.get(expiresKey) || 0) > Date.now() + 60 * 1000) return;

const user = env.get(prereg ? 'preregEmail' : 'username');
const pass = env.get(prereg ? 'preregPassword' : 'password');
if (!user || !pass) {
  throw new Error('Set ' + (prereg ? 'preregEmail and preregPassword' : 'username and password') +
                  ' in the selected environment.');
}
const basic = CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(user + ':' + pass));
pm.sendRequest({
  url: env.get('baseUrl') + (prereg ? '/api/pre_registration/access-token' : '/api/get-access-token'),
  method: 'GET',
  header: { Authorization: 'Basic ' + basic, Accept: 'application/json' }
}, function (err, res) {
  if (err || res.code !== 200) {
    throw new Error('Could not get a token: ' + (err || res.code + ' ' + res.text()));
  }
  apply(res.json().access_token);
  env.set(expiresKey, String(Date.now() + 55 * 60 * 1000));  // tokens last 1 hour
});
""".strip()

RENAMES = {
    "{{basicAuthUsername}}": None,  # depends on the request, see below
    "{{basicAuthPassword}}": None,
    "{{bearerToken}}": "{{accessToken}}",
    "{{apiKey}}": "{{preregToken}}",
}


def walk(items):
    for item in items:
        if "item" in item:
            yield from walk(item["item"])
        else:
            yield item


ENTITY_HEADERS = {"API-ENTITY-ID": "{{entityId}}", "API-SECRET-KEY": "{{entitySecretKey}}"}


def example_value(param):
    schema = param.get("schema") or {}
    for value in (param.get("example"), schema.get("example"), schema.get("default")):
        if value is not None:
            return value
    enum = schema.get("enum") or schema.get("examples")
    if enum:
        return "ahc" if "ahc" in enum else enum[0]
    return ""


def as_text(value):
    return json.dumps(value) if isinstance(value, (bool, dict, list)) else str(value)


def body_example(op):
    content = (op.get("requestBody") or {}).get("content") or {}
    media = content.get("application/json")
    if not media:
        return None
    if "example" in media:
        return media["example"]
    examples = media.get("examples") or {}
    return next((e.get("value") for e in examples.values() if "value" in e), None)


def apply_spec(req, spec):
    url = req["request"]["url"]
    path = "/" + "/".join(url["path"])
    method = req["request"]["method"].lower()
    for template, ops in spec["paths"].items():
        if path == template.replace("{", ":").replace("}", "") and method in ops:
            op, shared = ops[method], ops.get("parameters", [])
            break
    else:
        raise SystemExit(f"no spec operation for {method.upper()} {path}")
    params = {(p["in"], p["name"]): p for p in shared + op.get("parameters", [])}

    for q in url.get("query", []):
        p = params.get(("query", q["key"]), {})
        q["value"] = as_text(example_value(p))
        # pincode is optional only because coordinates can replace it; the guides lead with it.
        q["disabled"] = not (p.get("required", False) or q["key"] == "pincode")
    for v in url.get("variable", []):
        v["value"] = as_text(example_value(params.get(("path", v["key"]), {})))
    for h in req["request"].get("header", []):
        if h["key"] in ENTITY_HEADERS:
            h["value"], h["disabled"] = ENTITY_HEADERS[h["key"]], True
        elif ("header", h["key"]) in params:
            p = params[("header", h["key"])]
            h["value"], h["disabled"] = as_text(example_value(p)), not p.get("required", False)
    example = body_example(op)
    body = req["request"].get("body")
    if example is not None and body and body.get("mode") == "raw":
        body["raw"] = json.dumps(example, indent=2)


def main() -> int:
    src, spec_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    c = json.loads(src.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    c["info"]["description"] = (
        "Generated from the hlthstack OpenAPI spec "
        "(https://github.com/hlthstack/integration-guide). Pick the Staging or Production "
        "environment and fill in the credentials hlthstack issued you; tokens are fetched for you."
    )
    for req in walk(c["item"]):
        raw = json.dumps(req)
        prereg_token_call = "pre_registration" in json.dumps(req["request"].get("url"))
        raw = raw.replace("{{basicAuthUsername}}", "{{preregEmail}}" if prereg_token_call else "{{username}}")
        raw = raw.replace("{{basicAuthPassword}}", "{{preregPassword}}" if prereg_token_call else "{{password}}")
        for old, new in RENAMES.items():
            if new:
                raw = raw.replace(old, new)
        req.clear()
        req.update(json.loads(raw))
        apply_spec(req, spec)
    # A fixed id, the one of the collection published in hlthstack's Postman workspace, so
    # importing a new build there offers "Replace" and keeps the published docs' link.
    c["info"]["_postman_id"] = "5fa8e16a-24e0-4e01-b5cc-5af35fb6d179"
    c["auth"] = {"type": "bearer", "bearer": [{"key": "token", "value": "{{accessToken}}", "type": "string"}]}
    c["event"] = [{"listen": "prerequest", "script": {"type": "text/javascript", "exec": PRE_REQUEST.splitlines()}}]
    c["variable"] = [v for v in c.get("variable", []) if v.get("key") != "baseUrl"]
    leftovers = [k for k in ("basicAuth", "bearerToken", "{{apiKey}}") if k in json.dumps(c)]
    if leftovers:
        raise SystemExit(f"unexpected converter variables left: {leftovers}")

    out.mkdir(parents=True, exist_ok=True)
    (out / "hlthstack.postman_collection.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
    for name, base in (("Staging", "https://staging-api.hlthstack.io"), ("Production", "https://api.hlthstack.io")):
        env = {
            "name": f"hlthstack {name}",
            "values": [
                {"key": "baseUrl", "value": base, "type": "default", "enabled": True},
                {"key": "username", "value": "", "type": "default", "enabled": True},
                {"key": "password", "value": "", "type": "secret", "enabled": True},
                {"key": "preregEmail", "value": "", "type": "default", "enabled": True},
                {"key": "preregPassword", "value": "", "type": "secret", "enabled": True},
                {"key": "entityId", "value": "", "type": "default", "enabled": True},
                {"key": "entitySecretKey", "value": "", "type": "secret", "enabled": True},
                {"key": "accessToken", "value": "", "type": "secret", "enabled": True},
                {"key": "preregToken", "value": "", "type": "secret", "enabled": True},
            ],
            "_postman_variable_scope": "environment",
        }
        (out / f"hlthstack-{name.lower()}.postman_environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    print(f"wrote collection ({sum(1 for _ in walk(c['item']))} requests) and 2 environments to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# hlthstack integration guide

hlthstack is a health-benefits API for partners. Through it you can book health checkups
and lab tests, in-clinic and online doctor consultations, and ePharmacy orders for your
members, check their benefit wallets, register your members and their dependants in bulk,
and receive status updates by webhook.

**New here?** Start with [Getting started](docs/getting-started.md).

- **API reference:** https://developers.hlthstack.io
- **Postman docs:** https://documenter.getpostman.com/view/32733686/2sBYHbrFjt, with a **Run in Postman** button.
- **Postman files:** in Postman choose **Import** and paste the
  [collection](https://developers.hlthstack.io/postman/hlthstack.postman_collection.json) link,
  then the [staging](https://developers.hlthstack.io/postman/hlthstack-staging.postman_environment.json)
  or [production](https://developers.hlthstack.io/postman/hlthstack-production.postman_environment.json)
  environment link.
- **OpenAPI spec:** [`openapi/openapi.yaml`](openapi/openapi.yaml), version 1.0.1.
- **Changes:** [CHANGELOG.md](CHANGELOG.md).

## Ways to integrate

| Integration | What it is | Where |
|---|---|---|
| REST API | The HTTP API: reference, OpenAPI spec, guides and Postman collection | https://developers.hlthstack.io, and this repo: [`openapi/openapi.yaml`](openapi/openapi.yaml), [`docs/`](docs/) |
| JavaScript | Server-side SDK for Node.js, plus a guide to calling the API with plain `fetch` | https://github.com/hlthstack/js |
| Python | SDK (sync and async), plus a guide to calling the API with plain `requests` | https://github.com/hlthstack/python |
| Java | SDK for Java 11+, plus a guide to calling the API with the JDK's `HttpClient` | https://github.com/hlthstack/java |
| Web / PWA embed | Embed the hlthstack member experience in your app or site, with your own login (SSO) or the employer's identity provider (SAML 2.0) | https://github.com/hlthstack/web |
| AI assistant skills | A skill and plugin that teach Claude Code, Codex and ChatGPT to use this API | This repo: [`skills/`](skills/), install guide in [docs/ai-skills.md](docs/ai-skills.md) |

### Install an SDK

```bash
npm install github:hlthstack/js#v1.0.1                            # JavaScript / TypeScript
pip install "git+https://github.com/hlthstack/python@v1.0.1"      # Python
```

Java: add the JitPack repository and depend on `com.github.hlthstack:java:v1.0.1`; see the
[Java SDK README](https://github.com/hlthstack/java#readme) for Maven and Gradle.

## Environments

| Environment | Base URL |
|---|---|
| Production | `https://api.hlthstack.io` |
| Staging | `https://staging-api.hlthstack.io` |

These hosts serve paths under `/api/` and the pre-registration paths under
`/v1/corporate/pre_registrations`. Staging has separate credentials and extra endpoints for
simulating status changes. See [docs/environments.md](docs/environments.md).

## Getting credentials

Contact hlthstack through https://www.hlthstack.io/. At onboarding you receive:

- an API username and password (per environment),
- if you use pre-registration, a separate pre-registration login (email and password) and
  your company ids,
- your package ids and plan ids,
- your company slug (for the wallet endpoints),
- for multi-entity partners, entity ids and an API secret key,
- a webhook signing secret, once you register your webhook URLs.

## Quickstart

```bash
BASE=https://staging-api.hlthstack.io

# 1. Get an access token (valid 1 hour)
TOKEN=$(curl -s -u "$HS_USERNAME:$HS_PASSWORD" "$BASE/api/get-access-token" | jq -r .access_token)

# 2. Find providers for a health-check package near a pincode
curl -s "$BASE/api/providers?service_name=ahc&package_ids=1001&pincode=500081" \
  -H "Authorization: Bearer $TOKEN"

# 3. Get slots for one provider for the next 14 days (add &booking_date=YYYY-MM-DD for one day)
curl -s "$BASE/api/providers/1001/ahc/slots?package_ids=1001&pincode=500081" \
  -H "Authorization: Bearer $TOKEN"

# 4. Book: set appointment_date_time to a utc_slot_time from step 3
curl -s -X POST "$BASE/api/appointments" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "service_name": "ahc",
    "appointment_type": "inclinic",
    "provider_id": 1001,
    "appointment_date_time": "2030-01-15T02:30:00Z",
    "customers": [{
      "name": "Jane Doe", "dob": "1990-08-24", "gender": "female",
      "mobile_number": "9999999999", "api_customer_id": "CUST1001",
      "package_ids": [1001]
    }]
  }'

# 5. Get the booking (booking_id from step 4)
curl -s "$BASE/api/appointments?booking_id=EKI0000000001700000000" \
  -H "Authorization: Bearer $TOKEN"
```

Then listen for webhooks to follow the appointment to `confirmed`, `completed` and
`received` (reports). See [docs/webhooks.md](docs/webhooks.md).

## Guides

- [Getting started](docs/getting-started.md): from access request to go-live
- [Authentication](docs/authentication.md)
- [Environments](docs/environments.md)
- [Health checkups and lab tests](docs/health-checkups.md)
- [Consultations](docs/consultations.md)
- [ePharmacy](docs/epharmacy.md)
- [Wallet](docs/wallet.md)
- [Pre-registration](docs/pre-registration.md): register, update and deactivate members
- [Webhooks](docs/webhooks.md)
- [Errors](docs/errors.md)
- [Common errors and how to fix them](docs/common-errors.md)
- [Product communications](docs/product-communications.md): what members receive, and when
- [White-labelling](docs/white-labelling.md): send member communications under your brand
- [Testing on staging](docs/testing.md)
- [FAQ](docs/faq.md)
- [AI coding assistant skills](docs/ai-skills.md): install and run the skill in Claude Code, Codex and ChatGPT

## Support

Contact your hlthstack account contact or https://www.hlthstack.io/. Report problems with the
docs in this repository's issues, and security issues privately as described in
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)

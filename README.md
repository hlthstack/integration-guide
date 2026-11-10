# hlthstack integration guide

hlthstack is a health-benefits API for partners. Through it you can book health checkups
and lab tests, in-clinic and online doctor consultations, and ePharmacy orders for your
members, check their benefit wallets, and receive status updates by webhook.

## Ways to integrate

| Integration | What it is | Where |
|---|---|---|
| REST API | The HTTP API: OpenAPI spec and guides | This repo: [`openapi/openapi.yaml`](openapi/openapi.yaml), [`docs/`](docs/) |
| JavaScript SDK | Client library for Node.js and browsers | https://github.com/hlthstack/js |
| Python SDK | Client library for Python | https://github.com/hlthstack/python |
| Web / PWA embed | Embed the hlthstack member experience in your app or site | https://github.com/hlthstack/web |
| AI assistant skills | Instructions that teach Claude and ChatGPT to use this API | This repo: [`skills/`](skills/) |

## Environments

| Environment | Base URL |
|---|---|
| Production | `https://api.hlthstack.io` |
| Staging | `https://staging-api.hlthstack.io` |

Only paths under `/api/` are served on these hosts. Staging has separate credentials and
extra endpoints for simulating status changes. See [docs/environments.md](docs/environments.md).

## Getting credentials

Contact hlthstack through https://www.hlthstack.io/. At onboarding you receive:

- an API username and password (per environment),
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

# 3. Get slots for one provider on a date
curl -s "$BASE/api/providers/1001/ahc/slots?package_ids=1001&pincode=500081&booking_date=2026-01-15" \
  -H "Authorization: Bearer $TOKEN"

# 4. Book (use a slot's utc_slot_time as appointment_date_time)
curl -s -X POST "$BASE/api/appointments" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "service_name": "ahc",
    "appointment_type": "inclinic",
    "provider_id": 1001,
    "appointment_date_time": "2026-01-15T02:30:00Z",
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

- [Authentication](docs/authentication.md)
- [Environments](docs/environments.md)
- [Health checkups and lab tests](docs/health-checkups.md)
- [Consultations](docs/consultations.md)
- [ePharmacy](docs/epharmacy.md)
- [Wallet](docs/wallet.md)
- [Webhooks](docs/webhooks.md)
- [Errors](docs/errors.md)
- [Testing on staging](docs/testing.md)
- [FAQ](docs/faq.md)

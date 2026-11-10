# Environments

| Environment | Base URL | Use |
|---|---|---|
| Production | `https://api.hlthstack.io` | Live members and bookings |
| Staging | `https://staging-api.hlthstack.io` | Integration testing |

- These hosts serve paths under `/api/` and the [pre-registration](pre-registration.md)
  paths under `/v1/corporate/pre_registrations`. Nothing else under `/v1/` is available.
- Credentials, package ids, plan ids, entity ids and webhook secrets are **different per
  environment**. Don't reuse staging values in production.
- Staging has extra endpoints that move bookings and orders through their lifecycle and fire
  real webhooks. They don't exist in production. See [testing.md](testing.md).
- Bookings made through these hosts are tagged `booking_source: "hlthstack-api"` in webhook
  payloads, and voucher links in webhooks point at the same API host.

## Client recommendations

- Set a client timeout of 30-60 seconds. Create, reschedule and cancel calls can take a few
  seconds; `GET /api/epharmacy/fulfillment_options` typically takes 3-8 seconds.
- There are no published per-partner rate limits, but avoid polling. Use webhooks to learn
  about status changes, and the GET endpoints to reconcile.

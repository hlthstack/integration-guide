<!-- Copied from docs/faq.md by scripts/sync_skill_references.py. Edit the source. -->

# FAQ

Short answers to the questions partners ask most often, grouped by topic. Each answer links to
the guide with the full details.

**On this page:** [Authentication](#authentication) · [Appointments](#appointments) ·
[Webhooks](#webhooks) · [Pre-registration](#pre-registration) · [Operations](#operations)

## Authentication

### How do I authenticate?

1. Call `GET /api/get-access-token` with HTTP Basic auth (the username and password hlthstack
   issued).
2. You get `access_token` and `expires_at`.
3. Send `Authorization: Bearer <token>` on every other call.

**See also:** [authentication.md](authentication.md)

### How long is the token valid?

1 hour. Request a new one before it expires; an expired token fails with 401.

### We have several entities. Do we need credentials for each?

No. Use the credentials issued for your first entity and send `API-ENTITY-ID` (the target
entity's id) on each request. Without it, requests act for the entity tied to the credentials.

### What is `API-SECRET-KEY` for?

It is a key shared across all your entities. It is required whenever you send
`API-ENTITY-ID`, and is what lets that header be trusted.

### Which headers does each kind of partner send?

| Partner | Headers |
|---|---|
| Single entity | `Authorization` |
| Multi-entity | `Authorization`, `API-ENTITY-ID`, `API-SECRET-KEY` |

## Appointments

### What is the difference between `booking_id` and `appointment_id`?

Both come back from `POST /api/appointments`.

| Id | Covers | Use it to |
|---|---|---|
| `booking_id` | The whole booking, which can include several members | Reschedule, cancel or fetch everything |
| `appointment_id` | One member's appointment | Act on one member |

### How do I know an appointment is confirmed?

`status` becomes `confirmed` in the webhook and in `GET /api/appointments`. From then on the
payload includes `voucher_api_url`.

### When do report links appear?

In `reports`, once the status is `partially_received` or `received`.

### How do I reschedule, and what is the cut-off?

| Scope | Endpoint |
|---|---|
| Whole booking | `PATCH /api/bookings/{booking_id}/reschedule` |
| One appointment | `PATCH /api/appointments/{appointment_id}/reschedule` |

- **Cut-off:** until 30 minutes before the slot. Some providers also refuse changes once a
  phlebotomist is assigned, or have other rules (see
  [booking rules](health-checkups.md#booking-rules)).
- `appointment_date_time` is always required.
- Add `provider_id` to change provider, and `address` (with `provider_id`) to change a home
  collection address.

### Can I change `appointment_type` when rescheduling?

No. An in-clinic appointment can't become home collection.

### Can I move an appointment to another provider?

Not at providers connected through a partner integration: you get
`Appointment cannot be rescheduled to a different provider.` Cancel and book again instead.

### What do partial reschedule/cancel results look like?

Booking-level calls can return a partial result (comma-separated ids):

```json
{"message": "...", "success": "APT...,APT...", "failed": "APT..."}
```

If nothing could be changed you get an `errors` object instead.

### How do I cancel?

`PATCH /api/bookings/{booking_id}/cancel` or `PATCH /api/appointments/{appointment_id}/cancel`.
Same cut-offs as rescheduling.

### Should I use the slots in the providers response?

No, `provider_slots` is deprecated.

- Use `GET /api/providers/{provider_id}/{benefit_type}/slots`.
- Compute the earliest bookable date from the provider's `slot_lead_time` and `timezone`
  (see [health-checkups.md](health-checkups.md#first-bookable-date)).

## Webhooks

### Why is `api_customer_id` sometimes null?

hlthstack's team sometimes books on a member's behalf. Those bookings have no partner
customer id, but you still receive the webhooks.

### Are there separate webhooks for update, confirmation and reports?

No. One payload shape covers them.

- `voucher_api_url`, `reports`, `phlebo_name` and `phlebo_number` appear depending on the
  status.
- `type` is `reports_upload` when reports are attached, otherwise `status_update`.

### How long does hlthstack wait for my endpoint?

30 seconds per attempt.

### How are failed deliveries retried?

| Outcome | Behaviour |
|---|---|
| Connection errors, timeouts, HTTP 408/502/503/504 | Up to 5 retries over about 24 minutes (12 s, 36 s, 108 s, 324 s, 972 s) |
| Other error responses (400, 401, 404, 500, ...) | Final, not retried |

**See also:** [webhooks.md](webhooks.md#delivery-and-retries)

## Pre-registration

### Can I use my booking API token for pre-registration?

No. Pre-registration has its own login and token: get it from
`GET /api/pre_registration/access-token` and send it as `X-EKINCARE-KEY`.

**See also:** [pre-registration.md](pre-registration.md)

### Why is a row missing from the status?

On create, every required key must be present in every row (even with an empty value). Rows
missing a key are dropped without being reported.

### How do I know a pre-registration finished?

1. Poll `GET /v1/corporate/pre_registrations/{request_id}/status` until `status` is
   `completed` (or `failed`, if processing stopped part-way).
2. Read `success_records` and `failure_records`.
3. Resend only the corrected failed rows.

## Operations

### Is there a request timeout I should design around?

Use a client-side timeout of 30-60 seconds. Create, reschedule and cancel can take a few
seconds.

### Is webhook delivery monitored?

Yes. Every attempt is logged with its outcome and duration; ask hlthstack to investigate a
specific endpoint.

### Are there rate limits?

No per-partner limits are currently enforced on booking or token endpoints. Avoid polling:
use webhooks, since sustained high-frequency calls may be throttled at the infrastructure
level.

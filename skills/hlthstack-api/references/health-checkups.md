<!-- Copied from docs/health-checkups.md by scripts/sync_skill_references.py. Edit the source. -->

# Health checkups and lab tests

## 1. Overview

Book health checks, lab tests, dental and vision checkups and vaccinations at a provider
(in-clinic) or at the member's address (home collection). Full request and response schemas
are in [`openapi.yaml`](openapi.yaml) (tag **Health Checkups**).

`service_name` values commonly used: `ahc` (health checks / diagnostics), `dental`, `vision`,
`flu_vaccination`. The full list is in the API reference.

| Term | Meaning |
|---|---|
| Package | A test bundle or service you can book. Package ids are shared at onboarding. |
| Provider | The centre (or branch) that delivers the service. `provider_id` from `listProviders`. |
| Booking | One booking request, identified by `booking_id` (e.g. `EKI` + 19 characters). It can cover several members. |
| Appointment | One member's appointment within a booking, identified by `appointment_id` (`APT` + 9 characters). |

Plans: `plan_id` is optional on a booking and defaults to the base plan. `customer_plan_id` /
`subscription_id` pick which subscription pays (see [wallet.md](wallet.md)).

Booking types: `inclinic` (at the provider) or `home_collection` (at the member's address);
see [section 4](#4-booking-types).

## 2. Onboarding checklist

- **Package ids**: shared at onboarding; you send them as `package_ids`.
- **Enabled services**: each `service_name` you call must be enabled on your plan.
- **Plan ids**: only if you book on a plan other than the base plan (`plan_id`).
- **Webhook receiver**: to track bookings by webhook ([webhooks.md](webhooks.md)).
- **Lab results**: `GET /api/appointments/{id}/lab_results` is enabled on request.

## 3. How a booking works

1. **List providers**: `GET /api/providers` ([7.1](#71-list-providers)).
2. **Get slots**: `GET /api/providers/{provider_id}/{benefit_type}/slots`
   ([7.2](#72-get-slots)).
3. **Book**: `POST /api/appointments` ([7.3](#73-create-a-booking)).
4. **Track**: webhooks ([webhooks.md](webhooks.md)) or `GET /api/appointments?booking_id=...`
   ([7.4](#74-get-a-booking)).
5. **After confirmation**: voucher PDF, then reports and lab results after the visit
   ([7.7](#77-voucher) to [7.9](#79-lab-results)).

## 4. Booking types

Set `appointment_type` on the booking to `inclinic` or `home_collection`. The provider and
package must support it.

| | `inclinic` | `home_collection` |
|---|---|---|
| Where | At the provider (centre or branch) | At the member's address |
| Provider | A provider and package that support it | One with `home_collection_enabled`; or pass `auto_allocate_provider` to `listProviders` to let hlthstack pick the provider |
| `address` on create | Not needed | Required, see [7.3](#73-create-a-booking) |
| First bookable date | `slot_lead_time` 1: tomorrow if before 2:00 PM provider time | `slot_lead_time` 1: tomorrow if before 7:00 PM provider time |
| Change address on reschedule | Not possible; an `address` is ignored | Send `address` together with `provider_id` |

In-clinic can't be converted to home collection. To switch, cancel it and book again.

## 5. Conventions and common errors

- **Date-times**: `appointment_date_time` is ISO 8601 UTC. A time without `Z` or an offset
  is read as UTC. Always send the offset; the safest value is the slot's `utc_slot_time`.
- **Provider time zone**: the first bookable date and the payment link expiry use the
  provider's time (`timezone`). Booking hours are in IST.
- **Ids**: `booking_id` is `EKI` + 19 characters (e.g. `EKI0000000001700000000`);
  `appointment_id` is `APT` + 9 characters (e.g. `APT1A2B3C4D5`). `api_customer_id` is your
  id for the member: alphanumeric, unique within the request.
- **Lists**: `package_ids` for `listProviders` is comma-separated. Partial booking-level
  responses give `success` and `failed` as comma-separated appointment ids.
- **Mobile numbers**: 10 digits, no `+91`.

Error shapes:

| Shape | When |
|---|---|
| `400 {"errors": {field: [messages]}}` | Validation errors; nested fields are prefixed, e.g. `customer_mobile_number`, `address_pincode` |
| `400 {"message": "..."}` | e.g. a `booking_date` before the first bookable date |
| `403 {"errors":{"service_name":["this service is not enabled for you"]}}` | The service isn't enabled on your plan |
| `422 {"errors":{"messages":[...]}}` | e.g. a duplicate booking |
| `422 {"msg": "...", "recall": false}` | Booking couldn't be created |

Build status handling to tolerate statuses you don't recognise.

## 6. Booking rules and time windows

### Booking rules

These apply when you book and when you reschedule or cancel:

- **Booking hours:** the slot must start between 06:00 and 20:59 IST (until 22:59 at some
  providers), otherwise `appointment time is outside provider booking hours`. Booking with a
  slot's `utc_slot_time` keeps you inside these hours.
- **Day's notice:** at a provider with a `slot_lead_time` of 1 or more, a time today fails
  with `provider requires at least one day's notice`.
- **Time zone:** a time without `Z` or an offset is read as UTC. Always send the offset; the
  safest value is the slot's `utc_slot_time`.
- **Recent changes:** at providers connected through a partner integration, an appointment
  booked or rescheduled less than 5 minutes ago can't be changed yet (`This appointment cannot be rescheduled` / `This appointment cannot be
  cancelled`). Retry after a few minutes.
- **Provider rules:** some providers don't accept changes after confirmation or after a
  phlebotomist is assigned, limit the number of reschedules, stop changes to next-day
  bookings after a cut-off the evening before, or don't allow same-day cancellation. If the
  booking wasn't made or changed in the last 5 minutes, treat such a refusal as final.
- **Reschedule and cancel cut-off:** until 30 minutes before the slot.
- **Plan service period:** a new date must fall inside the plan's service period. A booking
  whose plan is no longer active can't be rescheduled.

### First bookable date

Compute it from the provider's `slot_lead_time` in the provider's `timezone`:

| `slot_lead_time` | First bookable date |
|---|---|
| 0 or null | Today; after 7:00 PM provider time, tomorrow |
| 1 | Tomorrow if before 2:00 PM provider time (7:00 PM for home-collection providers), else the day after |
| 2 or more | Today + `slot_lead_time` days |

An earlier `booking_date` returns `400 {"message": "Booking date ... is before the provider's earliest available date ..."}`.

### Payment window

A `payment_pending` booking's `payment_link` stops working at `payment_link_expires_at`:
normally 17:00 (provider time) the day before the slot, or 2 hours after booking for
bookings made later than that.

## 7. API reference

### 7.1 List providers

`GET /api/providers`

- Required: `service_name`, `package_ids` (comma-separated) and `pincode` (or `latitude` +
  `longitude`).
- Optional: `radius` (km, default 100), `page`/`per_page` (max 50), `plan_id`,
  `auto_allocate_provider` (home collection: let hlthstack pick the provider).
- Results are sorted by distance. Each provider has `home_collection_enabled`, `timezone` and
  `slot_lead_time`.
- Don't rely on `provider_slots` in this response; it is deprecated. Use 7.2.
- A service that isn't enabled on your plan returns
  `403 {"errors":{"service_name":["this service is not enabled for you"]}}`.

### 7.2 Get slots

`GET /api/providers/{provider_id}/{benefit_type}/slots`

- Send `package_ids` and `pincode`. Pass `booking_date` for one day, or omit it for up to
  `count_days` (default 14).
- Read `booking_slots[].slots[]`; use a slot's `utc_slot_time` when booking.
- A `booking_date` before the [first bookable date](#first-bookable-date) returns a `400`.

### 7.3 Create a booking

`POST /api/appointments`

| Field | Required | Notes |
|---|---|---|
| `provider_id` | yes | From `listProviders` |
| `appointment_date_time` | yes | ISO 8601 UTC, a valid slot for the provider |
| `appointment_type` | yes | `inclinic` or `home_collection` (the provider and package must support it) |
| `service_name` | yes | e.g. `ahc` |
| `customers[]` | yes | One entry per member, see below |
| `address` | home collection | Required: `address_line_one`, `address_line_two` (each up to 254 chars), `city`, `state`, `country` (India), `latitude`, `longitude` (non-negative decimals). Optional: `pincode` (6 digits, not starting with 0; derived from the coordinates when omitted). The address lines, city, state and country must not contain any other 6-digit pincode |
| `plan_id` | no | Defaults to the base plan |
| `customer_plan_id` / `subscription_id` | no | Pick which subscription pays, see [wallet.md](wallet.md) |
| `api_partner_order_id` | no | Your order reference (a per-customer value overrides it) |

`customers[]` fields: `name`, `api_customer_id` (your id, alphanumeric, unique within the
request), `mobile_number` (10 digits, no `+91`), `gender` (`male`, `female`, `non-binary`;
lowercase), `dob` (`YYYY-MM-DD`; members must be at least 1 year old), `package_ids`, and
optionally `booking_customer`, `vip`, `api_partner_order_id`. The booking customer is the last
entry with `booking_customer: true`, or the first entry. Set `booking_customer` on one entry
only.

There's no fixed limit on members per booking, but every member takes a place in the same
slot. If the provider's slot can't take all of them, the booking fails with an
`appointment_date_time` error that starts `Booking threshold reached` and ends
`(its slots are full)`. Pick another slot or provider, or split the members across bookings.

Response:

```json
{
  "provider_id": 1001,
  "home_collection_enable": false,
  "booking_id": "EKI0000000001700000000",
  "status": "confirmed",
  "customers": [
    { "customer_id": 5001, "name": "Jane Doe", "api_customer_id": "CUST1001",
      "package_ids": [1001], "appointment_id": "APT1A2B3C4D5",
      "customer_plan_id": null, "subscription_id": null }
  ]
}
```

- `status: "confirmed"` means the booking was paid from the wallet. The appointment itself
  starts at `new` and moves to `confirmed` when the provider confirms (you get a webhook).
- `status: "payment_pending"` with `payment_link` (and `payment_link_expires_at`) means the
  member must pay the remainder. Its appointments start at `payment_pending` and move to
  `new` once the member pays. The link stops working at `payment_link_expires_at`: normally
  17:00 (provider time) the day before the slot, or 2 hours after booking for bookings made
  later than that. An unpaid booking is never confirmed, and no webhook is sent while it is
  `payment_pending`.

Errors:

- Validation errors are `400 {"errors": {field: [messages]}}`; nested fields are prefixed,
  e.g. `customer_mobile_number`, `address_pincode`.
- A duplicate booking for the same member, package, provider and slot returns
  `422 {"errors":{"messages":["customer has an ongoing appointment for same package and provider for same slot"]}}`.
- Other failures: `422 {"msg": "failed to create booking please try again later", "recall": false}`,
  and `422 {"msg": "Failed to confirm booking due to payment failure.", ...}` when the benefit
  deduction failed (the wallet is not charged).
- The [booking rules](#booking-rules) apply.

### 7.4 Get a booking

`GET /api/appointments?booking_id=...` returns every appointment in the booking; add
`appointment_id=...` for one. Each appointment has the same shape as the webhook payload
(status, provider, voucher link once confirmed, report links once received, payment).

### 7.5 Reschedule

- Whole booking: `PATCH /api/bookings/{booking_id}/reschedule`
- One appointment: `PATCH /api/appointments/{appointment_id}/reschedule`

Body: `appointment_date_time` (required); `provider_id` to move to another provider; and,
for home collection, `address` together with `provider_id` to change the address.

Rules:

- Until 30 minutes before the slot. Some providers also refuse changes once a phlebotomist is
  assigned (see [Booking rules](#booking-rules)).
- Appointments at providers connected through a partner integration can't move to another
  provider: sending a different `provider_id` returns
  `422 {"errors":{"provider_id":["Appointment cannot be rescheduled to a different provider."]}}`.
  Cancel and book again instead.
- The new date must fall inside the plan's service period, otherwise
  `400 {"errors":{"messages":["The slots are not available for the selected date. please reschedule the appointment for next available date"]}}`.
  A booking whose plan is no longer active can't be rescheduled.
- In-clinic can't be converted to home collection. An `address` sent when rescheduling an
  in-clinic appointment is ignored without an error, and the appointment stays in-clinic. To
  switch, cancel it and book again.

Booking-level responses can be partial. `success` and `failed` are comma-separated
appointment ids:

```json
{ "message": "Some appointments cannot be rescheduled", "success": "APT1A2B3C4D5", "failed": "APT1A2B3C4D6" }
```

If nothing can be rescheduled: `400 {"errors":{"messages":["This booking cannot be rescheduled"]}}`.

### 7.6 Cancel

- Whole booking: `PATCH /api/bookings/{booking_id}/cancel`
- One appointment: `PATCH /api/appointments/{appointment_id}/cancel`

Body (optional): `reason`, up to 255 characters, recorded as the cancellation reason.
Without it, the reason is `Cancelled by your booking partner`.

```json
{ "reason": "Member is travelling" }
```

Same cut-offs as reschedule. Booking-level cancellation can be partial, in the same shape as
above (`"Some appointments cannot be cancelled"`).

### 7.7 Voucher

`GET /api/appointments/{id}/voucher`

Available when the appointment is `confirmed`; returns a PDF. Before that:
`400 voucher only available for download when appointment is confirmed`.

### 7.8 Reports

`GET /api/appointments/{id}/reports`

Available at `partially_received` or `received`. Returns `{"reports": [urls]}`, or
`{"message": "Reports will be available to download once they are verified"}`.

Report links (from this endpoint, `getAppointment` and the webhook's `reports`) are signed
URLs that expire **5 minutes** after they're issued. Download the files right away, and fetch
fresh links when you need them again; don't store the URLs.

### 7.9 Lab results

`GET /api/appointments/{id}/lab_results`

Available after digitization; returns structured values. Enabled on request; otherwise
`401 Unauthorised`.

## 8. Webhooks

Use webhooks ([webhooks.md](webhooks.md)) to track bookings; the payload has the same shape as
an appointment from [7.4](#74-get-a-booking).

- You get a webhook when the provider confirms an appointment (`new` → `confirmed`).
- No webhook is sent while a booking is `payment_pending`.
- The webhook's `reports` are signed links that expire after 5 minutes (see
  [7.8](#78-reports)).

<a id="appointment-statuses"></a>
## 9. Appointment statuses

| Status | Meaning |
|---|---|
| `payment_pending` | The member hasn't paid the amount due yet (see `payment_link`) |
| `new` | Waiting for confirmation from the centre |
| `confirmed` | Confirmed; voucher available |
| `rejected` | Rejected by the provider |
| `noshow` | Member missed the appointment |
| `cancelled` | Cancelled |
| `rescheduled` | Rescheduled, waiting for confirmation. The new time and provider are in `appointment_date_time` and `provider_id` |
| `completed` | Visit done |
| `verification_required` | Completed, waiting for reports |
| `partially_received` | Some reports uploaded, being digitized |
| `received` | Reports uploaded, being digitized |

Build status handling to tolerate statuses you don't recognise.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `403` `this service is not enabled for you` | The `service_name` isn't enabled on your plan | Use a service enabled on your plan |
| `400` `Booking date ... is before the provider's earliest available date ...` | `booking_date` is before the [first bookable date](#first-bookable-date) | Compute the date from `slot_lead_time` in the provider's `timezone` |
| `appointment time is outside provider booking hours` | The slot doesn't start between 06:00 and 20:59 IST (22:59 at some providers); a time without `Z` or an offset is read as UTC | Book with the slot's `utc_slot_time` |
| `provider requires at least one day's notice` | A time today at a provider with `slot_lead_time` of 1 or more | Pick a later date |
| `Booking threshold reached ... (its slots are full)` | The slot can't take every member in the booking | Pick another slot or provider, or split the members across bookings |
| `customer has an ongoing appointment for same package and provider for same slot` | Duplicate booking for the same member, package, provider and slot | Use the existing booking |
| `Failed to confirm booking due to payment failure.` | The benefit deduction failed | Nothing was charged to the wallet; the booking wasn't confirmed |
| Booking never reaches `confirmed`, no webhooks | It is `payment_pending`; the member hasn't paid | The member pays via `payment_link` before `payment_link_expires_at` |
| `This appointment cannot be rescheduled` / `This appointment cannot be cancelled` | Booked or rescheduled less than 5 minutes ago at a partner-integrated provider, or a provider rule | Retry after a few minutes; otherwise treat the refusal as final |
| `Appointment cannot be rescheduled to a different provider.` | The provider is connected through a partner integration | Cancel and book again |
| `The slots are not available for the selected date...` | The new date is outside the plan's service period | Pick a date inside the service period |
| Home-collection `address` ignored on reschedule | The appointment is in-clinic | Cancel it and book again as home collection |
| `400 voucher only available for download when appointment is confirmed` | The appointment isn't `confirmed` yet | Wait for the `confirmed` webhook |
| `Reports will be available to download once they are verified` | Reports aren't verified yet | Fetch again later |
| Report link no longer works | Signed URLs expire 5 minutes after they're issued | Fetch fresh links; don't store the URLs |
| `401 Unauthorised` on `lab_results` | Lab results aren't enabled for you | Ask for them to be enabled |

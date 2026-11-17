# Health checkups and lab tests

Book health checks, lab tests, dental and vision checkups and vaccinations at a provider
(in-clinic) or at the member's address (home collection). Full request and response schemas
are in [`openapi.yaml`](../openapi/openapi.yaml) (tag **Health Checkups**).

## Concepts

| Term | Meaning |
|---|---|
| Package | A test bundle or service you can book. Package ids are shared at onboarding. |
| Provider | The centre (or branch) that delivers the service. `provider_id` from `listProviders`. |
| Booking | One booking request, identified by `booking_id` (e.g. `EKI` + 19 characters). It can cover several members. |
| Appointment | One member's appointment within a booking, identified by `appointment_id` (`APT` + 9 characters). |

`service_name` values commonly used: `ahc` (health checks / diagnostics), `dental`, `vision`,
`flu_vaccination`, `covid_vaccination`. The service must be enabled on your plan, otherwise
`403 {"errors":{"service_name":["this service is not enabled for you"]}}`.

## Flow

1. **List providers**: `GET /api/providers` with `service_name`, `package_ids` (comma-separated)
   and `pincode` (or `latitude` + `longitude`). Optional `radius` (km, default 100),
   `page`/`per_page` (max 50), `plan_id`, `auto_allocate_provider` (home collection: let
   hlthstack pick the provider). Results are sorted by distance. Each provider has
   `home_collection_enabled`, `timezone` and `slot_lead_time`.
2. **Get slots**: `GET /api/providers/{provider_id}/{benefit_type}/slots` with `package_ids`
   and `pincode`. Pass `booking_date` for one day, or omit it for up to `count_days`
   (default 14). Read `booking_slots[].slots[]`; use a slot's `utc_slot_time` when booking.
   Don't rely on `provider_slots` from step 1; it is deprecated.
3. **Book**: `POST /api/appointments`.
4. **Track**: webhooks ([webhooks.md](webhooks.md)) or `GET /api/appointments?booking_id=...`.
5. **After confirmation**: voucher PDF, then reports and lab results after the visit.

### First bookable date

Compute it from the provider's `slot_lead_time` in the provider's `timezone`:

| `slot_lead_time` | First bookable date |
|---|---|
| 0 or null | Today; after 7:00 PM provider time, tomorrow |
| 1 | Tomorrow if before 2:00 PM provider time (7:00 PM for home-collection providers), else the day after |
| 2 or more | Today + `slot_lead_time` days |

An earlier `booking_date` returns `400 {"message": "Booking date ... is before the provider's earliest available date ..."}`.

## Create a booking

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
lowercase), `dob` (`YYYY-MM-DD`; members must be at least 1 year old), `package_ids`, and optionally `booking_customer`, `vip`,
`api_partner_order_id`. The booking customer is the last entry with `booking_customer: true`,
or the first entry. Set `booking_customer` on one entry only.

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
- Validation errors are `400 {"errors": {field: [messages]}}`; nested fields are prefixed,
  e.g. `customer_mobile_number`, `address_pincode`.
- A duplicate booking for the same member, package, provider and slot returns
  `422 {"errors":{"messages":["customer has an ongoing appointment for same package and provider for same slot"]}}`.

Other failures: `422 {"msg": "failed to create booking please try again later", "recall": false}`,
and `422 {"msg": "Failed to confirm booking due to payment failure.", ...}` when the benefit
deduction failed (the wallet is not charged).

## Booking rules

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

## Get a booking

`GET /api/appointments?booking_id=...` returns every appointment in the booking; add
`appointment_id=...` for one. Each appointment has the same shape as the webhook payload
(status, provider, voucher link once confirmed, report links once received, payment).

## Reschedule

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

## Cancel

- Whole booking: `PATCH /api/bookings/{booking_id}/cancel`
- One appointment: `PATCH /api/appointments/{appointment_id}/cancel`

Body (optional): `reason`, up to 255 characters, recorded as the cancellation reason.
Without it, the reason is `Cancelled by your booking partner`.

```json
{ "reason": "Member is travelling" }
```

Same cut-offs as reschedule. Booking-level cancellation can be partial, in the same shape as
above (`"Some appointments cannot be cancelled"`).

## Voucher, reports, lab results

| Endpoint | When | Returns |
|---|---|---|
| `GET /api/appointments/{id}/voucher` | Appointment `confirmed` | PDF. Before that: `400 voucher only available for download when appointment is confirmed` |
| `GET /api/appointments/{id}/reports` | `partially_received` or `received` | `{"reports": [urls]}`, or `{"message": "Reports will be available to download once they are verified"}` |

Report links (from this endpoint, `getAppointment` and the webhook's `reports`) are signed
URLs that expire **5 minutes** after they're issued. Download the files right away, and fetch
fresh links when you need them again; don't store the URLs.
| `GET /api/appointments/{id}/lab_results` | After digitization | Structured values. Enabled on request; otherwise `401 Unauthorised` |

## Appointment statuses

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

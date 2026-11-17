<!-- Copied from docs/consultations.md by scripts/sync_skill_references.py. Edit the source. -->

# Consultations

Doctor appointments. Schemas are in [`openapi.yaml`](openapi.yaml) (tag
**Consultations**).

| Type | `benefit_type` | Mode |
|---|---|---|
| In-clinic | `inclinic_consultation` | In person at the clinic (`service_mode: at_provider_location`) |
| Specialist, scheduled | `specialist_consultation` | `audio_call` or `video_call` at a booked slot |
| Specialist, priority | `specialist_consultation` with `priority_consultation: true` | A doctor calls within about 4 hours |

| | In-clinic | Scheduled online | Priority online |
|---|---|---|---|
| Member picks doctor and slot | Yes | Yes | No |
| Confirmed by | The clinic (some confirm automatically) | The doctor | Automatic |
| `meeting_link` | No | `video_call` only, once the doctor confirms | `video_call` only, once a doctor is assigned |
| Voucher | Yes, once confirmed | No | No |
| Summary and prescription | No API summary | API and webhooks | API and webhooks |

For `audio_call` there is no link: the doctor phones the `mobile_number` you sent. The
doctor's speciality must match the packages; each consultation provider is one doctor.

## In-clinic consultation

1. `GET /api/consultations/inclinic_consultation/providers?package_ids=...&pincode=...`
   (or `latitude`/`longitude`). Optional: `radius`, `page`, `per_page` (max 50),
   `sort_by` (`fee`, `experience`, `distance`, `rating`, `visited_before`), `sort_asc`,
   `gender` (`Male`, `Female`, `Non-binary`, any case). `sort_by=visited_before` also needs
   `api_customer_id`. Each provider carries doctor details (`doctor_name`,
   `doctor_specialities`, `doctor_fee_details`, `hospital_name`, ...).
2. `GET /api/providers/{provider_id}/inclinic_consultation/slots?package_ids=...`
3. `POST /api/consultations/inclinic_consultation`:

```json
{
  "appointment_date_time": "2030-01-15T04:30:00.000Z",
  "service_mode": "at_provider_location",
  "provider_id": 2001,
  "customers": [{
    "name": "Jane Doe", "dob": "1990-08-24", "mobile_number": "9999999999",
    "api_customer_id": "CUST1001", "gender": "female", "package_ids": [2001]
  }],
  "address": {
    "address_line_one": "1 Example Road", "address_line_two": "Kondapur",
    "city": "Hyderabad", "state": "Telangana", "country": "India",
    "pincode": "500084", "latitude": 17.47, "longitude": 78.35
  }
}
```

`address` (the member's) is required for in-clinic, including `pincode` (it is not derived
from the coordinates here). Send `service_mode` (`at_provider_location` for in-clinic;
`audio_call` or `video_call` for specialist); without it the booking fails with
`service mode can't be blank`. `appointment_date_time` must be in the future. Customers
follow the same rules as health-checkup bookings: distinct alphanumeric `api_customer_id`s,
10-digit `mobile_number`, lowercase `gender`, and a `dob` at least 1 year ago.

Each entry in `customers` is booked as its own consultation (its own `appointment_id`) with
the same doctor and slot, under one `booking_id`. The first customer's `mobile_number` is
used as the contact number for all of them.

Send `appointment_date_time` with an offset (`Z` or `+05:30`); without one it is read as
IST. Responses and webhooks return UTC. Time rules such as the priority hours are in IST.

4. `GET /api/consultations/inclinic_consultation/{appointment_id}` for details, including
   `hospital_name`, `hospital_location`, `hospital_address`, `latitude`, `longitude`.
5. `GET /api/consultations/{appointment_id}/voucher` once confirmed: the voucher PDF
   (`<appointment_id>.pdf`) the member shows at the clinic. In-clinic only.

## Scheduled specialist consultation

1. `GET /api/consultations/specialist_consultation/providers?package_ids=...` (no location needed).
2. `GET /api/providers/{provider_id}/specialist_consultation/slots?package_ids=...`
3. `POST /api/consultations/specialist_consultation` with `priority_consultation: false`,
   `service_mode` `audio_call` or `video_call`, `appointment_date_time`, `provider_id`,
   `customers` (no address). Some doctors need at least 90 minutes' notice: booking closer
   to the slot returns `Specialist appointments must be booked at least 90 minutes in
   advance`. For those doctors, a slot that is already taken returns `The selected slot is
   not available for this doctor`.
4. `GET /api/consultations/specialist_consultation/{appointment_id}`. For video calls the
   response (and webhooks) include `meeting_link`, which is `null` until the doctor
   confirms. For audio calls the doctor phones the `mobile_number` you sent.
5. Optionally upload the member's reports for the doctor:
   `POST /api/consultations/{appointment_id}/upload_documents` (multipart,
   `files[][name]` + `files[][value]` pairs; PDF, JPEG or PNG). `Invalid file format`
   means the form is wrong, not the file type; file problems (wrong type,
   password-protected or unreadable PDF, virus found) return
   `{"message": {"emr": ["..."]}}`.
6. After the call: `GET /api/consultations/{appointment_id}/summary_and_prescription`.
   `summary.file_name` and `summary.file_url` are `null` when the doctor wrote a
   prescription but no summary; `doctor_prescriptions` is empty when there is none. A 404
   (`Consultation not found`) means no consultation record yet; try again after
   `completed`. File links expire after a few minutes: download them, don't store them.

## Priority specialist consultation

1. `GET /api/consultations/specialist_consultation/providers?package_ids=...&default_provider=true`.
   It returns the priority provider for the package's speciality, or an empty list when no
   doctor of that speciality is rostered in the next 4 hours.
2. `POST /api/consultations/specialist_consultation` with `priority_consultation: true` and a
   `provider_id` from step 1. `appointment_date_time` is optional.
   - Available 8 AM-4 PM IST (`Priority consultation is only available between 8 AM and 4 PM`).
   - The consultation is `confirmed` straight away with a placeholder provider
     (`is_default_provider: true`). You may get more than one `confirmed` webhook: the
     first with the placeholder provider, then one with the assigned doctor (and time).
     Always show the doctor from the latest event.
   - Expect a call from the doctor within about four hours.
   - Using a priority provider for a scheduled booking, or vice versa, is rejected.

## Create response

```json
{
  "provider_id": 2001,
  "booking_id": "EKI0000000001700000000",
  "customers": [{
    "customer_id": "EKI000000001", "name": "Jane Doe", "api_customer_id": "CUST1001",
    "package_ids": [2001], "appointment_id": "APT1A2B3C4D5",
    "consultation_status": "new", "customer_plan_id": null, "subscription_id": null
  }]
}
```

`status: "confirmed"` means the booking was paid in full from the member's benefit. It is
not the doctor's confirmation: each consultation's own state is
`customers[].consultation_status`, usually `new`, then `confirmed` by webhook when the
doctor or clinic confirms.

When the member must pay part of the fee, `status` is absent, `consultation_status` is
`payment_pending`, and the response carries `payment_link` and `payment_link_expires_at`.
Send the member to the link. The booking is confirmed after payment, and the usual webhooks
follow. An unpaid booking is never confirmed: it sends no webhook and is dropped after the
slot passes. The link normally expires at 17:00 IST on the day before the slot; for
bookings made close to the slot it can be much shorter, down to about 15 minutes. Always
use `payment_link_expires_at`.

## Reschedule and cancel

- `PATCH /api/consultations/{appointment_id}/reschedule` with `{"appointment_date_time": "..."}`
  (must be in the future). Same doctor only (to change doctor, cancel and book again).
- `PATCH /api/consultations/{appointment_id}/cancel` (no body). Success is
  `{"msg": "Appointment cancelled"}` (note `msg`, not `message`). Amounts paid from the
  benefit or by the member are refunded automatically, an unpaid payment link is cancelled,
  and a `cancelled` webhook follows.

Both are allowed up to **30 minutes** before the slot. Cancellation is not allowed after a
no-show or rejection. `rejected` and `noshow` consultations can be rescheduled at any time
(the 30-minute rule does not apply), as long as the member's plan still covers the package.
At clinics connected through a partner integration, cancel is also refused for 5 minutes
after booking (`Please wait N minutes before you cancel this appointment.`).

Errors:

- Rule violations: `400 {"errors":{"reschedule_error":["..."]}}` or `400 {"errors":{"cancel_error":["..."]}}`
- Policy blocks: `422 {"errors":{"messages":["..."]}}`, for example
  `Consultations with this partner can only be moved up to 2 hours before the slot.` (some
  partner doctors need 2 hours' notice, for reschedule and cancel), `The company plan this
  appointment was booked under is no longer active.` (reschedule) or, on cancel, the
  5-minute wait. Except for the wait, these are final for the booking.
- Slot unavailable: `400 {"errors":{"messages":["Selected slot is unavailable, please select different slot"]}}`
- `Doctor not found`, or the speciality is no longer on the plan: cancel and book again.

## Consultation statuses

| Status | Meaning |
|---|---|
| `payment_pending` | Waiting for the member's co-pay; only in the create response and GET, never by webhook |
| `new` | Waiting for confirmation from the clinic or doctor |
| `confirmed` | Confirmed; doctor details included |
| `rejected` | The clinic or doctor could not take it; the reason is in `comment`. Offer a reschedule (allowed at any time) or a new booking |
| `noshow` | Member missed the consultation. Not refunded, and it cannot be cancelled. A scheduled consultation can be rescheduled; for priority, book again |
| `cancelled` | Cancelled. Refunded |
| `rescheduled` | Rescheduled, waiting for confirmation |
| `completed` | Consultation done |
| `received` | Summary and prescription available. Summaries and prescriptions can also arrive on `completed`: read `summary` and `doctor_prescriptions` on every event |

Typical webhook sequences:

- In-clinic: `new` → `confirmed` → `completed`.
- Scheduled online: `new` → `confirmed` (with `meeting_link` for video) → `completed`.
- Priority: `new` → `confirmed` (placeholder provider) → `confirmed` again when a doctor is
  assigned → `completed`.
- After a reschedule: `rescheduled`, then `confirmed`.

Any of these can instead end in `rejected` (reason in `comment`), `noshow` or `cancelled`.

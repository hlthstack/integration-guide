# Consultations

Doctor appointments. Schemas are in [`openapi.yaml`](../openapi/openapi.yaml) (tag
**Consultations**).

| Type | `benefit_type` | Mode |
|---|---|---|
| In-clinic | `inclinic_consultation` | In person at the clinic (`service_mode: at_provider_location`) |
| Specialist, scheduled | `specialist_consultation` | `audio_call` or `video_call` at a booked slot |
| Specialist, priority | `specialist_consultation` with `priority_consultation: true` | A doctor calls within about 4 hours |

## In-clinic consultation

1. `GET /api/consultations/inclinic_consultation/providers?package_ids=...&pincode=...`
   (or `latitude`/`longitude`). Optional: `radius`, `page`, `per_page` (max 50),
   `sort_by` (`fee`, `experience`, `distance`, `rating`, `visited_before`), `sort_asc`,
   `gender` (`Male`, `Female`, `Non-binary`). `sort_by=visited_before` also needs
   `api_customer_id`. Each provider carries doctor details (`doctor_name`,
   `doctor_specialities`, `doctor_fee_details`, `hospital_name`, ...).
2. `GET /api/providers/{provider_id}/inclinic_consultation/slots?package_ids=...`
3. `POST /api/consultations/inclinic_consultation`:

```json
{
  "appointment_date_time": "2026-01-15T04:30:00.000Z",
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

`address` (the member's) is required for in-clinic. The consultation is booked for the first
customer in `customers`.

4. `GET /api/consultations/inclinic_consultation/{appointment_id}` for details, including
   `hospital_name`, `hospital_location`, `hospital_address`, `latitude`, `longitude`.
5. `GET /api/consultations/{appointment_id}/voucher` once confirmed (PDF; in-clinic only).

## Scheduled specialist consultation

1. `GET /api/consultations/specialist_consultation/providers?package_ids=...` (no location needed).
2. `GET /api/providers/{provider_id}/specialist_consultation/slots?package_ids=...`
3. `POST /api/consultations/specialist_consultation` with `priority_consultation: false`,
   `service_mode` `audio_call` or `video_call`, `appointment_date_time`, `provider_id`,
   `customers` (no address).
4. `GET /api/consultations/specialist_consultation/{appointment_id}`. For video calls the
   response (and webhooks) include `meeting_link`.
5. Optionally upload the member's reports for the doctor:
   `POST /api/consultations/{appointment_id}/upload_documents` (multipart,
   `files[][name]` + `files[][value]` pairs; PDF, JPEG or PNG).
6. After the call: `GET /api/consultations/{appointment_id}/summary_and_prescription`.

## Priority specialist consultation

1. `GET /api/consultations/specialist_consultation/providers?package_ids=...&default_provider=true`.
   An empty list means priority consultation is not available for the package or right now.
2. `POST /api/consultations/specialist_consultation` with `priority_consultation: true` and a
   `provider_id` from step 1. `appointment_date_time` is optional.
   - Available 8 AM-4 PM IST (`Priority consultation is only available between 8 AM and 4 PM`).
   - The consultation is `confirmed` straight away with a placeholder provider
     (`is_default_provider: true`). Doctor details arrive by webhook when a doctor is assigned.
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

`status: "confirmed"` is added when the wallet paid in full; `payment_link` and
`payment_link_expires_at` are added when the member must pay.

## Reschedule and cancel

- `PATCH /api/consultations/{appointment_id}/reschedule` with `{"appointment_date_time": "..."}`.
  Same doctor only (to change doctor, cancel and book again).
- `PATCH /api/consultations/{appointment_id}/cancel`. Success is `{"msg": "Appointment cancelled"}`
  (note `msg`, not `message`).

Both are allowed up to **30 minutes** before the slot, and not within 5 minutes of the
previous booking or reschedule. Cancellation is not allowed after a no-show or rejection.

Errors:

- Rule violations: `400 {"errors":{"reschedule_error":["..."]}}` or `400 {"errors":{"cancel_error":["..."]}}`
- Policy blocks and the 5-minute buffer: `422 {"errors":{"messages":["Please wait N minute(s) before you reschedule this appointment."]}}`
- Slot unavailable: `400 {"errors":{"messages":["Selected slot is unavailable, please select different slot"]}}`

## Consultation statuses

| Status | Meaning |
|---|---|
| `new` | Waiting for confirmation from the doctor |
| `confirmed` | Confirmed; doctor details included |
| `rejected` | Rejected |
| `noshow` | Member missed the consultation |
| `cancelled` | Cancelled |
| `rescheduled` | Rescheduled, waiting for confirmation |
| `completed` | Consultation done |
| `received` | Summary and prescription available |

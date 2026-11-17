# Consultations

**Resources for this service**

- **API reference:** [Consultations on developers.hlthstack.io](https://developers.hlthstack.io/#tag/Consultations): every endpoint with its parameters, responses and errors.
- **Try it in Postman:** the *Consultations* folder of the [Postman docs](https://documenter.getpostman.com/view/32733686/2sBYHbrFjt), with code samples and **Run in Postman**.
- **SDK methods:** [JavaScript](https://github.com/hlthstack/js/blob/main/docs/sdk-integration.md#api) · [Python](https://github.com/hlthstack/python/blob/main/docs/sdk-integration.md#api-surface) · [Java](https://github.com/hlthstack/java/blob/main/docs/sdk-integration.md#api).
- **Calling the API without an SDK:** [JavaScript](https://github.com/hlthstack/js/blob/main/docs/api-integration.md#in-clinic-consultation) · [Python](https://github.com/hlthstack/python/blob/main/docs/api-integration.md#consultations) · [Java](https://github.com/hlthstack/java/blob/main/docs/api-integration.md#in-clinic-consultation).

**On this page**

1. [Overview](#1-overview)
2. [Onboarding checklist](#2-onboarding-checklist)
3. [How a consultation works](#3-how-a-consultation-works)
4. [The three consultation types](#4-the-three-consultation-types)
5. [Conventions and common errors](#5-conventions-and-common-errors)
6. [Booking rules and time windows](#6-booking-rules-and-time-windows)
7. [API reference](#7-api-reference)
8. [Webhooks](#8-webhooks)
9. [Consultation statuses](#9-consultation-statuses)
10. [Troubleshooting](#10-troubleshooting)

## 1. Overview

Doctor appointments. Schemas are in [`openapi.yaml`](../openapi/openapi.yaml) (tag
**Consultations**).

| Type | `benefit_type` | Mode |
|---|---|---|
| In-clinic | `inclinic_consultation` | In person at the clinic (`service_mode: at_provider_location`) |
| Specialist, scheduled | `specialist_consultation` | `audio_call` or `video_call` at a booked slot |
| Specialist, priority | `specialist_consultation` with `priority_consultation: true` | A doctor calls within about 4 hours |

The doctor's speciality must match the packages; each consultation provider is one doctor.

## 2. Onboarding checklist

- Know the `package_ids` the member's plan covers: every provider and slot call needs them.
- Decide which types you offer: in-clinic, scheduled online, priority online (see
  [section 4](#4-the-three-consultation-types)).
- For in-clinic, collect the member's full address, including `pincode`.
- For each member, collect `name`, `dob`, a 10-digit `mobile_number`, `gender` and your own
  `api_customer_id` (see [section 5](#5-conventions-and-common-errors)).
- Be ready to receive webhooks: confirmations, results and other status changes arrive by
  webhook (see [section 8](#8-webhooks)).
- If members may have to pay part of the fee, handle `payment_link` (see
  [7.3](#73-create-consultation)).

## 3. How a consultation works

1. List providers (doctors) for the member's packages ([7.1](#71-list-providers)).
2. Fetch the doctor's slots ([7.2](#72-fetch-slots)); priority bookings skip this.
3. Create the consultation ([7.3](#73-create-consultation)). If the member owes a co-pay,
   send them to the payment link.
4. Wait for the `confirmed` webhook from the doctor or clinic ([section 8](#8-webhooks)).
5. Before the consultation: show details ([7.4](#74-get-consultation-details)), optionally
   upload reports ([7.9](#79-upload-documents)), and for in-clinic fetch the voucher
   ([7.8](#78-voucher)).
6. Reschedule or cancel if needed ([7.5](#75-reschedule), [7.6](#76-cancel)).
7. After the call: fetch the summary and prescription ([7.7](#77-summary-and-prescription)).

## 4. The three consultation types

| | In-clinic | Scheduled online | Priority online |
|---|---|---|---|
| Member picks doctor and slot | Yes | Yes | No |
| Confirmed by | The clinic (some confirm automatically) | The doctor | Automatic |
| `meeting_link` | No | `video_call` only, once the doctor confirms | `video_call` only, once a doctor is assigned |
| Voucher | Yes, once confirmed | No | No |
| Summary and prescription | No API summary | API and webhooks | API and webhooks |

For `audio_call` there is no link: the doctor phones the `mobile_number` you sent.

**In-clinic** (`inclinic_consultation`):

1. List providers by location.
2. Fetch slots.
3. Create with `service_mode: at_provider_location` and the member's `address`.
4. Once confirmed, the member shows the voucher at the clinic.

**Scheduled online** (`specialist_consultation`, `priority_consultation: false`):

1. List providers (no location needed).
2. Fetch slots.
3. Create with `service_mode` `audio_call` or `video_call` (no address). For video calls
   `meeting_link` is `null` until the doctor confirms.
4. Optionally upload the member's reports for the doctor.

**Priority online** (`specialist_consultation`, `priority_consultation: true`):

- List providers with `default_provider=true` to get the priority provider; no slots.
  `appointment_date_time` is optional on create.
- Available 8 AM-4 PM IST.
- The consultation is `confirmed` straight away with a placeholder provider
  (`is_default_provider: true`). You may get more than one `confirmed` webhook: the first
  with the placeholder provider, then one with the assigned doctor (and time).
- Expect a call from the doctor within about four hours.
- Using a priority provider for a scheduled booking, or vice versa, is rejected.

> [!IMPORTANT]
> For priority consultations, always show the doctor from the latest event.

## 5. Conventions and common errors

| Topic | Convention |
|---|---|
| **Date-time and time zones** | Send `appointment_date_time` with an offset (`Z` or `+05:30`); without one it is read as IST. Responses and webhooks return UTC. Time rules such as the priority hours are in IST. |
| **`service_mode`** | Always send it: `at_provider_location` for in-clinic; `audio_call` or `video_call` for specialist. Without it the booking fails with `service mode can't be blank`. |
| **Customers** | Customers follow the same rules as health-checkup bookings: distinct alphanumeric `api_customer_id`s, 10-digit `mobile_number`, lowercase `gender`, and a `dob` at least 1 year ago. |
| **Several customers** | Each entry in `customers` is booked as its own consultation (its own `appointment_id`) with the same doctor and slot, under one `booking_id`. The first customer's `mobile_number` is used as the contact number for all of them. |

**Error shapes.**

| Case | Shape |
|---|---|
| Reschedule and cancel rule violations | `400 {"errors":{"reschedule_error":["..."]}}` or `400 {"errors":{"cancel_error":["..."]}}` |
| Policy blocks | `422 {"errors":{"messages":["..."]}}` |
| Slot unavailable | `400 {"errors":{"messages":["Selected slot is unavailable, please select different slot"]}}` |
| Upload file problems | `{"message": {"emr": ["..."]}}` |
| Cancel success | Uses `msg`, not `message`: `{"msg": "Appointment cancelled"}` |

## 6. Booking rules and time windows

| Rule | Details |
|---|---|
| **Future time** | `appointment_date_time` must be in the future (on create and on reschedule). |
| **Notice period** | Some doctors need at least 90 minutes' notice: booking closer to the slot returns `Specialist appointments must be booked at least 90 minutes in advance`. |
| **Priority hours** | 8 AM-4 PM IST (`Priority consultation is only available between 8 AM and 4 PM`). A doctor calls within about 4 hours; the priority provider list is empty when no doctor of that speciality is rostered in the next 4 hours. |
| **Reschedule and cancel window** | Both are allowed up to **30 minutes** before the slot. Cancellation is not allowed after a no-show or rejection. `rejected` and `noshow` consultations can be rescheduled at any time (the 30-minute rule does not apply), as long as the member's plan still covers the package. |
| **2-hour rule** | Some partner doctors need 2 hours' notice, for reschedule and cancel (`Consultations with this partner can only be moved up to 2 hours before the slot.`). |
| **5-minute wait** | At clinics connected through a partner integration, cancel is also refused for 5 minutes after booking (`Please wait N minutes before you cancel this appointment.`). |
| **Co-pay link expiry** | See the warning below. |

> [!WARNING]
> **Co-pay link expiry:** the payment link normally expires at 17:00 IST on the day before
> the slot; for bookings made close to the slot it can be much shorter, down to about 15
> minutes. Always use `payment_link_expires_at`. An unpaid booking is never confirmed: it
> sends no webhook and is dropped after the slot passes.

## 7. API reference

| Method | Path | What it does |
|---|---|---|
| `GET` | `/api/consultations/inclinic_consultation/providers`, `/api/consultations/specialist_consultation/providers` | [List providers](#71-list-providers) (doctors) |
| `GET` | `/api/providers/{provider_id}/inclinic_consultation/slots`, `/api/providers/{provider_id}/specialist_consultation/slots` | [Fetch slots](#72-fetch-slots) |
| `POST` | `/api/consultations/inclinic_consultation`, `/api/consultations/specialist_consultation` | [Create consultation](#73-create-consultation) |
| `GET` | `/api/consultations/inclinic_consultation/{appointment_id}`, `/api/consultations/specialist_consultation/{appointment_id}` | [Get consultation details](#74-get-consultation-details) |
| `PATCH` | `/api/consultations/{appointment_id}/reschedule` | [Reschedule](#75-reschedule) |
| `PATCH` | `/api/consultations/{appointment_id}/cancel` | [Cancel](#76-cancel) |
| `GET` | `/api/consultations/{appointment_id}/summary_and_prescription` | [Summary and prescription](#77-summary-and-prescription) |
| `GET` | `/api/consultations/{appointment_id}/voucher` | [Voucher](#78-voucher) (in-clinic) |
| `POST` | `/api/consultations/{appointment_id}/upload_documents` | [Upload documents](#79-upload-documents) for the doctor |

### 7.1 List providers

List the doctors who can see the member for their packages.

| Type | Request |
|---|---|
| **In-clinic** | `GET /api/consultations/inclinic_consultation/providers?package_ids=...&pincode=...` (or `latitude`/`longitude`) |
| **Scheduled specialist** | `GET /api/consultations/specialist_consultation/providers?package_ids=...` (no location needed) |
| **Priority specialist** | `GET /api/consultations/specialist_consultation/providers?package_ids=...&default_provider=true` |

In-clinic options:

- Optional: `radius`, `page`, `per_page` (max 50), `sort_by` (`fee`, `experience`,
  `distance`, `rating`, `visited_before`), `sort_asc`, `gender` (`Male`, `Female`,
  `Non-binary`, any case).
- `sort_by=visited_before` also needs `api_customer_id`.
- Each provider carries doctor details (`doctor_name`, `doctor_specialities`,
  `doctor_fee_details`, `hospital_name`, ...).

Priority response: it returns the priority provider for the package's speciality, or an
empty list when no doctor of that speciality is rostered in the next 4 hours.

### 7.2 Fetch slots

Get a doctor's bookable slots.

- In-clinic: `GET /api/providers/{provider_id}/inclinic_consultation/slots?package_ids=...`
- Scheduled specialist: `GET /api/providers/{provider_id}/specialist_consultation/slots?package_ids=...`

Priority bookings have no slots.

### 7.3 Create consultation

Book a consultation for one or more members.

- In-clinic: `POST /api/consultations/inclinic_consultation`
- Specialist (scheduled or priority): `POST /api/consultations/specialist_consultation`

In-clinic request:

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

| Type | What to send |
|---|---|
| **In-clinic** | `address` (the member's) is required, including `pincode` (it is not derived from the coordinates here). |
| **Scheduled specialist** | `priority_consultation: false`, `service_mode` `audio_call` or `video_call`, `appointment_date_time`, `provider_id`, `customers` (no address). |
| **Priority specialist** | `priority_consultation: true` and a `provider_id` from the `default_provider=true` list ([7.1](#71-list-providers)). `appointment_date_time` is optional. |

For every type, `service_mode` is required (`service mode can't be blank`);
`appointment_date_time` must be in the future; customer rules are in
[section 5](#5-conventions-and-common-errors).

Response:

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

Response notes:

- `status: "confirmed"` means the booking was paid in full from the member's benefit. It is
  not the doctor's confirmation: each consultation's own state is
  `customers[].consultation_status`, usually `new`, then `confirmed` by webhook when the
  doctor or clinic confirms.
- When the member must pay part of the fee, `status` is absent, `consultation_status` is
  `payment_pending`, and the response carries `payment_link` and `payment_link_expires_at`.
  Send the member to the link. The booking is confirmed after payment, and the usual webhooks
  follow. For link expiry and unpaid bookings, see
  [section 6](#6-booking-rules-and-time-windows).

Errors:

| Message | Cause |
|---|---|
| `service mode can't be blank` | `service_mode` missing |
| `Specialist appointments must be booked at least 90 minutes in advance` | Doctors that need 90 minutes' notice |
| `The selected slot is not available for this doctor` | For those doctors, a slot that is already taken |
| `Priority consultation is only available between 8 AM and 4 PM` | Priority booked outside those hours |
| The request is rejected | A priority provider used for a scheduled booking, or vice versa |

### 7.4 Get consultation details

Read a consultation's current details.

| Type | Request | Notes |
|---|---|---|
| In-clinic | `GET /api/consultations/inclinic_consultation/{appointment_id}` | Includes `hospital_name`, `hospital_location`, `hospital_address`, `latitude`, `longitude` |
| Specialist | `GET /api/consultations/specialist_consultation/{appointment_id}` | For video calls the response (and webhooks) include `meeting_link`, which is `null` until the doctor confirms. For audio calls the doctor phones the `mobile_number` you sent |

### 7.5 Reschedule

Move a consultation to a new time with the same doctor.

`PATCH /api/consultations/{appointment_id}/reschedule` with
`{"appointment_date_time": "..."}` (must be in the future). Same doctor only (to change
doctor, cancel and book again). Timing rules are in
[section 6](#6-booking-rules-and-time-windows).

Errors:

| Error | Response | What to do |
|---|---|---|
| Rule violations | `400 {"errors":{"reschedule_error":["..."]}}` | See [section 6](#6-booking-rules-and-time-windows) |
| Policy blocks | `422 {"errors":{"messages":["..."]}}`, for example `Consultations with this partner can only be moved up to 2 hours before the slot.` or `The company plan this appointment was booked under is no longer active.` | These are final for the booking |
| Slot unavailable | `400 {"errors":{"messages":["Selected slot is unavailable, please select different slot"]}}` | Pick another slot |
| Doctor or speciality gone | `Doctor not found`, or the speciality is no longer on the plan | Cancel and book again |

### 7.6 Cancel

Cancel a consultation.

`PATCH /api/consultations/{appointment_id}/cancel` (no body). Success is
`{"msg": "Appointment cancelled"}` (note `msg`, not `message`).

- Amounts paid from the benefit or by the member are refunded automatically.
- An unpaid payment link is cancelled.
- A `cancelled` webhook follows.
- Timing rules are in [section 6](#6-booking-rules-and-time-windows).

Errors:

| Error | Response | What to do |
|---|---|---|
| Rule violations | `400 {"errors":{"cancel_error":["..."]}}` | See [section 6](#6-booking-rules-and-time-windows) |
| Policy blocks | `422 {"errors":{"messages":["..."]}}`, for example `Consultations with this partner can only be moved up to 2 hours before the slot.` or the 5-minute wait (`Please wait N minutes before you cancel this appointment.`) | Except for the wait, these are final for the booking |
| Doctor or speciality gone | `Doctor not found`, or the speciality is no longer on the plan | Cancel and book again |

### 7.7 Summary and prescription

Get the doctor's summary and prescription after the call.

`GET /api/consultations/{appointment_id}/summary_and_prescription`, after the call.

- `summary.file_name` and `summary.file_url` are `null` when the doctor wrote a
  prescription but no summary; `doctor_prescriptions` is empty when there is none.
- A 404 (`Consultation not found`) means no consultation record yet; try again after
  `completed`.
- In-clinic consultations have no API summary.

> [!WARNING]
> File links expire after a few minutes: download them, don't store them.

### 7.8 Voucher

Download the in-clinic voucher.

`GET /api/consultations/{appointment_id}/voucher` once confirmed: the voucher PDF
(`<appointment_id>.pdf`) the member shows at the clinic. In-clinic only.

### 7.9 Upload documents

Share files with the doctor before the call.

`POST /api/consultations/{appointment_id}/upload_documents`: optionally upload the member's
reports for the doctor (scheduled specialist consultations). Multipart, `files[][name]` +
`files[][value]` pairs; PDF, JPEG or PNG.

Errors:

| Response | Cause |
|---|---|
| `Invalid file format` | The form is wrong, not the file type |
| `{"message": {"emr": ["..."]}}` | File problems (wrong type, password-protected or unreadable PDF, virus found) |

## 8. Webhooks

Typical webhook sequences:

| Type | Sequence |
|---|---|
| In-clinic | `new` → `confirmed` → `completed` |
| Scheduled online | `new` → `confirmed` (with `meeting_link` for video) → `completed` |
| Priority | `new` → `confirmed` (placeholder provider) → `confirmed` again when a doctor is assigned → `completed` |
| After a reschedule | `rescheduled`, then `confirmed` |

Any of these can instead end in `rejected` (reason in `comment`), `noshow` or `cancelled`.

- `payment_pending` is never sent by webhook, and an unpaid booking sends no webhook. After
  payment, the usual webhooks follow.
- For priority, always show the doctor from the latest `confirmed` event.
- A cancel is followed by a `cancelled` webhook.
- Webhooks return times in UTC and include `meeting_link` for video calls (`null` until the
  doctor confirms).

> [!IMPORTANT]
> Summaries and prescriptions can arrive on `completed` or `received`: read `summary` and
> `doctor_prescriptions` on every event.

Payload fields are described in [webhooks.md](webhooks.md#appointment-and-consultation-payload).

<a id="consultation-statuses"></a>
## 9. Consultation statuses

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

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Create fails with `service mode can't be blank` | `service_mode` missing | Send `at_provider_location` (in-clinic) or `audio_call` / `video_call` (specialist) |
| Create returns `Specialist appointments must be booked at least 90 minutes in advance` | The doctor needs at least 90 minutes' notice | Pick a later slot |
| Create returns `The selected slot is not available for this doctor` | The slot is already taken | Fetch slots again and pick another |
| Create returns `Priority consultation is only available between 8 AM and 4 PM` | Priority booked outside 8 AM-4 PM IST | Offer priority only in those hours, or a scheduled consultation |
| Priority provider list is empty | No doctor of that speciality is rostered in the next 4 hours | Offer a scheduled consultation |
| Create is rejected for the provider | Priority provider used for a scheduled booking, or vice versa | Use the `default_provider=true` provider only for priority |
| Response has no `status: "confirmed"` and `consultation_status` is `payment_pending` | The member must pay part of the fee | Send the member to `payment_link` before `payment_link_expires_at` |
| No webhook for a booking | Unpaid co-pay: an unpaid booking is never confirmed, sends no webhook and is dropped after the slot passes | Make sure the member pays via `payment_link` |
| `meeting_link` is `null` | The doctor has not confirmed yet, or the call is `audio_call` (no link; the doctor phones the `mobile_number`) | Wait for `confirmed` |
| Summary and prescription returns 404 `Consultation not found` | No consultation record yet | Try again after `completed` |
| Summary file link stops working | File links expire after a few minutes | Download the files; don't store the links |
| Upload returns `Invalid file format` | The form is wrong, not the file type | Send `files[][name]` + `files[][value]` pairs as multipart |
| Reschedule or cancel returns 400 `reschedule_error` / `cancel_error` | A booking rule was broken (for example the 30-minute window) | See [section 6](#6-booking-rules-and-time-windows) |
| Reschedule or cancel returns 422 | A policy block (2-hour partner rule, inactive company plan, 5-minute wait) | Read `errors.messages`; except for the wait, it is final for the booking |
| Reschedule or cancel returns `Doctor not found`, or the speciality is no longer on the plan | The booking can't be kept with this doctor | Cancel and book again |
| Member wants a different doctor | Reschedule keeps the same doctor | Cancel and book again |

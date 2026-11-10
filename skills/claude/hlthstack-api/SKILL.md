---
name: hlthstack-api
description: Integrate with or call the hlthstack health-benefits REST API (health checkup and lab test bookings, doctor consultations, ePharmacy orders, benefit wallets, webhooks). Use when writing code against api.hlthstack.io, debugging hlthstack API calls or webhooks, or answering questions about hlthstack endpoints.
---

# hlthstack API

hlthstack is a partner API for booking and managing members' health benefits. The source of
truth is the OpenAPI 3.1 spec at `openapi/openapi.yaml` in
https://github.com/hlthstack/integration-guide; guides are in `docs/`. Read the relevant
operation in the spec before writing a call. Don't invent endpoints, fields or enum values.

## Essentials

- Base URLs: production `https://api.hlthstack.io`, staging `https://staging-api.hlthstack.io`.
  Only `/api/...` paths exist.
- Auth: `GET /api/get-access-token` with HTTP Basic (partner username/password) returns
  `access_token` and `expires_at` (1 hour). Send `Authorization: Bearer <token>` on every
  other call. Refresh before expiry; there is no refresh token.
- Multi-entity partners add `API-ENTITY-ID` and `API-SECRET-KEY` headers.
- Credentials, the entity secret key and the webhook secret are server-side secrets. Read
  them from environment variables; never hard-code them, print them, or put them in client
  code.
- Prefer the official SDKs when the user's stack matches: https://github.com/hlthstack/js,
  https://github.com/hlthstack/python. The web/PWA embed is https://github.com/hlthstack/web.

## Main flows (operationIds from the spec)

- Health checkups: `listProviders` -> `listSlots` -> `createAppointment` -> `getAppointment`;
  then `rescheduleAppointment`/`rescheduleBooking`, `cancelAppointment`/`cancelBooking`,
  `getAppointmentVoucher`, `getAppointmentReports`, `getAppointmentLabResults`.
- Consultations: `listInclinicConsultationProviders` / `listSpecialistConsultationProviders`
  -> `listSlots` -> `createInclinicConsultation` / `createSpecialistConsultation` ->
  `getInclinicConsultation` / `getSpecialistConsultation`; `rescheduleConsultation`,
  `cancelConsultation`, `getConsultationSummaryAndPrescription`, `uploadConsultationDocuments`.
- ePharmacy: `searchMedicines` (or `digitizePrescription`) -> `updateCart` ->
  `getFulfillmentOptions` -> `getOrderPaymentDetails` -> `createOrder` -> `getOrder`;
  `confirmOrder` (partner-collected payments only), `cancelOrder`.
- Wallet: `getCustomerWallet`, `listCustomerPlans` (path includes the partner's company slug).
- Staging-only simulators (tag Testing): `simulateAppointmentStatus`,
  `simulateConsultationStatus`, `simulateOrderStatus`.

## Rules that commonly trip people up

- `appointment_date_time` must be a slot's `utc_slot_time` from `listSlots`; don't use the
  deprecated `provider_slots` from `listProviders`.
- `customers[].gender` is lowercase `male`, `female` or `non-binary`; `mobile_number` is 10
  digits without `+91`; `api_customer_id` is alphanumeric.
- `package_ids` is a comma-separated string in query params and an array in JSON bodies.
- Booking-level reschedule/cancel can partially succeed; `success`/`failed` are
  comma-separated strings.
- Consultation cancel returns `{"msg": ...}`, not `message`.
- ePharmacy: payment details takes `selected_delivery_option`; create order takes
  `delivery_option`. Pass the chosen option's `vendor_id` as `medicine_vendor_id` and its
  `location_token` to `createOrder`. Check nested `success` flags in fulfillment options.
- Error bodies vary (`errors` object, `errors.messages`, `message`, `msg`, `error`); see
  `docs/errors.md`. A 401 with plain text `HTTP Token: Access denied.` means the token is bad
  or expired.
- Never rename fields to match a preferred style: send and read field names exactly as the
  spec shows.

## Webhooks

Status changes arrive by POST with a `Signature` header: an HS256 JWT signed with the
partner's webhook secret. It doesn't cover the body, so verify the signature, check that its
ids (`appointment_id`/`booking_id`, `order_id` or `request_id`) match the body, and reject
stale `timestamp`s. Reply 2xx within 30 s and process asynchronously; most non-2xx replies
are not retried. Payload schemas are under `webhooks` in the spec; verification code is in
`docs/webhooks.md`.

## When calling the live API on the user's behalf

Use staging unless the user explicitly asks for production. Confirm with the user before
creating, rescheduling or cancelling real bookings or orders, since these affect real members
and benefit balances.

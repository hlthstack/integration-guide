---
name: hlthstack-api
description: Answer questions about hlthstack, the health-benefits platform for partners, and build integrations with it. Covers what members can get (health checkups and lab tests, doctor consultations, ePharmacy, benefit wallets), embedding the hlthstack member app vs building your own screens on the API, onboarding and go-live, member communications and white-labelling, and writing or debugging code against api.hlthstack.io (bookings, webhooks, pre-registration, errors). Use when someone is exploring, evaluating, planning or building an hlthstack integration, whether or not they are a developer.
---

# hlthstack

hlthstack lets partners (HR platforms, insurers, employers' apps) offer health benefits to
their members: they either embed hlthstack's ready-made member app, or build their own
screens on the hlthstack API, or both. The source of truth is the OpenAPI 3.1 spec, bundled
with this skill as `references/openapi.yaml`, and the guides next to it in `references/`.
Both are also on GitHub at https://github.com/hlthstack/integration-guide, the API reference
is at https://developers.hlthstack.io, and access requests go through
https://www.hlthstack.io/. Read the page that answers the question (below) before answering;
for API calls, read the operation in the spec (search it by `operationId` rather than
reading it whole) and the guide for its area. Don't invent endpoints, fields, enum values,
prices, timelines or commitments; if the references don't say something, say so and suggest
asking hlthstack.

## Which page answers what

| The question is about | Read |
|---|---|
| What hlthstack is, what members get, embed vs API, what a partner decides and receives, the path to go-live, support, security (non-technical) | `references/for-business-teams.md` |
| A term (entity, slug, plan, package, PWA, webhook, phlebotomist...) | `references/glossary.md` |
| How to start, credentials, first calls, go-live checklist (technical) | `references/getting-started.md` |
| Messages hlthstack sends members (email, WhatsApp, SMS, in-app, push) | `references/product-communications.md` |
| Sending those messages under the partner's brand | `references/white-labelling.md` |
| A specific error and how to fix it | `references/common-errors.md`, then `references/errors.md` |
| Booking flows, rules, statuses for one service | `references/health-checkups.md`, `consultations.md`, `epharmacy.md`, `wallet.md`, `pre-registration.md` |
| Tokens, environments, webhooks, staging test endpoints, quick answers | `references/authentication.md`, `environments.md`, `webhooks.md`, `testing.md`, `faq.md` |
| Endpoints, fields, enums | `references/openapi.yaml` |
| Embedding the member app (sign-in payload, encryption, WebView) or employer SAML sign-in | https://github.com/hlthstack/web (not bundled; say so and link it) |

## Answering people new to hlthstack

- If the person isn't a developer, or is exploring or evaluating, answer in plain words from
  `for-business-teams.md` and `glossary.md`, without code, and explain any term you use. Offer
  the developer path (`getting-started.md`, the SDKs) as a next step rather than leading with it.
- When they ask which way to integrate, lay out the options from the "Three ways to
  integrate" table in `for-business-teams.md` and ask what they already have (their own app?
  developers available? need their own branding?) rather than picking for them.
- For pricing, contracts, timelines or anything not in the references, say it is agreed with
  hlthstack and point to https://www.hlthstack.io/.

## Essentials

- Base URLs: production `https://api.hlthstack.io`, staging `https://staging-api.hlthstack.io`.
  Only `/api/...` paths and the pre-registration paths `/v1/corporate/pre_registrations...`
  exist.
- Auth: `GET /api/get-access-token` with HTTP Basic (partner username/password) returns
  `access_token` and `expires_at` (1 hour). Send `Authorization: Bearer <token>` on every
  other call. Refresh before expiry; there is no refresh token.
- Multi-entity partners add `API-ENTITY-ID` and `API-SECRET-KEY` headers.
- Pre-registration uses separate credentials: `GET /api/pre_registration/access-token` (HTTP
  Basic) returns a token sent as `X-EKINCARE-KEY: <token>` (no `Bearer`). Its `expires_at`
  is `YYYY-MM-DD HH:MM:SS UTC`, not ISO 8601. 401/403 bodies are empty.
- Credentials, the entity secret key and the webhook secret are server-side secrets. Read
  them from environment variables; never hard-code them, print them, or put them in client
  code.
- Send the `plan_id` issued with the partner's package ids; without it the base plan is
  used, and a service not on it returns `403 this service is not enabled for you`.
- Prefer the official SDKs when the user's stack matches: https://github.com/hlthstack/js,
  https://github.com/hlthstack/python, https://github.com/hlthstack/java. The web/PWA embed
  is https://github.com/hlthstack/web.

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
- Pre-registration (async): `getPreRegistrationAccessToken` -> `createPreRegistrations` /
  `updatePreRegistrations` / `deactivatePreRegistrations` (each returns `request_id`) ->
  poll `getPreRegistrationStatus` until `status` is `completed` or `failed`. On create, every required
  key must be present in every row (empty values allowed) or the row is silently dropped;
  at most 250 rows per request. See `references/pre-registration.md`.
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
  `references/errors.md`. A 401 with plain text `HTTP Token: Access denied.` means the token is bad
  or expired.
- Never rename fields to match a preferred style: send and read field names exactly as the
  spec shows.

## Webhooks

Status changes arrive by POST with a `Signature` header: an HS256 JWT signed with the
partner's webhook secret. It doesn't cover the body, so verify the signature, check that its
ids (`appointment_id`/`booking_id`, `order_id` or `request_id`) match the body, and reject
stale `timestamp`s. Reply 2xx within 30 s and process asynchronously; most non-2xx replies
are not retried. Payload schemas are under `webhooks` in the spec; verification code is in
`references/webhooks.md`.

## When calling the live API on the user's behalf

Use staging unless the user explicitly asks for production. Confirm with the user before
creating, rescheduling or cancelling real bookings or orders, or pre-registering, updating or
deactivating members, since these affect real members and benefit balances.

<!-- Copied from docs/glossary.md by scripts/sync_skill_references.py. Edit the source. -->

# Glossary

Plain-language meanings of the terms used across the hlthstack docs, in alphabetical order.
Each row links to the guide where the term matters most.

| Term | Meaning | Where it's used |
|---|---|---|
| **Access token** | A short-lived key your backend gets by exchanging its API username and password (`GET /api/get-access-token`). It is valid for 1 hour and is sent as `Authorization: Bearer <token>` on every API call. | [Authentication](authentication.md) |
| **AHC** | Annual health checkup. Booked with `service_name` `ahc`, which covers health checks and diagnostics. | [Health checkups and lab tests](health-checkups.md) |
| **API** | The hlthstack REST API: the HTTP calls your backend makes to book services, read benefits and register members. | [API reference](https://developers.hlthstack.io), [Getting started](getting-started.md) |
| **Appointment** (`appointment_id`) | One member's appointment within a booking, identified by `appointment_id` (`APT` + 9 characters). Use it to act on one member. Compare **Booking**. | [FAQ](faq.md#what-is-the-difference-between-booking_id-and-appointment_id), [Health checkups](health-checkups.md) |
| **Booking** (`booking_id`) | One booking request, identified by `booking_id` (`EKI` + 19 characters). It can cover several members, each with their own appointment. Use it to reschedule, cancel or fetch everything. | [FAQ](faq.md#what-is-the-difference-between-booking_id-and-appointment_id), [Health checkups](health-checkups.md) |
| **Co-pay / payment link** | When a member has to pay part of the cost (or the wallet doesn't cover it), the response carries a `payment_link` to send them. The link expires; an unpaid booking or order is not confirmed. | [Health checkups](health-checkups.md#payment-window), [Consultations](consultations.md), [ePharmacy](epharmacy.md#payment-flows) |
| **Consultation types** | **In-clinic**: in person at the doctor's clinic. **Scheduled online**: an audio or video call at a slot the member books. **Priority online**: no slot; a doctor calls within about 4 hours (available 8 AM-4 PM IST). | [Consultations](consultations.md#4-the-three-consultation-types) |
| **Deeplink** | A value sent when launching the member app that opens a specific page after sign-in, such as `new-benefits/ahc`. Any value that isn't recognised opens the home page. | [PWA guide](pwa.md#deeplinks) |
| **Entity / multi-entity partner** | An entity is the employer, group or programme a member belongs to (`entity_id`). A multi-entity partner serves several entities; its API credentials are issued for the first one, and the `API-ENTITY-ID` and `API-SECRET-KEY` headers act for the others. | [Authentication](authentication.md#multi-entity-partners) |
| **Environment** | **Staging** is for building and testing your integration; **production** is for live members. Credentials, package ids, plan ids, entity ids and webhook secrets differ between them. | [Environments](environments.md) |
| **Home collection** | A booking type (`home_collection`) where the service happens at the member's address instead of at the provider (`inclinic`). The provider must support it. | [Health checkups](health-checkups.md#4-booking-types) |
| **Package / package id** | A test bundle or service you can book. Package ids are shared at onboarding and sent as `package_ids`. | [Health checkups](health-checkups.md#1-overview), [Consultations](consultations.md) |
| **Phlebotomist ("phlebo")** | The person assigned to an appointment to collect samples. Once one is assigned, webhooks carry `phlebo_name` and `phlebo_number`, and some providers no longer accept changes. | [Webhooks](webhooks.md), [Health checkups](health-checkups.md#booking-rules) |
| **Plan / plan id** | The benefit plan your members are enrolled on, identified by `plan_id`. Plan ids are shared at onboarding and can't be discovered through the API. When you leave `plan_id` out, the base plan is used. | [ePharmacy](epharmacy.md#plan_id), [Health checkups](health-checkups.md#1-overview) |
| **Pre-registration** | Registering your members and their dependants with hlthstack in bulk (up to 250 rows a request) before they first sign in, and updating or deactivating them later. It has its own login and token. | [Pre-registration](pre-registration.md) |
| **Provider** | The centre (or branch) that delivers a service, identified by `provider_id`. For consultations, each provider is one doctor. | [Health checkups](health-checkups.md#1-overview), [Consultations](consultations.md#1-overview) |
| **PWA (member app)** | The hlthstack progressive web app: a ready-made member app with the health benefits, which you open in a WebView inside your Android or iOS app, or in a browser tab from your website. | [PWA guide](pwa.md) |
| **SAML** | SAML 2.0 single sign-on: employees sign in to the member app with their work account through the employer's own identity provider (such as Okta or Microsoft Entra ID), with no hlthstack password. | [SAML guide](saml.md) |
| **SDK** | Server-side libraries for JavaScript, Python and Java that call the API for you. They fetch and refresh tokens and check requests against the API's rules before sending. | [JavaScript](https://github.com/hlthstack/js), [Python](https://github.com/hlthstack/python), [Java](https://github.com/hlthstack/java) |
| **`service_name`** | Names the service on a call. Commonly used values: `ahc`, `dental`, `vision`, `flu_vaccination`. Each one you call must be enabled on your plan. | [Health checkups](health-checkups.md#1-overview) |
| **Slot** | A bookable time at a provider. You read a provider's slots (the next 14 days by default) and book with the slot's `utc_slot_time`. | [Health checkups](health-checkups.md#72-get-slots), [Consultations](consultations.md) |
| **Slug** | A short name issued at onboarding. Two kinds: the **PWA slug** (`slug`) identifies you as an integration partner in the member-app launch URL; the **company slug** goes in the path of the wallet endpoints. | [PWA guide](pwa.md#2-onboarding-checklist), [Wallet](wallet.md) |
| **SSO** | Single sign-on. For the member app, your backend vouches for a member already signed in to your app with an encrypted, short-lived payload, so they never see a login screen. Compare **SAML**. | [PWA guide](pwa.md#3-how-sso-works) |
| **Subscription** | A member's enrolment in a plan. A member can have more than one; `customer_plan_id` / `subscription_id` choose which one pays for a booking. | [Wallet](wallet.md) |
| **Voucher** | A PDF available once a booking or in-clinic consultation is confirmed. For an in-clinic consultation, the member shows it at the clinic. | [Health checkups](health-checkups.md#77-voucher), [Consultations](consultations.md#78-voucher) |
| **Wallet** | A member's benefit balances (for them and their family) and plan subscriptions. | [Wallet](wallet.md) |
| **Webhook** | A message hlthstack sends (an HTTP `POST`) to a URL you register, telling you a status changed, so you don't have to poll. Every webhook is signed with your webhook secret. | [Webhooks](webhooks.md) |
| **White-labelling** | Sending hlthstack's messages to your members under your app name, sender name and logo, by email only or by email, WhatsApp and SMS. hlthstack sets it up for you. | [White-labelling](white-labelling.md) |
| **`X-EKINCARE-KEY`** | The header that carries the pre-registration token (without a `Bearer` prefix). | [Pre-registration](pre-registration.md#authentication), [Authentication](authentication.md#pre-registration) |

**See also:** [hlthstack for business teams](for-business-teams.md) ·
[Getting started](getting-started.md)

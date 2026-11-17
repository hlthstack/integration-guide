# Getting started

From first contact to live bookings in six steps. Each step links to the guide with the
details.

| Step | What you do | Details |
|---|---|---|
| [1. Request access](#1-request-access) | Ask hlthstack for staging credentials and ids | [hlthstack.io](https://www.hlthstack.io/) |
| [2. Make your first calls on staging](#2-make-your-first-calls-on-staging) | Call the API with Postman, curl or an SDK | [authentication.md](authentication.md), [environments.md](environments.md) |
| [3. Build the flows you need](#3-build-the-flows-you-need) | Implement the services on your contract | Service guides |
| [4. Receive webhooks](#4-receive-webhooks) | Register URLs and verify deliveries | [webhooks.md](webhooks.md) |
| [5. Test end to end on staging](#5-test-end-to-end-on-staging) | Drive bookings through their lifecycle | [testing.md](testing.md) |
| [6. Go live](#6-go-live) | Switch to production credentials and URLs | This page |

## 1. Request access

Contact hlthstack through https://www.hlthstack.io/ with:

- the services you want (health checkups and lab tests, consultations, ePharmacy, wallet,
  pre-registration), and
- whether you book for one company or several entities.

For staging you receive:

- [ ] an API username and password,
- [ ] your package ids and plan ids, and your company slug for the wallet endpoints,
- [ ] if you use pre-registration, a pre-registration login (email and password) and your
      company ids,
- [ ] if you are a multi-entity partner, entity ids and an API secret key.

## 2. Make your first calls on staging

Pick one:

| Option | How |
|---|---|
| **Postman** | Import the collection and staging environment (steps below) |
| **curl** | The [README quickstart](../README.md#quickstart) |
| **An SDK** | [JavaScript](https://github.com/hlthstack/js), [Python](https://github.com/hlthstack/python) or [Java](https://github.com/hlthstack/java). They fetch and refresh tokens for you and check requests against the API's rules before sending |

To set up **Postman**:

1. Open the [published Postman docs](https://documenter.getpostman.com/view/32733686/2sBYHbrFjt)
   and choose **Run in Postman**, or in Postman choose **Import**, paste
   `https://developers.hlthstack.io/postman/hlthstack.postman_collection.json`, then import
   `https://developers.hlthstack.io/postman/hlthstack-staging.postman_environment.json` the
   same way.
2. Select the *hlthstack Staging* environment and fill in `username` and `password`. Tokens
   are fetched and cached for you.
3. Replace the example ids (packages, providers, bookings) with your own.

The API reference is at https://developers.hlthstack.io.

**See also:** [authentication.md](authentication.md) and [environments.md](environments.md).

## 3. Build the flows you need

- [Health checkups and lab tests](health-checkups.md)
- [Consultations](consultations.md)
- [ePharmacy](epharmacy.md)
- [Wallet](wallet.md)
- [Pre-registration](pre-registration.md)
- [Errors](errors.md) and [common errors and how to fix them](common-errors.md)

> [!IMPORTANT]
> Also read [product communications](product-communications.md), so your app doesn't send
> members the same messages hlthstack already sends, and [white-labelling](white-labelling.md)
> if those messages should carry your brand.

## 4. Receive webhooks

- [ ] Send hlthstack your staging webhook URLs. You receive a signing secret for them.
- [ ] Verify every delivery.
- [ ] Handle duplicates and out-of-order events.

**See also:** [webhooks.md](webhooks.md)

## 5. Test end to end on staging

Staging has endpoints that move bookings and orders through their lifecycle and fire real
webhooks. Work through the checklist in [testing.md](testing.md).

## 6. Go live

> [!WARNING]
> Production credentials, package ids, plan ids and entity ids differ from staging; don't
> reuse staging values.

- [ ] Ask hlthstack for production credentials, package ids, plan ids and (if used) entity
      ids.
- [ ] Register your production webhook URLs and store the production signing secret.
- [ ] Switch the base URL to `https://api.hlthstack.io`.
- [ ] Remove any calls to staging-only endpoints (production returns 401 or 404 for them).
- [ ] Make one booking for a test member with hlthstack, follow it to `confirmed` by webhook,
      then cancel it.

## Support

| Need | Where |
|---|---|
| Integration questions | Your hlthstack contact, or https://www.hlthstack.io/ |
| Problems with these docs or the SDKs | Open an issue in the repository concerned |
| Security issues | See [SECURITY.md](../SECURITY.md); don't open a public issue |
| API changes | Listed in [CHANGELOG.md](../CHANGELOG.md) |

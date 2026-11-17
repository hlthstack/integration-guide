# Getting started

From first contact to live bookings. Each step links to the guide with the details.

## 1. Request access

Contact hlthstack through https://www.hlthstack.io/ with the services you want (health
checkups and lab tests, consultations, ePharmacy, wallet, pre-registration) and whether you
book for one company or several entities.

For staging you receive:

- an API username and password,
- your package ids and plan ids, and your company slug for the wallet endpoints,
- if you use pre-registration, a pre-registration login (email and password) and your
  company ids,
- if you are a multi-entity partner, entity ids and an API secret key.

## 2. Make your first calls on staging

Pick one:

- **Postman:** in Postman choose **Import**, paste
  `https://developers.hlthstack.io/postman/hlthstack.postman_collection.json`, then import
  `https://developers.hlthstack.io/postman/hlthstack-staging.postman_environment.json` the
  same way. Select the *hlthstack Staging* environment and fill in `username` and
  `password`. Tokens are fetched and cached for you. Replace the example ids (packages,
  providers, bookings) with your own.
- **curl:** the [README quickstart](../README.md#quickstart).
- **An SDK:** [JavaScript](https://github.com/hlthstack/js),
  [Python](https://github.com/hlthstack/python) or [Java](https://github.com/hlthstack/java).
  They fetch and refresh tokens for you and check requests against the API's rules
  before sending.

The API reference is at https://developers.hlthstack.io. See
[authentication.md](authentication.md) and [environments.md](environments.md).

## 3. Build the flows you need

- [Health checkups and lab tests](health-checkups.md)
- [Consultations](consultations.md)
- [ePharmacy](epharmacy.md)
- [Wallet](wallet.md)
- [Pre-registration](pre-registration.md)
- [Errors](errors.md)

## 4. Receive webhooks

Send hlthstack your staging webhook URLs. You receive a signing secret for them. Verify
every delivery and handle duplicates and out-of-order events; see [webhooks.md](webhooks.md).

## 5. Test end to end on staging

Staging has endpoints that move bookings and orders through their lifecycle and fire real
webhooks. Work through the checklist in [testing.md](testing.md).

## 6. Go live

1. Ask hlthstack for production credentials, package ids, plan ids and (if used) entity
   ids. They differ from staging; don't reuse staging values.
2. Register your production webhook URLs and store the production signing secret.
3. Switch the base URL to `https://api.hlthstack.io`.
4. Remove any calls to staging-only endpoints (production returns 401 or 404 for them).
5. Make one booking for a test member with hlthstack, follow it to `confirmed` by webhook,
   then cancel it.

## Support

- Integration questions: your hlthstack contact, or https://www.hlthstack.io/.
- Problems with these docs or the SDKs: open an issue in the repository concerned.
- Security issues: see [SECURITY.md](../SECURITY.md); don't open a public issue.
- API changes are listed in [CHANGELOG.md](../CHANGELOG.md).

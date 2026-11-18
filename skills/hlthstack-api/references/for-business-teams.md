<!-- Copied from docs/for-business-teams.md by scripts/sync_skill_references.py. Edit the source. -->

# hlthstack for business teams

A plain-language overview for product and business leads: what hlthstack offers your members,
the ways to integrate it, what your team decides and provides, and what happens from first
contact to go-live. There is no code on this page; share the developer pages linked at the end
with your technical team.

**On this page**

1. [What hlthstack is](#what-hlthstack-is)
2. [What members can get](#what-members-can-get)
3. [Three ways to integrate](#three-ways-to-integrate)
4. [What you decide and provide](#what-you-decide-and-provide)
5. [What you receive](#what-you-receive)
6. [From first contact to go-live](#from-first-contact-to-go-live)
7. [What members experience](#what-members-experience)
8. [Support and contact](#support-and-contact)
9. [Security](#security)
10. [Next: share these pages with your developers](#next-share-these-pages-with-your-developers)

Unfamiliar term? See the [glossary](glossary.md).

## What hlthstack is

hlthstack lets you offer health benefits to your members (for example, the employees of the
companies you serve) inside your own app or website. You can do this in two ways, or combine
them:

- **The member app**: a ready-made web app with the health benefits, which opens inside your
  Android or iOS app or in a browser tab from your website.
- **The API**: your developers build your own screens and your systems book services through
  hlthstack. hlthstack tells your systems when a booking's status changes.

## What members can get

Which services your members see depends on your contract and plan.

| Service | What members get |
|---|---|
| Health checkups and lab tests | Annual health checkups and lab tests, booked at a centre or with home sample collection at the member's address. A voucher is available once the booking is confirmed, and reports after the visit. |
| Dental, vision and vaccinations | Dental and vision checkups and vaccinations, booked the same way as health checkups. |
| Doctor consultations | In-clinic visits; scheduled online consultations by audio or video call; and priority online consultations, where a doctor calls within about 4 hours. After an online consultation, a summary and prescription are available. |
| ePharmacy | Medicine orders, found by name or from a prescription, with home delivery or store pickup. The member's benefit pays what it covers; any balance is paid by the member through a payment link, or collected by you if your contract allows. |
| Benefit wallets | The member's benefit balances (for them and their family) and their plan subscriptions. |
| Member registration | Your members and their dependants registered with hlthstack in bulk, so their account is ready when they first sign in. |

The member app also includes mental wellness, gyms, a health coach programme, a health risk
assessment, medical reports and a personal health profile, challenges, events, rewards,
booking history and family members. Not every page is available on every plan; hlthstack
confirms which are enabled for yours.

## Three ways to integrate

Many partners use both the member app and the API.

| | Embed the member app | Build your own screens with the API | Both |
|---|---|---|---|
| **What you build** | No service screens. An entry point in your app or site (for example a "Health benefits" button) that opens the member app. | Your own screens for each service, and the backend that books through hlthstack and receives status updates. | Your own screens where you use the API, plus the member-app entry point. |
| **Who does the work** | Your backend developer (signs members in securely) and your app team (WebView settings such as camera, file upload and cookies). | Your developers, who build screens and backend calls for each service and an endpoint for status updates. | Both teams. |
| **Look and feel** | hlthstack's member app. Ask hlthstack which theming options (colours, logo) are available for your integration. | Your own screens, with a native look and feel. | Your screens for the API services; the member app for the rest. |
| **Which services** | Every service enabled on your plan, through one integration. New features reach members without changes on your side. | The services you integrate one at a time: health checkups and lab tests, consultations, ePharmacy, wallet, member registration. | The services you integrate with the API, plus those enabled in the member app. |
| **Member sign-in** | Through your own login (members never see an hlthstack login screen), or with the employer's own sign-in (SAML). | Members use your app's sign-in; your systems identify each member to hlthstack with your own member id. | Both, as in the columns to the left. |

**See also:** [PWA or REST API?](pwa.md#1-overview) in the member-app
guide.

## What you decide and provide

Use this as your team's checklist when you contact hlthstack and during onboarding.

**Scope**

- [ ] Which services you want: health checkups and lab tests, consultations, ePharmacy,
      wallet, member registration (pre-registration).
- [ ] Whether you book for one company or for several entities (employers, groups or
      programmes).
- [ ] Which way to integrate: the member app, the API, or both.

**Member app (if you embed it)**

- [ ] Confirm with hlthstack which pages are enabled for your plan, so your app only links to
      those.
- [ ] Confirm how long a member-app session lasts, what members see when it times out, and how
      they get back to your app.
- [ ] Confirm which theming options (colours, logo) are available.
- [ ] Choose how members sign in: through your own app's login, or with the employer's own
      sign-in (SAML). For SAML, the employer's IT team sets up an app in their identity
      provider and sends hlthstack its details. Agree with hlthstack whether employees who
      aren't registered yet get a profile on first sign-in or see a "not registered" message.

**Members and services**

- [ ] Whether you register members in advance (pre-registration). Some entities are set up so
      that only members registered in advance can sign in; hlthstack tells you whether yours
      works this way.
- [ ] For consultations, which types you offer: in-clinic, scheduled online, priority online.
- [ ] For ePharmacy, your payment flow. It is fixed by your contract: fully covered by the
      member's wallet, a payment link sent to the member for the rest, or collected by you.

**Messages and branding**

- [ ] Which messages your own app sends, so members don't get the same message from you and
      from hlthstack (see [product communications](product-communications.md)).
- [ ] Whether those messages should carry your brand (white-labelling): email only, or email,
      WhatsApp and SMS, and for which companies. If so, provide your app name, sender name and
      logo (see [white-labelling](white-labelling.md#4-how-to-set-it-up)).

**Status updates**

- [ ] The web addresses where your systems receive status updates (webhooks), first for
      staging and then for production. Your developers provide these.

## What you receive

hlthstack issues these at onboarding. They are for your developers and must stay on your
servers.

| What you receive | When |
|---|---|
| An API username and password | Always, per environment |
| Package ids and plan ids (each package id paired with the plan and service it belongs to) | Always |
| Your company slug | For the wallet |
| A separate pre-registration login and your company ids | If you use pre-registration |
| Entity ids and an API secret key | If you serve several entities |
| A webhook signing secret | Once you register your webhook addresses |
| A partner slug, entity ids and an encryption key and IV | If you embed the member app |

> [!WARNING]
> Staging and production values are different. Your developers must not reuse staging values
> in production.

## From first contact to go-live

1. **Request access.** Contact hlthstack through [hlthstack.io](https://www.hlthstack.io/) with
   the services you want and whether you book for one company or several entities.
2. **Staging.** hlthstack gives you staging credentials and ids. Staging is a separate
   environment for building and testing.
3. **Build and test.** Your developers build the flows (or the member-app launch), register
   staging webhook addresses, and test end to end. On staging they can move bookings and
   orders through every status, and users and sessions created there never touch production
   data.
4. **Go live.** You ask hlthstack for production credentials and ids, register production
   webhook addresses and switch to production. A final check: one booking for a test member,
   made with hlthstack, followed to `confirmed` and then cancelled.

**See also:** the developer view of the same steps in [Getting started](getting-started.md).

## What members experience

| Topic | What happens | Read more |
|---|---|---|
| **Messages** | hlthstack sends members emails, WhatsApp, SMS, in-app and push messages about pharmacy orders, vision orders and consultations, automatically. Your app should not send its own copies. | [Product communications](product-communications.md) |
| **Branding** | Those messages can go out under your app name, sender name and logo. The member app's own theming is agreed with hlthstack. | [White-labelling](white-labelling.md) |
| **Sign-in** | With your own login, members open the member app from your app and never see a login screen. With SAML, employees sign in with their work account and never see an hlthstack password. | [Member-app SSO](pwa.md#3-how-sso-works), [SAML](saml.md) |
| **Payments** | When a benefit doesn't cover the full cost, the member may get a payment link for the rest (a co-pay). | [Glossary](glossary.md) |

## Support and contact

| For | Where |
|---|---|
| Questions and access | Your hlthstack contact, or [hlthstack.io](https://www.hlthstack.io/) |
| Problems with these docs or the SDKs | An issue in the repository concerned |
| Security issues | Privately, as described in [SECURITY.md](https://github.com/hlthstack/integration-guide/blob/main/SECURITY.md); not in a public issue |
| API changes | [CHANGELOG.md](https://github.com/hlthstack/integration-guide/blob/main/CHANGELOG.md) |

## Security

- **Reporting.** Report security issues privately through [hlthstack.io](https://www.hlthstack.io/)
  or your hlthstack contact, as described in [SECURITY.md](https://github.com/hlthstack/integration-guide/blob/main/SECURITY.md).
- **Credentials stay on your servers.** API passwords, pre-registration passwords, API secret
  keys and webhook signing secrets are issued per environment and must never be shipped in a
  mobile app or browser code. If one leaks, ask hlthstack to rotate it.
- **Member-app sign-in.** The member's sign-in details are encrypted on your server, and each
  sign-in request expires after 30 seconds.
- **Webhooks are signed.** Every status update hlthstack sends carries a signature made with
  your webhook secret, and your developers verify it before acting on it.

## Next: share these pages with your developers

- [Getting started](getting-started.md): the developer path from access to go-live, including
  the member-app embed track.
- [The member-app (PWA) guide](pwa.md), if you embed the
  member app.
- The [glossary](glossary.md), so both teams use the same words.

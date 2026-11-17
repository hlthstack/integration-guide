# Changelog

Changes to the hlthstack API spec ([`openapi/openapi.yaml`](openapi/openapi.yaml)) and the
guides. The spec's `info.version` follows [semantic versioning](https://semver.org/):

- **Major** (2.0.0): a breaking change, such as a removed endpoint or field, a new required
  field, or a changed type. Announced to partners in advance, with a migration window.
- **Minor** (1.1.0): something new that existing clients can ignore, such as an endpoint, an
  optional field, a response field or a new enum value. Clients should tolerate unknown
  fields and enum values.
- **Patch** (1.0.1): documentation fixes and clarifications; the API itself is unchanged.

Each release is a git tag (`v1.0.1`). Watch this repository's releases to be notified.

## 1.0.1 (2026-11-17)

Documentation and corrections; no endpoint or field was added or removed.

- Each API area's guide is now part of the reference at developers.hlthstack.io and of each
  Postman folder, with Getting started, Environments, Webhooks, Errors and FAQ sections.
- Health checkups: booking hours, day's notice, time zone handling, the 5-minute wait and
  provider-specific rules, the plan service period on reschedule, and the co-pay link
  deadline. The phlebotomist cut-off is a provider setting, and the different-provider block
  applies at providers connected through a partner integration.
- Consultations: `service_mode` is required (as the API already enforced); every customer in
  a request is booked; the 90-minute notice for some doctors; co-pay and `payment_pending`;
  reschedule and cancel rules and refunds; `meeting_link`, uploads, summary and voucher;
  webhook sequences; `is_disrupted` and `disruption_reason` on providers.
- Pre-registration: requests can end `failed`; retry only failed rows; adding a dependant to
  an existing employee.
- Errors: 400 for malformed ids vs 403 for ids that aren't yours. Webhooks: return 503, not
  500, for temporary failures.

## 1.0.0 (2026-11-17)

First stable release of the spec and guides.

- Health checkups and lab tests, consultations, ePharmacy, wallet, pre-registration and
  webhooks, with request schemas that encode the server's input validation and
  `x-hlthstack-rules` for cross-field rules.
- `CancelRequest` with an optional `reason`; `payment_pending` status; report link expiry.
- Hosted API reference and Postman collection at https://developers.hlthstack.io.
- Getting started guide, AI assistant skill and plugins for Claude Code, Codex and ChatGPT.

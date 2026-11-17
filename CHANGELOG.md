# Changelog

Changes to the hlthstack API spec ([`openapi/openapi.yaml`](openapi/openapi.yaml)) and the
guides. The spec's `info.version` follows [semantic versioning](https://semver.org/):

- **Major** (2.0.0): a breaking change, such as a removed endpoint or field, a new required
  field, or a changed type. Announced to partners in advance, with a migration window.
- **Minor** (1.1.0): something new that existing clients can ignore, such as an endpoint, an
  optional field, a response field or a new enum value. Clients should tolerate unknown
  fields and enum values.
- **Patch** (1.0.1): documentation fixes and clarifications; the API itself is unchanged.

Each release is a git tag (`v1.0.0`). Watch this repository's releases to be notified.

## 1.0.0 (2026-11-17)

First stable release of the spec and guides.

- Health checkups and lab tests, consultations, ePharmacy, wallet, pre-registration and
  webhooks, with request schemas that encode the server's input validation and
  `x-hlthstack-rules` for cross-field rules.
- `CancelRequest` with an optional `reason`; `payment_pending` status; report link expiry.
- Hosted API reference and Postman collection at https://developers.hlthstack.io.
- Getting started guide, AI assistant skill and plugins for Claude Code, Codex and ChatGPT.

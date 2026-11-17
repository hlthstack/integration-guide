# Security

## Reporting a vulnerability

If you find a security issue in the hlthstack API, the SDKs or these docs, report it
privately through https://www.hlthstack.io/ (or to your hlthstack account contact) rather
than in a public GitHub issue. Include the endpoint or file, the steps to reproduce and
the impact. We'll acknowledge the report and keep you updated until it is fixed.

## Handling your credentials

- API passwords, pre-registration passwords, API secret keys and webhook signing secrets
  are issued per environment. Keep them server-side; never ship them in a mobile app or
  browser code.
- If a credential leaks, ask hlthstack to rotate it.
- Verify every webhook's signature, id and timestamp before acting on it; see
  [docs/webhooks.md](docs/webhooks.md).
- The examples in this repository use fake values only.

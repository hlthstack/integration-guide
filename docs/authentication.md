# Authentication

## 1. Get an access token

`GET /api/get-access-token` with HTTP Basic auth, using the username and password hlthstack
issued to you.

```bash
curl -u "$HS_USERNAME:$HS_PASSWORD" https://api.hlthstack.io/api/get-access-token
```

```json
{ "access_token": "YOUR_ACCESS_TOKEN", "expires_at": "2026-01-15T07:16:21Z" }
```

- The token is valid for **1 hour** (`expires_at`, ISO 8601 UTC). There is no refresh token:
  request a new one before it expires. Refresh a few minutes early rather than reacting to 401s.
- Wrong credentials: `401 {"message": "Wrong credentials"}`.

## 2. Call the API with the token

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

A missing, invalid or expired token returns `401` with the plain-text body
`HTTP Token: Access denied.`

## Multi-entity partners

If your company has several entities, credentials are issued for your first entity. To act
for another entity, add two headers to every call (except `get-access-token`):

| Header | Value |
|---|---|
| `API-ENTITY-ID` | The id of the entity to act for (shared at onboarding) |
| `API-SECRET-KEY` | The secret key shared at onboarding. Required whenever `API-ENTITY-ID` is sent |

Without `API-ENTITY-ID`, calls act for the entity tied to the credentials. For example, with
entities A and B and credentials issued for A, a booking without the header is created under
A; with `API-ENTITY-ID: <B's id>` it is created under B.

Header errors are `400 {"message": "..."}`:

| Message | Cause |
|---|---|
| `API-ENTITY-ID header cannot be blank` | Header present but empty |
| `API-SECRET-KEY header cannot be blank` | Entity id sent without the secret key |
| `Invalid Entity` | Unknown entity id |
| `API integration not enabled for this entity` | The entity is not set up for API access |
| `API-SECRET-KEY is invalid` | Wrong secret key |

## API access per entity

If the entity's contract is not enabled for API booking, every call returns
`400 {"message": "The entity is not enabled for API booking."}`. Contact hlthstack.

## Pre-registration

The pre-registration endpoints use separate credentials and a separate token, sent as
`X-EKINCARE-KEY` instead of `Authorization: Bearer`. See
[pre-registration.md](pre-registration.md#authentication).

## Keep credentials secret

Credentials, tokens, the entity secret key and the webhook secret are server-side secrets.
Never ship them in a browser or mobile app; call the API from your backend.

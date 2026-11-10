# Pre-registration

Register your members (employees) and their dependants with hlthstack in bulk, update them,
and deactivate them when they leave. Every write is processed asynchronously: the call
returns a `request_id`, and `getPreRegistrationStatus` reports each row's outcome.

| Operation | Endpoint |
|---|---|
| `getPreRegistrationAccessToken` | `GET /api/pre_registration/access-token` |
| `createPreRegistrations` | `POST /v1/corporate/pre_registrations` |
| `updatePreRegistrations` | `POST /v1/corporate/pre_registrations/update` |
| `deactivatePreRegistrations` | `POST /v1/corporate/pre_registrations/deactivate` |
| `getPreRegistrationStatus` | `GET /v1/corporate/pre_registrations/{request_id}/status` |

The endpoints are served on the same hosts as the rest of the API
(`https://api.hlthstack.io`, `https://staging-api.hlthstack.io`).

## Authentication

Pre-registration has **its own credentials**, separate from the booking API username and
password: an account email and password that hlthstack issues for pre-registration. Ask for
them at onboarding. The booking API's bearer token does not work here, and this token does
not work on the booking API.

1. `GET /api/pre_registration/access-token` with HTTP Basic auth (the account email as the
   username):

   ```bash
   curl -u "$HS_PREREG_USERNAME:$HS_PREREG_PASSWORD" \
     https://staging-api.hlthstack.io/api/pre_registration/access-token
   ```

   ```json
   { "access_token": "YOUR_PRE_REGISTRATION_TOKEN", "expires_at": "2026-01-15 07:16:21 UTC" }
   ```

   Wrong or missing credentials: `401 {"message": "Wrong credentials"}`.

2. Send the token, without a `Bearer` prefix, in the `X-EKINCARE-KEY` header:

   ```
   X-EKINCARE-KEY: YOUR_PRE_REGISTRATION_TOKEN
   ```

- The token is valid for **1 hour**. `expires_at` is UTC but formatted
  `YYYY-MM-DD HH:MM:SS UTC`, not ISO 8601. There is no refresh token: request a new one
  before it expires.
- A missing, invalid or expired token returns `401` with an **empty body**. So does any token
  once your company's contract has ended.
- `403` with an empty body means the account's role may not use this API. Contact hlthstack.
- The `API-ENTITY-ID` / `API-SECRET-KEY` headers are not used here. Each row names its
  company with `company_id` instead.

## Register members and dependants

`POST /v1/corporate/pre_registrations`

```bash
curl -s -X POST "$BASE/v1/corporate/pre_registrations" \
  -H "X-EKINCARE-KEY: $PREREG_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "employees": [{
      "employee_code": "EMP1001", "company_id": "1001",
      "first_name": "Jane", "last_name": "Doe", "email": "jane.doe@example.com",
      "date_of_birth": "24-08-1990", "gender": "Female", "mobile_number": "9999999999",
      "vip": "No", "entity_name": "", "employee_office_location": "Hyderabad",
      "department": "Engineering", "grade": "B", "date_of_joining": "01-01-2026"
    }],
    "dependants": [{
      "guardian_email": "jane.doe@example.com", "dependent_code": "DEP-001",
      "first_name": "John", "last_name": "Doe", "date_of_birth": "10-02-1960",
      "gender": "Male", "mobile_number": "9999999998", "relation": "Father"
    }]
  }'
```

```json
{ "message": "Request has been accepted", "request_id": "3f2b8c1e-0d4a-4c5e-9b7a-2e6f1d8c9a01" }
```

Send `employees`, `dependants` or both, with **at most 250 rows in total**. Employees are
processed before dependants, so a dependant can refer to an employee in the same request.

> **Every required key must be present in every row**, even when the value is empty (`""`
> or `null`). A row missing one of them is dropped silently: it is neither registered nor
> listed in the status. If no row is left, the call fails with
> `400 {"message": "missing param or invalid params"}`.

### Employee fields

| Field | Key required | Notes |
|---|---|---|
| `company_id` | yes | The company (or entity) the member belongs to, shared at onboarding. Must be one your credentials can act on, otherwise the row fails with `provided company_id is not valid` |
| `employee_code` | yes | Value required when `email` is empty. Unique within the company |
| `email` | no | Value required when `employee_code` is empty. Unique |
| `first_name` | yes | Value required |
| `last_name` | yes | |
| `date_of_birth` | yes | `DD-MM-YYYY` or `DD/MM/YYYY`, in the past |
| `gender` | yes | `Male`, `Female` or `Non-binary` (any case) |
| `mobile_number` | yes | 10 digits, no country code |
| `vip` | yes | `Yes` or `No` (any case) |
| `entity_name` | yes | |
| `employee_office_location` | yes | |
| `department` | yes | |
| `grade` | yes | |
| `date_of_joining` | yes | `DD-MM-YYYY` or `DD/MM/YYYY` |
| `api_customer_id` | no | Your id for the member |
| `voluntary_plan_ids` | no | Plans to enrol the member in; see below |

An employee is identified by `email`, or by `employee_code` within `company_id` when there
is no email.

### Dependant fields

| Field | Key required | Notes |
|---|---|---|
| `guardian_email` | no | The employee's email. Required unless `company_id` + `guardian_employee_code` are sent |
| `company_id` + `guardian_employee_code` | no | The employee's company and `employee_code`, for employees without an email |
| `dependent_code` | no | Your id for the dependant. Unique per employee, case-insensitive |
| `email` | no | |
| `first_name` | yes | Value required |
| `last_name` | yes | |
| `date_of_birth` | yes | `DD-MM-YYYY` or `DD/MM/YYYY`, in the past |
| `gender` | yes | `Male` or `Female` (any case) |
| `mobile_number` | yes | 10 digits, no country code |
| `relation` | yes | `Father`, `Mother`, `Brother`, `Sister`, `Husband`, `Wife`, `Son`, `Daughter`, `Father in law` or `Mother in law` |
| `api_customer_id` | no | Your id for the dependant |
| `authorised_dependent` | no | `Yes` or `No`; defaults to `Yes` |

`voluntary_plan_ids` is not accepted on dependants: plans are held by the employee and
reach the family through it. The dependant is still registered, but the row is reported as
failed with `Voluntary plans can only be assigned to the primary member`.

### Voluntary plans

`voluntary_plan_ids` is an array. Each entry is a plan id (shared at onboarding) or an
object; the two forms can be mixed:

```json
"voluntary_plan_ids": [
  "EXAMPLE_PLAN",
  { "plan_id": "EXAMPLE_TOPUP", "start_date": "01-11-2026" },
  { "plan_id": "EXAMPLE_TOPUP", "additional": true, "subscription_id": "ORD-0001" }
]
```

| Key | Notes |
|---|---|
| `plan_id` | Required |
| `start_date` | `DD-MM-YYYY` or `YYYY-MM-DD`; defaults to today. Refused if after the plan's end date |
| `additional` | `true` adds another subscription to the plan, up to its limit. Otherwise a subscription the member already holds is reused. Counts only with `subscription_id` |
| `subscription_id` | Your own order id. Resending it returns the subscription it created, so retries never duplicate it |

The resulting subscriptions are listed in the status (`customer_plans`) and by
[`listCustomerPlans`](wallet.md#list-subscriptions).

## Update members and dependants

`POST /v1/corporate/pre_registrations/update` takes the same `employees` / `dependants`
arrays (at most 250 rows in total). Send the identifier and only the fields to change; no
other key is required.

```json
{
  "employees": [{ "email": "jane.doe@example.com", "department": "Finance" }],
  "dependants": [{ "guardian_email": "jane.doe@example.com", "dependent_code": "DEP-001", "last_name": "Doe-Smith" }]
}
```

Employees:

- Found by `email`, or by `company_id` + `employee_code` when no email is sent. The email
  itself can't be changed.
- Updatable: `first_name`, `last_name`, `date_of_birth`, `gender`, `mobile_number`, `vip`,
  `entity_name`, `employee_office_location`, `department`, `grade` (must be one of the
  company's grades), `date_of_joining`, `employee_code`, `api_customer_id`, and
  `voluntary_plan_ids` (same entries as above; an invalid or already active plan fails the
  row).

Dependants:

- Found by `api_customer_id`, then `dependent_code`, under the employee given by
  `guardian_email` (or `company_id` + `guardian_employee_code`). Otherwise by
  `mobile_number`, which must match exactly one dependant. At least one of the three is
  required.
- Updatable: `first_name`, `last_name`, `email`, `date_of_birth`, `gender`, `mobile_number`,
  `relation`, `authorised_dependent`, `api_customer_id`. Sending `dependent_code` on a
  dependant found another way sets or changes its code; an empty one never clears it.

On update, `mobile_number` is stored as the member's alternate mobile number.

## Deactivate members or dependants

`POST /v1/corporate/pre_registrations/deactivate`

```json
{ "employees": ["jane.doe@example.com"], "dependants": ["9999999997"] }
```

- `employees` is a list of employee emails; `dependants` a list of dependant mobile numbers.
  At most 250 entries in total.
- Deactivating an employee also deactivates all their dependants and cancels their ongoing
  appointments.
- Only members of companies your credentials can act on are deactivated; others are
  reported as not found.

## Check the outcome

`GET /v1/corporate/pre_registrations/{request_id}/status`

```json
{
  "request_id": "3f2b8c1e-0d4a-4c5e-9b7a-2e6f1d8c9a01",
  "status": "completed",
  "success_records": [{
    "employee_code": "EMP1001", "first_name": "Jane", "last_name": "Doe",
    "email": "jane.doe@example.com", "date_of_birth": "1990-08-24", "gender": "Female",
    "mobile_number": "9999999999", "vip": "No", "entity_name": null,
    "employee_office_location": "Hyderabad", "department": "Engineering",
    "customer_token": "EXAMPLE_CUSTOMER_TOKEN", "errors": [], "grade": "B",
    "guardian_email": null, "relation": null,
    "customer_plans": [{
      "customer_plan_id": 101, "subscription_id": null, "plan_id": "EXAMPLE_TOPUP",
      "plan_name": "Top-up", "start_date": "2026-01-15", "end_date": "2026-12-31",
      "grace_end_date": "2027-01-31", "status": "active"
    }]
  }],
  "failure_records": [{
    "employee_code": "EMP1002", "first_name": "Sam", "last_name": "Roe",
    "email": "sam.roe@example", "date_of_birth": "24-08-1990", "gender": "Male",
    "mobile_number": "12345", "vip": "No", "entity_name": "",
    "employee_office_location": "Hyderabad", "department": "Engineering",
    "guardian_email": null,
    "errors": ["Email is invalid", "Mobile number is not in the correct format for India"]
  }],
  "created_at": "2026-01-15T06:16:21Z"
}
```

- `status` moves `initialized` -> `scheduled` -> `inprogress` -> `completed`. Records are
  added while it is `inprogress`; poll (every few seconds, with backoff) until `completed`.
- Create and update requests: success records are the members as stored, dependants
  included (`employee_code` holds a dependant's `dependent_code`; `guardian_email` and
  `relation` are set). `customer_plans` lists active, upcoming and grace-period
  subscriptions. Failure records echo the row's fields with `errors`.
- Deactivate requests: success records carry `status` (`Active` / `Inactive`). Failure
  records are `{"errors": ["employee with email: ... not found"]}`.
- Unknown `request_id`: `404 {"message": "Request couldn't find with the id provided"}`.

### Row errors you may see

| Message | Meaning |
|---|---|
| `provided company_id is not valid` | Missing `company_id`, or one your credentials can't act on |
| `Email or employee code must be present` | Neither identifier sent |
| `First name must be present` / `First name is invalid` | |
| `Email is invalid` | |
| `Date of birth is invalid - valid format is DD-MM-YYYY or DD/MM/YYYY` / `Date of birth should be in the past` | |
| `Mobile number is not in the correct format for India` | Not a valid 10-digit number |
| `Gender is not included in the list` / `Vip is not included in the list` / `Relation is not included in the list` | |
| `Email already registered, but the profile is in active status.` / `Employee has already been taken` | Duplicate email or employee code |
| `Voluntary plan ids : (...), invalid or already exists` / `Invalid Plan ...` | Unknown plan, or already held |
| `Guardian email does not belong to any customer` / `Guardian email must be present` | Dependant's employee not found or not given |
| `Guardian not found - send guardian_email, or company_id with guardian_employee_code` | |
| `Dependent code already exists for this guardian` | |
| `Voluntary plans can only be assigned to the primary member` | Plans sent on a dependant |
| `Customer not found` | Update: no member matches the identifiers |
| `Mobile number or api_customer_id is required` | Update: dependant without an identifier |
| `Multiple members match this mobile number - send api_customer_id or dependent_code` | Update: ambiguous mobile number |
| `Failed to save record` | Unexpected failure for that row. Check the member before resending it |

## Call errors

| Status | Body | Cause |
|---|---|---|
| 400 | `{"message": "missing param or invalid params"}` | `employees`/`dependants` not a non-empty array, or no row has all the required keys |
| 400 | `{"message": "Request is too large"}` | More than 250 rows |
| 401 | empty | Missing, invalid or expired token, or contract ended |
| 403 | empty | The account's role may not use this API |
| 422 | `{"message": "something went wrong"}` | The request could not be queued; retry |

# Wallet and subscriptions

Read a member's benefit balances and plan subscriptions. Both endpoints include your
**company slug** (shared at onboarding) in the path. It must match the entity of the access
token, otherwise `403 {"error":"Invalid company slug for authenticated partner."}`.

## Get wallet details

`GET /api/{company_slug}/customers/wallet`

| Query param | Required | Notes |
|---|---|---|
| `api_customer_id` | one of the two | Your id for the member. Wins when both are sent |
| `customer_id` | one of the two | hlthstack's customer id |
| `plan_id` | no | Defaults to the base plan |
| `customer_plan_id` / `subscription_id` | no | Read one subscription (upcoming and ended ones included) |

Returns the member and their active family, primary member first. Passing a dependant's id
returns the whole family.

```json
{
  "status": "success",
  "data": {
    "members": [{
      "name": "Jane Doe", "gender": "FEMALE", "dob": "1990-08-24",
      "phone": "9999999999", "email": "jane@example.com",
      "relationship": "SELF", "relation": "self", "member_status": "ACTIVE",
      "wallet_details": {
        "benefits": [{
          "benefit_type": "pharmacy",
          "allocated_benefit_amount": 12500.0,
          "available_benefit_amount": 10000.0,
          "allocated_benefit_utilization_count": 0,
          "current_benefit_utilization_count": 0
        }],
        "total_allocated_amount": 12500.0,
        "available_amount": 10000.0
      }
    }]
  }
}
```

- A benefit appears only when an allocation exists for the member's relationship and age.
  With none, `benefits` is `[]` and both totals are `0`.
- `available_benefit_amount` never goes below zero.
- When a subscription was named, `data` also has `customer_plan_id` and `subscription_id`.

Errors:

| Status | Body |
|---|---|
| 400 | `{"errors":{"plan_id":["is invalid"]}}` |
| 400 | `{"message":"The entity is not enabled for API booking."}` |
| 401 | `HTTP Token: Access denied.` |
| 403 | `{"error":"Invalid company slug for authenticated partner."}` |
| 404 | `{"error":"No wallet details found for the provided customer and plan."}` |
| 422 | `{"errors":{"base":["At least one of api_customer_id or customer_id must be provided."]}}` |

## List subscriptions

`GET /api/{company_slug}/customers/plans?api_customer_id=...` (or `customer_id`)

One row per subscription: `customer_plan_id`, `subscription_id`, `plan_id`, `plan_name`,
`start_date`, `end_date`, `grace_end_date`, `status` (`active`, `upcoming` or `grace`;
lapsed subscriptions are left out) and `available_balance`. Unknown member:
`404 {"error":"Customer not found."}`.

## Paying from a specific subscription

When a member holds more than one subscription on a plan, send `customer_plan_id` (from this
endpoint) or `subscription_id` (your own id) on bookings and pharmacy orders to choose which
one pays. `customer_plan_id` wins when both are sent.

- Without `plan_id`, the subscription's plan is used. With `plan_id`, both must match.
- The subscription must belong to the member the booking is for.
- Errors are `400` and only occur when these fields are sent:

| Body | Meaning |
|---|---|
| `{"errors":{"customer_plan_id":["is invalid"]}}` (or `subscription_id`) | The member doesn't hold that subscription |
| `["does not belong to plan_id"]` | The subscription is on another plan |
| `["is not active"]` | It hasn't started or has ended. Nothing falls back to another subscription |
| `{"errors":{"subscription_id":["is held on more than one plan; send plan_id"]}}` | Ambiguous `subscription_id` |

Booking responses and webhooks carry `customer_plan_id` and `subscription_id` (both `null`
for base-plan bookings).

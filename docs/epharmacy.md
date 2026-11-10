# ePharmacy

Order medicines for members, paid from their pharmacy benefit. Schemas are in
[`openapi.yaml`](../openapi/openapi.yaml) (tag **ePharmacy**).

## Flow

```
1 GET  /api/get-access-token                  -> bearer token
2 GET  /api/epharmacy/medicines/search        -> medicine ids          (or step 3)
3 POST /api/prescriptions/digitize (+ status) -> items + cart_id       (optional, from a prescription)
4 PATCH /api/epharmacy/cart                   -> products, address, prescriptions
5 GET  /api/epharmacy/fulfillment_options     -> express | standard | pickup stores
6 PATCH /api/epharmacy/cart                   -> fulfillment_type + store  (store pickup only)
7 POST /api/epharmacy/orders/payment_details  -> final amounts, wallet split
8 POST /api/epharmacy/orders                  -> confirmed | payment_pending | partner_payment_pending
9 GET  /api/epharmacy/orders/{order_id} + webhooks -> track to delivery
```

## plan_id

`plan_id` identifies the benefit plan your members are enrolled on. It isn't discoverable
through the API: hlthstack shares your plan ids at onboarding. It is optional on every call
(the entity's base plan is used when omitted). Carts, orders and webhooks echo it back.

- Unknown or another company's plan: `400 {"errors":{"plan_id":["is invalid"]}}`
- Plan without a pharmacy benefit (payment details, create order):
  `422 {"success":false,"errors":{"msg":"Pharmacy benefit not enabled for this plan","recall":false}}`

## Payment flows

Your flow is fixed by your contract, not chosen per request.

| Flow | When | Create order returns | What you do | Webhook types |
|---|---|---|---|---|
| Wallet-covered | The wallet covers the whole order | `status: "confirmed"` | Nothing; track via webhooks | `status_update` |
| Payment pending | The wallet doesn't cover it; hlthstack collects the rest | `status: "payment_pending"` + `payment_link` | Send the link to the member. Unpaid orders are abandoned after 3 hours | `status_update` |
| Partner-collected | Enabled on your contract | `status: "partner_payment_pending"` + `amount_to_collect` | Collect that amount, then call Confirm order. Unconfirmed orders are abandoned after 3 hours | `status_update`, `additional_payment_required`, `post_billing` |

In the partner-collected flow hlthstack never holds the money, so `payment.refunded_amount`
stays `0.0`; settle using `post_billing.settlement.adjustment_amount` instead.

## 1. Find medicines

`GET /api/epharmacy/medicines/search?name=paracetamol&page=1`

- The parameter is `name` (at least 3 characters), not `query`.
- The returned `id` is the only id the cart accepts.
- `rx_required: true` means a prescription must be attached before ordering.

## 2. Or digitize a prescription

`POST /api/prescriptions/digitize` (multipart):

| Field | Required | Notes |
|---|---|---|
| `customers[][name]` | yes | `customers` must contain exactly one customer |
| `customers[][api_customer_id]` | yes | Alphanumeric |
| `customers[][mobile_number]` | yes | 10 digits |
| `customers[][gender]` | yes | `male`, `female` or `non-binary` |
| `customers[][dob]` | yes | Not in the future |
| `files[]` | yes | JPEG, PNG or PDF, each up to 10 MB |
| `plan_id` | no | |

Send an `Idempotency-Key` header (any unique string per upload) so retries return the
original request instead of creating a duplicate. The response is `202` with `request_id`
and `status: "pending"`.

Track with `GET /api/prescriptions/digitize/{request_id}` or the `digitization_results`
webhook. Statuses: `pending` -> `ai_processing` -> `manual_review` -> `completed` | `partial`
| `rejected` | `failed`. On `completed`/`partial` you get `items` and a ready `cart_id`.
File URLs are pre-signed and expire after 5 minutes: don't store them.

## 3. Build the cart

`PATCH /api/epharmacy/cart`. There is one cart per member per plan; this call finds or
creates it and merges your changes. Send `customer_details.api_customer_id` and at least one
change, otherwise `422 cart updates are required`. The update is atomic.

| Change | Body |
|---|---|
| Products | `products: [{id, quantity}]` (non-empty). `quantity` is a whole number: `0` removes a line, a positive value must not exceed the medicine's `limit_per_order`; ids you don't send are untouched; duplicate ids are rejected |
| New address | `address: {line1, line2, city, state, pincode, country, latitude, longitude}`. `line1`, `city`, `state`, `pincode` (6 digits; `zip_code` is accepted as an alias) are required; country defaults to India. The lines, city, state and country must not contain any other 6-digit pincode |
| Saved address | `address_id` (must belong to the member). Don't send both `address` and `address_id` |
| Prescription by URL | `prescription_urls: [...]` (up to 5; public HTTPS on port 443, no user info in the URL; PDF/PNG/JPEG under 7 MB) |
| Prescription upload | multipart `prescription_files[]` (each under 7 MB) |
| Remove prescriptions | `remove_prescription_ids: [...]` (non-empty; each must be attached to the cart) |
| Store pickup | `fulfillment_type: "store_pickup"` + `selected_chemist_id` (a store `id` from fulfillment options) |

`customer_details.name`, `dob`, `mobile_number` and `gender` are optional; they create the
member if `api_customer_id` is new and update the member otherwise. When sent non-empty,
`mobile_number` must be 10 digits and `gender` `male`, `female` or `non-binary` (any case).

Read the cart with `GET /api/epharmacy/cart?customer_details[api_customer_id]=...&plan_id=...`.
Carts don't expire. Because a cart can be old, prices, stock and serviceability are
re-evaluated on every fulfillment-options and payment-details call.

## 4. Fulfillment options

`GET /api/epharmacy/fulfillment_options?customer_details[api_customer_id]=...&cart_id=...`

- Slow: typically 3-8 seconds.
- Delivery and pickup are evaluated independently. HTTP 200 can still carry
  `{"success": false, ...}` inside `delivery_options` or `pickup_options`; check those flags.
- `express`/`standard` are omitted when no pharmacy can fulfil that mode.
- `missing_products` lists items no pharmacy can supply for that option.
- Each option has a `vendor_id` and a `location_token`:
  - pass `vendor_id` as `medicine_vendor_id` to payment details;
  - pass the chosen option's `location_token` to create order. Tokens are specific to one mode
    or one store and must not be cached; fetch options again if the member changes their mind.
- Offer store pickup only when `pickup_options.success` is true and stores are listed.

## 5. Payment details

`POST /api/epharmacy/orders/payment_details`

```json
{
  "plan_id": "EXAMPLE_PLAN",
  "customer_details": { "api_customer_id": "CUST1001" },
  "cart_id": 701,
  "selected_delivery_option": "standard",
  "medicine_vendor_id": 3
}
```

`selected_delivery_option` is `express`, `standard` or `store_pickup` (store pickup also
needs `selected_chemist_id`, matching the cart's store). In the response,
`payment_details.total_amount` is the order value, `wallet_deduction` +
`spending_balance_deduction` is the sponsor-funded part, and `total_payable` is what the
member still owes.

## 6. Create the order

`POST /api/epharmacy/orders`

```json
{
  "plan_id": "EXAMPLE_PLAN",
  "customer_details": { "api_customer_id": "CUST1001" },
  "cart_id": 701,
  "delivery_option": "standard",
  "location_token": "OPAQUE_TOKEN"
}
```

- The field is `delivery_option` here (default `standard`), not `selected_delivery_option`.
- For store pickup, set it on the cart first; don't pass the store here.
- `location_token` must belong to the option you're ordering. Some pharmacies reject the order
  at confirmation without it.
- Optional: `medicine_vendor_id`, `coupon_code`, `customer_plan_id` / `subscription_id`.

The response `status` is `confirmed`, `payment_pending` (with `payment_link`) or
`partner_payment_pending` (with `order_id`, `amount_to_collect`, `currency`). Each includes
`booking_id` and the order in `user_prescription_details` (its `unique_id` is the order id).

## 7. Confirm a partner-collected payment

`POST /api/epharmacy/orders/{order_id}/confirm`

```json
{
  "customer_details": { "api_customer_id": "CUST1001" },
  "partner_collected_amount": "261.0",
  "partner_payment_reference": "TXN-0001"
}
```

| Result | Response |
|---|---|
| First confirmation | `200 {"status": "confirmed", ...}` |
| Replay with the same amount and reference | `200 {"status": "already_confirmed", ...}`, safe to retry |
| Concurrent confirmation in progress | `409 {"status": "transaction_locked", ...}`; back off and retry |
| Bad amount (must be a decimal greater than 0) or blank reference, wrong state, amount mismatch, already confirmed with another reference | `422 {"status": "invalid_payment", "errors": ...}` |

`errors` on 409/422 is either an array of strings or an object with a `base` key; handle both.

## 8. Track, list, cancel

- `GET /api/epharmacy/orders/{order_id}?customer_details[api_customer_id]=...` (the path id is
  the order's `unique_id`, e.g. `EPO...`). This is the source of truth.
- `GET /api/epharmacy/orders?customer_details[api_customer_id]=...&page=1&per_page=10`
  (newest first; `meta` has `current_page`, `next_page`, `prev_page`, `total_pages`, `total_count`).
- `PATCH /api/epharmacy/orders/{order_id}/cancel` with `customer_details`, `reason` and
  optional `message`. Only before the pharmacy ships, and never for split orders. Refunds run
  automatically. `422 {"success":false,"message":"Order cannot be cancelled"}` when outside
  the window.

## Substitutions and splits

- When a pharmacy substitutes an item, the next `status_update` webhook (and `getOrder`)
  carries the updated `order_items`. Compare against your previous snapshot.
- Partner-collected only: a more expensive substitute triggers `additional_payment_required`;
  a cheaper one comes back through `post_billing.settlement.adjustment_amount`.
- A pharmacy may split an order into shipments; `split_details.sub_orders` lists them, each
  with its own status and `shipment_details`.

## Order statuses

Match on `status`, never on `status_text` (it varies by pharmacy). Treat unknown statuses
gracefully.

| Group | Statuses |
|---|---|
| Before fulfilment | `received` (waiting for payment or your confirmation), `abandoned` (final; unpaid or unconfirmed after 3 hours), `failed` (final) |
| Prescription checks | `consultation_required`, `prescription_under_verification`, `verification_pending`, `onhold`, `verified`, `prescription_rejected` (final), `prescription_cancelled` (final), `ops_rejected` (final) |
| Fulfilment | `created`, `in_progress`, `processed`, `packing`, `packed` (for pickup: ready to collect), `invoice_generated`, `in_transit`, `in_delivery`, `out_for_delivery`, `delivery_postponed`, `delivered` |
| Cancellation and returns | `cancellation_request`, `cancellation_inprogress`, `cancelled` (final), `rejected` (final), `out_of_stock` (final), `returned`, `returned_and_refunded` (final) |

`delivered` is final except for a later move to `returned` / `returned_and_refunded`.

See [webhooks.md](webhooks.md) for payloads and [testing.md](testing.md) to simulate statuses
on staging.

# ePharmacy

**Resources for this service**

- **API reference:** [ePharmacy on developers.hlthstack.io](https://developers.hlthstack.io/#tag/ePharmacy): every endpoint with its parameters, responses and errors.
- **Try it in Postman:** the *ePharmacy* folder of the [Postman docs](https://documenter.getpostman.com/view/32733686/2sBYHbrFjt), with code samples and **Run in Postman**.
- **SDK methods:** [JavaScript](https://github.com/hlthstack/js/blob/main/docs/sdk-integration.md#api) · [Python](https://github.com/hlthstack/python/blob/main/docs/sdk-integration.md#api-surface) · [Java](https://github.com/hlthstack/java/blob/main/docs/sdk-integration.md#api).
- **Calling the API without an SDK:** [JavaScript](https://github.com/hlthstack/js/blob/main/docs/api-integration.md#epharmacy-cart-to-order) · [Python](https://github.com/hlthstack/python/blob/main/docs/api-integration.md#epharmacy) · [Java](https://github.com/hlthstack/java/blob/main/docs/api-integration.md#epharmacy-cart-to-order).

**On this page**

1. [Overview](#1-overview)
2. [Onboarding checklist](#2-onboarding-checklist)
3. [How it works](#3-how-it-works)
4. [Fulfilment and payment options](#4-fulfilment-and-payment-options)
5. [Conventions and common errors](#5-conventions-and-common-errors)
6. [Rules and limits](#6-rules-and-limits)
7. [API reference](#7-api-reference)
8. [Webhooks](#8-webhooks)
9. [Statuses](#9-statuses)
10. [Troubleshooting](#10-troubleshooting)

## 1. Overview

Order medicines for members, paid from their pharmacy benefit. Schemas are in
[`openapi.yaml`](../openapi/openapi.yaml) (tag **ePharmacy**).

Find medicines by name or digitize a prescription, build the member's cart, choose delivery
or store pickup, check what the wallet covers, then create the order and track it to
delivery through `getOrder` and webhooks.

## 2. Onboarding checklist

- **Plan ids**: hlthstack shares your `plan_id` values at onboarding; they aren't
  discoverable through the API (see [plan_id](#plan_id)).
- **Your payment flow**: it is fixed by your contract (see
  [Payment flows](#payment-flows)). Partner-collected payment must be enabled on your
  contract.
- **Webhooks**: be ready to receive the webhook types for your flow (see
  [8. Webhooks](#8-webhooks) and [webhooks.md](webhooks.md)).

## 3. How it works

The calls in order, with what each one gives you:

```text
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

## 4. Fulfilment and payment options

### Delivery or store pickup

| Option | How to choose it |
|---|---|
| **Delivery** | `express` or `standard`. Choose the option in payment details (`selected_delivery_option`) and create order (`delivery_option`). |
| **Store pickup** | Set `fulfillment_type: "store_pickup"` + `selected_chemist_id` on the cart (step 6), then use `store_pickup` in payment details. Offer store pickup only when `pickup_options.success` is true and stores are listed. For pickup, `packed` means ready to collect. |

### Payment flows

Your flow is fixed by your contract, not chosen per request.

| Flow | When | Create order returns | What you do | Webhook types |
|---|---|---|---|---|
| Wallet-covered | The wallet covers the whole order | `status: "confirmed"` | Nothing; track via webhooks | `status_update` |
| Payment pending | The wallet doesn't cover it; hlthstack collects the rest | `status: "payment_pending"` + `payment_link` | Send the link to the member. Unpaid orders are abandoned after 3 hours | `status_update` |
| Partner-collected | Enabled on your contract | `status: "partner_payment_pending"` + `amount_to_collect` | Collect that amount, then call Confirm order. Unconfirmed orders are abandoned after 3 hours | `status_update`, `additional_payment_required`, `post_billing` |

> [!IMPORTANT]
> In the partner-collected flow hlthstack never holds the money, so `payment.refunded_amount`
> stays `0.0`; settle using `post_billing.settlement.adjustment_amount` instead.

## 5. Conventions and common errors

### plan_id

`plan_id` identifies the benefit plan your members are enrolled on. It isn't discoverable
through the API: hlthstack shares your plan ids at onboarding. It is optional on every call
(the entity's base plan is used when omitted). Carts, orders and webhooks echo it back.

| Case | Error |
|---|---|
| Unknown or another company's plan | `400 {"errors":{"plan_id":["is invalid"]}}` |
| Plan without a pharmacy benefit (payment details, create order) | `422 {"success":false,"errors":{"msg":"Pharmacy benefit not enabled for this plan","recall":false}}` |

### Other conventions

- Identify the member with `customer_details.api_customer_id` (cart, fulfillment options,
  payment details, orders).
- The medicine search parameter is `name`, not `query`.
- Payment details takes `selected_delivery_option`; create order takes `delivery_option`.
- An order's path id is its `unique_id` (e.g. `EPO...`).
- HTTP 200 from fulfillment options can still carry `{"success": false, ...}` inside
  `delivery_options` or `pickup_options`; check those flags.
- Match on `status`, never on `status_text` (it varies by pharmacy). Treat unknown statuses
  gracefully.
- `errors` on 409/422 from Confirm order is either an array of strings or an object with a
  `base` key; handle both.

## 6. Rules and limits

| Area | Rule |
|---|---|
| Medicine search | `name`: at least 3 characters. |
| Prescription digitization | `customers` must contain exactly one customer; `files[]` are JPEG, PNG or PDF, each up to 10 MB. Result file URLs expire after 5 minutes. |
| Cart | One per member per plan; carts don't expire. `quantity` is a whole number and a positive value must not exceed the medicine's `limit_per_order`. `prescription_urls` up to 5 (PDF/PNG/JPEG under 7 MB); `prescription_files[]` each under 7 MB. |
| Prescriptions | `rx_required: true` means a prescription must be attached before ordering. |
| Fulfillment options | Slow (typically 3-8 seconds); `location_token` values must not be cached. |
| Unpaid orders | Unpaid (`payment_pending`) or unconfirmed (`partner_payment_pending`) orders are abandoned after 3 hours. |
| Cancel | Only before the pharmacy ships, and never for split orders. |

> [!WARNING]
> Unpaid (`payment_pending`) or unconfirmed (`partner_payment_pending`) orders are abandoned
> after 3 hours. Send the `payment_link`, or call Confirm order, promptly.

## 7. API reference

| Method | Path | What it does |
|---|---|---|
| `GET` | `/api/epharmacy/medicines/search` | [Find medicines](#71-find-medicines) by name |
| `POST` | `/api/prescriptions/digitize` | [Digitize a prescription](#72-digitize-a-prescription) into items and a cart |
| `GET` | `/api/prescriptions/digitize/{request_id}` | [Track a digitization](#72-digitize-a-prescription) |
| `PATCH` | `/api/epharmacy/cart` | [Build the cart](#73-build-the-cart) (find or create, then merge changes) |
| `GET` | `/api/epharmacy/cart` | [Read the cart](#73-build-the-cart) |
| `GET` | `/api/epharmacy/fulfillment_options` | [Fulfillment options](#74-fulfillment-options): delivery modes and pickup stores |
| `POST` | `/api/epharmacy/orders/payment_details` | [Payment details](#75-payment-details): final amounts and wallet split |
| `POST` | `/api/epharmacy/orders` | [Create the order](#76-create-the-order) |
| `POST` | `/api/epharmacy/orders/{order_id}/confirm` | [Confirm a partner-collected payment](#77-confirm-a-partner-collected-payment) |
| `GET` | `/api/epharmacy/orders/{order_id}` | [Get an order](#78-get-an-order) |
| `GET` | `/api/epharmacy/orders` | [List orders](#79-list-orders) |
| `PATCH` | `/api/epharmacy/orders/{order_id}/cancel` | [Cancel an order](#710-cancel-an-order) |

### 7.1 Find medicines

Search the catalogue for medicine ids to put in the cart.

`GET /api/epharmacy/medicines/search?name=paracetamol&page=1`

- The parameter is `name` (at least 3 characters), not `query`.
- The returned `id` is the only id the cart accepts.
- `rx_required: true` means a prescription must be attached before ordering.

### 7.2 Digitize a prescription

Turn a prescription file into cart items. Optional alternative to 7.1.

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

> [!TIP]
> Send an `Idempotency-Key` header (any unique string per upload) so retries return the
> original request instead of creating a duplicate.

Response notes:

- The response is `202` with `request_id` and `status: "pending"`.
- Track with `GET /api/prescriptions/digitize/{request_id}` or the `digitization_results`
  webhook (statuses in [9. Statuses](#digitization-statuses)).
- On `completed`/`partial` you get `items` and a ready `cart_id`.
- File URLs are pre-signed and expire after 5 minutes: don't store them.

### 7.3 Build the cart

Add products, an address and prescriptions to the member's cart.

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

Member details: `customer_details.name`, `dob`, `mobile_number` and `gender` are optional;
they create the member if `api_customer_id` is new and update the member otherwise. When
sent non-empty, `mobile_number` must be 10 digits and `gender` `male`, `female` or
`non-binary` (any case).

Read the cart with `GET /api/epharmacy/cart?customer_details[api_customer_id]=...&plan_id=...`.
Carts don't expire. Because a cart can be old, prices, stock and serviceability are
re-evaluated on every fulfillment-options and payment-details call.

### 7.4 Fulfillment options

See which delivery modes and pickup stores can fulfil the cart.

`GET /api/epharmacy/fulfillment_options?customer_details[api_customer_id]=...&cart_id=...`

- Slow: typically 3-8 seconds.
- Delivery and pickup are evaluated independently. HTTP 200 can still carry
  `{"success": false, ...}` inside `delivery_options` or `pickup_options`; check those flags.
- `express`/`standard` are omitted when no pharmacy can fulfil that mode.
- `missing_products` lists items no pharmacy can supply for that option.
- Each option has a `vendor_id` and a `location_token`:
  - pass `vendor_id` as `medicine_vendor_id` to payment details;
  - pass the chosen option's `location_token` to create order.
- Offer store pickup only when `pickup_options.success` is true and stores are listed.

> [!WARNING]
> Tokens are specific to one mode or one store and must not be cached; fetch options again
> if the member changes their mind.

### 7.5 Payment details

Get the final amounts and how much the wallet covers.

`POST /api/epharmacy/orders/payment_details`. Example body:

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
needs `selected_chemist_id`, matching the cart's store).

| Response field | Meaning |
|---|---|
| `payment_details.total_amount` | The order value |
| `wallet_deduction` + `spending_balance_deduction` | The sponsor-funded part |
| `total_payable` | What the member still owes |

### 7.6 Create the order

Place the order from the cart.

`POST /api/epharmacy/orders`. Example body:

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

Response notes: each response includes `booking_id` and the order in
`user_prescription_details` (its `unique_id` is the order id).

| Response `status` | Comes with |
|---|---|
| `confirmed` | |
| `payment_pending` | `payment_link` |
| `partner_payment_pending` | `order_id`, `amount_to_collect`, `currency` |

### 7.7 Confirm a partner-collected payment

Tell hlthstack you have collected the member's payment (partner-collected flow).

`POST /api/epharmacy/orders/{order_id}/confirm`. Example body:

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

> [!NOTE]
> `errors` on 409/422 is either an array of strings or an object with a `base` key; handle both.

### 7.8 Get an order

Read one order's current state.

`GET /api/epharmacy/orders/{order_id}?customer_details[api_customer_id]=...` (the path id is
the order's `unique_id`, e.g. `EPO...`). This is the source of truth.

### 7.9 List orders

List a member's orders.

`GET /api/epharmacy/orders?customer_details[api_customer_id]=...&page=1&per_page=10`
(newest first; `meta` has `current_page`, `next_page`, `prev_page`, `total_pages`, `total_count`).

### 7.10 Cancel an order

Cancel an order before it ships.

`PATCH /api/epharmacy/orders/{order_id}/cancel` with `customer_details`, `reason` and
optional `message`.

- Only before the pharmacy ships, and never for split orders.
- Refunds run automatically.
- Errors: `422 {"success":false,"message":"Order cannot be cancelled"}` when outside the
  window.

## 8. Webhooks

See [webhooks.md](webhooks.md) for payloads.

| Type | Sent for |
|---|---|
| `status_update` | Order status changes, in every payment flow |
| `additional_payment_required` | Partner-collected only: a more expensive substitute |
| `post_billing` | Partner-collected only: settlement, including a cheaper substitute through `post_billing.settlement.adjustment_amount` |
| `digitization_results` | Prescription digitization results |

### Substitutions and splits

- When a pharmacy substitutes an item, the next `status_update` webhook carries the updated
  `order_items`, and `getOrder` the updated `order.products`. Compare them with your previous
  snapshot.
- Partner-collected only: a more expensive substitute triggers `additional_payment_required`;
  a cheaper one comes back through `post_billing.settlement.adjustment_amount`.
- A pharmacy may split an order into shipments; `split_details.sub_orders` lists them, each
  with its own status and `shipment_details`.

## 9. Statuses

<a id="order-statuses"></a>

### Order statuses

> [!IMPORTANT]
> Match on `status`, never on `status_text` (it varies by pharmacy). Treat unknown statuses
> gracefully.

| Group | Statuses |
|---|---|
| Before fulfilment | `received` (waiting for payment or your confirmation), `abandoned` (final; unpaid or unconfirmed after 3 hours), `failed` (final) |
| Prescription checks | `consultation_required`, `prescription_under_verification`, `verification_pending`, `onhold`, `verified`, `prescription_rejected` (final), `prescription_cancelled` (final), `ops_rejected` (final) |
| Fulfilment | `created`, `in_progress`, `processed`, `packing`, `packed` (for pickup: ready to collect), `invoice_generated`, `in_transit`, `in_delivery`, `out_for_delivery`, `delivery_postponed`, `delivered` |
| Cancellation and returns | `cancellation_request`, `cancellation_inprogress`, `cancelled` (final), `rejected` (final), `out_of_stock` (final), `returned`, `returned_and_refunded` (final) |

`delivered` is final except for a later move to `returned` / `returned_and_refunded`.

See [testing.md](testing.md) to simulate statuses on staging.

### Digitization statuses

`pending` -> `ai_processing` -> `manual_review` -> `completed` | `partial` | `rejected` |
`failed`. On `completed`/`partial` you get `items` and a ready `cart_id`.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `400 {"errors":{"plan_id":["is invalid"]}}` | Unknown or another company's plan | Use a plan id shared at onboarding, or omit it for the entity's base plan |
| `422` `Pharmacy benefit not enabled for this plan` on payment details or create order | The plan has no pharmacy benefit | Use a plan with a pharmacy benefit |
| Medicine search returns nothing useful | Searched with `query`, or `name` shorter than 3 characters | Use `name` with at least 3 characters |
| Cart rejects a product | Not an `id` from medicine search, a duplicate id, or `quantity` above `limit_per_order` | Use the search `id`, send each id once, stay within `limit_per_order` |
| `422 cart updates are required` | No change sent with `customer_details.api_customer_id` | Send at least one change |
| Delivery or pickup missing despite HTTP 200 | `{"success": false, ...}` inside `delivery_options` or `pickup_options`, or no pharmacy can fulfil that mode | Check those flags and `missing_products` |
| Pharmacy rejects the order at confirmation | `location_token` missing, cached, or from another option | Pass the chosen option's `location_token`; fetch options again if the member changes their mind |
| Order moves to `abandoned` | Unpaid or unconfirmed after 3 hours | Send the `payment_link` promptly, or call Confirm order after collecting |
| `409 {"status": "transaction_locked", ...}` | Concurrent confirmation in progress | Back off and retry |
| `422 {"status": "invalid_payment", "errors": ...}` | Bad amount (must be a decimal greater than 0) or blank reference, wrong state, amount mismatch, or already confirmed with another reference | Fix the amount or reference; a replay with the same amount and reference returns `already_confirmed` |
| `422 {"success":false,"message":"Order cannot be cancelled"}` | Outside the cancel window: the pharmacy has shipped, or it is a split order | The order can't be cancelled |
| `payment.refunded_amount` stays `0.0` | Partner-collected flow: hlthstack never holds the money | Settle using `post_billing.settlement.adjustment_amount` |
| Stored prescription file URLs stop working | Pre-signed URLs expire after 5 minutes | Don't store them |
| Order items differ from what was ordered | The pharmacy substituted an item | Compare `order_items` from `status_update` (or `order.products` from `getOrder`) with your previous snapshot |

<!-- Copied from docs/webhooks.md by scripts/sync_skill_references.py. Edit the source. -->

# Webhooks

hlthstack POSTs JSON to URLs you register at onboarding, so you learn about status changes
without polling. Payload schemas are under `webhooks` in [`openapi.yaml`](openapi.yaml).

**On this page:** [Authentication](#authentication) · [Delivery and retries](#delivery-and-retries) ·
[Appointment and consultation payload](#appointment-and-consultation-payload) ·
[Lab results payload](#lab-results-payload) · [Pharmacy payloads](#pharmacy-payloads) ·
[Digitization results payload](#digitization-results-payload)

## At a glance

| Endpoint you register | Events (`type` in the body) |
|---|---|
| Status updates | Appointments and consultations: `status_update`, `reports_upload`. Pharmacy orders: `status_update`, plus `additional_payment_required` and `post_billing` for partner-collected payments |
| Lab results (on request) | `lab_results` |
| Digitization results | `digitization_results` (prescription digitization finished) |

| `type` | Triggered by | Payload |
|---|---|---|
| `status_update` (appointments, consultations) | Every appointment status change | [Appointment and consultation payload](#appointment-and-consultation-payload) |
| `reports_upload` | Status `partially_received`/`received` with report links | [Appointment and consultation payload](#appointment-and-consultation-payload) |
| `lab_results` | Lab results available (only if a lab-results URL is registered) | [Lab results payload](#lab-results-payload) |
| `status_update` (pharmacy) | Every order status change, including refunds | [Pharmacy payloads](#pharmacy-payloads) |
| `additional_payment_required` | Partner-collected order needs more than you collected | [`additional_payment_required`](#additional_payment_required-partner-collected) |
| `post_billing` | Every order in a partner-collected order tree reached a final status | [`post_billing`](#post_billing-partner-collected) |
| `digitization_results` | Prescription digitization finished | [Digitization results payload](#digitization-results-payload) |

Appointment and pharmacy events share the status-updates URL. Tell them apart by the body:

- appointment payloads have `appointment_id`;
- pharmacy payloads have `order_id` and `service_type: "pharmacy"`.

> [!NOTE]
> You also receive webhooks for bookings hlthstack's team makes on a member's behalf. In
> those, `api_customer_id` is `null`.

## Authentication

Every request carries:

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |
| `Signature` | An HS256 JWT signed with your webhook secret |
| Your static headers | Any headers you give hlthstack at registration (for example `Authorization: Bearer <your token>`) are sent unchanged on every call |

The webhook secret is shared out of band by hlthstack, separately for staging and production.
Ask hlthstack to rotate it.

JWT claims by event:

| Event | Claims |
|---|---|
| Appointment / consultation (`status_update`, `reports_upload`) | `appointment_id`, `booking_id`, `timestamp`, `webhook_type: "status_update"` |
| Lab results | `appointment_id`, `booking_id`, `timestamp`, `webhook_type: "lab_results"` |
| Pharmacy | `order_id`, `timestamp`, `webhook_type` (`status_update`, `additional_payment_required` or `post_billing`, matching the body's `type`) |
| Prescription digitization | `request_id`, `timestamp`, `webhook_type: "digitization_results"` |

`timestamp` is Unix seconds at send time.

> [!CAUTION]
> The JWT has no `exp` claim and does **not** cover the body. Checking the signature alone is
> not enough: verify all three checks below on every delivery.

1. The signature is valid for your secret (HS256 only).
2. The ids in the claims match the ids in the body.
3. `timestamp` is within your tolerance window (5 minutes is a reasonable default), to block
   replays.

### Node.js

Verify the signature, claims and timestamp with Express and `jsonwebtoken`:

```js
// npm install jsonwebtoken express
const express = require("express");
const jwt = require("jsonwebtoken");

const SECRET = process.env.HLTHSTACK_WEBHOOK_SECRET; // <your-webhook-secret>
const app = express();
app.use(express.json());

function verify(req) {
  const claims = jwt.verify(req.get("Signature"), SECRET, { algorithms: ["HS256"] });
  const body = req.body;
  if (typeof claims.timestamp !== "number" || Math.abs(Date.now() / 1000 - claims.timestamp) > 300) {
    throw new Error("stale");
  }
  if (claims.order_id !== undefined) {
    if (claims.order_id !== body.order_id || claims.webhook_type !== body.type) throw new Error("mismatch");
  } else if (claims.request_id !== undefined) {
    if (claims.request_id !== body.request_id) throw new Error("mismatch");
  } else if (!claims.appointment_id || claims.appointment_id !== body.appointment_id ||
             claims.booking_id !== body.booking_id) {
    throw new Error("mismatch");
  }
  return claims;
}

app.post("/hlthstack/webhooks", (req, res) => {
  try {
    verify(req);
  } catch (e) {
    return res.sendStatus(401);
  }
  res.sendStatus(200);          // acknowledge fast
  enqueue(req.body);            // process asynchronously
});
```

### Python

The same checks with Flask and PyJWT:

```python
# pip install pyjwt flask
import os, time, jwt
from flask import Flask, request, abort

SECRET = os.environ["HLTHSTACK_WEBHOOK_SECRET"]  # <your-webhook-secret>
app = Flask(__name__)

def verify(headers, body):
    claims = jwt.decode(headers["Signature"], SECRET, algorithms=["HS256"])
    if abs(time.time() - claims["timestamp"]) > 300:
        raise ValueError("stale")
    if "order_id" in claims:
        ok = claims["order_id"] == body.get("order_id") and claims["webhook_type"] == body.get("type")
    elif "request_id" in claims:
        ok = claims["request_id"] == body.get("request_id")
    else:
        ok = (claims["appointment_id"] == body.get("appointment_id")
              and claims["booking_id"] == body.get("booking_id"))
    if not ok:
        raise ValueError("mismatch")
    return claims

@app.post("/hlthstack/webhooks")
def webhook():
    body = request.get_json()
    try:
        verify(request.headers, body)
    except Exception:
        abort(401)
    enqueue(body)  # process asynchronously
    return "", 200
```

## Delivery and retries

> [!IMPORTANT]
> Each attempt times out after 30 seconds. Reply 2xx quickly and process asynchronously.

| Situation | What happens |
|---|---|
| Connection refused/reset, TLS errors, timeouts, HTTP 408, 502, 503, 504 | Retried up to 5 times (about 24 minutes; backoff 12 s, 36 s, 108 s, 324 s, 972 s) |
| Every other non-2xx, including 400, 401, 403, 404, 422, 429 and 500 | **Not retried**. If your endpoint rejected or missed events, reconcile with the GET endpoints |

- If your endpoint has a temporary problem, return `503` (retried) rather than `500` (final).
- Every attempt is logged on hlthstack's side; ask for a delivery report if you suspect gaps.

> [!WARNING]
> Ordering is not guaranteed. Each body is a full snapshot of the current state, so apply the
> latest one, use the JWT `timestamp` (and `event_timestamp` on appointments) to drop older
> events, and use `getAppointment` / `getOrder` as the source of truth.

Because appointment payloads are rebuilt from the current state on each attempt, keys such
as `voucher_api_url` or `reports` reflect the appointment now, which can be ahead of
`status`.

## Appointment and consultation payload

One shape for every status change; extra keys appear depending on the state. A confirmed
health checkup:

```json
{
  "type": "status_update",
  "booking_id": "EKI0000000001700000000",
  "appointment_id": "APT1A2B3C4D5",
  "customer_id": "EKI000000001",
  "customer_name": "Jane Doe",
  "mobile_number": "9999999999",
  "api_customer_id": "CUST1001",
  "member_id": "EMP0001",
  "appointment_date_time": "2026-01-15T02:30:00Z",
  "event_timestamp": 1768440000.123,
  "booking_source": "hlthstack-api",
  "service_type": "ahc",
  "plan_id": "EXAMPLE_PLAN",
  "customer_plan_id": null,
  "subscription_id": null,
  "status": "confirmed",
  "status_text": "Confirmed",
  "comment": "Your appointment is confirmed.",
  "provider_id": 1001,
  "provider_name": "Example Diagnostics",
  "provider_branch": "Madhapur",
  "provider_address": "1 Example Road, Madhapur, Hyderabad",
  "voucher_api_url": "https://api.hlthstack.io/api/appointments/APT1A2B3C4D5/voucher",
  "phlebo_name": "John Doe",
  "phlebo_number": "+919999999999",
  "payment": {
    "status": "captured", "total_collected_amount": "0.0", "razorpay_amount": "0.0",
    "razorpay_payment_id": null, "razorpay_order_id": null,
    "customer_wallet_amount": "0.0", "sponsor_wallet_amount": "0.0",
    "promotional_wallet_amount": "0.0", "cod_amount": "0.0", "h_points_amount": "0.0",
    "refunded_amount": "0.0", "captured_at": "2026-01-14T07:03:10Z", "refunded_at": null
  }
}
```

| Key | Present when |
|---|---|
| `type` | Always. `reports_upload` when the status is `partially_received`/`received` and report links exist; otherwise `status_update` |
| `booking_source` | Always. Fixed at booking time: `hlthstack-api` for bookings made through the hlthstack hosts |
| `provider_*` | A provider is assigned |
| `voucher_api_url` | The appointment is confirmed. Fetch it with your bearer token. Online consultations have no voucher: ignore it for `specialist_consultation` |
| `phlebo_name`, `phlebo_number` | Confirmed and a phlebotomist is assigned |
| `reports` | `partially_received` or `received` |
| `doctor_*`, `summary`, `doctor_prescriptions` | Consultations (`summary` is `null` and `doctor_prescriptions` empty until available) |
| `hospital_name`, `hospital_location`, `hospital_address`, `latitude`, `longitude` | In-clinic consultations |
| `meeting_link` | Video consultations (`null` until the doctor confirms) |
| `payment` | A payment exists |

Consultations send no webhook while waiting for the member's co-pay (`payment_pending`).

**See also:** statuses in [health-checkups.md](health-checkups.md#appointment-statuses) and
[consultations.md](consultations.md#consultation-statuses) (which also lists the typical
consultation sequences).

## Lab results payload

> [!NOTE]
> Not sent by default; ask hlthstack to register a lab-results URL.

Digitized results for one appointment:

```json
{
  "type": "lab_results",
  "booking_id": "EKI0000000001700000000",
  "appointment_id": "APT1A2B3C4D5",
  "customer_id": "EKI000000001",
  "api_customer_id": "CUST1001",
  "member_id": null,
  "plan_id": "EXAMPLE_PLAN",
  "digitization": {
    "results": [
      { "result": "80", "units": "mg/dL", "ranges": "<70,70-140,>140",
        "test_component_id": 1, "test_component_name": "Fasting Blood Sugar",
        "lab_test_id": 1, "lab_test_name": "Blood Glucose" }
    ],
    "notes": []
  }
}
```

## Pharmacy payloads

`status_update` fires on every order status change, including refunds. An order out for
delivery:

```json
{
  "type": "status_update",
  "order_id": "EPO000000000001",
  "customer_id": "EKI000000001",
  "api_customer_id": "CUST1001",
  "member_id": null,
  "ordered_for_name": "Jane Doe",
  "mobile_number": "9999999999",
  "order_type": "cart_order",
  "vendor_name": "Example Pharmacy",
  "service_type": "pharmacy",
  "plan_id": "EXAMPLE_PLAN",
  "customer_plan_id": null,
  "subscription_id": null,
  "status": "out_for_delivery",
  "status_text": "Order out for delivery",
  "status_description": "Your order is on its way",
  "partner_status": "30",
  "order_items": [
    { "id": 50001, "product_id": "SKU-1", "name": "Example 500 Tablet", "quantity": 2, "mrp": 50.0, "offered_price": 45.0 }
  ],
  "total_amount": 95.0,
  "total_selling_price": 90.0,
  "total_discount": 5.0,
  "tracking_url": "https://track.example.com/TRK1",
  "tracking_partner": "Example Courier",
  "tracking_number": "TRK1",
  "eta_from": null,
  "eta_to": null,
  "shipment_details": {
    "delivery_type": "standard", "otp": "1234", "tracking_partner": "Example Courier",
    "tracking_number": "TRK1", "tracking_url": "https://track.example.com/TRK1",
    "eta_from": null, "eta_to": null, "store_details": null
  },
  "address": "1 Example Road, Motera, Ahmedabad, Gujarat, 380005",
  "city": "Ahmedabad",
  "pincode": "380005",
  "state": "Gujarat",
  "split_details": { "is_splitted": false, "parent_order": null, "sub_orders": [] },
  "payment": {
    "status": "captured", "razorpay_amount": 0.0, "razorpay_payment_id": null,
    "razorpay_order_id": null, "sponsor_wallet_amount": 95.0, "customer_wallet_amount": 0.0,
    "promotional_wallet_amount": 0.0, "h_points_amount": 0.0, "refunded_amount": 0.0,
    "total_collected_amount": 95.0, "captured_at": "2026-01-15T09:00:00+05:30", "refunded_at": null
  }
}
```

| Key | Present when / values |
|---|---|
| `address`, `city`, `pincode`, `state` | The order has an address |
| `payment` | A payment exists |
| `shipment_details.delivery_type` | `store_pickup`, `express`, `standard` or `null` |
| `shipment_details.store_details` | Set only for store pickup |
| `sub_total`, `additional_charge`, `total_payable`, `order_items[].selling_price` / `discounted_price` | Partner-collected orders |
| In `payment`: `partner_collected`, `partner_collected_amount`, `additional_collected_amount`, `partner_payment_reference` | Partner-collected orders |
| `booking_source` | Never: pharmacy payloads have no `booking_source` |

### `additional_payment_required` (partner-collected)

The pharmacy needs more than you collected (typically a pricier substitute).

- Collect `additional_payment.amount_payable` from the member.
- `additional_payment.order_id` is the pharmacy's reference (it may be a split child); the
  top-level `order_id` is the hlthstack order.
- Sent again only when the amount changes.

The `additional_payment` block (plus the same envelope keys as `status_update`):

```json
{
  "type": "additional_payment_required",
  "order_id": "EPO000000000003",
  "additional_payment": {
    "order_id": "V-1", "amount_payable": 200.0, "partner_collected_amount": 1000.0,
    "additional_collected_amount": 200.0, "signalled_at": "2026-01-15T18:00:00+05:30"
  }
}
```

### `post_billing` (partner-collected)

Sent as soon as every order in the tree reaches a final status.

- `adjustment_amount = total_collected_amount - final_amount` is what you owe the member back;
  `final_amount` is authoritative (it accounts for cancellations, returns, price changes and
  pro-rata shipping).

> [!IMPORTANT]
> Always apply the latest `post_billing` for an order, and reconcile refunds against
> `adjustment_amount`, never `payment.refunded_amount`.

The `settlement` block:

```json
{
  "type": "post_billing",
  "order_id": "EPO000000000003",
  "settlement": {
    "original_collected_amount": 1200.0,
    "additional_collected_amount": 0.0,
    "total_collected_amount": 1200.0,
    "final_amount": 900.0,
    "adjustment_amount": 300.0,
    "settled_at": "2026-01-16T18:30:00+05:30",
    "orders": [
      { "order_id": "EPO000000000003", "status": "delivered", "selling_price": 900.0 }
    ]
  }
}
```

Worked example: the member orders A (2 x 250), B (1 x 450) and C (1 x 250); you collect
1,200. C goes out of stock (-250) and B is substituted with a 400 brand (-50). When A and B
are delivered, `post_billing` arrives with `final_amount` 900 and `adjustment_amount` 300:
refund 300 to the member.

## Digitization results payload

Sent when prescription digitization finishes:

```json
{
  "type": "digitization_results",
  "event_type": "pharmacy.prescription.digitized",
  "request_id": "DIGI_RQ_A1B2C3D4E",
  "status": "completed",
  "customer_id": "EKI000000001",
  "api_customer_id": "CUST1001",
  "member_id": null,
  "plan_id": "EXAMPLE_PLAN",
  "items": [{ "medicine_id": 50001, "name": "Example 500 Tablet", "quantity": 1 }],
  "reviewed_items": null,
  "cart_id": 701,
  "documents": [{ "id": 1, "url": "https://files.example.com/prescription.pdf", "type": "pdf", "name": "prescription.pdf" }],
  "comment": null
}
```

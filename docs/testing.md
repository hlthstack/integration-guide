# Testing on staging

Use `https://staging-api.hlthstack.io` with your staging credentials. The endpoints below
exist **only on staging**. They move a booking or order through its lifecycle and fire the
same webhooks real updates would, so you can test your webhook handler end to end. Never
call them from production code (production returns 401 or 404).

## Health checkups

`POST /api/appointments/{appointment_id}/update_status`

```json
{ "status": "confirm" }
```

| `status` | Effect |
|---|---|
| `confirm` | Confirm the appointment |
| `assign_phlebo` | Assign a sample phlebotomist (needs a confirmed appointment) |
| `cancel` | Cancel |
| `completed` | Mark completed |
| `reschedule` | Move to the next day |
| `reports_partially_received` | Mark reports partially received |
| `reports_received` | Mark reports received (adds a sample report) |
| `lab_result` | Create sample lab results (needs `received` and a lab-results webhook URL) |

Success: `{"messages": ["Appointment status updated successfully"]}` (or `"Phlebo has been
assigned"`, `"Lab result has been created"`). Errors use `{"errors": ["..."]}`: `422` for an
invalid status or unmet precondition (`Appointment is not confirmed yet`,
`Appointment is not in received state`), `500` for a transition that isn't allowed
(`Appointment status cannot be changed from confirmed to confirm`).

A typical run: book, `confirm`, `assign_phlebo`, `completed`, `reports_received`,
`lab_result`.

## Consultations

`PATCH /api/consultations/{appointment_id}/update_status`

```json
{ "status": "reschedule", "reschedule_time": "2026-01-16T04:30:00Z" }
```

| `status` | Effect |
|---|---|
| `confirm` | Confirm (doctor details in the webhook) |
| `cancel` | Cancel |
| `completed` | Mark completed |
| `reschedule` | Move to `reschedule_time` (default: 1 day from now) |
| `reports_received` | Attach a sample summary and prescription, then move to `received` |

Success: `{"messages": ["Appointment status updated successfully"]}`. Invalid status:
`422 {"errors": ["Invalid status"]}`. Disallowed transition:
`422 {"errors": {"messages": ["..."]}}`.

## ePharmacy

`PATCH /api/epharmacy/orders/{order_id}/update_status`

```json
{
  "customer_details": { "api_customer_id": "CUST1001" },
  "status": "in_progress",
  "status_text": "Order is being processed",
  "status_description": "Optional free text",
  "tracking_number": "Optional",
  "tracking_url": "Optional",
  "tracking_partner": "Optional"
}
```

`status` must be an order status (see [epharmacy.md](epharmacy.md#order-statuses)), otherwise
`422 {"success": false, "message": "Invalid status: ..."}`. The optional text and tracking
fields are copied into the webhook. The response includes the order's status history
(`journey`).

## Checklist

- [ ] Token refresh before expiry.
- [ ] Booking, reschedule, cancel (booking-level partial results handled).
- [ ] Webhook signature, id and timestamp checks; duplicates and out-of-order events handled.
- [ ] Voucher download after `confirmed`; reports after `received`.
- [ ] ePharmacy: nested `success` flags on fulfillment options, `location_token` per option,
      each payment flow your contract uses.

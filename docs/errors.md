# Errors

Error bodies are not uniform across endpoints. Check the HTTP status first, then parse the
body defensively. The shapes you will see:

| Shape | Example | Where |
|---|---|---|
| Field errors | `{"errors": {"package_ids": ["should be an integer array"]}}` | Validation (usually 400). Nested fields are prefixed: `customer_mobile_number`, `address_pincode` |
| Messages | `{"errors": {"messages": ["This booking cannot be rescheduled"]}}` | Business-rule failures (400/422) and any unexpected error (422) |
| Plain message | `{"message": "Required details are missing"}` | Auth, entity headers, slots |
| Bare list | `{"errors": ["Invalid status"]}` | Staging simulation endpoints |
| Success flag | `{"success": false, "message": "Order not found"}` | ePharmacy |
| Booking failure | `{"msg": "...", "recall": false}` | Booking could not be placed |
| Single error | `{"error": "Invalid company slug for authenticated partner."}` | Wallet endpoints |

## Status codes

| Status | Meaning |
|---|---|
| 200 | Success. Some ePharmacy responses still carry `"success": false` in nested objects; see [epharmacy.md](epharmacy.md) |
| 202 | Accepted for async processing (prescription digitization) |
| 400 | Invalid parameters, invalid `plan_id` / subscription, bad entity headers, entity not enabled for API booking, or an action not allowed in the current state |
| 401 | Missing, invalid or expired token: plain-text `HTTP Token: Access denied.`. `get-access-token` returns `{"message": "Wrong credentials"}`. Lab results not enabled: `{"errors":{"messages":["Unauthorised"]}}` |
| 403 | The booking/appointment isn't yours (`invalid booking_id` / `invalid appointment_id`), the service isn't enabled for your plan, or the company slug doesn't match |
| 404 | Member, cart or order not found; staging-only route called in production |
| 409 | Concurrent partner-payment confirmation; retry |
| 422 | Business rule or processing failure, or an unexpected error |
| 500 | Server error, or a provider's system couldn't be reached |

## Common messages

| Message | Fix |
|---|---|
| `this service is not enabled for you` | The `service_name` isn't on your plan |
| `Invalid package ids: ...` | Use package ids shared for that service and plan |
| `invalid appointment time` / `provider slot not available ...` | Pick a slot from `listSlots` |
| `Booking date ... is before the provider's earliest available date ...` | See "First bookable date" in [health-checkups.md](health-checkups.md) |
| `customer has an ongoing appointment for same package and provider for same slot` | Duplicate booking |
| `Appointment cannot be rescheduled to a different provider.` | The appointment is already confirmed at its provider |
| `Previous request is in progress, please try ... after few minutes` | Wait and retry |
| `Please wait N minute(s) before you reschedule this appointment.` | Consultations: 5-minute buffer after booking or reschedule |

## Retrying

- Retry 5xx, 409 and network errors with backoff.
- Don't blindly retry `POST /api/appointments` or consultation creation: first check with
  `getAppointment` / your webhooks whether the booking was created.
- Prescription digitization and partner-payment confirmation are safe to retry (use an
  `Idempotency-Key` for digitization).

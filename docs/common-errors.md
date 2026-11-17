# Common errors and how to fix them

The errors partners run into most often, why they happen, and what to do. For every error
shape and status code, see [errors.md](errors.md).

**On this page:** [1. Sign-in and access](#1-sign-in-and-access) ·
[2. Packages and providers](#2-packages-and-providers) ·
[3. Slots and booking times](#3-slots-and-booking-times) ·
[4. Creating a booking](#4-creating-a-booking) ·
[5. Reschedule and cancel](#5-reschedule-and-cancel) ·
[6. Results, reports and vouchers](#6-results-reports-and-vouchers)

> [!TIP]
> **Before contacting support:** a 4xx error returns the same result until the request
> changes, so don't retry it in a loop. Send hlthstack the endpoint, the time, the request
> (without the token) and the full response.

## 1. Sign-in and access

| Error | Cause | Fix |
|---|---|---|
| 401 `HTTP Token: Access denied.` | The access token is missing, malformed or expired. | Get a new token and retry once. Refresh the token before it expires instead of waiting for a 401. |
| 401 `Wrong credentials` | The API username or password is wrong, or belongs to the other environment. | Use the credentials issued for that environment. Staging credentials don't work in production. |
| 400 `The entity is not enabled for API booking.` | Your account isn't set up for API bookings yet. | Ask your hlthstack contact to enable API booking. |
| 403 `this service is not enabled for you` | The service you requested isn't part of your plan. | Call only the services agreed at onboarding, or ask your hlthstack contact to add the service. |
| 404 `customer not found: <id>` | The customer id isn't registered under your account, or comes from the other environment. | Register the customer first and send the id exactly as registered. |

## 2. Packages and providers

| Error | Cause | Fix |
|---|---|---|
| 400 `invalid package_ids` · `Invalid package ids: <id> (package not found)` | The package id doesn't exist for your account. | Use only the package ids shared at onboarding. |
| 400 `Invalid package ids: <id> (not tagged to <benefit> benefit)` | The package is valid but doesn't belong to the service you are calling. | Send each package id only with the service it was issued for. |
| 400 `(package is inactive)` · `(benefit tagging is inactive)` · `(benefit tagging end date expired on <date>)` | The package has been retired, or its contract period has ended. | Stop sending that id and ask your hlthstack contact for the replacement. Keep package ids in configuration, not in code. |
| 400 `package_ids: can't be blank, should be an integer array` | `package_ids` is missing or sent as text. | Send `package_ids` as an array of numbers. |
| 400 `service_name: is not a valid service_name` | The service name is missing or misspelt. | Use the exact service names in the [API reference](https://developers.hlthstack.io). |
| 400 `pincode: is the wrong length (should be 6 characters)` · `latitude: can't be blank` | Location details are missing or malformed in the provider search. | Send a 6-digit pincode, or latitude and longitude as decimals. |
| 400 `The provider is temporarily unserviceable` | The provider has been paused since you last listed providers. | List providers again for every booking and offer the member another provider. |
| 400 `provider_id does not have a doctor associated with it` | You asked for consultation slots from a provider that has no doctor. | Request slots only for providers returned by the provider list for that same service. |

## 3. Slots and booking times

| Error | Cause | Fix |
|---|---|---|
| 400 `Booking date <date> is before the provider's earliest available date <date>` | The provider needs advance notice, so the date you asked for is too soon. | Start from the earliest date in the message, and show only the dates the slots call returns. |
| 400 or 500 `invalid appointment time` · `invalid appointment date` | The date-time is in the wrong format, in the past, or missing its time zone. | Send ISO 8601 with a time zone offset, and only future times. |
| 400 `provider slot not available` · `slot unavailable` · `this provider offers no slots on <date>` | The time you sent wasn't in the slots response, or the response was stale. | Book only a time copied from a slots response fetched just before booking. |
| 400 `Provider's slots are full` · `Booking threshold reached…` | The slot filled up, or you are booking more people than it has room for. | Fetch slots again and offer another time. Split large groups across slots. |
| 400 `This provider is not serviceable on the selected date` | The provider is closed that day. | Choose a date from the slots response. |
| 400 `provider requires at least one day's notice` · `appointment time is outside provider booking hours` · `must be booked at least 90 minutes in advance` | The time breaks the provider's notice period or working hours. | Hide times that are too soon, and use only times from the slots response. See [booking rules](health-checkups.md#booking-rules). |

## 4. Creating a booking

| Error | Cause | Fix |
|---|---|---|
| 400 with `provider_id`, `appointment_date_time`, `customers` and `address` all `can't be blank` | The request arrived with an empty body. | Send JSON with `Content-Type: application/json` and the fields at the top level. If you monitor the API, don't use the booking endpoint as a health check. |
| 400 `provider_id: is not a number, invalid id` | The provider id is wrong or sent as text. | Send the numeric provider id from the provider list. |
| 400 `address_city` · `address_state` · `address_address_line_one: can't be blank` | The address is incomplete. | Send both address lines, city, state, pincode, latitude and longitude. |
| 400 `address_address_line_one: is too long (maximum is 254 characters)` | An address line is over the limit. | Keep each address line to 254 characters. |
| 400 `contains pincode <x>, which does not match the address pincode <y>` | A pincode typed inside the address differs from the `pincode` field. | Make both match, or remove the pincode from the address text. |
| 400 `customer_dob: invalid dob` · `customer_gender: is not included in the list` | Date of birth or gender is in the wrong format. | Use the date format and gender values in the API reference. |
| 400 `appointment_type: package doesn't support inclinic service` | The package doesn't allow that appointment type. | Use an appointment type the package supports. |
| 400 `service mode can't be blank` | A consultation booking was sent without `service_mode`. | Send `service_mode`: `at_provider_location` for in-clinic, `audio_call` or `video_call` for online. |
| 422 `customer has an ongoing appointment for same package and provider for same slot` | The same booking was sent twice. | Disable the submit button after one tap, and show the existing booking. |
| 422 `failed to confirm booking` | The provider couldn't confirm the slot. | Fetch slots again and retry with another slot. Contact hlthstack if it repeats. |

## 5. Reschedule and cancel

| Error | Cause | Fix |
|---|---|---|
| 400 `invalid booking_id` · `invalid appointment_id` | The id is in the wrong format, the wrong kind of id, or from the other environment. | Store the id returned at booking and send it unchanged. |
| 403 `invalid appointment_id` | The id is well-formed but isn't a booking under your account. | Check you are using the right environment and account. |
| 422 `Appointment cannot be rescheduled to a different provider.` | The reschedule carried a different provider, at a provider connected through a partner integration. | Leave the provider out when rescheduling. To change provider, cancel and book again. |
| 400 `This booking cannot be rescheduled` · `cannot be cancelled` | The booking is already completed, cancelled or rejected, or a provider rule blocks the change. | Check the booking's status first and hide these options when they don't apply. See [booking rules](health-checkups.md#booking-rules). |
| 400 `Cancellation not allowed: The appointment time must be at least <n> from now.` | The appointment is too close to its start time. | Hide cancel and reschedule inside the cut-off period. |
| 422 `Previous request is in progress, please try rescheduling after few minutes` | An earlier change is still being processed. | Wait a few minutes and retry once. |

## 6. Results, reports and vouchers

| Error | Cause | Fix |
|---|---|---|
| 400 `Digitized lab results will be available once they are verified` | The results aren't verified yet. | Wait for the results webhook instead of polling. |
| 400 `Reports unavailable` | The report hasn't been uploaded yet. | Wait for the reports webhook, then download. |
| 404 `Consultation not found` (summary and prescription) | The doctor hasn't completed the write-up yet. | Wait until the consultation is `completed`. |
| 401 `Unauthorised` (lab results) | Your account doesn't have access to results for that booking. | Check the booking is yours and that lab results are enabled for your account. |
| 400 `voucher is not required` | That booking type has no voucher. | Request vouchers only for in-clinic bookings. |
| 400 `voucher only available for download when appointment is confirmed` | The booking isn't confirmed yet. | Wait for confirmation, then download the voucher. |

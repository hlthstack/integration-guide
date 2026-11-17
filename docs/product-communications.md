# Product communications

What hlthstack sends your members about pharmacy orders, vision (Lenskart) orders and
consultations: which message, on which channel, triggered by what. Members receive these
automatically; you don't call an API to send them. If you embed hlthstack or integrate through
the API, don't send your own copies of these messages, or members get them twice. To send them
under your own name and logo, see [white-labelling.md](white-labelling.md).

Channels:

| Channel | Meaning |
|---|---|
| Email | Email to the member's registered address |
| WhatsApp | WhatsApp message to the member's registered mobile |
| SMS | Text message to the member's registered mobile |
| In-app | Notification inside the hlthstack app |
| Push | Mobile push notification |

Placeholders such as `[name]`, `[order id]` or `[date and time]` are filled at send time.

## 1. At a glance

| Product | Channels |
|---|---|
| Pharmacy | Email, WhatsApp, push |
| Vision (Lenskart) | WhatsApp, email, in-app |
| Consultations (in-clinic, doctor consultation, 24x7) | Email, WhatsApp, in-app, push, SMS (24x7 chat only) |

## 2. Pharmacy

### 2.1 Order events (email)

One email per order event. The event names are hlthstack's; for your own logic, match on the
webhook `status` (see [epharmacy.md](epharmacy.md#order-statuses)). Where a status lines up
directly, it is shown.

| Event | Webhook `status` | Email the member receives |
|---|---|---|
| `order_received` | | Your pharmacy order [order id] is placed successfully |
| `order_items_out_of_stock` | | Product out of stock in your order [order id] |
| `order_price_changed` | | Your pharmacy order [order id] price has changed |
| `order_prescription_rejected` | `prescription_rejected` | Prescription of your order [order id] rejected by pharmacy |
| `order_cancelled` | | Your pharmacy order [order id] is cancelled by partner |
| `order_customer_cancelled` | | Your pharmacy order [order id] is cancelled by customer |
| `bill_amount_received` | | Your pharmacy order [order id] payment detail is confirmed |
| `order_packed` | `packed` | Your pharmacy order [order id] is packed |
| `out_for_delivery` | `out_for_delivery` | Your pharmacy order [order id] has been shipped |
| `order_delivered` | `delivered` | Your pharmacy order [order id] is delivered |
| `order_splitted` | (`split_details` in the payload) | Important update on your pharmacy order |
| `store_pickup_otp` | | Your Pharmacy Order Pickup OTP |
| `home_delivery_otp` | | Your Pharmacy Order Delivery OTP |

### 2.2 Call-to-confirm updates (push and WhatsApp)

The pharmacy calls the member to confirm the medicines before fulfilling the order.

| Trigger | Channels | Title | Message |
|---|---|---|---|
| Order placed | Push, WhatsApp | OneRx will call you shortly | A call is coming to confirm the medicines; answer it to confirm the order |
| Two missed calls | Push, WhatsApp | You missed a call from OneRx | A call was missed; answer the next one to confirm the order |

### 2.3 WhatsApp messages

| When | Message (summary) |
|---|---|
| Order placed | Order [order id] was placed with hlthstack pharmacy and is being processed; updates will follow |
| Order shipped | Order [order id] is shipped; the delivery partner may call the registered mobile to confirm |
| Order delivered | Order [order id] was delivered; thanks for shopping with hlthstack |
| Prescription rejected | The prescription for order [order id] was rejected by the pharmacy partner; the partner will call shortly to help upload a valid one |
| Order rejected by the pharmacy partner | Order [order id] was cancelled by the pharmacy partner; any refund is processed within 3-5 business days |
| Refund initiated | A refund of ₹[amount] for order [order id] was initiated and reaches the member's account in 3-5 business days |

## 3. Vision (Lenskart)

Members get a corporate code, order on Lenskart, and hlthstack reviews the order before payment
or confirmation. In member messages, CTA is the button on the message.

### 3.1 Code and order

| # | Trigger | Channels | What the member is told | CTA |
|---|---|---|---|---|
| 1 | Lenskart code requested or resent | WhatsApp, email | Their hlthstack corporate code `[code]`, and how to use it: pick eyewear on Lenskart, apply the code at checkout, complete the order with the hlthstack-registered mobile. hlthstack then reviews the order and shares next steps. Includes a picture | Shop on Lenskart |
| 2 | Order received by hlthstack (sponsored or out-of-pocket) | Email, WhatsApp | WhatsApp: the order is received and under review; next steps will follow. Email: the order is received; a payment link follows shortly, to be paid to confirm the order | View Order Status |

### 3.2 Prescription

| # | Trigger | Channels | What the member is told | CTA |
|---|---|---|---|---|
| 3 | Prescription pending: day 0, day 3, day 5 (same copy each day) | Email, WhatsApp, in-app | The prescription is still pending; provide a valid one with vendor details, date, name and power. After verification a payment or confirmation link follows | Upload Prescription |
| 4 | Prescription marked invalid | WhatsApp, in-app | The prescription could not be verified. Power saved in Lenskart doesn't count; upload a valid prescription from Lenskart or any vendor. After verification a payment or confirmation link follows | Upload Valid Prescription |
| 5 | Day 3, still invalid | In-app, WhatsApp | Reminder repeating the reason-specific instruction | Upload Prescription |
| 6 | Day 5, still invalid | In-app, WhatsApp | Same copy as row 4 | Upload Valid Prescription |

### 3.3 Payment or confirmation

After the prescription is verified, the member gets either a payment link (to pay) or a
confirmation link (to approve payment from their wallet).

| # | Trigger | Channels | What the member is told | CTA |
|---|---|---|---|---|
| 7 | Payment pending (payment link sent) | Email, WhatsApp, in-app | Payment is pending for the Lenskart order; pay with the link to confirm it. Once paid, the order is approved and moves to delivery | Complete Payment |
| 8 | Confirmation pending (confirmation link sent) | Email, WhatsApp, in-app | Almost there: click the link to approve payment from the wallet and confirm the Lenskart order | Confirm Order |
| 9 | Payment received | Email, WhatsApp | Payment of ₹[amount] received; the order is processed and Lenskart will share delivery details | View Order Status |
| 10 | Order confirmed | Email, WhatsApp | The order is confirmed and processed; Lenskart will share delivery details | View Order Status |
| 11 | 8 hours after the payment link | WhatsApp, in-app | Payment still pending; pay to avoid cancellation | Complete payment |
| 12 | 15 hours after the payment link | WhatsApp, in-app | Same copy as row 11 | Complete payment |
| 13 | 22 hours after the payment link | WhatsApp, in-app | Final reminder: the payment link expires in 2 hours; pay now to avoid cancellation | Complete payment |

After payment there is no further message from hlthstack; the order arrives in 3-5 days.

### 3.4 Rejection, cancellation and completion

| # | Trigger | Channels | What the member is told | CTA |
|---|---|---|---|---|
| 14 | Order rejected (by Lenskart or hlthstack) | WhatsApp | The order can't be processed due to `[reason]`; contact support with questions | Contact Support |
| 15 | Order cancelled by the member | WhatsApp | The order is cancelled, with `[reason]`; contact support with questions | Contact Support |
| 16 | Order completed (may be sent) | In-app | The order is complete; please rate the experience | Rate Your Experience Here |

## 4. Consultations

Most consultation messages follow the appointment status, so they line up with the webhook
`status` values in [consultations.md](consultations.md#consultation-statuses): `new`,
`confirmed`, `rescheduled`, `rejected`, `cancelled`, `noshow`, `completed` and `received`.
Reminders are time-based and have no webhook. In the tables, E = email, W = WhatsApp, I =
in-app, P = push, S = SMS.

### 4.1 In-clinic consultation

| Step | Webhook `status` | Channels | What the member receives |
|---|---|---|---|
| Request received | `new` | E, W, I, P | The request is received; a doctor usually confirms in 10-12 hours, and the clinic may call to confirm. No email for cashless walk-ins or onsite bookings |
| Confirmed | `confirmed` | E, W, I, P | The appointment with [doctor] is confirmed. Email attaches the appointment voucher (PDF) and a calendar file (.ics); WhatsApp carries the voucher. Print the voucher and carry a photo or employee ID |
| One day before | | W, I, P | Reminder of tomorrow's appointment, with a link to the voucher. Sent at 17:00 local time the day before; not for bookings made that day or the day before |
| Morning of | | W, I, P | Reminder of today's appointment. Sent at 06:00 local time for appointments after 6 AM; not for bookings made that day |
| Rescheduled | `rescheduled` | E, W, I, P | The appointment is rescheduled to [date]; confirmation follows (usually 8-24 hours) |
| Rejected by the clinic | `rejected` | E, W, I, P | [clinic] can't fulfil the appointment on [date], with the reason; hlthstack is trying to reschedule |
| About 2 hours after a rejection | | E, W, I, P | Follow-up: the appointment can't be fulfilled right now; reschedule in the app or call support |
| Cancelled | `cancelled` | E, W, I, P | The appointment is cancelled; rebook any time. Email attaches a calendar cancellation (.ics) |
| No-show | `noshow` | E, W, I, P | The member missed the appointment and can reschedule. Refunds are not processed for missed appointments |
| Completed | `completed` | E, W | Email asks for a rating, attaches the invoice, and says the prescription and summary arrive in the app within 24 hours. WhatsApp thanks the member and asks for feedback |

Completion varies with the booking:

| Case | Channels | What the member receives |
|---|---|---|
| A prescription upload is required | W | The appointment is complete; upload the prescription to use other health services |
| Prescription rejected on review | W, I, P | The uploaded prescription (or prescription and invoice) was rejected, with the reason; re-upload. No completion email in this case |

Cashless in-clinic bookings (paid from the member's sponsored wallet at the clinic):

| Step | Channels | What the member receives |
|---|---|---|
| Request received and confirmed | W | Adds how to pay: at the clinic, open the app, go to Profile → Booking History, tap Scan to Pay and scan the clinic's UPI QR; hlthstack pays the clinic. The confirmation also asks for the prescription and invoice within 12 hours of payment |
| 4 hours before | E | Reminder with the voucher and a Scan to pay at the clinic button |
| Completed | E, W | Upload the prescription and invoice within 12 hours to keep uninterrupted access to benefits |
| Prescription or invoice still missing | W | Health benefits are restricted until the prescription and invoice for the appointment are uploaded |
| Payment to the clinic succeeded | W, I, P | ₹[amount] was spent from the sponsored wallet at the chosen clinic |
| Payment to the clinic failed | W, I, P | The ₹[amount] transaction was unsuccessful. In-app adds: try again, or pay directly and raise a reimbursement claim |

Clinics with QR check-in (the member scans a QR at the clinic to confirm the visit):

| Step | Channels | What the member receives |
|---|---|---|
| Confirmed | W | Confirmation with the clinic and time; at the clinic, use Scan QR to confirm the visit |
| 2 hours before | W, I, P | Reminder that the appointment is in 2 hours; scan the QR at the clinic |
| Visit verified, completed | W, I, P | The clinic visit is verified. If a prescription is required: upload the prescription and invoice within 12 hours to keep benefits |
| Verification failed, prescription required | W | Upload the prescription and invoice to receive a refund, processed within 5 working days after verification |
| Verification failed (QR mismatch) | E, W | The visit couldn't be verified and the appointment is rejected; a refund is initiated, processed within 5 working days |

Prescription and summary messages (`received`) are not sent for in-clinic consultations.

### 4.2 Doctor consultation (scheduled and priority)

Online consultations (`audio_call` or `video_call`), scheduled or priority.

| Step | Webhook `status` | Channels | What the member receives |
|---|---|---|---|
| Request received | `new` | E, W, I, P | The request is received; doctors will review and confirm shortly |
| Confirmed | `confirmed` | E, W, I, P | The appointment is confirmed for [time slot]. No voucher or calendar file. Priority bookings: the specialist is assigned; the meeting link is enabled 5 minutes before the appointment |
| One day before | | W, I, P | Reminder, sent at 17:00 local time the day before; not for bookings made that day or the day before |
| Morning of | | W, I, P | Reminder, sent at 06:00 local time for appointments after 6 AM |
| 30 minutes before | | W, I, P | Reminder with a reschedule link, once a doctor is assigned |
| 10 minutes before (video only) | | E, W, I, P | The appointment is in 10 minutes; join link included. Audio calls get nothing at this step |
| Rescheduled | `rescheduled` | E, W, I, P | The appointment is rescheduled; confirmation follows |
| Rejected by the doctor | `rejected` | E, W, I, P | The doctor can't take the appointment; hlthstack is trying to reschedule (priority: re-book) |
| About 2 hours after a rejection | | E, W, I, P | Follow-up: the appointment can't be fulfilled right now; reschedule (priority: re-book) or call support |
| Cancelled | `cancelled` | E, W, I, P | The appointment is cancelled; rebook any time |
| No-show | `noshow` | E, W, I, P | The member missed the appointment; reschedule (priority: re-book). Audio calls: the doctor tried calling and couldn't reach the member |
| Completed | `completed` | E, W, P | Email asks for a rating and attaches the invoice. If a prescription is required, WhatsApp asks for it |
| Summary or prescription ready | `received` | E, W, I, P | The consultation summary is available in the app (Health → Doctor consultations) |

### 4.3 24x7 consultations

24x7 has three modes: chat, scheduled call and instant call.

**Chat.** Chat consultations don't send the booking messages above. The member receives:

| Trigger | Channels | What the member receives |
|---|---|---|
| Doctor replies after the member goes offline | I, P | You have a message from [doctor] |
| Doctor publishes the consultation summary | E, S, I, P | [doctor] has shared the summary; view it in the app; a follow-up can be requested any time |
| Doctor answers a follow-up question | E, S, I, P | [doctor] has answered the follow-up question |
| Doctor shares a diet or fitness plan | E, I, P | A new plan from the doctor, with a link to it |
| Documents attached to the consultation | E | "Your health passport": the documents shared during the consultation, attached |
| Doctor advises a follow-up (members with family doctor or 24x7 enabled) | E, I, P | [doctor] recommends a follow-up consultation; book within 2 days |
| 1 day after the consultation | P | Nudge to consult the doctor for the follow-up |
| 10 minutes after the member cancels a request | P | Doctors are available 24x7; consult now |
| No doctor picks up the request (at least 3 minutes) | P | The consultation is cancelled due to a longer wait; try again later |
| Doctor ends the chat because the member stopped replying | P | The consultation with [doctor] has been closed; request a new one any time |
| Monthly, for members in an active program with no consultation in the past month | I, P | Have a health concern? General physicians are available 24x7 |

**Scheduled call.** The call lasts 10-15 minutes and comes from a calling number given in
the confirmation.

| Step | Webhook `status` | Channels | What the member receives |
|---|---|---|---|
| Request received | `new` | E, W, I, P | The request is received |
| Confirmed | `confirmed` | E, W, I, P | Confirmed; email gives the 10-15 minute call detail and the calling number |
| One day before | | W | Reminder, sent at 17:00 local time the day before |
| Morning of | | W | Reminder, sent at 06:00 local time |
| 30 minutes before | | E, W, I, P | Reminder. Also sent straight away when a doctor is assigned within the last 30 minutes |
| Rescheduled | `rescheduled` | E, W | Rescheduled; email confirms the call length and that a doctor is assigned 30 minutes before the slot |
| Cancelled | `cancelled` | E, W | The appointment is cancelled |
| No-show | `noshow` | E, W, I, P | [doctor] tried calling from [call line] and couldn't reach the member; book again any time |
| Completed | `completed` | E, W, P | Email asks for a rating and attaches the invoice |
| Summary or prescription ready | `received` | E, W | The summary is available in the app |
| Request marked incomplete | | E | The consultation was missed; request a new one |

**Instant call.** A doctor connects within about 2 minutes. There are no reminders.

| Step | Webhook `status` | Channels | What the member receives |
|---|---|---|---|
| Confirmed, member paid part of the fee | `confirmed` | E | Payment confirmed; a doctor connects within 2 minutes; invoice attached. A fully sponsored instant call gets no confirmation message |
| No-show | `noshow` | E, W, I | The doctor tried several times but couldn't connect; request a new consultation. No push |
| Completed | `completed` | E, W, P | Email asks for a rating |
| Request marked incomplete | | E | The consultation was missed; request a new one |

## 5. Notes

- Timing: pharmacy refunds take 3-5 business days; consultation refunds after a failed clinic
  verification take 5 working days. Vision payment reminders go 8, 15 and 22 hours after the
  payment link; vision prescription reminders go on day 0, 3 and 5.
- Consultation reminders run at 17:00 local time the day before and 06:00 local time on the
  day, plus the time-before reminders listed per type.
- White-labelled companies: at request received for consultations, WhatsApp is the only
  channel (no email, in-app or push). Confirmation, rejection and summary messages have
  white-label WhatsApp variants. See [white-labelling.md](white-labelling.md).
- Mental wellness consultations say "counsellor" instead of "doctor".
- Messages to clinics, doctors and hlthstack staff are not listed here.

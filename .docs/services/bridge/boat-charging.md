# Bridge Boat Charging

## Purpose of the module
Provide one consistent boat-charging journey in the app: discover locations to charge a boat, start and follow sessions, read rules/settings, manage vignettes, and receive long-session notifications.

## Main business rules
- After payment collection, the session is CheckedOut and the socket is blocked for others until session end, or 20 minutes if charging never starts. This shows as occupied to the user. 
- Availability of a socket is determined by NRG. It is only true when  both socket status and charging station status are AVAILABLE, and the socket is not blocked (as described above).
- Location health is derived from socket-level data into a single user-facing state (operative, occupied, inoperative, unknown).
- Reported location capacity uses the highest relevant power value, prioritizing currently operative sockets.
- Session flow is payment-first: users initialize a session to obtain checkout, then can start/stop/cancel.
- Session lists support filtering by charging-session status (active or completed) before pagination.
- Stopping or cancelling a session ends local notification tracking for that session.
- During charging, reminder notifications are sent at +16h and +20h; from +24h onward, penalty reminders repeat hourly.
- When charging completes, a completion notification is sent and the session is removed from active notification tracking.
- Terms are versioned documents; the highest numeric version is the active one.
- Settings are exposed as typed values (amounts, VAT, expiry/fine flags), with missing or invalid upstream values returned as empty.
- Vignettes are user-bound: users can link, list, update, unlink, and pre-verify vignette ownership using vignette number plus postal code. Verification reasons use the supported reason codes; unrecognized upstream reasons are reported as `UNKNOWN`.

## Major non-standard architectural decisions
- The module trusts upstream availability/hold semantics as source of truth instead of recalculating occupancy locally.
- Multiple upstream status taxonomies are normalized into one stable app-facing status model.
- Notification timing is stateful and persisted per session/device, so reminders are idempotent across command reruns/restarts.
- Public and authenticated boat-charging capabilities are intentionally mixed (for example: discoverability and checks are public, personal assets require authentication).

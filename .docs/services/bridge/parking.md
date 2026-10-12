# Bridge Parking

## Purpose of the module
Provide a single, client-stable parking domain for Amsterdam App, covering permits, sessions, visitor usage, wallet flows, and parking machine discovery.

## Main business rules
- Access is role-based: permit holders can use full parking and account capabilities; visitor roles are restricted to visitor-relevant operations.
- Account login returns a short-lived app token scope and account details expose wallet balance in EUR where applicable.
- Permit overviews include only parking-usable permits, with normalized permit type labels and permit capabilities (session start, activation, visitor, balances, zone selection).
- Permit zone information is delivered in client-ready zone shapes and machine-based zone schedules.
- License plate management supports listing, adding, and removing plates, combining permit-bound plates with saved favorites when applicable.
- Session lifecycle supports start, activate, update end time, stop, list/history, visitor list, and receipt estimation.
- Session list retrieval supports status filtering and a dedicated next-24-hours mode that returns only sessions overlapping the next 24 hours.
- Visitor management supports creating/deactivating visitor accounts and moving visitor time balance between main and visitor balances.
- Wallet top-up supports payment initiation, confirmation, and transaction history in a consistent format.
- Parking machine retrieval is limited to Amsterdam machines and returned in normalized location fields.
- Parking reminder notifications are managed around session timing (create, update, cancel) to avoid stale reminders.
- For vehicle information: A licence plate that is not found must be handled as a valid functional outcome, not as a technical failure.

## Major non-standard architectural decisions
- The module brokers two upstream SSP API contexts (internal APIs and external APIs) behind one client contract and keeps provider-specific concerns inside the backend.
- Next-24-hours filtering is executed as backend domain logic, and pagination totals are intentionally omitted in that mode to avoid misleading counts.
- Session date-times are normalized for provider expectations to keep session timing behavior predictable across time zones.
- Reminder scheduling is keyed per parking session, allowing deterministic overwrite/cancel behavior when sessions change.
- Vehicle reference data is sourced from the Dutch RDW open data service as the external authority.

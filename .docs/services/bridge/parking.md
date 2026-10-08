# Bridge Parking

## Purpose of the module
Provide a consistent parking session experience for Amsterdam App by exposing parking session lifecycle data in a client-oriented format.

## Main business rules
- Session list retrieval supports regular status-based filtering and a dedicated next-24-hours mode.
- When next-24-hours mode is requested, the upstream status scope is constrained to active and planned sessions.
- In next-24-hours mode, only sessions that overlap the upcoming 24-hour time window are returned.
- In next-24-hours mode, pagination totals are intentionally omitted because totals are not meaningful after post-retrieval time-window filtering.
- Session status values from external providers are normalized to the app contract so clients receive stable domain terminology.

## Major non-standard architectural decisions
- Time-window filtering for next-24-hours mode is applied by this backend as domain logic to deliver predictable near-term planning behavior.
- In next-24-hours mode, pagination metadata is deliberately partial to avoid presenting misleading totals after domain filtering.

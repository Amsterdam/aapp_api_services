# Bridge Burning Guide

## Purpose of the module
Provide Amsterdam residents with wood-burning guidance per postal area and send proactive alerts when a new Code Red period is about to start.

## Main business rules
- Only Amsterdam postal codes are accepted for burning-guide usage.
- Users can opt in per device for burning-guide notifications; each device has a single burning-guide subscription with one active postal code.
- Address updates keep the burning-guide postal code in sync for already-subscribed devices; removing an address clears the stored postal code.
- Advice is retrieved per 4-digit postal area and exposed in fixed forecast windows (now, +6h, +12h, +18h) with definitive/non-definitive status.
- Push alerts are evaluated on fixed daily moments and sent only when there is a **new** upcoming definitive Code Red window (not when it is already red now).
- Devices without a postal code are excluded from notification selection.
- After each evaluation cycle, processed devices are timestamped to prevent duplicate alerts for the same cycle.

## Major non-standard architectural decisions
- The module depends on RIVM stookwijzer data as external source of truth for advice.
- Geographic lookup is based on postal-area geometry translated to deterministic bounding boxes.
- Advice and lookup data are cached and refreshed around fixed publication moments to balance freshness and load.

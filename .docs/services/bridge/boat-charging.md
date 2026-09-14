# Bridge Boat Charging

## Purpose of the module
Provide a stable boat charging experience for Amsterdam App by exposing consistent location availability, status, and capacity information.

## Main business rules
- After payment collection, the session is CheckedOut and the socket is blocked for others until session end, or 20 minutes if charging never starts.
- Availability must be taken from the provided availability boolean (list and detail) and used as source of truth for socket selection.
- Availability is true only when both socket status and charging station status are AVAILABLE.
- Location status is derived as OPERATIVE, OCCUPIED, INOPERATIVE, or UNKNOWN based on connector operability and availability.
- Location capacity uses the highest relevant connector power, prioritizing operative connectors.

## Major non-standard architectural decisions
- Availability authority is delegated to NRG signals (including hold effects) instead of being recomputed in this backend.
- Upstream statuses are normalized to a canonical status set for consistent client behavior.

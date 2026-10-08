# Bridge Burning Guide

## Purpose of the module
Provide neighborhood-level burning guidance for Amsterdam App users based on postal-area lookup and forecasted advisory signals.

## Main business rules
- Advice is determined per postal area and translated into a stable app-facing advisory shape.
- Advisory updates focus on identifying whether a new red-status window is expected in the near term.
- Postal-area guidance data is cached with time-based refresh behavior aligned to advisory publication moments.

## Major non-standard architectural decisions
- The service relies on a public RIVM WMS data source for advisory retrieval and does not require a dedicated service-key authentication model.
- Geographic lookup is resolved via precomputed postal-area bounding boxes to keep runtime lookups deterministic and efficient.

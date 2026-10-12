# Bridge Parking

## Purpose of the module
Provide reliable parking-related information for Amsterdam App, including vehicle details lookup by licence plate to support user parking workflows.

## Main business rules
- Vehicle information can be requested using a licence plate provided by the client.
- Licence plates are treated in a normalized form so common user input variants are accepted.
- A licence plate that is not found must be handled as a valid functional outcome, not as a technical failure.
- For not-found outcomes, the service returns a successful request with an explicit no-result state.
- When data is available, the response includes core vehicle identification attributes needed by the app.

## Major non-standard architectural decisions
- Vehicle reference data is sourced from the Dutch RDW open data service as the external authority.
- The module is designed to tolerate temporary upstream instability by applying bounded retry behavior before concluding the request.
- Functional not-found outcomes are separated from technical error outcomes to reduce false operational noise and preserve a stable client experience.

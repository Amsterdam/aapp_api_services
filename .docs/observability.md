# Observability

## Purpose of the module
Define how telemetry is collected so operational incidents can be investigated while keeping data volume predictable across environments. This is only for testing purposes, the real implementation is inside the infra repository.

## Main business rules
- Failed requests must always remain observable.
- Slow requests must remain observable even when regular successful traffic is sampled.
- Successful requests are sampled with stricter limits in higher-risk environments and broader capture in non-production environments.
- Services emit telemetry only when the required runtime configuration is present, preventing partial or misleading telemetry output.
- Application metrics (including successful request and parking session counters) are exported via OTLP so business counters remain observable after the Azure Monitor SDK removal.

## Major non-standard architectural decisions
- Tail sampling is applied centrally in the collector layer so final sampling decisions use complete request outcome information.
- Local development routes telemetry through a local collector to keep observability behavior aligned with deployed environments.
- The same collector also accepts OTLP metrics through a dedicated metrics pipeline to keep trace/log/metric export paths consistent.

## Testing
- First start otel collector container: `docker compose up otel-collector`
- Then start service `SERVICE_NAME=<service> make dev` 
- See how requests show up in the otel-collector container 
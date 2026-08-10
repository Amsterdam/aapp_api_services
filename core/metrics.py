from opentelemetry import metrics

meter = metrics.get_meter("amsterdam-app")

parking_sessions_started_counter = meter.create_counter(
    name="parking_sessions_started",
    description="Number of successfully started parking sessions",
)

successful_requests_counter = meter.create_counter(
    name="successful_requests",
    description="Number of successful requests in all services",
)

from opentelemetry import metrics

meter = metrics.get_meter("amsterdam-app")

parking_sessions_started_counter = meter.create_counter(
    name="parking_sessions_started",
    description="Number of successfully started parking sessions",
)

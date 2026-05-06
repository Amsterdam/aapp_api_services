Review the proposed design like a senior platform engineer. Be very critical and thorough. Provide detailed feedback and suggestions for improvement.

Review for:

# Architecture
- unnecessary complexity
- coupling concerns
- maintainability
- extensibility

# Scalability
- horizontal scaling
- queue growth
- database bottlenecks
- memory pressure
- caching opportunities

# Reliability
- retry handling
- timeout handling
- failure recovery
- idempotency
- race conditions

# Operational Concerns
- deployment safety
- observability gaps
- alerting requirements
- supportability
- on-call impact

# Kubernetes Concerns
- readiness/liveness probes
- resource limits
- autoscaling
- rollout safety
- pod disruption concerns

# Azure Concerns
- cost implications
- managed identity usage
- networking/security
- storage implications

# Security
- authR/authZ
- secrets management
- injection vulnerabilities
- privilege escalation risks

# Migration / Rollout
- backward compatibility
- zero-downtime concerns
- rollback complexity

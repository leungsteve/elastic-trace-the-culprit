# Rollback Webhook Service

Automated rollback service for the "From Commit to Culprit" workshop.

## Overview

This service receives webhook calls from Elastic Alerting workflows and performs automated rollbacks by:
1. Modifying the `.env` file to change service versions
2. Restarting the affected service using `docker-compose`
3. Providing detailed status and logging with OpenTelemetry trace correlation

## Architecture

```
Elastic Alerting Workflow
        |
        | (POST /rollback)
        v
Rollback Webhook Service
        |
        |-- Update .env file
        |-- Run docker-compose up -d --no-deps {service}
        |-- Return status
        v
    Service Restarted
```

## Endpoints

### `POST /rollback`
Trigger a rollback operation.

**Request Body:**
```json
{
  "service": "order-service",
  "target_version": "v1.0",
  "alert_id": "slo-burn-rate-order-service",
  "alert_name": "Order Service SLO Burn Rate Alert",
  "reason": "SLO burn rate exceeded threshold",
  "triggered_at": "2025-12-09T15:30:45Z",
  "additional_context": {
    "slo_name": "order-service-latency",
    "burn_rate": 14.5,
    "current_latency_p95": 2500
  }
}
```

**Response:**
```json
{
  "status": "ROLLBACK_COMPLETED",
  "message": "Successfully rolled back order-service from v1.1-bad to v1.0",
  "service": "order-service",
  "previous_version": "v1.1-bad",
  "target_version": "v1.0",
  "rollback_id": "rb-20251209-153045-order-service",
  "started_at": "2025-12-09T15:30:45Z",
  "completed_at": "2025-12-09T15:31:12Z",
  "trace_id": "4a8d3f6b2e1c9a7b5d3e1f9c8a6b4d2e"
}
```

### `GET /health`
Health check endpoint (used by Docker healthcheck).

### `GET /ready`
Readiness check endpoint (validates Docker, .env, and docker-compose.yml are accessible).

### `GET /status`
Get the status of the last rollback operation.

### `GET /`
Service information and available endpoints.

### `GET /docs`
OpenAPI/Swagger documentation (FastAPI auto-generated).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `local` | Environment type (`local` or `instruqt`) |
| `COMPOSE_FILE` | `/app/infra/docker-compose.yml` | Path to docker-compose.yml |
| `ENV_FILE` | `/app/infra/.env` | Path to .env file |
| `WEBHOOK_PORT` | `9000` | Port to listen on |
| `LOG_LEVEL` | `info` | Logging level |
| `ELASTIC_ENDPOINT` | - | Elastic Cloud endpoint URL |
| `ELASTIC_API_KEY` | - | Elastic Cloud API key |
| `OTEL_SERVICE_NAME` | `rollback-webhook` | OpenTelemetry service name |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | OTLP protocol |

## Security Considerations

**IMPORTANT:** This service has privileged access to:
- The Docker socket (via mounted volume)
- The `.env` file (containing service versions)
- The ability to restart services

In a production environment, this would require:
- Strict access controls
- Audit logging
- Secret management
- Network isolation
- Rate limiting
- Authentication/authorization

For the workshop, these are intentionally simplified to demonstrate the automated rollback concept.

## Development

### Local Development

```bash
# Install dependencies
poetry install

# Run locally (without Docker)
poetry run python -m src.webhook.main

# Run with OpenTelemetry instrumentation
poetry run opentelemetry-instrument python -m src.webhook.main
```

### Building the Docker Image

```bash
docker build -t rollback-webhook:1.0.0 .
```

### Running with Docker Compose

The service is included in the main `docker-compose.yml`:

```yaml
rollback-webhook:
  image: rollback-webhook:1.0.0
  ports:
    - "9000:9000"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # Docker socket access
    - ./infra:/app/infra  # Access to .env and docker-compose.yml
  environment:
    - ENVIRONMENT=${ENVIRONMENT}
    - ELASTIC_ENDPOINT=${ELASTIC_ENDPOINT}
    - ELASTIC_API_KEY=${ELASTIC_API_KEY}
```

## Testing

### Manual Testing

```bash
# Trigger a rollback
curl -X POST http://localhost:9000/rollback \
  -H "Content-Type: application/json" \
  -d '{
    "service": "order-service",
    "target_version": "v1.0",
    "alert_id": "test-alert",
    "reason": "Manual test"
  }'

# Check status
curl http://localhost:9000/status

# Health check
curl http://localhost:9000/health
```

### Unit Tests

```bash
poetry run pytest tests/
```

## Observability

The service is fully instrumented with:

- **Traces:** All endpoints and rollback operations create spans
- **Logs:** Structured logging with trace ID correlation
- **Metrics:** Automatic HTTP metrics from EDOT auto-instrumentation

### Key Spans

- `rollback_webhook` - Overall webhook handling
- `execute_rollback` - Complete rollback operation
- `update_env_file` - .env file modification
- `restart_service` - docker-compose restart

### Log Correlation

All log messages include trace and span IDs:
```
2025-12-09 15:30:45 - webhook.rollback - INFO - Starting rollback rb-20251209-153045-order-service - trace_id=4a8d3f6b2e1c9a7b5d3e1f9c8a6b4d2e span_id=1234567890abcdef
```

## Workshop Integration

This service is a key component of Challenge 3 in the workshop:

1. Participant deploys bad code (v1.1-bad)
2. SLO burn rate alert fires
3. Elastic Alerting workflow calls this webhook
4. Service automatically rolls back to v1.0
5. Participant observes the rollback in Kibana traces and logs

The automated rollback demonstrates how modern observability platforms can
integrate with incident response workflows for self-healing systems.

## License

Copyright 2025 - From Commit to Culprit Workshop

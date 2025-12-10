# Inventory Service

Python FastAPI microservice for NovaMart's inventory management system.

Part of the "From Commit to Culprit" Elastic Observability workshop.

## Overview

The Inventory Service manages stock availability and reservations for the NovaMart e-commerce platform. It provides:

- Stock availability checking
- Atomic inventory reservation
- In-memory inventory store (stateless for workshop simplicity)
- Full EDOT (Elastic Distribution of OpenTelemetry) instrumentation

## Technology Stack

- **Python 3.11**
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic v2** - Data validation
- **EDOT Python** - OpenTelemetry auto-instrumentation

## API Endpoints

### Health & Readiness

- `GET /health` - Health check (liveness probe)
- `GET /ready` - Readiness check

### Inventory Operations

- `POST /api/inventory/check` - Check stock availability
  ```json
  {
    "items": [
      {"item_id": "WIDGET-001", "quantity": 5},
      {"item_id": "GADGET-042", "quantity": 2}
    ]
  }
  ```

- `POST /api/inventory/reserve` - Reserve inventory for an order
  ```json
  {
    "order_id": "ORD-12345",
    "items": [
      {"item_id": "WIDGET-001", "quantity": 5},
      {"item_id": "GADGET-042", "quantity": 2}
    ]
  }
  ```

- `GET /api/inventory/summary` - Get inventory summary (diagnostic)

## Inventory Data

The service maintains an in-memory inventory with the following items:

| Item ID | Name | Initial Stock | Price |
|---------|------|---------------|-------|
| WIDGET-001 | Standard Widget | 1000 | $29.99 |
| WIDGET-002 | Premium Widget | 500 | $49.99 |
| GADGET-042 | Super Gadget | 250 | $82.52 |

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Install dependencies
pip install -e .

# Run locally (without EDOT)
uvicorn inventory.main:app --reload --port 8081

# Or with EDOT instrumentation
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
opentelemetry-instrument uvicorn inventory.main:app --reload --port 8081
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Docker

### Build

```bash
docker build -t inventory-service:v1.0 .
```

### Run

```bash
docker run -p 8081:8081 \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318 \
  -e ENVIRONMENT=local \
  inventory-service:v1.0
```

## OpenTelemetry Instrumentation

The service is automatically instrumented using EDOT Python:

- **Traces**: Automatic HTTP span creation for all endpoints
- **Metrics**: HTTP server metrics (request count, duration, etc.)
- **Logs**: Structured logging with automatic trace ID correlation

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_SERVICE_NAME` | Service name in traces | `inventory-service` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | - |
| `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED` | Enable log instrumentation | `true` |
| `OTEL_PYTHON_LOG_CORRELATION` | Enable trace ID injection | `true` |
| `ENVIRONMENT` | Deployment environment | `unknown` |
| `SERVICE_VERSION` | Service version | `1.0.0` |

## Project Structure

```
inventory-service/
├── Dockerfile              # Container definition
├── pyproject.toml          # Dependencies and project metadata
├── README.md               # This file
└── src/
    └── inventory/
        ├── __init__.py     # Package initialization
        ├── main.py         # FastAPI application and endpoints
        ├── models.py       # Pydantic models
        └── data.py         # In-memory inventory store
```

## Workshop Context

This service is part of the "From Commit to Culprit" workshop demonstrating:

1. Distributed tracing across microservices
2. Log correlation with trace IDs
3. Automatic instrumentation with EDOT
4. Service-to-service communication patterns

The Inventory Service remains stable throughout the workshop - only the Order Service receives the "bad deployment" to demonstrate incident investigation.

## Key Features for Workshop Learning

1. **Startup Banner**: Displays environment and configuration on startup
2. **Trace Correlation**: All logs include trace IDs from EDOT
3. **Request Logging**: Middleware logs all requests with trace context
4. **Atomic Operations**: Inventory reservation demonstrates transaction patterns
5. **Error Handling**: Comprehensive exception handling with logging

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8081/docs
- ReDoc: http://localhost:8081/redoc

## Support

For workshop questions, refer to the main repository README or workshop guide.

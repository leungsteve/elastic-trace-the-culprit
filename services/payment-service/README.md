# Payment Service

Part of the "From Commit to Culprit" Instruqt workshop.

## Overview

The Payment Service is a Python FastAPI microservice that handles payment processing for NovaMart's e-commerce platform. It simulates payment gateway interactions with realistic success/failure rates and full observability through Elastic Distribution of OpenTelemetry (EDOT).

## Features

- **RESTful API**: FastAPI-based service with automatic OpenAPI documentation
- **Payment Processing**: Simulates payment gateway with 99% success rate
- **Deterministic Failures**: Uses order_id hash for reproducible failure scenarios
- **Stateless Design**: In-memory storage for workshop purposes (no database required)
- **Full Observability**: EDOT Python auto-instrumentation for traces, logs, and metrics
- **Health Checks**: Kubernetes-ready health and readiness endpoints
- **Trace Correlation**: Logs include trace_id and span_id for correlation

## Technology Stack

- **Python**: 3.11
- **Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn
- **Telemetry**: OpenTelemetry Python (EDOT)
- **Data Validation**: Pydantic v2

## API Endpoints

### Payment Operations

- `POST /api/payments` - Process a payment
  - Request: `PaymentRequest` (order_id, amount, payment_method, etc.)
  - Response: `PaymentResponse` with payment status
  - Success Rate: 99% (deterministic based on order_id hash)

- `GET /api/payments/{payment_id}` - Retrieve payment details
  - Path Parameter: `payment_id` (UUID)
  - Response: `PaymentResponse` with payment details

### Health Checks

- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check endpoint

### Documentation

- `GET /api/docs` - Swagger UI documentation
- `GET /api/redoc` - ReDoc documentation

## Payment Simulation Logic

The service simulates realistic payment processing:

1. **Success Rate**: 99% of payments succeed
2. **Failure Determination**: Deterministic based on SHA-256 hash of order_id
   - Hash mod 100 == 0 → Payment fails (1% probability)
   - Otherwise → Payment succeeds (99% probability)
3. **Transaction IDs**: Generated for successful payments (format: `TXN-{hex}`)
4. **Failure Reasons**: Realistic error messages (e.g., "insufficient funds")

This deterministic approach ensures:
- Reproducible test scenarios
- Consistent behavior across runs
- Realistic failure patterns for demonstration

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Service name for logging | `payment-service` |
| `SERVICE_VERSION` | Service version | `v1.0` |
| `ENVIRONMENT` | Deployment environment | `local` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint | `http://localhost:4318` |
| `OTEL_SERVICE_NAME` | Service name for OTEL | `payment-service` |
| `OTEL_RESOURCE_ATTRIBUTES` | Additional OTEL attributes | See Dockerfile |

## Running Locally

### Using Docker

```bash
# Build the image
docker build -t payment-service:v1.0 .

# Run the container
docker run -p 8082:8082 \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318 \
  payment-service:v1.0
```

### Using Poetry

```bash
# Install dependencies
poetry install

# Run with auto-instrumentation
opentelemetry-instrument \
  --traces_exporter otlp \
  --metrics_exporter otlp \
  --logs_exporter otlp \
  uvicorn payment.main:app --host 0.0.0.0 --port 8082
```

## Testing

### Process a Payment

```bash
curl -X POST http://localhost:8082/api/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-123",
    "amount": 47.50,
    "currency": "USD",
    "payment_method": "credit_card",
    "customer_id": "customer-456"
  }'
```

### Get Payment Status

```bash
curl http://localhost:8082/api/payments/{payment_id}
```

### Health Check

```bash
curl http://localhost:8082/health
```

## Observability

The service is fully instrumented with EDOT Python:

### Traces

- Automatic span creation for HTTP requests
- Custom spans for payment processing logic
- Span attributes include:
  - `payment.order_id`
  - `payment.amount`
  - `payment.currency`
  - `payment.method`
  - `payment.status`
  - `payment.transaction_id`
  - `gateway.provider`
  - `gateway.result`

### Logs

- Structured logging with trace correlation
- Log format includes `trace_id` and `span_id`
- Log levels: INFO, WARNING, ERROR
- Key events logged:
  - Payment processing start/completion
  - Gateway approval/decline
  - Payment retrieval
  - Errors and exceptions

### Metrics

Auto-instrumentation provides:
- HTTP request duration
- Request count by endpoint
- Error rate
- Active requests

## Error Handling

The service handles errors gracefully:

- **402 Payment Required**: Payment declined by gateway
- **404 Not Found**: Payment ID not found
- **422 Validation Error**: Invalid request data
- **500 Internal Server Error**: Unexpected errors

All errors include:
- Trace correlation IDs
- Detailed error messages
- Service context

## Workshop Context

This service is part of the "From Commit to Culprit" workshop, which teaches:
- Distributed tracing with Elastic APM
- Log correlation across services
- Service health monitoring
- Incident investigation techniques

The Payment Service demonstrates:
- Proper OpenTelemetry instrumentation
- Trace propagation across service boundaries
- Error handling and observability
- Realistic failure scenarios for training

## Development

### Code Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Format with Black
- Sort imports with isort

### Adding Features

When adding new features:
1. Update models in `models.py`
2. Add endpoint logic in `main.py`
3. Add appropriate span attributes
4. Log key events with trace correlation
5. Update tests
6. Update this README

## License

Part of Elastic Observability workshop materials.

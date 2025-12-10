# Telemetry Validation Tests

Comprehensive test suite for validating OpenTelemetry instrumentation in the "From Commit to Culprit" workshop.

## Overview

This test suite validates that:
- W3C trace context propagates correctly across services
- Logs contain trace_id for correlation
- Spans include expected attributes (especially the bug span)
- OTEL Collector receives and processes telemetry

## Test Structure

```
tests/telemetry/
├── __init__.py                    # Package initialization
├── conftest.py                    # Shared fixtures and configuration
├── test_trace_propagation.py     # W3C trace context tests
├── test_log_correlation.py        # Log correlation tests
├── test_span_attributes.py        # Span attribute validation
└── test_collector.py              # OTEL collector integration tests
```

## Prerequisites

### 1. Install Test Dependencies

```bash
pip install -r tests/requirements.txt
```

### 2. Start Docker Compose Environment

```bash
# From the repository root
cd infra
docker-compose up -d

# Wait for services to be healthy
./scripts/health-check.sh
```

### 3. Configure Environment Variables

The tests use environment variables to locate services. Default values:

```bash
ORDER_SERVICE_URL=http://localhost:8088
INVENTORY_SERVICE_URL=http://localhost:8081
PAYMENT_SERVICE_URL=http://localhost:8082
OTEL_COLLECTOR_URL=http://localhost:4318
```

Override these in `pytest.ini` or via command line:

```bash
pytest tests/telemetry/ \
  --env ORDER_SERVICE_URL=http://custom-host:8080
```

## Running Tests

### Run All Telemetry Tests

```bash
pytest tests/telemetry/
```

### Run Specific Test Files

```bash
# Trace propagation tests only
pytest tests/telemetry/test_trace_propagation.py

# Log correlation tests only
pytest tests/telemetry/test_log_correlation.py

# Span attribute tests only
pytest tests/telemetry/test_span_attributes.py

# Collector tests only
pytest tests/telemetry/test_collector.py
```

### Run Specific Test Classes

```bash
# Test W3C trace propagation
pytest tests/telemetry/test_trace_propagation.py::TestW3CTracePropagation

# Test bug span attributes
pytest tests/telemetry/test_span_attributes.py::TestBugSpanAttributes
```

### Run Specific Test Methods

```bash
pytest tests/telemetry/test_span_attributes.py::TestBugSpanAttributes::test_bug_span_attribution_metadata
```

### Run with Verbose Output

```bash
pytest tests/telemetry/ -v
```

### Run with Test Coverage

```bash
pytest tests/telemetry/ --cov=tests --cov-report=html
```

### Run in Parallel

```bash
# Run tests across 4 CPU cores
pytest tests/telemetry/ -n 4
```

## Test Categories

### Trace Propagation Tests (`test_trace_propagation.py`)

Validates W3C trace context propagation:

- **W3C Trace Propagation**: Tests that trace_id propagates from order service through inventory to payment
- **Parent-Child Relationships**: Verifies span hierarchy is correct
- **Cross-Service Tracing**: Ensures HTTP clients inject trace context
- **Sampling Consistency**: Validates sampling decisions propagate
- **Baggage Propagation**: Tests W3C baggage header propagation

### Log Correlation Tests (`test_log_correlation.py`)

Validates log and trace correlation:

- **Log Trace Correlation**: Tests that logs contain trace_id
- **Log Format**: Verifies OTEL correlation fields are present
- **Log Filtering**: Tests filtering logs by trace_id
- **Structured Logging**: Validates JSON log output (if enabled)
- **Exception Logging**: Ensures exceptions include trace_id

### Span Attribute Tests (`test_span_attributes.py`)

Validates span attributes:

- **Bug Span Attributes**: Tests the "detailed-trace-logging" span from Jordan's bug
  - `logging.type`: `detailed-trace`
  - `logging.author`: `jordan.rivera`
  - `logging.commit_sha`: `a1b2c3d4`
  - `logging.pr_number`: `PR-1247`
  - `logging.delay_ms`: `2000`
- **Service Version**: Tests `service.version` attribute
- **Business Attributes**: Validates order, payment, inventory attributes
- **HTTP Attributes**: Tests standard HTTP semantic conventions
- **Resource Attributes**: Validates service.name, deployment.environment

### OTEL Collector Tests (`test_collector.py`)

Validates OTEL collector functionality:

- **Collector Health**: Tests health check endpoint
- **OTLP Receivers**: Validates HTTP and gRPC receivers
- **Pipeline Processing**: Tests trace, metric, and log pipelines
- **Processors**: Validates resource, batch, and memory_limiter processors
- **Exporter**: Tests export to Elastic (mocked)
- **Error Handling**: Validates graceful error handling

## Test Design Philosophy

These tests are designed to:

1. **Run Against Live Services**: Tests execute against the actual docker-compose environment
2. **Graceful Degradation**: Tests skip (not fail) if services are unavailable
3. **Workshop Context**: Tests validate the specific instrumentation used in the workshop
4. **Documentation**: Each test includes detailed docstrings explaining what it validates

### Note on Full vs Partial Tests

Many tests include comments like:

```python
# In a full test with OTEL collector access, we would:
# 1. Query for the trace
# 2. Verify span attributes
# 3. Check for specific values
```

This indicates where the test would be enhanced with:
- Direct access to the OTEL collector's internal state
- Access to Elastic APM API for querying traces
- Log aggregation for querying application logs

The current implementation validates that:
- Services are instrumented correctly
- Requests succeed with trace context
- HTTP endpoints behave as expected

A production test suite would extend these with actual trace/log/metric queries.

## Testing the Bug Span

To test the "detailed-trace-logging" span attributes, ensure the bad version is deployed:

```bash
# Deploy v1.1-bad
./scripts/deploy.sh order-service v1.1-bad

# Run span attribute tests
pytest tests/telemetry/test_span_attributes.py::TestBugSpanAttributes -v

# Rollback to good version
./scripts/rollback.sh order-service
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Telemetry Tests
  run: |
    docker-compose -f infra/docker-compose.yml up -d
    sleep 10  # Wait for services
    pytest tests/telemetry/ -v --junitxml=test-results.xml
    docker-compose -f infra/docker-compose.yml down
```

## Troubleshooting

### Services Not Available

If tests skip with "Service not available":

1. Check docker-compose is running:
   ```bash
   docker-compose -f infra/docker-compose.yml ps
   ```

2. Check service health:
   ```bash
   curl http://localhost:8088/api/orders/health
   curl http://localhost:8081/health
   curl http://localhost:8082/health
   ```

3. Check logs:
   ```bash
   docker-compose -f infra/docker-compose.yml logs order-service
   ```

### Connection Timeouts

If tests timeout:

1. Increase timeout in `pytest.ini`:
   ```ini
   timeout = 600  # 10 minutes
   ```

2. Or use `--timeout` flag:
   ```bash
   pytest tests/telemetry/ --timeout=600
   ```

### Port Conflicts

If services fail to start due to port conflicts:

1. Check what's using the ports:
   ```bash
   lsof -i :8080
   lsof -i :8081
   lsof -i :8082
   lsof -i :4318
   ```

2. Stop conflicting services or use different ports

## Contributing

When adding new telemetry tests:

1. Follow the existing test structure
2. Use descriptive test names (test_what_is_being_validated)
3. Include detailed docstrings
4. Add appropriate markers (`@pytest.mark.telemetry`)
5. Handle service unavailability gracefully (use `pytest.skip()`)
6. Document expected behavior in comments

## Related Documentation

- [EDOT Python Documentation](https://www.elastic.co/guide/en/apm/agent/python/current/index.html)
- [EDOT Java Documentation](https://www.elastic.co/guide/en/apm/agent/java/current/index.html)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Java](https://opentelemetry.io/docs/instrumentation/java/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)

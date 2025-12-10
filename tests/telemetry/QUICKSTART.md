# Telemetry Tests - Quick Start

## Prerequisites

```bash
# 1. Start docker-compose
cd infra
docker-compose up -d

# 2. Install test dependencies
pip install -r tests/requirements.txt
```

## Run All Tests

```bash
# Using the runner script (recommended)
./tests/run_telemetry_tests.sh

# Or using pytest directly
pytest tests/telemetry/ -v
```

## Run Specific Tests

```bash
# Trace propagation
pytest tests/telemetry/test_trace_propagation.py -v

# Log correlation
pytest tests/telemetry/test_log_correlation.py -v

# Span attributes (includes bug span tests)
pytest tests/telemetry/test_span_attributes.py -v

# OTEL collector
pytest tests/telemetry/test_collector.py -v
```

## Test the Bug Span

```bash
# 1. Deploy bad version
./scripts/deploy.sh order-service v1.1-bad

# 2. Run bug span tests
pytest tests/telemetry/test_span_attributes.py::TestBugSpanAttributes -v

# 3. Rollback
./scripts/rollback.sh order-service
```

## Common Commands

```bash
# Run with coverage
pytest tests/telemetry/ --cov=tests --cov-report=html

# Run in parallel (4 cores)
pytest tests/telemetry/ -n 4

# Run specific test method
pytest tests/telemetry/test_span_attributes.py::TestBugSpanAttributes::test_bug_span_attribution_metadata -v

# Run with extra verbosity
pytest tests/telemetry/ -vv

# Generate HTML report
pytest tests/telemetry/ --html=test-report.html --self-contained-html
```

## Troubleshooting

```bash
# Check services are running
docker-compose ps

# Check service health
curl http://localhost:8088/api/orders/health
curl http://localhost:8081/health
curl http://localhost:8082/health

# View service logs
docker-compose logs order-service
docker-compose logs inventory-service
docker-compose logs payment-service

# Restart services
docker-compose restart
```

## Expected Output

```
tests/telemetry/test_trace_propagation.py::TestW3CTracePropagation::test_trace_id_propagation_across_services PASSED
tests/telemetry/test_log_correlation.py::TestLogTraceCorrelation::test_logs_contain_trace_id PASSED
tests/telemetry/test_span_attributes.py::TestBugSpanAttributes::test_bug_span_attribution_metadata PASSED
tests/telemetry/test_collector.py::TestCollectorHealth::test_collector_health_endpoint PASSED
```

## Test Duration

- Full suite: ~2-3 minutes
- Individual test file: ~30-60 seconds
- Single test: ~5-10 seconds

## Key Test Files

- `test_trace_propagation.py` - W3C trace context (330 lines, 9 tests)
- `test_log_correlation.py` - Log correlation (380 lines, 11 tests)
- `test_span_attributes.py` - Span attributes (470 lines, 18 tests) ⭐ **Bug span tests**
- `test_collector.py` - OTEL collector (600 lines, 17 tests)

## Service URLs

Default configuration:
- Order Service: http://localhost:8088
- Inventory Service: http://localhost:8081
- Payment Service: http://localhost:8082
- OTEL Collector: http://localhost:4318

## More Info

See `tests/telemetry/README.md` for comprehensive documentation.

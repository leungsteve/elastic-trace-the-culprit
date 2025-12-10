# End-to-End Tests

Comprehensive E2E tests for the "From Commit to Culprit" workshop that validate the complete participant journey through all four challenges.

## Overview

These tests verify:

1. **Baseline State**: v1.0 is healthy with latency < 500ms
2. **Deploy Bad Version**: v1.1-bad deployment succeeds
3. **Verify Degradation**: Latency increases > 2000ms after bad deployment
4. **Trigger Rollback**: Manual and automated rollback mechanisms work
5. **Verify Recovery**: System returns to healthy state after rollback

## Test Structure

```
tests/e2e/
├── __init__.py                    # Package marker
├── conftest.py                    # Shared fixtures and configuration
├── test_workshop_scenario.py     # Full workshop flow tests
├── test_rollback_webhook.py      # Webhook functionality tests
└── README.md                      # This file
```

## Prerequisites

### Required Services

All services must be running before executing tests:

```bash
cd infra
docker-compose up -d
```

Verify all services are healthy:

```bash
../scripts/health-check.sh
```

### Required Environment

1. **Docker**: Must be running and accessible
2. **Environment File**: `infra/.env` must exist and be configured
3. **Images**: Both v1.0 and v1.1-bad images must be built
4. **Initial State**: Services should be on v1.0 before running tests

### Building Images

```bash
./scripts/build-images.sh
```

## Running Tests

### Run All E2E Tests

```bash
# From project root
pytest tests/e2e/ -v
```

### Run Specific Test Classes

```bash
# Test complete workshop flow
pytest tests/e2e/test_workshop_scenario.py::TestWorkshopScenario -v

# Test baseline validation
pytest tests/e2e/test_workshop_scenario.py::TestChallenge1Baseline -v

# Test deployment and detection
pytest tests/e2e/test_workshop_scenario.py::TestChallenge2DeployDetect -v

# Test rollback functionality
pytest tests/e2e/test_workshop_scenario.py::TestChallenge3InvestigateRemediate -v

# Test webhook functionality
pytest tests/e2e/test_rollback_webhook.py::TestRollbackWebhookFunctionality -v
```

### Run Specific Tests

```bash
# Test the complete workshop flow (master E2E test)
pytest tests/e2e/test_workshop_scenario.py::TestWorkshopScenario::test_complete_workshop_flow -v

# Test automated rollback webhook
pytest tests/e2e/test_rollback_webhook.py::TestRollbackWebhookFunctionality::test_webhook_triggers_rollback -v
```

### Run with Output

```bash
# Show print statements and detailed output
pytest tests/e2e/ -v -s

# Show only test names (quiet mode)
pytest tests/e2e/ -q
```

### Skip Slow Tests

Some tests marked as `@pytest.mark.slow` take longer to execute:

```bash
# Skip slow tests
pytest tests/e2e/ -v -m "not slow"
```

## Test Configuration

### Environment Variables

Override default service URLs:

```bash
export ORDER_SERVICE_URL=http://localhost:8088
export INVENTORY_SERVICE_URL=http://localhost:8081
export PAYMENT_SERVICE_URL=http://localhost:8082
export ROLLBACK_WEBHOOK_URL=http://localhost:9000
export OTEL_COLLECTOR_URL=http://localhost:13133
```

### Timing Configuration

Adjust timeouts in `conftest.py`:

- `BASELINE_LATENCY_THRESHOLD`: 500ms (healthy latency threshold)
- `BAD_LATENCY_THRESHOLD`: 1500ms (degraded latency threshold)
- `RECOVERY_LATENCY_THRESHOLD`: 500ms (recovered latency threshold)
- `NUM_LATENCY_SAMPLES`: 10 (number of requests to average)
- `SERVICE_RESTART_WAIT_TIME`: 30s (wait after service restart)
- `STABILIZATION_WAIT_TIME`: 10s (wait for metrics to stabilize)

## Test Fixtures

### Service Health

- `wait_for_services`: Waits for all services to be healthy before running tests
- `http_client`: Async HTTP client for making requests

### Service URLs

- `order_service_url`: Order service URL
- `inventory_service_url`: Inventory service URL
- `payment_service_url`: Payment service URL
- `rollback_webhook_url`: Rollback webhook URL

### Latency Measurement

- `latency_measurer`: Function that measures average latency over N requests

### Version Management

- `version_manager`: Functions to get current version and wait for version changes
  - `get_version()`: Returns current order-service version
  - `wait_for_version(version, timeout)`: Waits for specific version

### Script Execution

- `script_runner`: Function to execute scripts from `scripts/` directory
  - Example: `script_runner("deploy.sh", "order-service", "v1.1-bad")`

### Webhook Helpers

- `webhook_client`: Helper functions for webhook interaction
  - `trigger_rollback(service, target_version, ...)`: Trigger rollback via webhook
  - `get_status()`: Get webhook status

### State Management

- `initial_state`: Captures initial state and restores it after test (idempotency)
- `sample_order_request`: Sample order payload for testing

## Idempotent Tests

All tests use the `initial_state` fixture to ensure they restore the system to its original state after completion. This allows tests to run in any order without interfering with each other.

```python
async def test_example(initial_state, script_runner):
    # Test code here...
    # initial_state automatically restores version after test
    pass
```

## Test Markers

Tests are marked with pytest markers:

- `@pytest.mark.asyncio`: Async test (uses asyncio)
- `@pytest.mark.requires_services`: Requires all services to be running
- `@pytest.mark.requires_docker`: Requires Docker to be available
- `@pytest.mark.slow`: Test takes longer to execute

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker-compose -f infra/docker-compose.yml ps

# View logs
docker-compose -f infra/docker-compose.yml logs order-service

# Restart services
docker-compose -f infra/docker-compose.yml restart
```

### Tests Timeout Waiting for Services

Increase retry settings in `conftest.py`:

```python
max_retries = 60  # Increase from 30
retry_delay = 2
```

### Latency Measurements Inconsistent

- Ensure no other load is running on services
- Increase `NUM_LATENCY_SAMPLES` for more stable averages
- Check for resource constraints (CPU, memory)

### Version Not Changing

- Verify `.env` file exists and is writable
- Check docker-compose is using the `.env` file
- Ensure images are tagged correctly in registry

### Tests Leave System in Bad State

The `initial_state` fixture should restore state automatically. If it doesn't:

```bash
# Manually restore to v1.0
./scripts/rollback.sh order-service
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio httpx

      - name: Build images
        run: ./scripts/build-images.sh

      - name: Start services
        run: |
          cd infra
          docker-compose up -d

      - name: Wait for services
        run: ./scripts/health-check.sh

      - name: Run E2E tests
        run: pytest tests/e2e/ -v

      - name: Cleanup
        if: always()
        run: docker-compose -f infra/docker-compose.yml down
```

## Performance Benchmarks

Expected test execution times (on reference hardware):

- `test_complete_workshop_flow`: ~3-4 minutes
- Individual challenge tests: ~1-2 minutes each
- Webhook tests: ~30-60 seconds each
- Full E2E suite: ~10-15 minutes

## Best Practices

1. **Run tests in isolation**: Ensure no other workshop instances are running
2. **Clean state**: Start with v1.0 deployed for consistent results
3. **Resource availability**: Ensure sufficient CPU/memory for Docker containers
4. **Network stability**: Tests make many HTTP requests, ensure stable networking
5. **Review logs**: Check service logs if tests fail to understand root cause

## Related Documentation

- [Workshop Test Script](../../scripts/workshop-test.sh): Bash version of E2E flow
- [Telemetry Tests](../telemetry/): Tests for trace propagation and correlation
- [Unit Tests](../unit/): Service-specific unit tests
- [Integration Tests](../integration/): Service-to-service integration tests

## Support

If tests fail unexpectedly:

1. Check service health: `./scripts/health-check.sh`
2. Review service logs: `docker-compose -f infra/docker-compose.yml logs`
3. Verify images are built: `docker images | grep localhost:5000`
4. Check `.env` file configuration
5. Ensure Docker has sufficient resources allocated

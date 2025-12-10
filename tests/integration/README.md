# Integration Tests

Integration tests for service-to-service communication in the "From Commit to Culprit" workshop.

## Overview

These tests verify that the microservices communicate correctly with each other:

1. Order service calling inventory service
2. Order service calling payment service
3. Complete order flow (order -> inventory check -> payment -> confirmation)
4. Error handling when downstream services fail

## Prerequisites

All services must be running before executing integration tests. The tests will automatically skip if services are not available.

### Start Services

```bash
# From the project root
docker-compose -f infra/docker-compose.yml up -d

# Wait for services to be ready
./scripts/health-check.sh
```

## Running Tests

### Run All Integration Tests

```bash
# From the project root
cd tests/integration
pytest -v
```

### Run Specific Test Classes

```bash
# Test inventory service integration only
pytest -v test_service_integration.py::TestInventoryServiceIntegration

# Test payment service integration only
pytest -v test_service_integration.py::TestPaymentServiceIntegration

# Test full order flow
pytest -v test_service_integration.py::TestFullOrderFlow

# Test error handling
pytest -v test_service_integration.py::TestErrorHandling
```

### Run Specific Tests

```bash
# Test successful order flow
pytest -v test_service_integration.py::TestFullOrderFlow::test_successful_order_flow

# Test order with unavailable inventory
pytest -v test_service_integration.py::TestFullOrderFlow::test_order_flow_with_unavailable_inventory
```

### Run with Coverage

```bash
# Run tests with coverage report
pytest -v --cov=. --cov-report=html --cov-report=term
```

### Run with Detailed Output

```bash
# Show all print statements and logs
pytest -v -s

# Show only failed tests with full output
pytest -v --tb=short --maxfail=1
```

## Test Structure

### `conftest.py`
Shared fixtures for all integration tests:
- HTTP client configuration
- Service URL fixtures
- Health check fixtures
- Sample request payloads
- Service availability checks

### `test_service_integration.py`
Main integration test suite with four test classes:

#### 1. TestInventoryServiceIntegration
Tests for order service integration with inventory service:
- Health checks
- Available item checks
- Unavailable item checks
- Order service calling inventory service

#### 2. TestPaymentServiceIntegration
Tests for order service integration with payment service:
- Health checks
- Payment processing
- Order service calling payment service

#### 3. TestFullOrderFlow
Tests for complete order flow:
- Successful order creation
- Order with unavailable inventory
- Order retrieval
- Order not found scenarios

#### 4. TestErrorHandling
Tests for error handling scenarios:
- Invalid request payloads
- Empty order items
- Invalid inventory requests
- Invalid payment requests
- Concurrent order creation

#### 5. TestServiceHealthAndReadiness
Tests for service health and readiness:
- All services healthy
- All services ready

## Environment Variables

You can customize service URLs via environment variables:

```bash
export ORDER_SERVICE_URL=http://localhost:8088
export INVENTORY_SERVICE_URL=http://localhost:8081
export PAYMENT_SERVICE_URL=http://localhost:8082

pytest -v
```

## Expected Behavior

### Successful Tests
When all services are running correctly:
- All health checks pass
- Order creation succeeds
- Inventory checks work correctly
- Payment processing completes
- Full order flow works end-to-end

### Skipped Tests
When services are not running:
- Tests will be automatically skipped with a message
- No test failures occur
- Message indicates services need to be started

### Failed Tests
If tests fail when services are running:
- Check service logs: `docker-compose logs order-service`
- Verify service health: `curl http://localhost:8088/api/orders/health`
- Check docker-compose status: `docker-compose ps`

## Test Data

Tests use deterministic test data:
- Customer ID: `integration-test-customer`
- Products: `LAPTOP-001`, `MOUSE-002` (exist in inventory)
- Invalid product: `NONEXISTENT-PRODUCT-999` (does not exist)
- Payment failure simulation: Based on order_id hash

## Troubleshooting

### Services Not Available

```bash
# Check if containers are running
docker-compose ps

# Start services if not running
docker-compose -f infra/docker-compose.yml up -d

# Check service logs
docker-compose logs -f order-service
docker-compose logs -f inventory-service
docker-compose logs -f payment-service
```

### Port Conflicts

If default ports are in use, update service URLs:

```bash
export ORDER_SERVICE_URL=http://localhost:9088
export INVENTORY_SERVICE_URL=http://localhost:9081
export PAYMENT_SERVICE_URL=http://localhost:9082
```

### Connection Timeouts

Increase timeout in `conftest.py` if services are slow to respond:

```python
async with httpx.AsyncClient(timeout=60.0) as client:
    yield client
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```bash
# GitHub Actions example
- name: Start services
  run: docker-compose -f infra/docker-compose.yml up -d

- name: Wait for services
  run: ./scripts/health-check.sh

- name: Run integration tests
  run: |
    cd tests/integration
    pytest -v --tb=short

- name: Stop services
  run: docker-compose down
```

## Related Documentation

- [Telemetry Tests](../telemetry/README.md) - Tests for trace propagation
- [Unit Tests](../unit/README.md) - Tests for individual service logic
- [Workshop Documentation](../../docs/) - Full workshop documentation

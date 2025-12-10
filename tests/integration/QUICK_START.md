# Integration Tests - Quick Start

Quick reference for running integration tests in the "From Commit to Culprit" workshop.

## Prerequisites

Services must be running:

```bash
docker-compose -f infra/docker-compose.yml up -d
```

## Run Tests

### Quick Run (Recommended)

```bash
# From project root
./tests/run_integration_tests.sh
```

### Manual Run

```bash
# From project root
cd tests/integration
pytest -v
```

## Common Test Commands

### Run Specific Test Classes

```bash
# Inventory integration tests
pytest -v -k "TestInventoryServiceIntegration"

# Payment integration tests
pytest -v -k "TestPaymentServiceIntegration"

# Full order flow tests
pytest -v -k "TestFullOrderFlow"

# Error handling tests
pytest -v -k "TestErrorHandling"
```

### Run Specific Tests

```bash
# Test successful order
pytest -v test_service_integration.py::TestFullOrderFlow::test_successful_order_flow

# Test inventory unavailable
pytest -v test_service_integration.py::TestFullOrderFlow::test_order_flow_with_unavailable_inventory

# Test concurrent orders
pytest -v test_service_integration.py::TestErrorHandling::test_concurrent_order_creation
```

### Run with Options

```bash
# Show print statements
pytest -v -s

# Stop on first failure
pytest -v -x

# Run with coverage
pytest -v --cov=. --cov-report=html

# Parallel execution
pytest -v -n auto
```

## Test Coverage

The integration tests cover:

### 1. Service-to-Service Communication
- ✓ Order service → Inventory service
- ✓ Order service → Payment service
- ✓ HTTP request/response handling
- ✓ Error propagation

### 2. Full Order Flow
- ✓ Successful order creation
- ✓ Inventory check
- ✓ Payment processing
- ✓ Order confirmation
- ✓ Order retrieval

### 3. Error Scenarios
- ✓ Unavailable inventory
- ✓ Payment failures
- ✓ Invalid requests
- ✓ Empty orders
- ✓ Non-existent orders

### 4. Concurrent Operations
- ✓ Multiple simultaneous orders
- ✓ Thread safety
- ✓ Race conditions

### 5. Health Checks
- ✓ Service health endpoints
- ✓ Service readiness endpoints

## Expected Results

### All Services Running
```
test_inventory_service_health_check PASSED                      [  5%]
test_inventory_check_available_items PASSED                     [ 10%]
test_order_service_calls_inventory_service PASSED               [ 15%]
test_payment_service_health_check PASSED                        [ 20%]
test_payment_processing_success PASSED                          [ 25%]
test_order_service_calls_payment_service PASSED                 [ 30%]
test_successful_order_flow PASSED                               [ 35%]
test_order_flow_with_unavailable_inventory PASSED               [ 40%]
...
======================== 30 passed in 15.42s ========================
```

### Services Not Running
```
SKIPPED [1] conftest.py:123: Service not available: http://localhost:8088
```

## Troubleshooting

### Services Not Available

```bash
# Check service status
docker-compose ps

# Start services
docker-compose -f infra/docker-compose.yml up -d

# Check logs
docker-compose logs -f order-service
```

### Tests Failing

```bash
# Run single test with verbose output
pytest -v -s test_service_integration.py::TestFullOrderFlow::test_successful_order_flow

# Check service health manually
curl http://localhost:8088/api/orders/health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

### Port Conflicts

```bash
# Use custom ports
export ORDER_SERVICE_URL=http://localhost:9088
export INVENTORY_SERVICE_URL=http://localhost:9081
export PAYMENT_SERVICE_URL=http://localhost:9082

pytest -v
```

## Test Data Reference

### Available Products
- `LAPTOP-001` - Laptop ($999.99, in stock)
- `MOUSE-002` - Mouse ($24.99, in stock)
- `KEYBOARD-003` - Keyboard ($79.99, in stock)

### Unavailable Products
- `NONEXISTENT-PRODUCT-999` - Does not exist

### Customer IDs
- `integration-test-customer` - Standard test customer

## Next Steps

After integration tests pass:

1. Run telemetry tests to verify trace propagation:
   ```bash
   ./tests/run_telemetry_tests.sh
   ```

2. Run full test suite:
   ```bash
   ./tests/run-tests.sh
   ```

3. Check test coverage:
   ```bash
   pytest --cov=. --cov-report=html
   open htmlcov/index.html
   ```

## Need Help?

- See [README.md](./README.md) for detailed documentation
- Check service logs: `docker-compose logs <service-name>`
- Review workshop docs: [../../docs/](../../docs/)

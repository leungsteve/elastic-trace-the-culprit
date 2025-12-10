# Unit Tests

This directory contains unit tests for all services in the "From Commit to Culprit" workshop.

## Directory Structure

```
tests/unit/
├── README.md                    # This file
├── pytest.ini                   # pytest configuration
├── order-service/               # Java/JUnit tests
│   ├── OrderControllerTest.java
│   └── OrderServiceTest.java
├── inventory-service/           # Python/pytest tests
│   ├── test_main.py
│   └── test_data.py
├── payment-service/             # Python/pytest tests
│   ├── test_main.py
│   └── test_payment_logic.py
└── rollback-webhook/            # Python/pytest tests
    ├── test_main.py
    └── test_rollback.py
```

## Running Tests

### Order Service (Java/JUnit)

The Order Service tests are Java-based and use JUnit 5, MockMvc, and Mockito.

```bash
# From the order-service directory
cd services/order-service

# Run all tests
mvn test

# Run a specific test class
mvn test -Dtest=OrderControllerTest

# Run tests with coverage
mvn test jacoco:report
```

The test files are located in `tests/unit/order-service/` but should be copied to `services/order-service/src/test/java/com/novamart/order/` to run with Maven.

### Inventory Service (Python/pytest)

```bash
# From the tests/unit directory
cd tests/unit

# Run all inventory service tests
pytest inventory-service/

# Run a specific test file
pytest inventory-service/test_main.py

# Run with verbose output
pytest inventory-service/ -v

# Run with coverage
pytest inventory-service/ --cov=inventory --cov-report=html

# Run specific test class
pytest inventory-service/test_main.py::TestStockCheck

# Run specific test method
pytest inventory-service/test_main.py::TestStockCheck::test_check_stock_available
```

### Payment Service (Python/pytest)

```bash
# From the tests/unit directory
cd tests/unit

# Run all payment service tests
pytest payment-service/

# Run specific test file
pytest payment-service/test_main.py

# Run with coverage
pytest payment-service/ --cov=payment --cov-report=html

# Run only fast tests (skip slow tests)
pytest payment-service/ -m "not slow"
```

### Rollback Webhook (Python/pytest)

```bash
# From the tests/unit directory
cd tests/unit

# Run all rollback webhook tests
pytest rollback-webhook/

# Run specific test file
pytest rollback-webhook/test_rollback.py

# Run with coverage
pytest rollback-webhook/ --cov=webhook --cov-report=html
```

### Run All Python Tests

```bash
# From the tests/unit directory
cd tests/unit

# Run all Python tests
pytest

# Run with coverage for all services
pytest --cov=inventory --cov=payment --cov=webhook --cov-report=html

# Run with parallel execution (requires pytest-xdist)
pytest -n auto
```

## Test Coverage

### Order Service Tests

**OrderControllerTest.java:**
- Create order success
- Create order failure
- Create order with bug enabled (v1.1-bad delay)
- Get order by ID (found and not found)
- Health check endpoint
- Readiness check endpoint

**OrderServiceTest.java:**
- Create order with successful inventory and payment
- Create order with inventory unavailable
- Create order with payment declined
- Total amount calculation
- Product ID extraction
- Order retrieval (found and not found)
- In-memory order storage
- Empty items list handling

### Inventory Service Tests

**test_main.py:**
- Health and readiness checks
- Stock availability checking (available, insufficient, not found)
- Inventory reservation (success, failure, atomic operation)
- Inventory summary endpoint

**test_data.py:**
- Item retrieval (existing, non-existent, case sensitivity)
- Stock availability checking
- Item reservation (success, insufficient stock, atomic operation, thread safety)
- Inventory summary calculations
- Reset functionality

### Payment Service Tests

**test_main.py:**
- Health and readiness checks
- Payment processing (success and deterministic failure)
- Payment retrieval (found and not found)
- Idempotency handling
- Different payment methods (credit card, debit card, PayPal)
- Request validation

**test_payment_logic.py:**
- Deterministic failure calculation
- Failure rate distribution (approximately 1%)
- SHA256 hash-based failure logic
- Edge cases (empty string, special characters, long IDs)

### Rollback Webhook Tests

**test_main.py:**
- Root endpoint with service information
- Health check (with/without Docker)
- Readiness check (all dependencies)
- Status endpoint (no rollbacks, with history)
- Rollback trigger (success, failure, different services)
- Exception handling

**test_rollback.py:**
- RollbackExecutor initialization
- Environment validation (all valid, missing files, Docker unavailable)
- Current version retrieval
- Service version update
- Service restart (docker compose v1 and v2)
- Complete rollback execution
- Environment variable name generation

## Prerequisites

### Python Tests

Install test dependencies:

```bash
# For inventory service
cd services/inventory-service
pip install -e ".[dev]"

# For payment service
cd services/payment-service
pip install -e ".[dev]"

# For rollback webhook
cd services/rollback-webhook
pip install -e ".[dev]"

# Or install all at once
pip install pytest pytest-asyncio httpx pytest-cov
```

### Java Tests

Maven will automatically download test dependencies defined in `pom.xml`:
- spring-boot-starter-test (includes JUnit 5, MockMvc, AssertJ)
- mockito-core
- junit-jupiter

## Best Practices

### Writing Tests

1. **Use descriptive test names** that explain what is being tested
2. **Follow the Arrange-Act-Assert pattern**
3. **Mock external dependencies** (don't make real HTTP calls or database queries)
4. **Test both success and failure paths**
5. **Keep tests independent** (no shared state between tests)
6. **Use fixtures** for common setup code

### Test Organization

1. **Group related tests in classes** (Python) or nested test classes (Java)
2. **Use clear test method names** like `test_create_order_success`
3. **Add docstrings** explaining what each test validates
4. **Use markers** to categorize tests (slow, integration, etc.)

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Python tests
  run: |
    cd tests/unit
    pytest --cov --cov-report=xml

- name: Run Java tests
  run: |
    cd services/order-service
    mvn test
```

## Troubleshooting

### Python Import Errors

If you get import errors when running Python tests:

```bash
# Make sure you're in the tests/unit directory
cd tests/unit

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../services/inventory-service/src"
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../services/payment-service/src"
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../services/rollback-webhook/src"
```

### Java Test Location

The Java test files in `tests/unit/order-service/` are reference implementations. To run them with Maven, they should be in the standard Maven test directory: `services/order-service/src/test/java/com/novamart/order/`

### TestClient Issues

If FastAPI TestClient has issues, ensure you have the correct dependencies:

```bash
pip install "fastapi[test]" httpx
```

## Workshop Context

These tests are part of the "From Commit to Culprit" Elastic Observability workshop. They:

1. **Validate service functionality** before and after deployments
2. **Document expected behavior** for workshop participants
3. **Enable safe refactoring** as the workshop evolves
4. **Demonstrate testing best practices** for microservices

The tests are designed to be:
- **Fast**: Run in seconds, not minutes
- **Reliable**: No flaky tests due to timing or external dependencies
- **Readable**: Clear test names and structure
- **Maintainable**: Easy to update as services evolve

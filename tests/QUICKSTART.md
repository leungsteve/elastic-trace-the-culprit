# Unit Tests Quick Start Guide

## Quick Test Commands

### Run All Tests
```bash
# From repository root
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests
./run-tests.sh
```

### Run Tests by Service

**Order Service (Java):**
```bash
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/services/order-service
mvn test
```

**Inventory Service (Python):**
```bash
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests/unit
pytest inventory-service/ -v
```

**Payment Service (Python):**
```bash
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests/unit
pytest payment-service/ -v
```

**Rollback Webhook (Python):**
```bash
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests/unit
pytest rollback-webhook/ -v
```

### Run with Coverage

**Java:**
```bash
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/services/order-service
mvn test jacoco:report
# View report: open target/site/jacoco/index.html
```

**Python:**
```bash
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests/unit
pytest --cov=inventory --cov=payment --cov=webhook --cov-report=html
# View report: open htmlcov/index.html
```

## Test Structure

```
/Users/steveleung/Documents/github/elastic-trace-the-culprit/
├── services/
│   └── order-service/
│       └── src/test/java/com/novamart/order/
│           ├── controller/OrderControllerTest.java
│           └── service/OrderServiceTest.java
│
└── tests/
    ├── run-tests.sh                    # Main test runner
    ├── QUICKSTART.md                   # This file
    └── unit/
        ├── pytest.ini                  # pytest configuration
        ├── inventory-service/
        │   ├── test_main.py           # API endpoint tests
        │   └── test_data.py           # Data layer tests
        ├── payment-service/
        │   ├── test_main.py           # API endpoint tests
        │   └── test_payment_logic.py  # Business logic tests
        └── rollback-webhook/
            ├── test_main.py           # API endpoint tests
            └── test_rollback.py       # Rollback logic tests
```

## What's Tested

### Order Service (Java/JUnit)
- ✓ Order creation (success and failure scenarios)
- ✓ Inventory and payment integration
- ✓ Bug behavior (v1.1-bad 2-second delay)
- ✓ Health and readiness endpoints
- ✓ In-memory order storage

### Inventory Service (Python/pytest)
- ✓ Stock availability checking
- ✓ Inventory reservation (atomic operations)
- ✓ Item retrieval and validation
- ✓ Thread-safe stock management
- ✓ Health and readiness endpoints

### Payment Service (Python/pytest)
- ✓ Payment processing (99% success rate)
- ✓ Deterministic failures (1% based on order ID hash)
- ✓ Multiple payment methods
- ✓ Idempotency handling
- ✓ Payment retrieval and validation

### Rollback Webhook (Python/pytest)
- ✓ Webhook endpoint functionality
- ✓ Rollback execution logic
- ✓ Docker compose integration
- ✓ Environment variable management
- ✓ Service version updates

## Test Counts

- **Order Service**: 17 tests
- **Inventory Service**: 30+ tests
- **Payment Service**: 30+ tests
- **Rollback Webhook**: 20+ tests
- **Total**: 97+ unit tests

## Prerequisites

### Python Services
```bash
# Install pytest and dependencies
pip install pytest pytest-asyncio httpx pytest-cov

# Or use service-specific dev dependencies
cd services/inventory-service && pip install -e ".[dev]"
cd services/payment-service && pip install -e ".[dev]"
cd services/rollback-webhook && pip install -e ".[dev]"
```

### Java Service
```bash
# Maven will auto-download dependencies
cd services/order-service
mvn clean install
```

## Common Issues

### Python Import Errors
```bash
# Make sure you're in the tests/unit directory
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests/unit
pytest
```

### Java Version
```bash
# Requires Java 21
java -version
# Should show: openjdk version "21" or similar
```

## Useful Test Options

### pytest Options
```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Run specific test
pytest inventory-service/test_main.py::TestStockCheck::test_check_stock_available

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "stock"

# Show slowest tests
pytest --durations=10
```

### Maven Options
```bash
# Run specific test
mvn test -Dtest=OrderControllerTest

# Skip tests
mvn install -DskipTests

# Verbose output
mvn test -X

# Run single test method
mvn test -Dtest=OrderControllerTest#testCreateOrder_Success
```

## CI/CD Integration

Tests are designed to run in continuous integration:

```yaml
# Example GitHub Actions
- name: Run all tests
  run: |
    cd tests
    ./run-tests.sh --coverage
```

## Next Steps

1. **Run all tests**: `./tests/run-tests.sh`
2. **Check coverage**: Add `--coverage` flag
3. **View detailed report**: See UNIT_TESTS_OVERVIEW.md
4. **Explore test code**: Read test files for examples

## Documentation

- **Full Test Documentation**: `/Users/steveleung/Documents/github/elastic-trace-the-culprit/UNIT_TESTS_OVERVIEW.md`
- **Test README**: `/Users/steveleung/Documents/github/elastic-trace-the-culprit/tests/unit/README.md`
- **Workshop README**: `/Users/steveleung/Documents/github/elastic-trace-the-culprit/README.md`

# Test Inventory - From Commit to Culprit Workshop

Complete inventory of all unit tests in the workshop codebase.

## Test File Locations

### Order Service (Java/JUnit 5)

#### `/services/order-service/src/test/java/com/novamart/order/controller/OrderControllerTest.java`
**Purpose**: Tests REST API endpoints for order operations
**Test Count**: 6 tests
**Key Tests**:
- testCreateOrder_Success - Validates successful order creation
- testCreateOrder_Failure - Validates failed order handling
- testCreateOrder_WithBugEnabled - Tests v1.1-bad bug behavior (2-second delay)
- testGetOrder_Found - Tests order retrieval by ID
- testGetOrder_NotFound - Tests 404 handling
- testHealthCheck - Tests /api/orders/health endpoint
- testReadinessCheck - Tests /api/orders/ready endpoint

**Dependencies**: Mockito, JUnit 5, Spring Boot Test
**Mock Objects**: OrderService, Tracer

#### `/services/order-service/src/test/java/com/novamart/order/service/OrderServiceTest.java`
**Purpose**: Tests business logic for order processing
**Test Count**: 9 tests
**Key Tests**:
- testCreateOrder_Success - Full order creation flow
- testCreateOrder_InventoryUnavailable - Inventory unavailable scenario
- testCreateOrder_PaymentDeclined - Payment declined scenario
- testCreateOrder_CalculatesTotalCorrectly - Price calculation logic
- testCreateOrder_ExtractsProductIdsCorrectly - Product ID extraction
- testGetOrder_Found - Order retrieval from in-memory store
- testGetOrder_NotFound - Non-existent order handling
- testCreateOrder_StoresOrderInMemory - In-memory storage validation
- testCreateOrder_HandlesEmptyItemsList - Edge case: empty order

**Dependencies**: Mockito, JUnit 5, OpenTelemetry API
**Mock Objects**: InventoryClient, PaymentClient, Tracer, Span

---

### Inventory Service (Python/pytest)

#### `/tests/unit/inventory-service/test_main.py`
**Purpose**: Tests FastAPI REST endpoints
**Test Count**: 14 tests across 4 test classes
**Test Classes**:
- **TestHealthEndpoints** (2 tests)
  - test_health_check - Health endpoint validation
  - test_readiness_check - Readiness endpoint with dependency checks

- **TestStockCheck** (5 tests)
  - test_check_stock_available - All items available
  - test_check_stock_insufficient - Insufficient stock scenario
  - test_check_stock_item_not_found - Non-existent item handling
  - test_check_stock_missing_item_id - Missing item_id validation
  - test_check_stock_mixed_availability - Partial availability

- **TestInventoryReservation** (5 tests)
  - test_reserve_items_success - Successful reservation
  - test_reserve_items_insufficient_stock - Insufficient stock handling
  - test_reserve_items_no_items - Empty items validation
  - test_reserve_items_atomic_operation - All-or-nothing guarantee

- **TestInventorySummary** (2 tests)
  - test_get_inventory_summary - Summary endpoint
  - test_inventory_summary_after_reservation - Updated summary

**Dependencies**: pytest, FastAPI TestClient, httpx
**Fixtures**: client, reset_inventory_state

#### `/tests/unit/inventory-service/test_data.py`
**Purpose**: Tests data layer and business logic
**Test Count**: 19 tests across 5 test classes
**Test Classes**:
- **TestGetItem** (4 tests)
  - test_get_existing_item - Item retrieval
  - test_get_all_initial_items - All default items
  - test_get_non_existent_item - Missing item returns None
  - test_get_item_case_sensitive - Case sensitivity

- **TestCheckAvailability** (5 tests)
  - test_check_availability_sufficient_stock - Stock check
  - test_check_availability_exact_stock - Exact quantity
  - test_check_availability_insufficient_stock - Insufficient detection
  - test_check_availability_zero_quantity - Zero quantity
  - test_check_availability_non_existent_item - Missing item

- **TestReserveItems** (8 tests)
  - test_reserve_items_success - Multi-item reservation
  - test_reserve_items_deducts_stock - Stock decremented
  - test_reserve_items_insufficient_stock - Failure handling
  - test_reserve_items_atomic_operation - Transaction rollback
  - test_reserve_items_missing_item_id - Validation error
  - test_reserve_items_non_existent_item - Missing item
  - test_reserve_items_multiple_success - Sequential reservations
  - test_reserve_items_thread_safety - Thread locking

- **TestGetInventorySummary** (3 tests)
  - test_get_inventory_summary_initial_state - Initial state
  - test_get_inventory_summary_calculates_value_correctly - Value calc
  - test_get_inventory_summary_after_reservation - Updated summary

- **TestResetInventory** (3 tests)
  - test_reset_inventory_restores_initial_state - Reset functionality
  - test_reset_inventory_clears_reservations - Reservation cleanup
  - test_reset_inventory_restores_all_items - All items restored

**Dependencies**: pytest
**Fixtures**: reset_state

---

### Payment Service (Python/pytest)

#### `/tests/unit/payment-service/test_main.py`
**Purpose**: Tests FastAPI payment processing endpoints
**Test Count**: 16 tests across 5 test classes
**Test Classes**:
- **TestHealthEndpoints** (2 tests)
  - test_health_check - Health endpoint
  - test_readiness_check - Readiness endpoint

- **TestProcessPayment** (6 tests)
  - test_process_payment_success - Successful payment (99% case)
  - test_process_payment_deterministic_failure - 1% failure simulation
  - test_process_payment_stores_in_memory - In-memory storage
  - test_process_payment_with_debit_card - Debit card method
  - test_process_payment_with_paypal - PayPal method
  - test_process_payment_idempotency - Idempotency key handling

- **TestGetPayment** (3 tests)
  - test_get_payment_found - Payment retrieval by ID
  - test_get_payment_not_found - 404 for missing payment
  - test_get_payment_invalid_uuid - UUID validation

- **TestPaymentFailures** (1 test)
  - test_failed_payment_stored - Failed payments stored for audit

- **TestPaymentValidation** (3 tests)
  - test_process_payment_invalid_amount - Negative amount validation
  - test_process_payment_missing_required_fields - Required fields
  - test_process_payment_invalid_payment_method - Enum validation

**Dependencies**: pytest, FastAPI TestClient, httpx
**Fixtures**: client, clear_payments

#### `/tests/unit/payment-service/test_payment_logic.py`
**Purpose**: Tests payment failure simulation algorithm
**Test Count**: 18 tests across 2 test classes
**Test Classes**:
- **TestFailureProbability** (10 tests)
  - test_failure_probability_is_deterministic - Same ID = same result
  - test_failure_probability_different_ids - Different IDs vary
  - test_failure_probability_distribution - 1% failure rate (10k samples)
  - test_failure_probability_uses_sha256 - SHA256 verification
  - test_failure_probability_specific_failing_ids - Consistent failures
  - test_failure_probability_specific_succeeding_ids - Consistent successes
  - test_failure_probability_empty_string - Empty order ID
  - test_failure_probability_special_characters - Special chars
  - test_failure_probability_long_order_id - Very long IDs
  - test_failure_probability_case_sensitivity - Case-sensitive hashing

- **TestPaymentGatewaySimulation** (3 tests)
  - test_gateway_simulation_reproducibility - Reproducible outcomes
  - test_gateway_simulation_variety - Both success and failure
  - test_gateway_failure_rate_consistency - Consistent rate across batches

**Dependencies**: pytest, hashlib
**Test Data**: 10,000+ order IDs for statistical validation

---

### Rollback Webhook Service (Python/pytest)

#### `/tests/unit/rollback-webhook/test_main.py`
**Purpose**: Tests webhook API endpoints
**Test Count**: 12+ tests
**Key Areas**:
- Root endpoint with service information
- Health check (with/without Docker)
- Readiness check (dependency validation)
- Status endpoint (rollback history)
- Rollback trigger endpoint
- Exception handling

**Dependencies**: pytest, FastAPI TestClient

#### `/tests/unit/rollback-webhook/test_rollback.py`
**Purpose**: Tests rollback execution logic
**Test Count**: 8+ tests
**Key Areas**:
- RollbackExecutor initialization
- Environment validation
- Current version retrieval
- Service version updates
- Service restart (docker compose v1 and v2)
- Complete rollback flow
- Environment variable name generation

**Dependencies**: pytest, unittest.mock

---

## Test Configuration Files

### `/tests/unit/pytest.ini`
**Purpose**: pytest configuration for all Python tests
**Key Settings**:
- Test discovery patterns
- Markers: inventory, payment, webhook, slow, integration
- Minimum Python version: 3.11
- Console output style
- Coverage configuration

### `/services/order-service/pom.xml`
**Purpose**: Maven configuration including test dependencies
**Test Dependencies**:
- spring-boot-starter-test
- mockito-core
- junit-jupiter
- JaCoCo (coverage)

---

## Test Runner Scripts

### `/tests/run-tests.sh`
**Purpose**: Main test runner for all services
**Features**:
- Runs Java and Python tests
- Supports --java-only, --python-only flags
- Coverage report generation
- Verbose output mode
- Colored output for readability
- Overall success/failure summary

**Usage**:
```bash
./run-tests.sh                 # Run all tests
./run-tests.sh --java-only     # Java only
./run-tests.sh --python-only   # Python only
./run-tests.sh --coverage      # With coverage
./run-tests.sh --verbose       # Verbose output
```

---

## Test Statistics

| Service | Language | Framework | Test Files | Test Count | Lines of Code |
|---------|----------|-----------|------------|------------|---------------|
| Order Service | Java | JUnit 5 | 2 | 17 | ~500 |
| Inventory Service | Python | pytest | 2 | 33 | ~600 |
| Payment Service | Python | pytest | 2 | 34 | ~550 |
| Rollback Webhook | Python | pytest | 2 | 20+ | ~450 |
| **Total** | - | - | **8** | **104+** | **~2,100** |

---

## Test Coverage by Category

### Health Endpoints
- ✓ Order Service: /api/orders/health, /api/orders/ready
- ✓ Inventory Service: /health, /ready
- ✓ Payment Service: /health, /ready
- ✓ Rollback Webhook: /health, /ready

### Business Logic
- ✓ Order creation and retrieval
- ✓ Stock availability checking
- ✓ Inventory reservation (atomic)
- ✓ Payment processing (success/failure)
- ✓ Rollback execution

### Error Handling
- ✓ Invalid input validation
- ✓ Missing required fields
- ✓ Non-existent resource handling
- ✓ Insufficient stock scenarios
- ✓ Payment failures

### Edge Cases
- ✓ Empty order items
- ✓ Zero quantities
- ✓ Case sensitivity
- ✓ Special characters
- ✓ Very long inputs
- ✓ Concurrent access (thread safety)

---

## Mock Objects and Fixtures

### Java (Mockito)
- OrderService
- InventoryClient
- PaymentClient
- Tracer, Span, SpanBuilder, Scope (OpenTelemetry)

### Python (pytest fixtures)
- client (TestClient)
- reset_inventory_state
- clear_payments
- reset_state

---

## Quick Commands

### Run All Tests
```bash
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests
./run-tests.sh
```

### Run Individual Services
```bash
# Java
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/services/order-service
mvn test

# Python
cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/tests/unit
pytest inventory-service/
pytest payment-service/
pytest rollback-webhook/
```

### Generate Coverage Reports
```bash
# Java
cd services/order-service && mvn test jacoco:report

# Python
cd tests/unit && pytest --cov=inventory --cov=payment --cov=webhook --cov-report=html
```

---

## Documentation Files

1. **UNIT_TESTS_OVERVIEW.md** - Comprehensive test documentation
2. **tests/QUICKSTART.md** - Quick start guide for running tests
3. **tests/TEST_INVENTORY.md** - This file
4. **tests/unit/README.md** - Python test documentation
5. **tests/TEST_SUMMARY.md** - Test execution summary

---

## Workshop Context

These tests serve the "From Commit to Culprit" workshop by:

1. **Validating Service Functionality**: Ensure all services work correctly
2. **Testing the Bug**: Verify v1.1-bad has the 2-second delay bug
3. **Demonstrating Best Practices**: Show proper microservices testing
4. **Enabling Safe Changes**: Allow confident refactoring
5. **Supporting CI/CD**: Ready for continuous integration pipelines

All tests are production-ready and follow industry best practices for microservices testing.

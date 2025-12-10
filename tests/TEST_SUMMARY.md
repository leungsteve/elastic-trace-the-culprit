# Test Summary - From Commit to Culprit Workshop

This document provides an overview of all unit tests created for the workshop services.

## Test Coverage Overview

| Service | Test Files | Test Classes | Approximate Test Count | Language/Framework |
|---------|------------|--------------|----------------------|-------------------|
| Order Service | 2 | 2 | 18 | Java/JUnit 5 |
| Inventory Service | 2 | 9 | 35 | Python/pytest |
| Payment Service | 2 | 6 | 25 | Python/pytest |
| Rollback Webhook | 2 | 8 | 30 | Python/pytest |
| **Total** | **8** | **25** | **~108** | - |

## Test Files Structure

```
tests/
├── unit/
│   ├── README.md                           # Test documentation
│   ├── pytest.ini                          # pytest configuration
│   │
│   ├── order-service/                      # Java/JUnit tests
│   │   ├── OrderControllerTest.java        # Controller endpoint tests
│   │   └── OrderServiceTest.java           # Business logic tests
│   │
│   ├── inventory-service/                  # Python/pytest tests
│   │   ├── __init__.py
│   │   ├── test_main.py                    # FastAPI endpoint tests
│   │   └── test_data.py                    # Data operations tests
│   │
│   ├── payment-service/                    # Python/pytest tests
│   │   ├── __init__.py
│   │   ├── test_main.py                    # FastAPI endpoint tests
│   │   └── test_payment_logic.py           # Payment logic tests
│   │
│   └── rollback-webhook/                   # Python/pytest tests
│       ├── __init__.py
│       ├── test_main.py                    # FastAPI endpoint tests
│       └── test_rollback.py                # Rollback execution tests
│
└── TEST_SUMMARY.md                         # This file

Note: Java tests are also copied to services/order-service/src/test/java/
for Maven integration.
```

## Order Service Tests (Java/JUnit 5)

### OrderControllerTest.java

Tests REST API controller endpoints:

1. **testCreateOrder_Success** - Verify successful order creation returns 201 CREATED
2. **testCreateOrder_Failure** - Verify failed orders return 400 BAD_REQUEST
3. **testCreateOrder_WithBugEnabled** - Test v1.1-bad bug introduces delay
4. **testGetOrder_Found** - Verify order retrieval by ID returns 200 OK
5. **testGetOrder_NotFound** - Verify missing order returns 404 NOT_FOUND
6. **testHealthCheck** - Verify /health endpoint returns UP status
7. **testReadinessCheck** - Verify /ready endpoint returns ready status

**Key Testing Patterns:**
- Uses Mockito for mocking OrderService and Tracer
- Tests both success and failure HTTP responses
- Validates response status codes and body content
- Tests the workshop bug behavior (2-second delay in v1.1-bad)

### OrderServiceTest.java

Tests business logic and service layer:

1. **testCreateOrder_Success** - Full order creation with mocked dependencies
2. **testCreateOrder_InventoryUnavailable** - Order fails when inventory unavailable
3. **testCreateOrder_PaymentDeclined** - Order fails when payment declined
4. **testCreateOrder_CalculatesTotalCorrectly** - Verify price calculation logic
5. **testCreateOrder_ExtractsProductIdsCorrectly** - Verify product ID extraction
6. **testGetOrder_Found** - Verify order retrieval from in-memory store
7. **testGetOrder_NotFound** - Verify handling of non-existent orders
8. **testCreateOrder_StoresOrderInMemory** - Verify in-memory storage works
9. **testCreateOrder_HandlesEmptyItemsList** - Edge case: empty order items
10. Additional helper tests for order creation flow

**Key Testing Patterns:**
- Mocks InventoryClient and PaymentClient
- Tests order processing workflow
- Validates failure scenarios (inventory, payment)
- Tests in-memory storage behavior

**Dependencies:**
- JUnit 5 (Jupiter)
- Mockito
- Spring Boot Test
- AssertJ (via Spring Boot Test)

## Inventory Service Tests (Python/pytest)

### test_main.py

Tests FastAPI endpoints:

**TestHealthEndpoints:**
1. **test_health_check** - Verify health endpoint returns healthy status
2. **test_readiness_check** - Verify readiness with all checks passing

**TestStockCheck:**
3. **test_check_stock_available** - Check stock for available items
4. **test_check_stock_insufficient** - Check when quantity exceeds stock
5. **test_check_stock_item_not_found** - Handle non-existent items
6. **test_check_stock_missing_item_id** - Validation error for missing item_id
7. **test_check_stock_mixed_availability** - Mixed available/unavailable items

**TestInventoryReservation:**
8. **test_reserve_items_success** - Successful reservation deducts stock
9. **test_reserve_items_insufficient_stock** - Reservation fails gracefully
10. **test_reserve_items_no_items** - Validation error for empty items list
11. **test_reserve_items_atomic_operation** - All-or-nothing reservation behavior

**TestInventorySummary:**
12. **test_get_inventory_summary** - Verify summary calculations
13. **test_inventory_summary_after_reservation** - Summary reflects changes

### test_data.py

Tests data layer operations:

**TestGetItem:**
1. **test_get_existing_item** - Retrieve existing inventory item
2. **test_get_all_initial_items** - Verify initial inventory state
3. **test_get_non_existent_item** - Handle missing items
4. **test_get_item_case_sensitive** - Verify case-sensitive IDs

**TestCheckAvailability:**
5. **test_check_availability_sufficient_stock** - Stock is sufficient
6. **test_check_availability_exact_stock** - Requested equals available
7. **test_check_availability_insufficient_stock** - Not enough stock
8. **test_check_availability_zero_quantity** - Edge case: zero quantity
9. **test_check_availability_non_existent_item** - Missing item handling

**TestReserveItems:**
10. **test_reserve_items_success** - Successful multi-item reservation
11. **test_reserve_items_deducts_stock** - Verify stock deduction
12. **test_reserve_items_insufficient_stock** - Insufficient stock failure
13. **test_reserve_items_atomic_operation** - All-or-nothing behavior
14. **test_reserve_items_missing_item_id** - Validation errors
15. **test_reserve_items_non_existent_item** - Missing item handling
16. **test_reserve_items_multiple_success** - Sequential reservations
17. **test_reserve_items_thread_safety** - Thread locking verification

**TestGetInventorySummary:**
18. **test_get_inventory_summary_initial_state** - Initial summary
19. **test_get_inventory_summary_calculates_value_correctly** - Value calculations
20. **test_get_inventory_summary_after_reservation** - Post-reservation state

**TestResetInventory:**
21. **test_reset_inventory_restores_initial_state** - Reset functionality
22. **test_reset_inventory_clears_reservations** - Clear reservations
23. **test_reset_inventory_restores_all_items** - Complete reset

**Dependencies:**
- pytest
- pytest-asyncio
- httpx (for TestClient)
- FastAPI test client

## Payment Service Tests (Python/pytest)

### test_main.py

Tests FastAPI endpoints:

**TestHealthEndpoints:**
1. **test_health_check** - Health endpoint verification
2. **test_readiness_check** - Readiness endpoint verification

**TestProcessPayment:**
3. **test_process_payment_success** - Successful payment processing
4. **test_process_payment_deterministic_failure** - Find deterministic failures
5. **test_process_payment_stores_in_memory** - Verify in-memory storage
6. **test_process_payment_with_debit_card** - Debit card method
7. **test_process_payment_with_paypal** - PayPal method
8. **test_process_payment_idempotency** - Idempotent payment handling

**TestGetPayment:**
9. **test_get_payment_found** - Retrieve existing payment
10. **test_get_payment_not_found** - Handle missing payment
11. **test_get_payment_invalid_uuid** - Invalid UUID format

**TestPaymentFailures:**
12. **test_failed_payment_stored** - Failed payments are stored

**TestPaymentValidation:**
13. **test_process_payment_invalid_amount** - Negative amount validation
14. **test_process_payment_missing_required_fields** - Required fields validation
15. **test_process_payment_invalid_payment_method** - Invalid enum value

### test_payment_logic.py

Tests payment business logic:

**TestFailureProbability:**
1. **test_failure_probability_is_deterministic** - Same input, same output
2. **test_failure_probability_different_ids** - Different inputs vary
3. **test_failure_probability_distribution** - Verify 1% failure rate
4. **test_failure_probability_uses_sha256** - SHA256 hashing verification
5. **test_failure_probability_specific_failing_ids** - Find failing IDs
6. **test_failure_probability_specific_succeeding_ids** - Find succeeding IDs
7. **test_failure_probability_empty_string** - Edge case: empty order ID
8. **test_failure_probability_special_characters** - Special characters handling
9. **test_failure_probability_long_order_id** - Long order ID handling
10. **test_failure_probability_case_sensitivity** - Case sensitivity verification

**TestPaymentGatewaySimulation:**
11. **test_gateway_simulation_reproducibility** - Reproducible outcomes
12. **test_gateway_simulation_variety** - Variety of outcomes
13. **test_gateway_failure_rate_consistency** - Consistent failure rate

**Dependencies:**
- pytest
- pytest-asyncio
- httpx
- FastAPI test client
- hashlib (standard library)

## Rollback Webhook Tests (Python/pytest)

### test_main.py

Tests FastAPI endpoints:

**TestRootEndpoint:**
1. **test_root_endpoint** - Root endpoint with service info

**TestHealthEndpoints:**
2. **test_health_check_without_docker** - Health check when Docker unavailable
3. **test_health_check_with_docker** - Health check with Docker available
4. **test_health_check_docker_exception** - Exception handling
5. **test_readiness_check_all_ready** - All dependencies ready
6. **test_readiness_check_docker_not_ready** - Docker not ready
7. **test_readiness_check_files_not_ready** - Missing files

**TestStatusEndpoint:**
8. **test_status_no_rollbacks** - Status with no rollback history
9. **test_status_with_rollback_history** - Status after rollbacks

**TestRollbackEndpoint:**
10. **test_trigger_rollback_success** - Successful rollback trigger
11. **test_trigger_rollback_failure** - Failed rollback handling
12. **test_trigger_rollback_invalid_service** - Invalid service validation
13. **test_trigger_rollback_missing_fields** - Required fields validation
14. **test_trigger_rollback_for_inventory_service** - Inventory service rollback
15. **test_trigger_rollback_for_payment_service** - Payment service rollback

**TestExceptionHandling:**
16. **test_unhandled_exception** - Global exception handler

### test_rollback.py

Tests rollback execution logic:

**TestRollbackExecutorInit:**
1. **test_init_sets_paths** - Initialization with custom paths
2. **test_init_default_values** - Default initialization

**TestValidateEnvironment:**
3. **test_validate_environment_all_valid** - All checks pass
4. **test_validate_environment_env_file_missing** - Missing .env file
5. **test_validate_environment_compose_file_missing** - Missing compose file
6. **test_validate_environment_docker_not_available** - Docker unavailable
7. **test_validate_environment_docker_exception** - Docker check exception

**TestGetCurrentVersion:**
8. **test_get_current_version_found** - Version found in .env
9. **test_get_current_version_with_whitespace** - Handle whitespace
10. **test_get_current_version_not_found** - Version not found
11. **test_get_current_version_file_error** - File read error
12. **test_get_current_version_inventory_service** - Inventory service version
13. **test_get_current_version_payment_service** - Payment service version

**TestUpdateServiceVersion:**
14. **test_update_service_version_success** - Successful update
15. **test_update_service_version_appends_if_not_found** - Append new entry
16. **test_update_service_version_file_error** - File write error

**TestRestartService:**
17. **test_restart_service_success_with_docker_compose_v2** - Docker compose v2
18. **test_restart_service_success_with_docker_compose_v1** - Docker-compose v1
19. **test_restart_service_failure** - Restart failure handling
20. **test_restart_service_timeout** - Timeout handling
21. **test_restart_service_exception** - Exception handling

**TestExecuteRollback:**
22. **test_execute_rollback_success** - Complete successful rollback
23. **test_execute_rollback_validation_fails** - Validation failure
24. **test_execute_rollback_update_fails** - Update failure
25. **test_execute_rollback_restart_fails** - Restart failure

**TestGetEnvVarName:**
26. **test_get_env_var_name_order_service** - Order service env var
27. **test_get_env_var_name_inventory_service** - Inventory service env var
28. **test_get_env_var_name_payment_service** - Payment service env var

**Dependencies:**
- pytest
- pytest-asyncio
- httpx
- unittest.mock
- subprocess (standard library)
- pathlib (standard library)

## Running All Tests

### Quick Start

```bash
# Java tests (Order Service)
cd services/order-service
mvn test

# Python tests (all services)
cd tests/unit
pytest
```

### With Coverage

```bash
# Java tests with coverage
cd services/order-service
mvn test jacoco:report

# Python tests with coverage
cd tests/unit
pytest --cov=inventory --cov=payment --cov=webhook --cov-report=html
```

### Selective Test Execution

```bash
# Run only inventory service tests
pytest inventory-service/

# Run only a specific test file
pytest payment-service/test_payment_logic.py

# Run only a specific test class
pytest rollback-webhook/test_rollback.py::TestValidateEnvironment

# Run only a specific test method
pytest inventory-service/test_data.py::TestReserveItems::test_reserve_items_atomic_operation
```

## Test Design Principles

All tests follow these principles:

1. **Independence**: Each test can run in isolation
2. **Repeatability**: Tests produce consistent results
3. **Fast Execution**: Unit tests run in milliseconds
4. **Clear Intent**: Test names describe what is being tested
5. **Arrange-Act-Assert**: Clear test structure
6. **Mock External Dependencies**: No real HTTP calls or Docker operations
7. **Test Both Paths**: Success and failure scenarios

## Workshop Integration

These tests support the workshop by:

1. **Validating Service Behavior**: Ensure services work correctly before deployment
2. **Preventing Regressions**: Catch bugs introduced during development
3. **Documenting Behavior**: Tests serve as executable documentation
4. **Teaching Best Practices**: Demonstrate testing patterns for microservices
5. **Enabling Refactoring**: Safe code changes with test coverage

## Future Enhancements

Potential test improvements:

1. **Integration Tests**: Test service-to-service communication
2. **Telemetry Tests**: Validate trace propagation and log correlation
3. **Performance Tests**: Measure response times under load
4. **Contract Tests**: Verify API contracts between services
5. **E2E Tests**: Complete workshop scenario validation

## Continuous Integration

These tests are designed for CI/CD pipelines:

```yaml
# Example CI configuration
test:
  script:
    # Java tests
    - cd services/order-service && mvn test

    # Python tests
    - cd tests/unit && pytest --cov --cov-report=xml

  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Test Maintenance

To maintain test quality:

1. **Update tests with code changes**: Keep tests in sync with implementation
2. **Add tests for new features**: Maintain coverage as services evolve
3. **Remove obsolete tests**: Delete tests for removed functionality
4. **Refactor test code**: Apply same quality standards as production code
5. **Review test failures**: Investigate and fix failing tests promptly

## Support

For questions about tests:

1. Check the test README: `tests/unit/README.md`
2. Review test code comments and docstrings
3. Run tests with verbose output: `pytest -v` or `mvn test -X`
4. Check workshop documentation in `docs/` directory

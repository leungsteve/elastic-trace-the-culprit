# Integration Test Coverage

Complete overview of integration tests for service-to-service communication.

## Statistics

- **Test Classes:** 5
- **Test Functions:** 18
- **Test Files:** 1
- **Configuration Files:** 1 (pytest.ini)
- **Documentation Files:** 3 (README.md, QUICK_START.md, TEST_COVERAGE.md)

## Test Classes

### 1. TestInventoryServiceIntegration (4 tests)

Tests for order service integration with inventory service.

| Test | Description | Coverage |
|------|-------------|----------|
| `test_inventory_service_health_check` | Verify inventory service is accessible | Health endpoint |
| `test_inventory_check_available_items` | Check stock for available products | Stock availability, correct response format |
| `test_inventory_check_unavailable_items` | Check stock for non-existent products | Error handling for missing products |
| `test_order_service_calls_inventory_service` | End-to-end order creation with inventory check | Order → Inventory communication |

### 2. TestPaymentServiceIntegration (3 tests)

Tests for order service integration with payment service.

| Test | Description | Coverage |
|------|-------------|----------|
| `test_payment_service_health_check` | Verify payment service is accessible | Health endpoint |
| `test_payment_processing_success` | Process payment directly | Payment processing logic |
| `test_order_service_calls_payment_service` | End-to-end order creation with payment | Order → Payment communication |

### 3. TestFullOrderFlow (4 tests)

Tests for complete order flow across all services.

| Test | Description | Coverage |
|------|-------------|----------|
| `test_successful_order_flow` | Happy path: order → inventory → payment → confirm | Full successful flow |
| `test_order_flow_with_unavailable_inventory` | Order fails when inventory unavailable | Inventory failure handling |
| `test_order_retrieval` | Retrieve order by ID after creation | Order persistence and retrieval |
| `test_order_not_found` | Request non-existent order returns 404 | Not found error handling |

### 4. TestErrorHandling (5 tests)

Tests for error handling when downstream services fail.

| Test | Description | Coverage |
|------|-------------|----------|
| `test_invalid_order_request` | Order creation with missing required fields | Input validation |
| `test_empty_order_items` | Order with empty items list | Empty data handling |
| `test_inventory_service_invalid_request` | Inventory check with invalid payload | Inventory validation |
| `test_payment_service_invalid_request` | Payment processing with invalid payload | Payment validation |
| `test_concurrent_order_creation` | Multiple simultaneous orders | Concurrency, thread safety |

### 5. TestServiceHealthAndReadiness (2 tests)

Tests for service health and readiness endpoints.

| Test | Description | Coverage |
|------|-------------|----------|
| `test_all_services_healthy` | All services report healthy status | Health checks across all services |
| `test_all_services_ready` | All services report ready status | Readiness checks across all services |

## Coverage Matrix

### Service Communication Paths

| Source Service | Target Service | Endpoint | Tests |
|----------------|----------------|----------|-------|
| Order | Inventory | `/api/inventory/check` | 3 tests |
| Order | Payment | `/api/payments` | 3 tests |
| Client | Order | `/api/orders` (POST) | 10 tests |
| Client | Order | `/api/orders/{id}` (GET) | 2 tests |
| Client | Inventory | `/api/inventory/check` | 3 tests |
| Client | Payment | `/api/payments` | 2 tests |

### HTTP Status Codes Tested

| Status Code | Service | Scenario | Tests |
|-------------|---------|----------|-------|
| 200 OK | All | Successful GET requests | 6 tests |
| 201 Created | Order, Payment | Successful POST requests | 3 tests |
| 400 Bad Request | All | Invalid request payloads | 4 tests |
| 402 Payment Required | Payment | Payment declined | 1 test |
| 404 Not Found | Order | Order not found | 1 test |
| 422 Unprocessable Entity | Payment | Invalid payment data | 1 test |

### Error Scenarios Covered

| Category | Scenario | Expected Behavior | Tests |
|----------|----------|-------------------|-------|
| Inventory | Product not found | Order fails, clear error message | 1 test |
| Inventory | Invalid request | 400 Bad Request | 1 test |
| Payment | Payment declined | 402 Payment Required | 1 test |
| Payment | Invalid request | 400/422 error | 1 test |
| Order | Missing fields | 400 Bad Request | 1 test |
| Order | Empty items | 400/500 error | 1 test |
| Order | Order not found | 404 Not Found | 1 test |
| Concurrency | Multiple orders | All processed correctly | 1 test |

## Data Flow Testing

### Successful Order Flow

```
Client
  │
  └──> Order Service (POST /api/orders)
         │
         ├──> Inventory Service (POST /api/inventory/check)
         │    │
         │    └──> Returns: { "available": true, "items": [...] }
         │
         ├──> Payment Service (POST /api/payments)
         │    │
         │    └──> Returns: { "status": "completed", "transaction_id": "..." }
         │
         └──> Returns: { "status": "CONFIRMED", "orderId": "...", "totalAmount": 1049.97 }
```

**Tested by:** `test_successful_order_flow`

### Failed Order Flow (Inventory Unavailable)

```
Client
  │
  └──> Order Service (POST /api/orders)
         │
         ├──> Inventory Service (POST /api/inventory/check)
         │    │
         │    └──> Returns: { "available": false, "items": [...] }
         │
         └──> Returns: { "status": "FAILED", "message": "Inventory not available" }
              (Payment service is NOT called)
```

**Tested by:** `test_order_flow_with_unavailable_inventory`

## Test Fixtures

### Shared Fixtures (conftest.py)

| Fixture | Purpose | Used By |
|---------|---------|---------|
| `http_client` | Async HTTP client | All tests |
| `order_service_url` | Order service URL | 12 tests |
| `inventory_service_url` | Inventory service URL | 6 tests |
| `payment_service_url` | Payment service URL | 4 tests |
| `ensure_services_running` | Health check before tests | All tests |
| `sample_order_request` | Valid order payload | 8 tests |
| `sample_inventory_check_request` | Valid inventory check payload | 1 test |
| `sample_payment_request` | Valid payment payload | 1 test |
| `unavailable_product_order` | Order with non-existent product | 1 test |

## Execution Time Estimates

| Test Class | Tests | Est. Time | Notes |
|------------|-------|-----------|-------|
| TestInventoryServiceIntegration | 4 | ~2-3s | Fast HTTP calls |
| TestPaymentServiceIntegration | 3 | ~2-3s | Fast HTTP calls |
| TestFullOrderFlow | 4 | ~4-5s | Full flow takes longer |
| TestErrorHandling | 5 | ~3-4s | Concurrent test is slower |
| TestServiceHealthAndReadiness | 2 | ~1s | Simple health checks |
| **Total** | **18** | **~12-16s** | Sequential execution |

With parallel execution (`pytest -n auto`): ~5-8s

## Integration Points Tested

### 1. HTTP Communication
- ✓ Request serialization (JSON)
- ✓ Response deserialization (JSON)
- ✓ HTTP headers (Content-Type)
- ✓ HTTP methods (GET, POST)
- ✓ Status codes
- ✓ Error responses

### 2. Data Validation
- ✓ Required field validation
- ✓ Data type validation
- ✓ Empty data handling
- ✓ Invalid data handling

### 3. Business Logic
- ✓ Order calculation (totals)
- ✓ Inventory availability checking
- ✓ Payment processing
- ✓ Order state management

### 4. Error Handling
- ✓ Downstream service failures
- ✓ Invalid requests
- ✓ Not found scenarios
- ✓ Payment failures

### 5. Concurrent Operations
- ✓ Multiple simultaneous requests
- ✓ Thread safety
- ✓ Independent order processing

## Coverage Gaps and Future Tests

### Currently Not Tested
1. Network timeout scenarios
2. Service restart/recovery
3. Partial failures (inventory succeeds, payment fails)
4. Extremely large orders (stress testing)
5. Database transaction rollbacks
6. Rate limiting
7. Authentication/authorization

### Recommended Additions
1. Load testing (1000+ concurrent orders)
2. Chaos engineering (service failures)
3. Performance regression tests
4. Contract testing
5. API versioning tests

## Dependencies

### Test Dependencies (requirements.txt)
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- httpx >= 0.24.0
- pytest-cov >= 4.1.0

### Service Dependencies
- Order Service (Java Spring Boot)
- Inventory Service (Python FastAPI)
- Payment Service (Python FastAPI)

## Related Tests

| Test Type | Location | Focus |
|-----------|----------|-------|
| Unit Tests | `tests/unit/` | Individual service logic |
| Telemetry Tests | `tests/telemetry/` | Trace propagation, log correlation |
| Integration Tests | `tests/integration/` | Service-to-service communication |
| E2E Tests | `tests/e2e/` | Full workshop scenarios |

## Success Metrics

Integration tests are considered successful when:

1. ✓ All 18 tests pass
2. ✓ Tests complete in < 20 seconds
3. ✓ No flaky tests (consistent results)
4. ✓ All services health checks pass
5. ✓ Error scenarios handled correctly
6. ✓ Concurrent tests pass without race conditions

## Continuous Integration

These tests are designed to run in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Start services
  run: docker-compose up -d

- name: Wait for services
  run: ./scripts/health-check.sh

- name: Run integration tests
  run: ./tests/run_integration_tests.sh

- name: Upload coverage
  run: pytest --cov --cov-report=xml
```

## Maintenance

### When to Update Tests

1. **New Service Added:** Create new test class
2. **New Endpoint Added:** Add test for that endpoint
3. **Data Model Changed:** Update fixtures and assertions
4. **Error Handling Changed:** Add/update error tests
5. **Business Logic Changed:** Update flow tests

### Test Review Checklist

- [ ] All tests pass consistently
- [ ] No hardcoded values (use fixtures)
- [ ] Clear test names describe what's tested
- [ ] Comprehensive docstrings
- [ ] Error scenarios covered
- [ ] No test interdependencies
- [ ] Tests skip gracefully when services unavailable

## Documentation

- **Quick Start:** [QUICK_START.md](./QUICK_START.md)
- **Detailed Guide:** [README.md](./README.md)
- **Test Coverage:** This file
- **Workshop Docs:** [../../docs/](../../docs/)

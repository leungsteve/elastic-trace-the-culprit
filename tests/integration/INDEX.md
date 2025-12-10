# Integration Tests - Complete Index

Complete guide to the integration test suite for "From Commit to Culprit" workshop.

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [QUICK_START.md](./QUICK_START.md) | Fast reference, common commands | Developers running tests |
| [README.md](./README.md) | Comprehensive documentation | New contributors, detailed info |
| [TEST_COVERAGE.md](./TEST_COVERAGE.md) | Test coverage breakdown | QA, test reviewers |
| [INDEX.md](./INDEX.md) | This file - navigation hub | Everyone |

## Files in This Directory

### Test Files
```
test_service_integration.py    (18 tests, 5 test classes)
  ├─ TestInventoryServiceIntegration     (4 tests)
  ├─ TestPaymentServiceIntegration       (3 tests)
  ├─ TestFullOrderFlow                   (4 tests)
  ├─ TestErrorHandling                   (5 tests)
  └─ TestServiceHealthAndReadiness       (2 tests)
```

### Configuration
```
conftest.py           Shared fixtures and test setup
pytest.ini            Pytest configuration
```

### Documentation
```
README.md             Complete test documentation
QUICK_START.md        Quick reference guide
TEST_COVERAGE.md      Detailed coverage breakdown
INDEX.md              This file
```

### Scripts
```
../run_integration_tests.sh    Test runner script (in parent directory)
```

## What These Tests Do

### Core Purpose
Verify that microservices communicate correctly with each other through HTTP APIs.

### Key Areas
1. **Service Communication** - HTTP requests/responses work correctly
2. **Full Order Flow** - Complete order lifecycle functions properly
3. **Error Handling** - Services handle failures gracefully
4. **Data Validation** - Input validation works across services
5. **Concurrent Operations** - Services handle multiple requests

## Test Execution Modes

### 1. Quick Check (Recommended)
```bash
./tests/run_integration_tests.sh
```
Checks services are running, then executes all tests.

### 2. Direct Pytest
```bash
cd tests/integration
pytest -v
```
Standard pytest execution.

### 3. Specific Test Class
```bash
pytest -v -k "TestFullOrderFlow"
```
Run only tests in a specific class.

### 4. Single Test
```bash
pytest -v test_service_integration.py::TestFullOrderFlow::test_successful_order_flow
```
Run one specific test.

### 5. With Coverage
```bash
pytest -v --cov=. --cov-report=html
```
Generate coverage report.

## Test Dependencies

### Services Required
- Order Service (port 8088)
- Inventory Service (port 8081)
- Payment Service (port 8082)

### Python Packages
- pytest (test framework)
- pytest-asyncio (async support)
- httpx (HTTP client)
- pytest-cov (coverage reporting)

## When to Run These Tests

### During Development
- After modifying service APIs
- After changing request/response formats
- After adding new endpoints
- Before creating pull requests

### In CI/CD Pipeline
- On every commit to main branch
- Before deployment to staging
- As part of integration test suite

### During Debugging
- When service communication breaks
- When investigating HTTP errors
- When validating API contracts

## Common Use Cases

### 1. Verify Services are Working
```bash
# Quick health check
./tests/run_integration_tests.sh
```

### 2. Test New Feature
```bash
# Add new test to test_service_integration.py
# Run specific test
pytest -v -k "test_my_new_feature"
```

### 3. Debug Failing Test
```bash
# Run with verbose output
pytest -v -s test_service_integration.py::TestFullOrderFlow::test_successful_order_flow

# Check service logs
docker-compose logs order-service
```

### 4. Measure Coverage
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### 5. Performance Check
```bash
# Run tests multiple times
for i in {1..10}; do pytest -v; done
```

## Understanding Test Results

### All Tests Pass
```
======================== 18 passed in 12.43s ========================
```
All services communicating correctly.

### Tests Skipped
```
SKIPPED [1] Service not available: http://localhost:8088
```
Services not running. Start with `docker-compose up`.

### Tests Failed
```
FAILED test_service_integration.py::TestFullOrderFlow::test_successful_order_flow
```
Check service logs, verify endpoints, review error messages.

## Troubleshooting Guide

### Problem: Tests Skip with "Service not available"
**Solution:**
```bash
docker-compose -f infra/docker-compose.yml up -d
./scripts/health-check.sh
```

### Problem: Tests Fail with Connection Refused
**Solution:**
```bash
# Check if services are running
docker-compose ps

# Check if ports are accessible
curl http://localhost:8088/api/orders/health
```

### Problem: Tests Timeout
**Solution:**
```bash
# Increase timeout in conftest.py
async with httpx.AsyncClient(timeout=60.0) as client:
```

### Problem: Flaky Tests
**Solution:**
```bash
# Run multiple times to identify pattern
pytest -v --count=10
```

## Integration with Other Tests

```
tests/
├── unit/                    Unit tests (individual service logic)
├── integration/             Integration tests (this directory)
├── telemetry/              Telemetry tests (trace propagation)
└── e2e/                    End-to-end tests (full scenarios)
```

### Test Execution Order
1. Unit tests (fastest, no dependencies)
2. Integration tests (medium speed, requires services)
3. Telemetry tests (requires services + OTEL)
4. E2E tests (slowest, full environment)

## Code Quality Standards

### Test Quality Checklist
- [ ] Test names clearly describe what's being tested
- [ ] Each test has comprehensive docstring
- [ ] No hardcoded values (use fixtures)
- [ ] Tests are independent (no shared state)
- [ ] Error scenarios covered
- [ ] Assertions are specific and clear
- [ ] No sleeps or arbitrary waits

### Coverage Goals
- **Line Coverage:** > 80%
- **Branch Coverage:** > 70%
- **Integration Paths:** 100%

## Contributing

### Adding New Tests

1. **Identify Integration Point**
   - What service-to-service communication?
   - What HTTP endpoint?
   - What error scenarios?

2. **Choose Test Class**
   - Inventory integration → `TestInventoryServiceIntegration`
   - Payment integration → `TestPaymentServiceIntegration`
   - Full flow → `TestFullOrderFlow`
   - Error handling → `TestErrorHandling`
   - New category → Create new class

3. **Write Test**
   ```python
   @pytest.mark.asyncio
   async def test_my_new_feature(
       self,
       http_client: httpx.AsyncClient,
       order_service_url: str,
       ensure_services_running,
   ):
       """
       Test description explaining what this verifies.

       Flow description if applicable.
       """
       response = await http_client.post(
           f"{order_service_url}/api/new-endpoint",
           json={"data": "value"}
       )

       assert response.status_code == 200
       data = response.json()
       assert data["expected_field"] == "expected_value"
   ```

4. **Run Test**
   ```bash
   pytest -v -k "test_my_new_feature"
   ```

5. **Update Documentation**
   - Add to TEST_COVERAGE.md
   - Update README.md if needed

### Code Review Checklist
- [ ] Test passes consistently (run 5 times)
- [ ] Test has clear docstring
- [ ] Test uses fixtures appropriately
- [ ] Test assertions are specific
- [ ] Test cleanup (if needed)
- [ ] Documentation updated

## Performance Benchmarks

### Expected Execution Times
- Individual test: 0.5-2 seconds
- Test class: 2-5 seconds
- Full suite: 12-16 seconds
- With coverage: 15-20 seconds

### Optimization Tips
1. Use parallel execution: `pytest -n auto`
2. Skip slow tests during dev: `pytest -m "not slow"`
3. Run only changed tests in CI
4. Cache service startup in CI

## References

### External Documentation
- [pytest documentation](https://docs.pytest.org/)
- [httpx documentation](https://www.python-httpx.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Spring Boot testing](https://spring.io/guides/gs/testing-web/)

### Workshop Documentation
- [Workshop Overview](../../README.md)
- [Service Architecture](../../docs/ARCHITECTURE.md)
- [API Documentation](../../docs/ENGINEERING.md)
- [Telemetry Tests](../telemetry/README.md)

## Support

### Getting Help
1. Check [QUICK_START.md](./QUICK_START.md) for common commands
2. Review [README.md](./README.md) for detailed info
3. Check service logs: `docker-compose logs <service-name>`
4. Review workshop documentation: [../../docs/](../../docs/)

### Reporting Issues
Include in bug reports:
- Test command used
- Full error output
- Service logs
- Docker compose status
- Environment (OS, Python version)

## Version History

- **v1.0** (2024-12) - Initial integration test suite
  - 18 tests across 5 test classes
  - Coverage for all service-to-service paths
  - Error handling scenarios
  - Concurrent operation tests

---

**Last Updated:** December 2024
**Maintainer:** NovaMart Platform Team
**Workshop:** From Commit to Culprit - Elastic Observability

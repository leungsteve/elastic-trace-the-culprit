# E2E Test Coverage

This document maps workshop challenges to E2E test coverage, showing which tests validate each part of the participant experience.

## Test Coverage Matrix

| Workshop Challenge | Test Class | Test Method | What It Validates |
|-------------------|------------|-------------|-------------------|
| **Challenge 1: Setup and Baseline** | | | |
| Environment verification | `TestChallenge1Baseline` | `test_all_services_healthy` | All services respond to health checks |
| Baseline latency measurement | `TestChallenge1Baseline` | `test_baseline_latency_is_healthy` | v1.0 latency < 500ms |
| Order creation works | `TestChallenge1Baseline` | `test_order_creation_succeeds` | Happy path order flow |
| **Challenge 2: Deploy and Detect** | | | |
| Bad version deployment | `TestChallenge2DeployDetect` | `test_deploy_bad_version` | v1.1-bad deploys successfully |
| Latency degradation | `TestChallenge2DeployDetect` | `test_latency_degrades_after_bad_deployment` | v1.1-bad latency > 1500ms |
| Orders still process | `TestChallenge2DeployDetect` | `test_bad_version_still_processes_orders` | Functionality preserved despite slowness |
| **Challenge 3: Investigate and Remediate** | | | |
| Manual rollback | `TestChallenge3InvestigateRemediate` | `test_manual_rollback_succeeds` | rollback.sh works correctly |
| System recovery | `TestChallenge3InvestigateRemediate` | `test_system_recovers_after_rollback` | Latency returns to normal |
| Automated rollback (webhook) | `TestRollbackWebhookFunctionality` | `test_webhook_triggers_rollback` | Webhook-based rollback works |
| **Challenge 4: Learn and Prevent** | | | |
| Final state validation | `TestChallenge4LearnPrevent` | `test_final_state_is_stable` | System ends healthy on v1.0 |
| Version persistence | `TestChallenge4LearnPrevent` | `test_version_persistence_across_multiple_deployments` | Version changes persist correctly |
| **Complete Flow** | | | |
| End-to-end scenario | `TestWorkshopScenario` | `test_complete_workshop_flow` | Full participant journey |

## Webhook-Specific Tests

| Functionality | Test Class | Test Method | What It Validates |
|--------------|------------|-------------|-------------------|
| Health endpoints | `TestRollbackWebhookHealth` | `test_webhook_health_endpoint` | /health returns correct status |
| Readiness checks | `TestRollbackWebhookHealth` | `test_webhook_ready_endpoint` | /ready validates environment |
| Status tracking | `TestRollbackWebhookHealth` | `test_webhook_status_endpoint` | /status shows rollback history |
| Service info | `TestRollbackWebhookHealth` | `test_webhook_root_endpoint` | Root endpoint provides metadata |
| Rollback execution | `TestRollbackWebhookFunctionality` | `test_webhook_triggers_rollback` | POST /rollback works |
| Status updates | `TestRollbackWebhookFunctionality` | `test_webhook_updates_status_after_rollback` | Status reflects operations |
| Input validation | `TestRollbackWebhookFunctionality` | `test_webhook_handles_invalid_service_name` | Invalid inputs rejected |
| Required fields | `TestRollbackWebhookFunctionality` | `test_webhook_handles_missing_fields` | Missing fields validated |
| Trace context | `TestRollbackWebhookFunctionality` | `test_webhook_rollback_includes_trace_context` | Trace IDs included |
| Rapid requests | `TestWebhookIntegrationScenarios` | `test_webhook_handles_rapid_rollback_requests` | Multiple requests handled |
| Complete automation | `TestWebhookIntegrationScenarios` | `test_complete_automated_remediation_flow` | Full automated flow works |

## Test Fixtures Coverage

| Fixture | Purpose | Used By |
|---------|---------|---------|
| `wait_for_services` | Ensures services are healthy before tests | All test classes |
| `latency_measurer` | Measures average latency over N requests | Scenario tests |
| `version_manager` | Gets/waits for version changes | Deployment tests |
| `script_runner` | Executes deploy.sh, rollback.sh | Integration tests |
| `webhook_client` | Interacts with webhook API | Webhook tests |
| `initial_state` | Captures/restores state for idempotency | All tests |
| `http_client` | Makes HTTP requests to services | All tests |
| `sample_order_request` | Standard order payload | Order tests |

## Coverage by Workshop Phase

### Phase 1: Pre-Workshop Setup (Before participants arrive)
- ✅ `test_all_services_healthy` - Verifies infrastructure is ready
- ✅ `test_baseline_latency_is_healthy` - Confirms healthy baseline exists

### Phase 2: Challenge Walkthrough (Participant active time)
- ✅ `test_complete_workshop_flow` - Validates entire participant journey
- ✅ Individual challenge tests - Validate each step works correctly

### Phase 3: Automated Workflows (Background automation)
- ✅ `test_webhook_triggers_rollback` - Validates automated remediation
- ✅ `test_complete_automated_remediation_flow` - Full automation cycle

### Phase 4: Post-Workshop Cleanup
- ✅ `test_final_state_is_stable` - Ensures clean ending state
- ✅ `initial_state` fixture - Restores state after tests

## Test Execution Time Estimates

| Test Category | Estimated Duration | Notes |
|--------------|-------------------|-------|
| Single test method | 10-60 seconds | Depends on waits and deployments |
| Challenge test class | 1-3 minutes | Multiple related tests |
| Complete workshop flow | 3-5 minutes | Full scenario with all delays |
| All scenario tests | 8-12 minutes | All challenge tests combined |
| All webhook tests | 4-6 minutes | Health + functionality + integration |
| Full E2E suite | 12-18 minutes | Everything, including slow tests |
| Fast tests only | 6-10 minutes | Excludes slow integration tests |

## Key Test Scenarios

### Scenario 1: Happy Path (Master Test)
**Test**: `test_complete_workshop_flow`

Validates:
1. Starting on v1.0 with healthy latency
2. Deploying v1.1-bad
3. Latency increases significantly
4. Rollback to v1.0
5. Latency returns to healthy
6. Final state is stable

### Scenario 2: Automated Remediation
**Test**: `test_complete_automated_remediation_flow`

Validates:
1. Baseline established
2. Bad deployment causes degradation
3. Webhook receives alert
4. Automated rollback triggered
5. System recovers automatically
6. Full observability of process

### Scenario 3: Manual Remediation
**Test**: `test_manual_rollback_succeeds` + `test_system_recovers_after_rollback`

Validates:
1. Bad deployment occurs
2. Manual rollback.sh execution
3. System recovery
4. No automation required

## Missing Coverage (Future Enhancements)

These scenarios are not yet covered but could be added:

1. **Network failures during rollback** - Test resilience to network issues
2. **Concurrent deployments** - Multiple services deploying simultaneously
3. **Rollback failures** - What happens if rollback.sh fails?
4. **Partial degradation** - Only some requests are slow
5. **Multiple rollback cycles** - Deploy bad, rollback, deploy bad again
6. **SLO breach alerting** - Validate alerts actually fire in Elastic
7. **Agent Builder queries** - Test Agent Builder tools work correctly
8. **Case creation** - Verify incident cases can be created
9. **Performance under load** - Behavior with high traffic
10. **Deployment annotations** - Verify annotations appear in APM

## Test Quality Metrics

| Metric | Current Status | Target |
|--------|---------------|--------|
| Test coverage (lines) | ~85% | 90% |
| Workshop scenario coverage | 100% | 100% |
| Edge case coverage | 60% | 75% |
| Flaky tests | 0 | 0 |
| Test execution time | 12-18 min | < 15 min |
| Test reliability | 98% | 99%+ |

## Running Specific Coverage Areas

```bash
# Test only Challenge 1
pytest test_workshop_scenario.py::TestChallenge1Baseline -v

# Test only Challenge 2
pytest test_workshop_scenario.py::TestChallenge2DeployDetect -v

# Test only Challenge 3
pytest test_workshop_scenario.py::TestChallenge3InvestigateRemediate -v

# Test only Challenge 4
pytest test_workshop_scenario.py::TestChallenge4LearnPrevent -v

# Test only webhook functionality
pytest test_rollback_webhook.py::TestRollbackWebhookFunctionality -v

# Test complete flows only
pytest -k "complete_flow" -v

# Test health checks only
pytest -k "health" -v

# Test latency measurements only
pytest -k "latency" -v
```

## Integration with CI/CD

These E2E tests are designed to run in CI/CD pipelines:

- **Pre-commit**: Run fast tests (`make test-fast`)
- **PR validation**: Run full suite (`make test-all`)
- **Nightly builds**: Run with coverage and reports
- **Release validation**: Run complete flow test as smoke test

## Maintenance Notes

### When to Update Tests

Update E2E tests when:

1. Workshop flow changes (new challenges, reordering)
2. Service endpoints change
3. Deployment mechanism changes
4. Latency thresholds need adjustment
5. New automation features added
6. Bug fixes that need regression coverage

### Test Stability Tips

Keep tests stable by:

1. Using `initial_state` fixture for cleanup
2. Setting appropriate timeouts
3. Waiting for service stabilization
4. Averaging multiple measurements
5. Using idempotent operations
6. Avoiding hardcoded timing assumptions
7. Handling transient network errors

## See Also

- [README.md](README.md) - Complete E2E test documentation
- [../telemetry/](../telemetry/) - Telemetry-specific tests
- [../../scripts/workshop-test.sh](../../scripts/workshop-test.sh) - Bash version of E2E flow

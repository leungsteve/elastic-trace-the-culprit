# Workshop Testing Findings and Recommendations

## Document Purpose

This document captures findings from creating and validating the workshop test automation, including potential issues, recommendations, and areas requiring manual verification.

## Test Script Overview

**Location:** `/scripts/workshop-test.sh`

**Purpose:** Automated end-to-end testing of the complete workshop participant journey

**Coverage:**
- All 4 workshop challenges
- 13 distinct test cases
- Health checks for all 5 services
- Latency measurements at 3 key points
- Both automated and manual rollback paths

## Test Coverage Analysis

### ✅ Fully Automated Tests

These tests run completely automatically:

1. **Service Health Checks**
   - Order Service (port 8088)
   - Inventory Service (port 8081)
   - Payment Service (port 8082)
   - Rollback Webhook (port 9000)
   - OTEL Collector (port 13133)

2. **Latency Measurements**
   - Baseline (<500ms expected)
   - After v1.1-bad deployment (>1500ms expected)
   - After rollback (<500ms expected)

3. **Deployment Operations**
   - Version update to v1.1-bad
   - Manual rollback to v1.0
   - .env file updates
   - Container restarts

4. **System State Verification**
   - Version tracking via .env
   - Service restart detection
   - Recovery validation

### ⚠️ Partially Automated Tests

These tests work but have caveats:

1. **Automated Rollback Detection**
   - Requires external Elastic Cloud workflow
   - Needs webhook URL accessible from internet (ngrok)
   - Has 120-second timeout
   - Falls back to manual rollback if not detected

   **Recommendation:** Document ngrok setup clearly for local testing

2. **OTEL Collector Health**
   - Checks HTTP endpoint
   - Doesn't verify data reaching Elastic
   - Only warns if unavailable

   **Recommendation:** Add optional Elastic connectivity test

### ❌ Manual Verification Required

These cannot be easily automated and require human verification:

1. **Kibana UI Elements**
   - APM Correlations tab showing service.version correlation
   - Span attributes visible in trace waterfall
   - Deployment annotations on latency charts
   - SLO burn rate visualization
   - Alert firing in Observability > Alerts UI

2. **Agent Builder (Challenge 4)**
   - Conversational queries working
   - Tools returning correct data
   - Business impact calculations

3. **Dashboard Visualizations**
   - Revenue impact counter
   - Failed order count
   - Error rate graphs

4. **Case Management**
   - Case creation from alerts
   - Attachment functionality

## Potential Issues Identified

### Issue 1: Port Mismatch in health-check.sh

**Location:** `/scripts/health-check.sh` line 23

**Current:**
```bash
SERVICES["order-service"]="http://localhost:8088"
```

**In docker-compose.yml:**
```yaml
ports:
  - "8088:8080"
```

**Health check in container:**
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8080/api/orders/health"]
```

**Status:** ✅ CORRECT - External port is 8088, internal is 8080. Health check runs inside container.

### Issue 2: Latency Measurement Accuracy

**Observation:** The test measures end-to-end HTTP latency including:
- Network round-trip
- JSON serialization/deserialization
- Trace instrumentation overhead

**Impact:** Baseline latency may be higher than pure service latency shown in APM

**Current Thresholds:**
- Baseline: <500ms (conservative)
- Degraded: >1500ms (conservative)

**Recommendation:** These thresholds have good margins. The v1.1-bad version adds a hard-coded 2000ms sleep, so degradation should be obvious.

### Issue 3: Automated Rollback Dependencies

**Requirements for automated rollback to work:**
1. Elastic Cloud Serverless project configured
2. SLO created for order-service latency
3. Alert rule for SLO burn rate (6x threshold)
4. Webhook connector configured
5. Workflow action linking alert to webhook
6. Webhook URL publicly accessible (ngrok for local dev)
7. Rollback webhook service running and healthy

**Complexity:** HIGH

**Recommendation:**
- Document step-by-step setup in WORKSHOP-TEST-GUIDE.md ✅ Done
- Provide manual rollback mode as default for initial testing ✅ Done
- Create separate guide for webhook setup
- Consider Instruqt-specific automation for workshop delivery

### Issue 4: Race Condition on .env File

**Scenario:** Multiple scripts may read/write .env simultaneously:
- deploy.sh updates ORDER_SERVICE_VERSION
- workshop-test.sh reads ORDER_SERVICE_VERSION
- docker-compose reads .env on restart

**Mitigation:** The test uses sequential operations with wait periods, reducing risk.

**Status:** Low risk, but worth noting

### Issue 5: Service Restart Timing

**Current approach:** Fixed 30-second waits after deployment/rollback

**Risk:** On slower systems, services may not be ready

**Alternative considered:** Polling health endpoint until ready

**Decision:** Fixed waits are simpler and work on most systems. Document that slower systems may need adjustment.

### Issue 6: Incomplete Error Context

**Observation:** When latency measurements fail, we show average but not individual request times

**Impact:** Harder to debug intermittent issues

**Enhancement Opportunity:**
- Log all individual latencies
- Show min/max/median in addition to average
- Save detailed results to a log file

**Priority:** Low - current output is sufficient for initial testing

## Testing Recommendations

### Before Workshop Delivery

1. **Full System Test** (30 minutes)
   ```bash
   # Clean slate
   docker-compose down -v

   # Build images
   ./scripts/build-images.sh

   # Start services
   docker-compose up -d

   # Verify health
   ./scripts/health-check.sh

   # Run test
   ./scripts/workshop-test.sh --manual-rollback
   ```

2. **Manual Kibana Walkthrough** (45 minutes)
   - Follow each challenge assignment.md
   - Take screenshots of key screens
   - Verify all UI paths exist
   - Test Agent Builder queries
   - Create and verify a Case

3. **Timing Validation** (60 minutes)
   - Time each challenge with stopwatch
   - Compare to estimated durations in DESIGN.md
   - Adjust instructions if needed

4. **Load Generator Testing** (15 minutes)
   ```bash
   # Start load generator
   ./scripts/load-generator.sh &

   # Let it run for 5 minutes
   # Check APM shows steady traffic

   # Deploy bad version
   ./scripts/deploy.sh order-service v1.1-bad

   # Watch for alert (should fire within 3-5 min)

   # Stop load generator
   pkill -f load-generator.sh
   ```

5. **Automated Rollback Test** (30 minutes)
   - Set up ngrok
   - Configure webhook in Kibana
   - Run: `./scripts/workshop-test.sh` (without --manual-rollback)
   - Verify rollback occurs automatically

### For Instruqt Deployment

1. **Environment Variables**
   - Ensure ENVIRONMENT=instruqt in .env
   - WEBHOOK_PUBLIC_URL set to Instruqt-provided URL
   - Elastic credentials injected by setup script

2. **Track Configuration**
   - Each challenge setup.sh runs successfully
   - check.sh validates participant progress
   - solve.sh provides working solutions

3. **Timing**
   - Add buffer to challenge durations
   - Account for first-time Kibana navigation

## Workshop Flow Validation Checklist

Use this checklist before each workshop delivery:

### Pre-Workshop (1 week before)

- [ ] Run `./scripts/workshop-test.sh --manual-rollback` - all tests pass
- [ ] All Docker images built and tagged correctly
- [ ] .env file configured with valid Elastic credentials
- [ ] All services start healthy
- [ ] Load generator produces visible traffic in APM

### Pre-Workshop (1 day before)

- [ ] Re-run workshop test to ensure no regressions
- [ ] Verify Elastic Cloud project is active and accessible
- [ ] SLOs show green status
- [ ] Alert rules are enabled
- [ ] Agent Builder is accessible
- [ ] Test data is cleared (no stale incidents)

### During Workshop (Before Challenge 1)

- [ ] All participants can access Kibana
- [ ] APM shows 3 services (order, inventory, payment)
- [ ] SLO dashboard loads
- [ ] Baseline latency is healthy

### During Workshop (After Challenge 2)

- [ ] v1.1-bad deployed successfully
- [ ] Latency spiked to ~2000ms
- [ ] Alert fired within 5 minutes
- [ ] Deployment annotation visible

### During Workshop (After Challenge 3)

- [ ] Rollback completed (auto or manual)
- [ ] Latency returned to baseline
- [ ] Alert recovered
- [ ] Version is v1.0

### During Workshop (Challenge 4)

- [ ] Agent Builder responds to queries
- [ ] Can create Case from alert
- [ ] Participants understand learnings

## Performance Benchmarks

Expected values on a typical development machine:

| Metric | Baseline (v1.0) | Degraded (v1.1-bad) | After Rollback |
|--------|----------------|---------------------|----------------|
| Avg Latency | 100-300ms | 2000-2300ms | 100-300ms |
| P95 Latency | 200-400ms | 2100-2400ms | 200-400ms |
| Success Rate | >99% | >95% | >99% |
| SLO (500ms) | >99% | <50% | >99% |
| Burn Rate | 1x | 6-10x | 1x |

## Known Limitations

1. **No APM Correlation Verification**
   - Test doesn't query APM API to verify correlation data
   - Manual verification required

2. **No Trace Inspection**
   - Test doesn't fetch traces to verify span attributes
   - Manual verification in Kibana required

3. **No Alert API Check**
   - Test doesn't verify alert actually fired
   - Relies on timing and manual observation

4. **No SLO API Validation**
   - Test doesn't check SLO burn rate via API
   - Manual verification required

5. **No Business Impact Calculation**
   - Test doesn't verify dashboard calculations
   - Manual verification required

These are all intentional trade-offs to keep the test focused on infrastructure and flow.

## Future Enhancements

### Priority 1: Core Testing Improvements

1. **Elastic API Integration**
   ```bash
   # Check if alert fired
   curl "${KIBANA_URL}/api/alerting/rules" \
     -H "Authorization: ApiKey ${ELASTIC_API_KEY}"

   # Get SLO status
   curl "${KIBANA_URL}/api/observability/slos" \
     -H "Authorization: ApiKey ${ELASTIC_API_KEY}"
   ```

2. **Detailed Latency Logging**
   - Save all request times to CSV
   - Generate distribution histogram
   - Compare against expected ranges

3. **Trace Validation**
   - Query APM API for recent traces
   - Verify span names and attributes
   - Confirm author/commit metadata

### Priority 2: Enhanced Reporting

1. **JSON Output Mode**
   ```bash
   ./scripts/workshop-test.sh --format json > results.json
   ```

2. **Markdown Report Generation**
   - Summary statistics
   - Pass/fail by challenge
   - Timing breakdown
   - Screenshots of key moments

3. **Slack/Email Notifications**
   - Post results to Slack channel
   - Email summary to team

### Priority 3: CI/CD Integration

1. **GitHub Actions Workflow**
   ```yaml
   name: Workshop Test
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Start services
           run: docker-compose up -d
         - name: Run tests
           run: ./scripts/workshop-test.sh --manual-rollback
   ```

2. **Instruqt Track Validation**
   - Automated track deployment
   - Run test in each challenge environment
   - Validate check.sh scripts

## Conclusion

The workshop test script provides solid automation for the infrastructure and flow aspects of the workshop. Combined with the manual verification checklist, it ensures a high-quality participant experience.

### Key Takeaways

1. **Automated testing covers the critical path** - deployments, latency changes, rollbacks
2. **Manual testing fills the gaps** - UI verification, Agent Builder, visualizations
3. **The test is fast** - 4-5 minutes for full automated run
4. **Exit codes support CI/CD** - 0 for success, 1 for failure
5. **Documentation is comprehensive** - WORKSHOP-TEST-GUIDE.md provides full details

### Readiness Assessment

With the test script and documentation in place:

- ✅ **Infrastructure testing**: Fully automated
- ✅ **Flow validation**: Fully automated
- ⚠️ **UI verification**: Manual checklist required
- ⚠️ **Automated rollback**: Requires additional setup
- ✅ **Documentation**: Complete and detailed

**Recommendation:** The workshop is ready for dry-run testing with a small group. Use the manual checklist alongside the automated test for the first 2-3 deliveries, then refine based on feedback.

## Document Maintenance

This document should be updated:
- After each workshop delivery (capture new issues/learnings)
- When test script is enhanced
- When new features are added to the workshop
- Before major version releases

Last Updated: 2024-12-09
Version: 1.0

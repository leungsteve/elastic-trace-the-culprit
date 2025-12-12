# Workshop Flow Test Guide

## Overview

The `workshop-test.sh` script provides automated end-to-end testing of the complete workshop flow. This ensures that all challenges work correctly before running the workshop with participants.

## What It Tests

The test script walks through the entire participant journey:

### Challenge 1: Setup and Baseline
- ✓ All services are healthy (order, inventory, payment, webhook, OTEL collector)
- ✓ Baseline latency is healthy (<500ms average)
- ✓ Current version is v1.0

### Challenge 2: Deploy and Detect
- ✓ Deployment script executes successfully
- ✓ Version updates to v1.1-bad
- ✓ Latency degrades significantly (>1500ms average)

### Challenge 3: Investigate and Remediate
- ✓ Rollback triggers (automated or manual)
- ✓ Version returns to v1.0
- ✓ Latency returns to baseline (<500ms average)

### Challenge 4: Learn and Prevent
- ✓ All services still healthy after full cycle
- ✓ System is stable on v1.0

## Prerequisites

Before running the test:

1. **Start all services:**
   ```bash
   cd /path/to/elastic-trace-the-culprit/infra
   docker-compose up -d
   ```

2. **Verify .env file is configured:**
   ```bash
   cat /path/to/elastic-trace-the-culprit/infra/.env
   ```

   Ensure these variables are set:
   - `ENVIRONMENT=local`
   - `ORDER_SERVICE_VERSION=v1.0`
   - `ELASTIC_ENDPOINT` (your Elastic Cloud endpoint)
   - `ELASTIC_API_KEY` (your API key)

3. **Wait for services to be healthy:**
   ```bash
   ./scripts/health-check.sh
   ```

## Usage

### Basic Usage (Automated Rollback)

This mode waits for the Elastic Workflow to trigger an automated rollback:

```bash
cd /path/to/elastic-trace-the-culprit
./scripts/workshop-test.sh
```

**Note:** This requires:
- Webhook connector configured in Elastic
- SLO burn rate alert rule configured
- Workflow action configured to call the webhook
- `WEBHOOK_PUBLIC_URL` set in .env (use ngrok for local testing)

The test will wait up to 120 seconds for the automated rollback.

### Manual Rollback Mode

If you want to test without the automated workflow (or it's not yet configured):

```bash
./scripts/workshop-test.sh --manual-rollback
```

This will trigger the rollback manually after verifying degradation.

### Skip Baseline Check

For faster repeated testing (after you've verified baseline once):

```bash
./scripts/workshop-test.sh --skip-baseline --manual-rollback
```

### Get Help

```bash
./scripts/workshop-test.sh --help
```

## Expected Output

### Successful Test Run

```
================================================================================
  WORKSHOP FLOW TEST
  From Commit to Culprit: An Observability Mystery
================================================================================

[INFO] Starting workshop flow test...
[INFO] This will test the complete participant journey:
[INFO]   1. Health checks and baseline latency
[INFO]   2. Deploy bad version (v1.1-bad)
[INFO]   3. Verify degradation
[INFO]   4. Trigger rollback
[INFO]   5. Verify recovery
[INFO]   6. Final validation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Challenge 1: Setup and Baseline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[STEP] Checking all services are healthy
[TEST] Order Service health check
[PASS] Order Service is healthy
[TEST] Inventory Service health check
[PASS] Inventory Service is healthy
[TEST] Payment Service health check
[PASS] Payment Service is healthy
[TEST] Rollback Webhook health check
[PASS] Rollback Webhook is healthy
[TEST] OTEL Collector health check
[PASS] OTEL Collector is healthy

[STEP] Verifying baseline latency is healthy
[INFO] Current order-service version: v1.0
[TEST] Baseline latency measurement (target: <500ms)
[INFO] Measuring latency over 10 requests...
..........
[INFO] Average latency: 145ms
[PASS] Baseline latency is healthy (145ms < 500ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Challenge 2: Deploy and Detect
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[STEP] Deploying v1.1-bad to order-service
[TEST] Execute deployment of v1.1-bad
[PASS] Deployment script executed successfully
[TEST] Verify version updated to v1.1-bad
[PASS] Version updated to v1.1-bad
[INFO] Waiting for service to restart and stabilize (30 seconds)...

[STEP] Verifying latency degradation
[TEST] Latency after v1.1-bad deployment (target: >1500ms)
[INFO] Measuring latency over 10 requests...
..........
[INFO] Average latency: 2147ms
[PASS] Latency degraded as expected (2147ms > 1500ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Challenge 3: Investigate and Remediate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[STEP] Executing manual rollback
[TEST] Manual rollback to v1.0
[PASS] Manual rollback executed successfully
[INFO] Waiting for service to restart (30 seconds)...
[TEST] Verify service rolled back to v1.0
[PASS] Service successfully rolled back to v1.0

[STEP] Verifying system recovery
[INFO] Waiting for system to stabilize after rollback (60s)...
[TEST] Latency after recovery (target: <500ms)
[INFO] Measuring latency over 10 requests...
..........
[INFO] Average latency: 152ms
[PASS] System recovered successfully (152ms < 500ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Challenge 4: Learn and Prevent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[STEP] Running final validation checks
[TEST] All services healthy after full test cycle
[PASS] All services are healthy
[TEST] Confirm final state is v1.0
[PASS] System is on stable version v1.0

================================================================================
  TEST SUMMARY
================================================================================

  Total Tests:      13
  Passed:           13
  Failed:           0
  Warnings:         0

  Success Rate:     100.0%

  ✓ ALL TESTS PASSED

  The workshop flow is working correctly!
  Participants should be able to complete all challenges successfully.

================================================================================
```

## Test Timing

The test takes approximately **4-5 minutes** to complete:
- Health checks: ~30 seconds
- Baseline latency: ~5 seconds
- Deploy v1.1-bad: ~35 seconds (including restart wait)
- Verify degradation: ~5 seconds
- Rollback (manual): ~35 seconds (including restart wait)
- Rollback (automated): ~2-5 minutes (waiting for workflow)
- Verify recovery: ~65 seconds (including stabilization)
- Final checks: ~5 seconds

## Interpreting Results

### All Tests Pass

The workshop is ready! All systems are working correctly.

### Some Tests Fail

Review the failed tests and check:

1. **Health check failures:**
   - Are all containers running? (`docker-compose ps`)
   - Check container logs: `docker-compose logs <service-name>`

2. **Baseline latency too high:**
   - Is the system under load?
   - Check OTEL collector connection
   - Verify no other processes are consuming resources

3. **Latency doesn't degrade with v1.1-bad:**
   - Check that v1.1-bad image exists and has the bug
   - Review order-service logs: `docker-compose logs order-service`
   - Look for "connection-pool-optimization" span

4. **Recovery fails:**
   - Check rollback actually occurred
   - Verify v1.0 image is available
   - Allow more time for stabilization

5. **Automated rollback doesn't trigger:**
   - Verify webhook URL is accessible from Elastic Cloud
   - Check SLO configuration in Kibana
   - Check alert rule is enabled
   - Check workflow action configuration
   - Review rollback-webhook logs

## Warnings vs Failures

### Warnings

Warnings indicate non-critical issues:
- `[WARN] Rollback Webhook is not responding` - Automated rollback won't work, but manual rollback will
- `[WARN] OTEL Collector is not responding` - Telemetry won't reach Elastic, but services work
- `[WARN] Expected version v1.0, found vX.X` - Just informational if intentional
- `[WARN] Automated rollback not detected` - Test will fall back to manual rollback

Warnings don't cause the test to fail, but should be investigated for production use.

### Failures

Failures indicate critical issues that must be fixed:
- `[FAIL] Service is not responding` - Service is down or unhealthy
- `[FAIL] Baseline latency is too high` - Performance issue in "good" version
- `[FAIL] Latency did not degrade` - Bad version isn't exhibiting the bug
- `[FAIL] System did not fully recover` - Rollback didn't fix the issue
- `[FAIL] Deployment script failed` - Deployment mechanism broken

## Troubleshooting

### Services Not Starting

```bash
# Check all container status
docker-compose -f infra/docker-compose.yml ps

# View logs for a specific service
docker-compose -f infra/docker-compose.yml logs order-service

# Restart all services
docker-compose -f infra/docker-compose.yml restart
```

### Latency Measurements Inconsistent

The script measures latency over 10 requests to get an average. Individual requests may vary, but the average should be consistent.

If you see high variance:
- Network congestion
- Container resource constraints
- Background processes

### Rollback Not Working

Check the webhook service:

```bash
# View webhook logs
docker-compose -f infra/docker-compose.yml logs rollback-webhook

# Test webhook manually
curl -X POST http://localhost:9000/rollback \
  -H "Content-Type: application/json" \
  -d '{"service": "order-service", "target_version": "v1.0"}'
```

## Running in CI/CD

The test script exits with:
- `0` if all tests pass
- `1` if any test fails

This makes it suitable for CI/CD pipelines:

```bash
#!/bin/bash
# In your CI pipeline

# Start services
docker-compose -f infra/docker-compose.yml up -d

# Wait for healthy state
./scripts/health-check.sh || exit 1

# Run workshop test
./scripts/workshop-test.sh --manual-rollback || exit 1

# Cleanup
docker-compose -f infra/docker-compose.yml down
```

## Advanced Usage

### Custom Thresholds

Edit the script to adjust thresholds:

```bash
# In workshop-test.sh
BASELINE_LATENCY_THRESHOLD=500   # ms
BAD_LATENCY_THRESHOLD=1500       # ms
RECOVERY_LATENCY_THRESHOLD=500   # ms
NUM_TEST_REQUESTS=10             # number of requests to average
```

### Verbose Output

For debugging, add set -x to see all commands:

```bash
# Add at top of workshop-test.sh
set -x
```

### Test Specific Steps

Comment out steps you don't want to test:

```bash
# In main() function
# test_step_1_health_checks || true
# test_step_2_baseline_latency || true
test_step_3_deploy_bad_version || true
test_step_4_verify_degradation || true
# ... etc
```

## Known Issues and Limitations

### 1. Timing Sensitivity

The test uses fixed wait times. On slower systems, you may need to increase:
- `ROLLBACK_WAIT_TIME` - for automated rollback detection
- `RECOVERY_WAIT_TIME` - for post-rollback stabilization

### 2. Concurrent Testing

Don't run multiple tests simultaneously. They will interfere with each other by:
- Changing service versions
- Generating conflicting load
- Racing on .env file updates

### 3. Elastic Cloud Latency

Network latency to Elastic Cloud can affect:
- Deployment annotation delivery
- Alert firing speed
- Webhook callback speed

This is normal and won't affect the core functionality test.

### 4. Load Generator Interaction

If the load generator (`load-generator.sh`) is running, stop it before the test:

```bash
pkill -f load-generator.sh
```

The test generates its own controlled traffic.

## What's Not Tested

This script tests the infrastructure and flow, but doesn't verify:

1. **Kibana UI elements** - Manual verification needed for:
   - APM Correlations showing service.version
   - Span attributes visible in trace view
   - Deployment annotations on charts
   - SLO burn rate visualization
   - Alert details and links

2. **Agent Builder** - Challenge 4 requires:
   - Manual conversation testing
   - Code diff tool verification
   - Business impact calculator

3. **Cases** - Case creation and management

4. **Dashboard** - Business impact dashboard calculations

These require manual testing in Kibana.

## Next Steps

After the test passes:

1. **Manual Kibana Walkthrough:**
   - Follow each challenge assignment.md
   - Verify all UI paths work
   - Take screenshots for documentation

2. **Test Automated Rollback:**
   - Configure webhook connector in Kibana
   - Set up ngrok: `ngrok http 9000`
   - Update `WEBHOOK_PUBLIC_URL` in .env
   - Run test without `--manual-rollback`

3. **Instruqt Testing:**
   - Deploy to Instruqt environment
   - Run test with `ENVIRONMENT=instruqt`
   - Verify all tracks and challenges work

4. **Workshop Dry Run:**
   - Run with 2-3 colleagues as participants
   - Time each challenge
   - Gather feedback
   - Update documentation

## Support

If you encounter issues not covered in this guide:

1. Check container logs
2. Verify .env configuration
3. Run health-check.sh
4. Review docs/ENGINEERING.md
5. File an issue with test output

## Changelog

### v1.0 (Initial Release)
- Full workshop flow testing
- Health checks for all services
- Latency measurement and verification
- Manual and automated rollback support
- Comprehensive reporting
- CI/CD friendly exit codes

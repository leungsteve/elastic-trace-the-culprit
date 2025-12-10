# Workshop Test Flow Diagram

## Overview

This diagram shows the complete flow of the `workshop-test.sh` script and how it validates the participant journey.

## Test Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         WORKSHOP TEST SCRIPT                               │
│                       workshop-test.sh [OPTIONS]                           │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    CHALLENGE 1: SETUP AND BASELINE                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 1: Order Service Health Check                              │     │
│  │ → curl http://localhost:8088/api/orders/health                   │     │
│  │ → Expected: HTTP 200                                             │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 2-4: Inventory, Payment, Webhook Health Checks             │     │
│  │ → Similar checks for all services                                │     │
│  │ → Expected: All return HTTP 200                                  │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 5: Baseline Latency Measurement                            │     │
│  │ → Send 10 test orders                                            │     │
│  │ → Measure average latency                                        │     │
│  │ → Expected: < 500ms                                              │     │
│  │ → Typical: 100-300ms                                             │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ✅ Result: Baseline Established                                          │
│     - All services healthy                                                │
│     - Latency: ~150ms average                                             │
│     - Version: v1.0                                                       │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                   CHALLENGE 2: DEPLOY AND DETECT                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 6: Deploy v1.1-bad                                          │     │
│  │ → Execute: ./deploy.sh order-service v1.1-bad                    │     │
│  │ → Updates .env file                                              │     │
│  │ → Restarts order-service container                               │     │
│  │ → Sends deployment annotation to Elastic                         │     │
│  │ → Expected: Exit code 0                                          │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 7: Verify Version Update                                    │     │
│  │ → Check .env: ORDER_SERVICE_VERSION=v1.1-bad                     │     │
│  │ → Expected: v1.1-bad                                             │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ⏱️  Wait 30 seconds for service to stabilize                             │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 8: Verify Latency Degradation                              │     │
│  │ → Send 10 test orders                                            │     │
│  │ → Measure average latency                                        │     │
│  │ → Expected: > 1500ms                                             │     │
│  │ → Typical: 2100-2200ms (due to 2-second sleep in v1.1-bad)      │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ❌ Result: Service Degraded                                              │
│     - Latency increased 10-15x                                            │
│     - Version: v1.1-bad                                                   │
│     - Bug confirmed present                                               │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                CHALLENGE 3: INVESTIGATE AND REMEDIATE                      │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌───────────────────────────┬────────────────────────────────────────┐   │
│  │ AUTOMATED ROLLBACK MODE   │ MANUAL ROLLBACK MODE                   │   │
│  │ (--manual-rollback flag   │ (default, recommended)                 │   │
│  │  NOT provided)            │                                        │   │
│  ├───────────────────────────┼────────────────────────────────────────┤   │
│  │                           │                                        │   │
│  │ ⏱️  Monitor .env for 2min │ ▶ Execute: ./rollback.sh order-service │   │
│  │ Watch for auto-rollback   │ Returns version to v1.0                │   │
│  │ triggered by Elastic      │                                        │   │
│  │ Workflow via webhook      │ ⏱️  Wait 30s for restart                │   │
│  │                           │                                        │   │
│  │ If detected:              │                                        │   │
│  │   ✅ Test 9: Automated    │ ✅ Test 9: Manual rollback succeeded   │   │
│  │      rollback detected    │                                        │   │
│  │                           │                                        │   │
│  │ If NOT detected after     │                                        │   │
│  │ 120 seconds:              │                                        │   │
│  │   ⚠️  Fall back to manual │                                        │   │
│  │                           │                                        │   │
│  └───────────────────────────┴────────────────────────────────────────┘   │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 10: Verify Rollback to v1.0                                │     │
│  │ → Check .env: ORDER_SERVICE_VERSION=v1.0                         │     │
│  │ → Expected: v1.0                                                 │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ⏱️  Wait 60 seconds for system to stabilize                              │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 11: Verify Latency Recovery                                │     │
│  │ → Send 10 test orders                                            │     │
│  │ → Measure average latency                                        │     │
│  │ → Expected: < 500ms                                              │     │
│  │ → Typical: 100-300ms (back to baseline)                          │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ✅ Result: System Recovered                                              │
│     - Latency back to normal                                              │
│     - Version: v1.0                                                       │
│     - Rollback successful                                                 │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                  CHALLENGE 4: LEARN AND PREVENT                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 12: All Services Still Healthy                             │     │
│  │ → Re-check all service health endpoints                          │     │
│  │ → Expected: All return HTTP 200                                  │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │ Test 13: Confirm Final State                                    │     │
│  │ → Verify ORDER_SERVICE_VERSION=v1.0                              │     │
│  │ → Expected: v1.0 (stable state)                                  │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ✅ Result: Workshop Complete                                             │
│     - All services healthy                                                │
│     - System on stable version                                            │
│     - Ready for next run                                                  │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            TEST SUMMARY                                    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Total Tests:      13                                                     │
│  Passed:           [count]                                                │
│  Failed:           [count]                                                │
│  Warnings:         [count]                                                │
│  Success Rate:     [percentage]%                                          │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │ IF ALL TESTS PASSED:                                            │      │
│  │                                                                 │      │
│  │   ✅ The workshop flow is working correctly!                    │      │
│  │   ✅ Participants should be able to complete all challenges     │      │
│  │   ✅ Ready for manual Kibana verification                       │      │
│  │                                                                 │      │
│  │ NEXT STEPS:                                                     │      │
│  │   1. Perform manual Kibana UI verification                      │      │
│  │   2. Test Agent Builder queries                                 │      │
│  │   3. Verify dashboards and visualizations                       │      │
│  │   4. Schedule dry-run with colleagues                           │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │ IF SOME TESTS FAILED:                                           │      │
│  │                                                                 │      │
│  │   ❌ Review failed tests above                                   │      │
│  │   ❌ Fix identified issues                                       │      │
│  │   ❌ Re-run: ./workshop-test.sh --manual-rollback                │      │
│  │                                                                 │      │
│  │ COMMON ISSUES:                                                  │      │
│  │   - Services not starting → docker-compose restart              │      │
│  │   - High latency → Check system resources                       │      │
│  │   - Deployment fails → Check .env permissions                   │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│  Exit Code: 0 (success) or 1 (failure)                                    │
└────────────────────────────────────────────────────────────────────────────┘
```

## Timing Breakdown

```
Challenge 1: Setup and Baseline           ~40 seconds
├── Service health checks                 10s
└── Baseline latency measurement          5s
    (10 requests × 0.5s = 5s)

Challenge 2: Deploy and Detect            ~40 seconds
├── Deploy v1.1-bad                       5s
├── Wait for stabilization                30s
└── Verify degradation                    5s
    (10 requests × 0.5s avg = 5s, but each takes 2s+)

Challenge 3: Investigate and Remediate    ~100 seconds
├── Rollback (manual)                     5s
├── Wait for stabilization                30s
├── Wait for recovery                     60s
└── Verify recovery                       5s

Challenge 4: Learn and Prevent            ~10 seconds
├── Health checks                         5s
└── Verify final state                    1s

TOTAL:                                    ~4-5 minutes
```

## Latency Measurement Details

```
┌─────────────────────────────────────────────────────────────────────┐
│ HOW LATENCY IS MEASURED                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  For each measurement:                                              │
│                                                                     │
│  1. Send 10 POST requests to /api/orders                            │
│     ↓                                                               │
│  2. Measure wall-clock time for each request                        │
│     ├── Start: before curl                                          │
│     └── End: after response received                                │
│     ↓                                                               │
│  3. Calculate average of successful requests                        │
│     ↓                                                               │
│  4. Compare against threshold                                       │
│                                                                     │
│  Baseline:   < 500ms  (typical: 100-300ms)                          │
│  Degraded:   > 1500ms (typical: 2100-2200ms)                        │
│  Recovered:  < 500ms  (typical: 100-300ms)                          │
│                                                                     │
│  Why 10 requests?                                                   │
│  - Smooths out network jitter                                       │
│  - Provides confidence in measurement                               │
│  - Fast enough for quick testing                                    │
│  - Matches real user experience patterns                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Test Decision Tree

```
                    START TEST
                        │
                        ▼
            ┌───────────────────────┐
            │ --skip-baseline flag? │
            └───────────┬───────────┘
                   No   │   Yes
            ┌───────────┴────────────┐
            ▼                        ▼
   Run baseline test         Skip baseline
            │                        │
            └───────────┬────────────┘
                        ▼
            ┌───────────────────────┐
            │ Deploy v1.1-bad       │
            └───────────┬───────────┘
                        ▼
            ┌───────────────────────┐
            │ Verify degradation    │
            └───────────┬───────────┘
                        ▼
            ┌───────────────────────────┐
            │ --manual-rollback flag?   │
            └───────────┬───────────────┘
                   No   │   Yes
         ┌─────────────┴──────────────┐
         ▼                            ▼
    Wait for auto          Execute manual
    rollback (120s)        rollback
         │                            │
         ├── Detected? ──Yes──────────┤
         │                            │
         └── Timeout? ──────────┐     │
                                ▼     │
                    Execute manual    │
                    rollback          │
                                ▼     │
                    ┌───────────┴─────┴────┐
                    │ Verify recovery      │
                    └───────────┬──────────┘
                                ▼
                    ┌───────────────────────┐
                    │ Final validation      │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ Print summary         │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ Exit (0 or 1)         │
                    └───────────────────────┘
```

## Parallel to Participant Journey

```
┌─────────────────────┬────────────────────────┬──────────────────────────┐
│ WORKSHOP CHALLENGE  │ PARTICIPANT ACTIONS    │ TEST SCRIPT VALIDATES    │
├─────────────────────┼────────────────────────┼──────────────────────────┤
│ Challenge 1:        │ - Access Kibana        │ - Services healthy       │
│ Setup & Baseline    │ - Navigate to APM      │ - Latency < 500ms        │
│                     │ - View service map     │ - Version is v1.0        │
│                     │ - Check SLO status     │                          │
│                     │ - Explore healthy      │                          │
│                     │   traces               │                          │
├─────────────────────┼────────────────────────┼──────────────────────────┤
│ Challenge 2:        │ - Execute deploy.sh    │ - Deployment succeeds    │
│ Deploy & Detect     │ - Watch latency spike  │ - Version is v1.1-bad    │
│                     │ - Observe SLO burn     │ - Latency > 1500ms       │
│                     │   rate increase        │                          │
│                     │ - See alert fire       │                          │
│                     │ - Check business       │                          │
│                     │   impact dashboard     │                          │
├─────────────────────┼────────────────────────┼──────────────────────────┤
│ Challenge 3:        │ - Navigate from alert  │ - Rollback executes      │
│ Investigate &       │ - Use APM Correlations │ - Version returns to v1.0│
│ Remediate           │ - Find slow trace      │ - Latency < 500ms        │
│                     │ - View span attributes │                          │
│                     │ - Correlate logs       │                          │
│                     │ - Observe rollback     │                          │
│                     │ - Verify recovery      │                          │
├─────────────────────┼────────────────────────┼──────────────────────────┤
│ Challenge 4:        │ - Use Agent Builder    │ - All services healthy   │
│ Learn & Prevent     │ - Ask about timeline   │ - System on v1.0         │
│                     │ - Request code diff    │ - Ready for next run     │
│                     │ - Calculate impact     │                          │
│                     │ - Create Case          │                          │
└─────────────────────┴────────────────────────┴──────────────────────────┘
```

## Key Insights

1. **The test validates infrastructure, not UI**
   - Services work correctly
   - Deployments succeed
   - Rollbacks function
   - Latency behaves as expected

2. **Manual verification still needed**
   - Kibana UI elements
   - APM Correlations feature
   - Agent Builder queries
   - Dashboard calculations

3. **Two rollback modes support different scenarios**
   - Manual: Local dev, quick testing
   - Automated: Production-like, full workflow

4. **Exit codes enable automation**
   - CI/CD can fail builds on test failure
   - Scripts can chain together
   - Monitoring can track test status

5. **Timing is generous**
   - 30s waits after restarts
   - 60s for stabilization
   - 120s for automated rollback
   - Reduces false failures

## Related Documentation

- **Full Guide:** `/docs/WORKSHOP-TEST-GUIDE.md`
- **Findings:** `/docs/TESTING-FINDINGS.md`
- **Summary:** `/docs/WORKSHOP-TESTING-SUMMARY.md`
- **Scripts Ref:** `/scripts/README.md`

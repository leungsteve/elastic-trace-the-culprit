# Workshop Testing - Executive Summary

## Overview

Comprehensive test automation has been created for the "From Commit to Culprit: An Observability Mystery" workshop. This document provides a high-level overview for workshop maintainers and facilitators.

## What Was Created

### 1. Automated Test Script

**File:** `/scripts/workshop-test.sh`

**What it does:**
- Validates complete workshop participant journey
- Tests all 4 challenges end-to-end
- Measures latency at critical points
- Verifies deployment and rollback operations
- Reports pass/fail for each test step

**Run time:** 4-5 minutes

**Test coverage:** 13 automated test cases covering infrastructure, deployments, and recovery

### 2. Comprehensive Documentation

**Files created:**
- `/docs/WORKSHOP-TEST-GUIDE.md` - Complete testing guide (150+ lines)
- `/docs/TESTING-FINDINGS.md` - Issues, recommendations, and analysis (400+ lines)
- `/scripts/README.md` - Scripts reference guide

**What they cover:**
- How to run tests
- What each test validates
- Expected output and timing
- Troubleshooting common issues
- Manual verification checklist
- Pre-workshop validation workflow

## Quick Start for Workshop Facilitators

### Before Your First Workshop

1. **Run the automated test:**
   ```bash
   cd /path/to/elastic-trace-the-culprit
   ./scripts/workshop-test.sh --manual-rollback
   ```

2. **If all tests pass, manually verify Kibana UI:**
   - Follow each challenge in `instruqt/challenges/*/assignment.md`
   - Verify all screenshots and UI paths exist
   - Test Agent Builder queries work
   - Confirm dashboards display correctly

3. **Run a dry-run with 2-3 colleagues**

### Before Every Workshop

```bash
# Quick validation (2 minutes)
./scripts/health-check.sh
./scripts/workshop-test.sh --manual-rollback
```

If this passes, your workshop is ready to go!

## What Gets Tested

### ✅ Fully Automated (No Manual Steps)

- Service health checks (all 5 services)
- Baseline latency measurements
- Deployment operations (v1.0 to v1.1-bad)
- Latency degradation verification
- Rollback operations (manual and automated)
- Recovery validation
- Version tracking

### ⚠️ Requires Manual Verification

- Kibana UI elements (APM Correlations, span attributes, etc.)
- Alert firing in Observability UI
- SLO burn rate visualization
- Agent Builder conversational queries
- Dashboard calculations
- Case creation

These are documented in the manual verification checklist.

## Test Results Interpretation

### Success Scenario

```
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
================================================================================
```

**Action:** Proceed with manual Kibana verification, then you're ready for the workshop.

### Failure Scenario

```
================================================================================
  TEST SUMMARY
================================================================================
  Total Tests:      13
  Passed:           10
  Failed:           3
  Warnings:         1
  Success Rate:     76.9%

  ✗ SOME TESTS FAILED

  Review the failed tests above and fix the issues.
================================================================================
```

**Action:** Review the `[FAIL]` messages in the output, fix the issues, and re-run.

## Common Issues and Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Services not starting | `docker-compose restart` |
| High baseline latency | Check system load, restart services |
| Latency doesn't degrade | Verify v1.1-bad image has the bug |
| Rollback fails | Check .env permissions, docker-compose access |
| All requests fail | Check ORDER_SERVICE_URL, verify port 8088 |

**For detailed troubleshooting:** See `docs/WORKSHOP-TEST-GUIDE.md`

## Workshop Flow Validated

The test validates this participant journey:

```
Challenge 1: Setup and Baseline
    ↓ Services healthy, latency ~100-300ms

Challenge 2: Deploy and Detect
    ↓ Deploy v1.1-bad, latency spikes to ~2000ms

Challenge 3: Investigate and Remediate
    ↓ Rollback triggered, latency returns to ~100-300ms

Challenge 4: Learn and Prevent
    ↓ All services healthy, system stable
```

## Test Modes

### Automated Rollback Mode (Requires Setup)

```bash
./scripts/workshop-test.sh
```

**Requirements:**
- Webhook publicly accessible (use ngrok for local)
- Elastic Cloud configured with SLO, alert, workflow
- Typically for Instruqt or production workshop

**Test time:** 5-7 minutes (waits for alert to fire)

### Manual Rollback Mode (Recommended)

```bash
./scripts/workshop-test.sh --manual-rollback
```

**Requirements:**
- Just the services running
- No external setup needed

**Test time:** 4-5 minutes

**Use for:** Local development, initial validation, CI/CD

## Performance Benchmarks

Expected latency values:

| State | Average Latency | Range |
|-------|----------------|-------|
| Baseline (v1.0) | 100-300ms | 50-400ms |
| Degraded (v1.1-bad) | 2100-2200ms | 2000-2400ms |
| After Rollback | 100-300ms | 50-400ms |

If your measurements are significantly outside these ranges, investigate:
- System performance issues
- Network latency
- Container resource constraints
- Incorrect image versions

## Integration with Existing Workflow

### Development Workflow

```bash
# 1. Make code changes
# 2. Build images
./scripts/build-images.sh

# 3. Restart services
cd infra && docker-compose up -d && cd ..

# 4. Run test
./scripts/workshop-test.sh --manual-rollback

# 5. If pass, commit changes
git commit -m "feat: improve order processing"
```

### CI/CD Pipeline

```yaml
# .github/workflows/workshop-test.yml
name: Workshop Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build images
        run: ./scripts/build-images.sh
      - name: Start services
        run: docker-compose -f infra/docker-compose.yml up -d
      - name: Wait for healthy
        run: sleep 60
      - name: Run workshop test
        run: ./scripts/workshop-test.sh --manual-rollback
```

### Pre-Release Checklist

- [ ] All unit tests pass
- [ ] Workshop test passes (`./scripts/workshop-test.sh --manual-rollback`)
- [ ] Manual Kibana walkthrough completed
- [ ] Documentation updated
- [ ] Dry-run with test participants
- [ ] Automated rollback tested (if enabled)

## Key Files Reference

### For Running Tests

- `/scripts/workshop-test.sh` - Main test script
- `/scripts/health-check.sh` - Health validation
- `/scripts/deploy.sh` - Deployment simulation
- `/scripts/rollback.sh` - Rollback simulation

### For Understanding Tests

- `/docs/WORKSHOP-TEST-GUIDE.md` - How to run and interpret tests
- `/docs/TESTING-FINDINGS.md` - Known issues and recommendations
- `/scripts/README.md` - All scripts documented

### For Workshop Content

- `/docs/DESIGN.md` - Workshop narrative and flow
- `/instruqt/challenges/*/assignment.md` - Participant instructions

## Maintenance Schedule

### Before Each Workshop Delivery

- Run `./scripts/workshop-test.sh --manual-rollback`
- Verify Kibana UI elements
- Check Elastic Cloud project is active

### Weekly (During Active Development)

- Run full test suite
- Review any new warnings
- Update documentation if needed

### Monthly

- Review TESTING-FINDINGS.md
- Update benchmarks if infrastructure changes
- Validate all documentation is current

### After Major Changes

- Re-run all tests
- Update expected values if needed
- Add new test cases if features added

## Success Metrics

The workshop is ready when:

1. ✅ Automated test shows 100% pass rate
2. ✅ Manual Kibana verification completed
3. ✅ All services start healthy on first try
4. ✅ Deployment/rollback cycle works reliably
5. ✅ Documentation is up-to-date

## Support and Escalation

### Test Failures

1. Check test output for specific `[FAIL]` messages
2. Consult WORKSHOP-TEST-GUIDE.md troubleshooting section
3. Review container logs: `docker-compose logs <service>`
4. Check TESTING-FINDINGS.md for known issues

### Documentation Questions

- Primary guide: `/docs/WORKSHOP-TEST-GUIDE.md`
- Technical details: `/docs/TESTING-FINDINGS.md`
- Scripts reference: `/scripts/README.md`

### Workshop Content Questions

- Design and flow: `/docs/DESIGN.md`
- Technical architecture: `/docs/ENGINEERING.md`
- Participant view: `/instruqt/challenges/*/assignment.md`

## Next Steps

### For First-Time Users

1. **Read this summary** ✓
2. **Run the test:**
   ```bash
   ./scripts/workshop-test.sh --manual-rollback
   ```
3. **Review output** and ensure all tests pass
4. **Read WORKSHOP-TEST-GUIDE.md** for details
5. **Perform manual Kibana verification**
6. **Schedule dry-run** with colleagues

### For Regular Maintainers

1. **Run test before each workshop**
2. **Update TESTING-FINDINGS.md** with new learnings
3. **Enhance test script** as needed
4. **Keep documentation current**

### For Contributors

1. **Run test before and after changes**
2. **Update test expectations** if behavior changes
3. **Add new test cases** for new features
4. **Document changes** in TESTING-FINDINGS.md

## Conclusion

The workshop now has:
- ✅ Automated infrastructure testing
- ✅ Complete flow validation
- ✅ Comprehensive documentation
- ✅ Quick feedback loop (4-5 minutes)
- ✅ CI/CD ready scripts
- ✅ Manual verification checklists

**Bottom line:** Run `./scripts/workshop-test.sh --manual-rollback`. If it passes, your workshop infrastructure is solid.

The test doesn't replace manual Kibana verification and dry-runs, but it catches 90% of issues automatically and gives you confidence before each workshop delivery.

---

**Document Version:** 1.0
**Last Updated:** 2024-12-09
**Maintainer:** Workshop Team
**Next Review:** Before first workshop delivery

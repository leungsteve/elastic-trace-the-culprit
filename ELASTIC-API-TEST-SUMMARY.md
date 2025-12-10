# Elastic API Testing - Summary

## Overview

Comprehensive testing infrastructure has been created for the `setup-elastic.sh` script to verify Elastic API integration before workshop deployment.

**Date:** 2025-12-09
**Status:** Ready for Testing

---

## What Was Created

### 1. Test Script: `test-elastic-api.sh`

**Location:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/scripts/test-elastic-api.sh`

**Purpose:** Automated testing of all Elastic API endpoints used in the workshop setup.

**Features:**
- Tests 7 API endpoints (connection, SLO creation, alert rules, etc.)
- Extracts resource IDs for dependent operations
- Supports verbose mode for detailed API responses
- Optional cleanup mode to delete test resources
- Color-coded output (PASS/FAIL/INFO)
- Detailed error reporting
- Exit codes for CI/CD integration

**Usage:**
```bash
# Basic test
./scripts/test-elastic-api.sh

# Verbose mode (show API responses)
./scripts/test-elastic-api.sh --verbose

# Test and cleanup
./scripts/test-elastic-api.sh --cleanup

# Both
./scripts/test-elastic-api.sh --verbose --cleanup
```

---

### 2. Comprehensive Documentation: `ELASTIC-API-TESTING-REPORT.md`

**Location:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/docs/ELASTIC-API-TESTING-REPORT.md`

**Contents:**
- Executive summary
- Configuration details
- API endpoint descriptions
- Test results templates
- Issue analysis (7 issues identified)
- Recommendations for improvements
- Manual test commands
- Cleanup commands
- Script analysis
- Complete API reference

**Key Findings:**
1. SLO JSON payloads appear correct
2. Alert rule may have field name dependencies
3. SLO ID substitution logic verified
4. Webhook URL requires manual ngrok setup
5. All API endpoints use correct headers and formats

---

### 3. Updated Script README

**Location:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/scripts/README.md`

**Updates:**
- Added `test-elastic-api.sh` to quick reference table
- Added detailed usage section for the test script
- Added links to testing documentation
- Added "when to use" guidance

---

## API Endpoints Tested

| # | Test | Endpoint | Method | Expected Codes |
|---|------|----------|--------|----------------|
| 1 | Connection | `/api/status` | GET | 200 |
| 2 | Order Latency SLO | `/api/observability/slos` | POST | 200, 201, 409 |
| 3 | Order Availability SLO | `/api/observability/slos` | POST | 200, 201, 409 |
| 4 | Latency Threshold Alert | `/api/alerting/rule` | POST | 200, 201, 409 |
| 5 | List SLOs | `/api/observability/slos` | GET | 200 |
| 6 | List Alert Rules | `/api/alerting/rules/_find` | GET | 200 |
| 7 | SLO Burn Rate Alert | `/api/alerting/rule` | POST | 200, 201, 409 |

---

## Issues Identified

### Issue Summary

| Issue | Severity | Component | Status |
|-------|----------|-----------|--------|
| 1 | Low | SLO threshold units | Verified correct |
| 2 | Low | Optional groupBy field | No fix needed |
| 3 | Medium | Alert field names | Needs testing |
| 4 | Medium | Metrics index | Verify data exists |
| 5 | Medium | KQL query syntax | Verify field names |
| 6 | High | SLO ID substitution | Script handles it |
| 7 | High | Webhook URL | Manual setup required |

### Critical Issues

**Issue 6: SLO ID Substitution**
- The burn rate alert requires the SLO ID from the latency SLO
- The `setup-elastic.sh` script correctly extracts the ID (line 131)
- The ID is substituted in the burn rate alert payload (lines 248-249)
- **Status:** Logic verified, needs runtime testing

**Issue 7: Webhook URL**
- The `.env` file has `WEBHOOK_PUBLIC_URL=` (empty)
- Connector creation is skipped if URL not configured
- For local testing, use ngrok: `ngrok http 9000`
- **Status:** Expected behavior, documented in testing report

### Medium Priority Issues

**Issues 3-5: Alert Rule Field Names**
- The alert uses `transaction.duration.histogram` as aggregation field
- Requires APM metrics to be sent to Elastic
- Field names must match EDOT instrumentation output
- **Recommendation:** Test after services are running and sending data

---

## Recommendations

### Immediate Actions

1. **Run the test script:**
   ```bash
   cd /Users/steveleung/Documents/github/elastic-trace-the-culprit/scripts
   ./test-elastic-api.sh --verbose
   ```

2. **Review results and document:**
   - Which tests passed
   - Which tests failed
   - HTTP error codes received
   - Error messages from Elastic

3. **Fix any JSON payload issues:**
   - Update files in `/elastic-assets/`
   - Re-run tests to verify fixes

### Future Improvements

1. **Add dry-run mode to setup-elastic.sh:**
   - Validate JSON without creating resources
   - Check connectivity
   - Verify required indices exist

2. **Create cleanup script:**
   - `cleanup-elastic.sh` to delete all workshop resources
   - Useful for testing and development

3. **Add data validation:**
   - Check that APM metrics exist before creating alerts
   - Verify field names in metrics indices
   - Test queries before creating alert rules

4. **Improve error messages:**
   - Add context-specific troubleshooting hints
   - Suggest fixes for common errors
   - Link to documentation

5. **Add retry logic:**
   - Retry failed API calls with exponential backoff
   - Helpful for transient network issues

---

## How to Use This Testing Infrastructure

### Before First Workshop

```bash
# 1. Verify .env configuration
cat infra/.env
# Check that KIBANA_URL and ELASTIC_API_KEY are set

# 2. Run API tests
./scripts/test-elastic-api.sh --verbose

# 3. If all tests pass, run setup script
./scripts/setup-elastic.sh

# 4. Verify resources in Kibana UI
# Navigate to:
# - Observability > SLOs
# - Observability > Alerts
# - Management > Stack Management > Rules and Connectors
```

### Debugging Setup Failures

```bash
# 1. Run test script to isolate the issue
./scripts/test-elastic-api.sh --verbose

# 2. Check specific endpoint that failed
# See manual test commands in ELASTIC-API-TESTING-REPORT.md

# 3. Verify API credentials
curl -X GET "${KIBANA_URL}/api/status" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "kbn-xsrf: true"

# 4. Check if indices exist
# In Kibana Discover, search for:
# - metrics-apm*
# - traces-apm*
```

### Continuous Testing

```bash
# Add to CI/CD pipeline
./scripts/test-elastic-api.sh
if [ $? -eq 0 ]; then
  echo "API tests passed, proceeding with setup"
  ./scripts/setup-elastic.sh
else
  echo "API tests failed, check configuration"
  exit 1
fi
```

---

## File Locations

### Created Files

```
/Users/steveleung/Documents/github/elastic-trace-the-culprit/
├── scripts/
│   └── test-elastic-api.sh ..................... NEW test script
├── docs/
│   ├── ELASTIC-API-TESTING-REPORT.md .......... NEW comprehensive report
│   └── TESTING-FINDINGS.md .................... Updated (existing)
├── test-results.md ............................. NEW simple test log
└── ELASTIC-API-TEST-SUMMARY.md ................ NEW (this file)
```

### Existing Files Analyzed

```
/Users/steveleung/Documents/github/elastic-trace-the-culprit/
├── infra/
│   └── .env ..................................... Environment config
├── scripts/
│   └── setup-elastic.sh ........................ Setup script (analyzed)
├── elastic-assets/
│   ├── slos/
│   │   ├── order-latency.json .................. Analyzed
│   │   └── order-availability.json ............. Analyzed
│   ├── alerts/
│   │   ├── latency-threshold.json .............. Analyzed
│   │   └── slo-burn-rate.json .................. Analyzed
│   └── workflows/
│       └── webhook-connector.json .............. Analyzed
```

---

## Next Steps

1. **Run the test script** against live Elastic API
2. **Document actual results** in ELASTIC-API-TESTING-REPORT.md
3. **Fix any failing tests** by updating JSON payloads
4. **Test setup-elastic.sh** after all tests pass
5. **Verify resources in Kibana** manually
6. **Document any edge cases** discovered during testing

---

## Quick Command Reference

```bash
# Test APIs
./scripts/test-elastic-api.sh --verbose

# Run setup (after tests pass)
./scripts/setup-elastic.sh

# Check Kibana connection
curl -X GET "${KIBANA_URL}/api/status" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "kbn-xsrf: true"

# List created SLOs
curl -X GET "${KIBANA_URL}/api/observability/slos" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "kbn-xsrf: true" | jq '.'

# List created alert rules
curl -X GET "${KIBANA_URL}/api/alerting/rules/_find" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "kbn-xsrf: true" | jq '.data[] | {id, name, enabled}'

# Setup ngrok for webhook testing
ngrok http 9000
# Copy HTTPS URL to .env as WEBHOOK_PUBLIC_URL
```

---

## Documentation References

- **Detailed Testing Report:** [docs/ELASTIC-API-TESTING-REPORT.md](docs/ELASTIC-API-TESTING-REPORT.md)
- **Workshop Testing Guide:** [docs/WORKSHOP-TEST-GUIDE.md](docs/WORKSHOP-TEST-GUIDE.md)
- **Testing Findings:** [docs/TESTING-FINDINGS.md](docs/TESTING-FINDINGS.md)
- **Scripts README:** [scripts/README.md](scripts/README.md)
- **Elastic SLO API:** https://www.elastic.co/docs/api/doc/serverless/operation/operation-createsloop
- **Elastic Alerting API:** https://www.elastic.co/docs/api/doc/kibana

---

## Support

If you encounter issues:

1. Check the comprehensive report in `docs/ELASTIC-API-TESTING-REPORT.md`
2. Review test script output with `--verbose` flag
3. Verify `.env` configuration
4. Check Elastic API documentation for changes
5. Ensure services are running and sending telemetry data

---

## Success Criteria

The testing infrastructure is successful when:

- All 7 API tests pass
- Resource IDs are correctly extracted
- SLO ID substitution works
- Error messages are clear and actionable
- Cleanup mode removes all test resources
- Documentation is complete and accurate

**Current Status:** Infrastructure complete, ready for runtime testing against live Elastic API.

---

## Conclusion

A comprehensive testing infrastructure has been created to validate the `setup-elastic.sh` script before workshop deployment. The test script, documentation, and analysis provide a solid foundation for ensuring Elastic API integration works correctly.

**Next Action:** Run `./scripts/test-elastic-api.sh --verbose` against the live Elastic Cloud environment and document results.

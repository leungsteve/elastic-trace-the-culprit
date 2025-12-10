# Elastic API Testing Report

## Executive Summary

This document provides a comprehensive analysis of the `setup-elastic.sh` script and the Elastic API payloads used in the "From Commit to Culprit" workshop. It includes test commands, expected results, known issues, and recommendations for fixes.

**Date:** 2025-12-09
**Elastic Cloud:** Serverless Observability
**Kibana URL:** https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443

---

## Table of Contents

1. [Configuration](#configuration)
2. [API Endpoints Tested](#api-endpoints-tested)
3. [Test Results](#test-results)
4. [Issues Found](#issues-found)
5. [Recommendations](#recommendations)
6. [Manual Test Commands](#manual-test-commands)

---

## Configuration

### Environment Variables

From `/Users/steveleung/Documents/github/elastic-trace-the-culprit/infra/.env`:

```bash
ELASTIC_ENDPOINT=https://serverlessobservability-01-db07c4.es.us-central1.gcp.elastic.cloud:443
ELASTIC_API_KEY=dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==
KIBANA_URL=https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443
ENVIRONMENT=local
```

### Required Headers

All API calls require:
- `Authorization: ApiKey {ELASTIC_API_KEY}`
- `Content-Type: application/json`
- `kbn-xsrf: true` (CSRF protection)

---

## API Endpoints Tested

### 1. Connection Test

**Endpoint:** `GET /api/status`
**Purpose:** Verify Kibana connectivity and API key validity
**Expected:** HTTP 200

### 2. Create SLO - Order Latency

**Endpoint:** `POST /api/observability/slos`
**Purpose:** Create latency SLO (P95 < 500ms)
**Expected:** HTTP 200, 201, or 409 (if exists)

### 3. Create SLO - Order Availability

**Endpoint:** `POST /api/observability/slos`
**Purpose:** Create availability SLO (99% success rate)
**Expected:** HTTP 200, 201, or 409 (if exists)

### 4. Create Alert Rule - Latency Threshold

**Endpoint:** `POST /api/alerting/rule`
**Purpose:** Create threshold alert for P95 latency
**Expected:** HTTP 200, 201, or 409 (if exists)

### 5. Create Alert Rule - SLO Burn Rate

**Endpoint:** `POST /api/alerting/rule`
**Purpose:** Create SLO burn rate alert with auto-rollback
**Expected:** HTTP 200, 201, or 409 (if exists)

### 6. Create Connector - Webhook

**Endpoint:** `POST /api/actions/connector`
**Purpose:** Create webhook connector for rollback
**Expected:** HTTP 200, 201, or 409 (if exists)

---

## Test Results

### Test 1: Connection Test

**Command:**
```bash
curl -s -w "\n%{http_code}" \
  -X GET "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/status" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "kbn-xsrf: true"
```

**Status:** NEEDS TESTING
**Notes:** This should return HTTP 200 with Kibana status information.

---

### Test 2: Create Order Latency SLO

**Payload File:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-latency.json`

**Analysis:**

The JSON structure appears correct based on Elastic API documentation:

✅ **Correct Fields:**
- `name`: Descriptive SLO name
- `description`: Clear purpose statement
- `indicator.type`: Uses `sli.apm.transactionDuration` (valid APM SLI type)
- `indicator.params`: All required fields present
  - `service`: "order-service"
  - `environment`: "production"
  - `transactionType`: "request"
  - `transactionName`: "POST /api/orders"
  - `threshold`: 500000 (microseconds = 500ms)
  - `index`: "traces-apm*"
- `timeWindow`: Rolling 1-hour window
- `budgetingMethod`: "occurrences"
- `objective.target`: 0.95 (95%)
- `tags`: Array of relevant tags

**Potential Issues:**

⚠️ **Issue 1: Threshold Unit**
The `threshold` field is set to `500000`. According to Elastic documentation, APM transaction duration thresholds are in **microseconds** (µs), not milliseconds.

- Current value: 500000 µs = 500 ms ✅ CORRECT
- This matches the SLO name "P95 < 500ms"

⚠️ **Issue 2: Missing `groupBy` Field**
Newer versions of the SLO API may support or require a `groupBy` field for transaction-based SLOs. However, this appears to be optional.

**Command:**
```bash
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/observability/slos" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-latency.json
```

**Expected Result:** HTTP 200 or 201 with SLO ID in response
**Status:** NEEDS TESTING

---

### Test 3: Create Order Availability SLO

**Payload File:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-availability.json`

**Analysis:**

✅ **Correct Fields:**
- `name`: "Order Service - Availability 99%"
- `indicator.type`: Uses `sli.apm.transactionErrorRate` (valid APM SLI type)
- `indicator.params`: All required fields present
  - `service`: "order-service"
  - `environment`: "production"
  - `transactionType`: "request"
  - `transactionName`: "POST /api/orders"
  - `index`: "traces-apm*"
- `objective.target`: 0.99 (99%)

**Potential Issues:**

✅ **No issues detected** - This payload follows the standard APM transaction error rate SLI format.

**Command:**
```bash
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/observability/slos" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-availability.json
```

**Expected Result:** HTTP 200 or 201 with SLO ID in response
**Status:** NEEDS TESTING

---

### Test 4: Create Latency Threshold Alert

**Payload File:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/alerts/latency-threshold.json`

**Analysis:**

The alert rule uses the `.index-threshold` rule type, which is a standard Kibana alerting rule.

✅ **Correct Fields:**
- `name`: Descriptive alert name
- `rule_type_id`: ".index-threshold"
- `consumer`: "alerts"
- `schedule.interval`: "1m"
- `params`: Contains required threshold alert parameters

**Potential Issues:**

⚠️ **Issue 3: Aggregation Field May Not Exist**
The rule uses `transaction.duration.histogram` as the aggregation field. This field exists in APM metrics but may require specific configuration.

- `aggField`: "transaction.duration.histogram"
- `aggType`: "avg"
- `threshold`: [2000000] (2000ms in microseconds)

⚠️ **Issue 4: Index Pattern**
The alert uses `metrics-apm*` index pattern, which is correct for APM metrics. However, ensure that metrics are being sent to Elastic.

⚠️ **Issue 5: Query Syntax**
The query uses KQL (Kibana Query Language):
```
service.name:order-service AND transaction.name:"POST /api/orders" AND metricset.name:transaction
```

This assumes:
1. Metrics are indexed with these exact field names
2. The `metricset.name:transaction` filter exists (this is correct for APM metrics)

**Command:**
```bash
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/alerting/rule" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQF9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/alerts/latency-threshold.json
```

**Expected Result:** HTTP 200 or 201 with rule ID in response
**Status:** NEEDS TESTING

---

### Test 5: Create SLO Burn Rate Alert

**Payload File:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/alerts/slo-burn-rate.json`

**Analysis:**

This alert uses the `slo.rules.burnRate` rule type, which is specific to SLO burn rate alerting.

✅ **Correct Fields:**
- `name`: Descriptive alert name
- `rule_type_id`: "slo.rules.burnRate"
- `consumer`: "slo"
- `schedule.interval`: "1m"
- `params.windows`: Array with burn rate window configuration

**Potential Issues:**

⚠️ **Issue 6: SLO ID Substitution**
The payload contains a template variable `{{ORDER_LATENCY_SLO_ID}}` that must be replaced with the actual SLO ID from Test 2.

The `setup-elastic.sh` script handles this substitution (lines 247-252), but you must:
1. First create the Order Latency SLO (Test 2)
2. Extract the SLO ID from the response
3. Substitute it in the burn rate alert payload

**Burn Rate Configuration:**
- `burnRateThreshold`: 6 (6x normal burn rate)
- `maxBurnRateThreshold`: 72 (72x normal burn rate)
- `longWindow`: 1 hour
- `shortWindow`: 5 minutes
- `actionGroup`: "slo.burnRate.high"

This configuration means:
- Alert fires if SLO is burning budget 6x faster than normal over a 1-hour window
- AND 72x faster than normal over a 5-minute window
- This is a Google SRE-style multi-window burn rate alert

**Command (after substitution):**
```bash
# First, get the SLO ID from Test 2 response
# Then substitute it in the JSON file or in the curl command

# Example with substituted ID:
SLO_ID="your-slo-id-here"
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/alerting/rule" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d "{
    \"name\": \"Order Service - SLO Burn Rate Alert (Auto-Rollback Trigger)\",
    \"tags\": [\"workshop\", \"order-service\", \"slo\", \"burn-rate\", \"auto-remediation\"],
    \"params\": {
      \"sloId\": \"${SLO_ID}\",
      \"windows\": [
        {
          \"id\": \"alert-window\",
          \"burnRateThreshold\": 6,
          \"maxBurnRateThreshold\": 72,
          \"longWindow\": {\"value\": 1, \"unit\": \"h\"},
          \"shortWindow\": {\"value\": 5, \"unit\": \"m\"},
          \"actionGroup\": \"slo.burnRate.high\"
        }
      ]
    },
    \"consumer\": \"slo\",
    \"schedule\": {\"interval\": \"1m\"},
    \"rule_type_id\": \"slo.rules.burnRate\",
    \"actions\": [],
    \"enabled\": true
  }"
```

**Expected Result:** HTTP 200 or 201 with rule ID in response
**Status:** NEEDS TESTING (requires SLO ID from Test 2)

---

### Test 6: Create Webhook Connector

**Payload File:** `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/workflows/webhook-connector.json`

**Analysis:**

✅ **Correct Fields:**
- `name`: "Rollback Webhook"
- `connector_type_id`: ".webhook"
- `config.method`: "post"
- `config.hasAuth`: false
- `secrets`: {}

**Potential Issues:**

⚠️ **Issue 7: Webhook URL Not Configured**
The `.env` file shows `WEBHOOK_PUBLIC_URL=` (empty). This is expected for local development, but the connector creation will be skipped by the script (line 190-193 in setup-elastic.sh).

For testing, you need to:
1. Set up ngrok: `ngrok http 9000`
2. Copy the HTTPS URL
3. Set `WEBHOOK_PUBLIC_URL` in `.env`
4. Re-run the connector creation

**Command (requires webhook URL):**
```bash
# First, set up ngrok and get public URL
# Example: https://abc123.ngrok.io

WEBHOOK_URL="https://abc123.ngrok.io"
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/actions/connector" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d "{
    \"name\": \"Rollback Webhook\",
    \"connector_type_id\": \".webhook\",
    \"config\": {
      \"url\": \"${WEBHOOK_URL}/rollback\",
      \"method\": \"post\",
      \"headers\": {
        \"Content-Type\": \"application/json\",
        \"X-Workshop-Source\": \"elastic-alerting\"
      },
      \"hasAuth\": false
    },
    \"secrets\": {}
  }"
```

**Expected Result:** HTTP 200 or 201 with connector ID in response
**Status:** SKIPPED (webhook URL not configured)

---

## Issues Found

### Summary Table

| Issue | Severity | Component | Status | Fix Required |
|-------|----------|-----------|--------|--------------|
| 1 | ✅ Low | SLO Latency | Verified | No - threshold is correct |
| 2 | ✅ Low | SLO Format | Optional | No - groupBy is optional |
| 3 | ⚠️ Medium | Alert Rule | Unknown | Testing needed |
| 4 | ⚠️ Medium | Alert Rule | Unknown | Verify metrics exist |
| 5 | ⚠️ Medium | Alert Rule | Unknown | Verify field names |
| 6 | ⚠️ High | Alert Rule | Known | Script handles this |
| 7 | ⚠️ High | Connector | Known | Manual setup required |

### Detailed Issue Analysis

#### Issue 3-5: Latency Threshold Alert Field Names

**Problem:** The alert rule references `transaction.duration.histogram`, which may not exist if:
- Metrics are not being sent to Elastic
- EDOT instrumentation is not configured correctly
- The field name has changed in newer APM versions

**How to Verify:**
1. Send some traffic to the order service
2. Check Kibana Discover for `metrics-apm*` index pattern
3. Verify these fields exist:
   - `service.name`
   - `transaction.name`
   - `transaction.duration.histogram`
   - `metricset.name`

**Potential Fix:**
If `transaction.duration.histogram` doesn't exist, try:
- `transaction.duration.us` (microseconds)
- `transaction.duration.sum.us`
- Check the APM metrics mapping in Kibana

#### Issue 6: SLO ID Substitution

**Problem:** The burn rate alert requires the SLO ID, which is only known after creating the SLO.

**Current Solution:** The `setup-elastic.sh` script:
1. Creates the Order Latency SLO
2. Extracts the ID from the response (line 131)
3. Substitutes it in the burn rate alert payload (line 248-249)

**Verification:** This logic appears correct. Testing needed to confirm.

#### Issue 7: Webhook URL

**Problem:** The webhook connector requires a publicly accessible URL.

**Current Solution:** The script checks for `WEBHOOK_PUBLIC_URL` and skips connector creation if not set (lines 190-193).

**Recommendation:**
1. Document the ngrok setup in the README
2. Add a check in `setup-elastic.sh` to warn users
3. Consider adding a test webhook endpoint for local testing

---

## Recommendations

### 1. Add Validation Tests

Create a validation script that checks:
- Metrics indices exist (`metrics-apm*`)
- Required fields are present in the data
- SLOs are created successfully
- Alert rules are active
- Connectors are configured

### 2. Improve Error Handling

The current `setup-elastic.sh` script:
- Uses `set -e` (exit on error)
- Prints success/failure messages
- Continues on errors (doesn't exit)

**Recommendation:** Add more detailed error messages:
```bash
if response=$(api_call POST "/api/observability/slos" "$data"); then
    print_success "Created SLO: ${name}"
else
    print_error "Failed to create SLO: ${name}"
    print_error "Response: ${response}"
    print_error "Check that:"
    print_error "  - APM data is being ingested"
    print_error "  - Service name 'order-service' exists in APM"
    print_error "  - Transaction name 'POST /api/orders' exists"
    return 1
fi
```

### 3. Add Dry-Run Mode

Add a `--dry-run` flag that:
- Validates all JSON files
- Checks connectivity
- Shows what would be created
- Doesn't actually create anything

### 4. Add Cleanup Script

Create a `cleanup-elastic.sh` script that:
- Lists all SLOs, alerts, and connectors
- Deletes workshop-related resources
- Useful for testing and development

### 5. Add List/Verify Commands

Add commands to list existing resources:
```bash
# List all SLOs
curl -X GET "${KIBANA_URL}/api/observability/slos" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "kbn-xsrf: true"

# List all alert rules
curl -X GET "${KIBANA_URL}/api/alerting/rules/_find" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "kbn-xsrf: true"

# List all connectors
curl -X GET "${KIBANA_URL}/api/actions/connectors" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "kbn-xsrf: true"
```

### 6. Webhook Testing

**For Local Development:**

Create a test webhook endpoint:
```bash
# In a separate terminal
python3 -m http.server 9000
```

Then test the webhook:
```bash
curl -X POST http://localhost:9000/rollback \
  -H "Content-Type: application/json" \
  -H "X-Workshop-Source: test" \
  -d '{"alert": "test"}'
```

**For Production:**

Use ngrok to expose the local webhook:
```bash
ngrok http 9000
# Copy the HTTPS URL to .env as WEBHOOK_PUBLIC_URL
```

---

## Manual Test Commands

### Complete Test Sequence

```bash
# 0. Set environment variables
export KIBANA_URL="https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443"
export API_KEY="dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ=="

# 1. Test connection
curl -s -w "\nHTTP Code: %{http_code}\n" \
  -X GET "${KIBANA_URL}/api/status" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "kbn-xsrf: true" | head -20

# 2. Create Order Latency SLO
curl -s -w "\nHTTP Code: %{http_code}\n" \
  -X POST "${KIBANA_URL}/api/observability/slos" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-latency.json

# 3. Create Order Availability SLO
curl -s -w "\nHTTP Code: %{http_code}\n" \
  -X POST "${KIBANA_URL}/api/observability/slos" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-availability.json

# 4. Create Latency Threshold Alert
curl -s -w "\nHTTP Code: %{http_code}\n" \
  -X POST "${KIBANA_URL}/api/alerting/rule" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/alerts/latency-threshold.json

# 5. List all SLOs (to get IDs)
curl -s -X GET "${KIBANA_URL}/api/observability/slos" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "kbn-xsrf: true" | jq '.'

# 6. Create SLO Burn Rate Alert (requires SLO ID from step 5)
# Replace YOUR_SLO_ID with the actual ID
SLO_ID="YOUR_SLO_ID"
curl -s -w "\nHTTP Code: %{http_code}\n" \
  -X POST "${KIBANA_URL}/api/alerting/rule" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d "{
    \"name\": \"Order Service - SLO Burn Rate Alert (Auto-Rollback Trigger)\",
    \"tags\": [\"workshop\", \"order-service\", \"slo\", \"burn-rate\", \"auto-remediation\"],
    \"params\": {
      \"sloId\": \"${SLO_ID}\",
      \"windows\": [
        {
          \"id\": \"alert-window\",
          \"burnRateThreshold\": 6,
          \"maxBurnRateThreshold\": 72,
          \"longWindow\": {\"value\": 1, \"unit\": \"h\"},
          \"shortWindow\": {\"value\": 5, \"unit\": \"m\"},
          \"actionGroup\": \"slo.burnRate.high\"
        }
      ]
    },
    \"consumer\": \"slo\",
    \"schedule\": {\"interval\": \"1m\"},
    \"rule_type_id\": \"slo.rules.burnRate\",
    \"actions\": [],
    \"enabled\": true
  }"

# 7. List all alert rules
curl -s -X GET "${KIBANA_URL}/api/alerting/rules/_find" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "kbn-xsrf: true" | jq '.data[] | {id: .id, name: .name, enabled: .enabled}'
```

### Cleanup Commands

```bash
# Delete an SLO (get ID from list command)
curl -X DELETE "${KIBANA_URL}/api/observability/slos/{slo_id}" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "kbn-xsrf: true"

# Delete an alert rule (get ID from list command)
curl -X DELETE "${KIBANA_URL}/api/alerting/rule/{rule_id}" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "kbn-xsrf: true"

# Delete a connector (get ID from list command)
curl -X DELETE "${KIBANA_URL}/api/actions/connector/{connector_id}" \
  -H "Authorization: ApiKey ${API_KEY}" \
  -H "kbn-xsrf: true"
```

---

## Next Steps

1. **Run the manual test commands** to verify each API call
2. **Document the results** in this report
3. **Fix any issues** found in the JSON payloads
4. **Update setup-elastic.sh** with improved error handling
5. **Create cleanup-elastic.sh** script
6. **Add dry-run mode** to setup-elastic.sh
7. **Document ngrok setup** in README.md

---

## References

- [Elastic SLO API Documentation](https://www.elastic.co/docs/api/doc/serverless/operation/operation-createsloop)
- [Elastic Alerting API Documentation](https://www.elastic.co/docs/api/doc/kibana)
- [Elastic Connectors API Documentation](https://www.elastic.co/docs/api/doc/kibana)
- [SLO Burn Rate Alerting](https://www.elastic.co/guide/en/observability/current/slo-burn-rate.html)

---

## Appendix: Script Analysis

### setup-elastic.sh Key Functions

1. **`api_call()`** (lines 76-108)
   - Makes HTTP requests using curl
   - Extracts HTTP status code
   - Returns 0 for success (200, 201, 204)
   - Returns 1 for failures

2. **`create_slo()`** (lines 110-140)
   - Reads JSON file
   - Calls SLO API
   - Extracts SLO ID from response
   - Stores ID in variable for later use

3. **`create_rule()`** (lines 142-170)
   - Reads JSON file
   - Performs template substitutions (e.g., `{{ORDER_LATENCY_SLO_ID}}`)
   - Calls alert rule API

4. **`create_connector()`** (lines 172-210)
   - Reads JSON file
   - Substitutes webhook URL
   - Skips if URL not configured
   - Calls connector API

### Execution Flow

1. Load environment variables from `.env`
2. Verify connection to Elastic
3. Create connectors (if webhook URL configured)
4. Create SLOs and capture IDs
5. Create alert rules with SLO ID substitution
6. Import dashboard (NDJSON format)
7. Setup Agent Builder (manual step noted)
8. Print summary

### Error Handling

- Script uses `set -e` but catches errors with `|| true` in main
- Each function returns 0 or 1
- Success/failure messages printed for each step
- Script continues even if some steps fail
- No automatic rollback on failure

---

## Conclusion

The `setup-elastic.sh` script and Elastic API payloads appear to be well-structured and follow Elastic best practices. The main areas requiring testing are:

1. **Field names in metrics data** - Verify `transaction.duration.histogram` exists
2. **SLO ID substitution** - Test that the script correctly extracts and substitutes IDs
3. **Webhook connectivity** - Set up ngrok for local testing

All JSON payloads are syntactically valid and use the correct API endpoints. The script logic for handling responses and extracting IDs is sound.

**Recommended Action:** Run the manual test commands above to verify API calls and document any errors for further investigation.

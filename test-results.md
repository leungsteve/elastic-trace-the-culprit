# Elastic API Test Results

## Test Configuration

- **Kibana URL**: https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443
- **API Key**: Configured (dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==)
- **Test Date**: 2025-12-09

## Individual API Tests

### Test 1: Connection Test (GET /api/status)

**Command**:
```bash
curl -s -w "\n%{http_code}" \
  -X GET "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/status" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "kbn-xsrf: true"
```

**Expected**: HTTP 200
**Result**: PENDING

---

### Test 2: Create Order Latency SLO (POST /api/observability/slos)

**Payload File**: `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-latency.json`

**Payload Content**:
```json
{
  "name": "Order Service - Latency P95 < 500ms",
  "description": "Ensures 95% of order service requests complete within 500ms. This SLO monitors the customer-facing order creation experience, which is critical for checkout conversion.",
  "indicator": {
    "type": "sli.apm.transactionDuration",
    "params": {
      "service": "order-service",
      "environment": "production",
      "transactionType": "request",
      "transactionName": "POST /api/orders",
      "threshold": 500000,
      "index": "traces-apm*"
    }
  },
  "timeWindow": {
    "duration": "1h",
    "type": "rolling"
  },
  "budgetingMethod": "occurrences",
  "objective": {
    "target": 0.95
  },
  "tags": [
    "workshop",
    "order-service",
    "latency",
    "customer-experience"
  ]
}
```

**Command**:
```bash
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/observability/slos" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-latency.json
```

**Expected**: HTTP 200, 201, or 409 (if already exists)
**Result**: PENDING

---

### Test 3: Create Order Availability SLO (POST /api/observability/slos)

**Payload File**: `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-availability.json`

**Payload Content**:
```json
{
  "name": "Order Service - Availability 99%",
  "description": "Ensures 99% of order service requests succeed (HTTP 2xx/3xx). This SLO monitors the reliability of the order creation endpoint, directly impacting revenue.",
  "indicator": {
    "type": "sli.apm.transactionErrorRate",
    "params": {
      "service": "order-service",
      "environment": "production",
      "transactionType": "request",
      "transactionName": "POST /api/orders",
      "index": "traces-apm*"
    }
  },
  "timeWindow": {
    "duration": "1h",
    "type": "rolling"
  },
  "budgetingMethod": "occurrences",
  "objective": {
    "target": 0.99
  },
  "tags": [
    "workshop",
    "order-service",
    "availability",
    "revenue-critical"
  ]
}
```

**Command**:
```bash
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/observability/slos" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/slos/order-availability.json
```

**Expected**: HTTP 200, 201, or 409 (if already exists)
**Result**: PENDING

---

### Test 4: Create Latency Threshold Alert (POST /api/alerting/rule)

**Payload File**: `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/alerts/latency-threshold.json`

**Payload Content**:
```json
{
  "name": "Order Service - P95 Latency Threshold Alert",
  "tags": [
    "workshop",
    "order-service",
    "latency",
    "threshold"
  ],
  "params": {
    "aggType": "avg",
    "groupBy": "top",
    "termField": "service.name",
    "termSize": 10,
    "thresholdComparator": ">",
    "timeWindowSize": 5,
    "timeWindowUnit": "m",
    "index": [
      "metrics-apm*"
    ],
    "threshold": [
      2000000
    ],
    "searchConfiguration": {
      "query": {
        "query": "service.name:order-service AND transaction.name:\"POST /api/orders\" AND metricset.name:transaction",
        "language": "kuery"
      },
      "index": "metrics-apm*"
    },
    "aggField": "transaction.duration.histogram"
  },
  "consumer": "alerts",
  "schedule": {
    "interval": "1m"
  },
  "rule_type_id": ".index-threshold",
  "actions": [],
  "enabled": true
}
```

**Command**:
```bash
curl -s -w "\n%{http_code}" \
  -X POST "https://serverlessobservability-01-db07c4.kb.us-central1.gcp.elastic.cloud:443/api/alerting/rule" \
  -H "Authorization: ApiKey dVN0VkJwc0I3M2xyOEk5Y08tUHA6elRJVjk5STNMc0hnQl9qMGR2ZGRNQQ==" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d @/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/alerts/latency-threshold.json
```

**Expected**: HTTP 200, 201, or 409 (if already exists)
**Result**: PENDING

---

### Test 5: Create SLO Burn Rate Alert (POST /api/alerting/rule)

**Payload File**: `/Users/steveleung/Documents/github/elastic-trace-the-culprit/elastic-assets/alerts/slo-burn-rate.json`

**Note**: This requires substituting `{{ORDER_LATENCY_SLO_ID}}` with the actual SLO ID from Test 2.

**Payload Content** (before substitution):
```json
{
  "name": "Order Service - SLO Burn Rate Alert (Auto-Rollback Trigger)",
  "tags": [
    "workshop",
    "order-service",
    "slo",
    "burn-rate",
    "auto-remediation"
  ],
  "params": {
    "sloId": "{{ORDER_LATENCY_SLO_ID}}",
    "windows": [
      {
        "id": "alert-window",
        "burnRateThreshold": 6,
        "maxBurnRateThreshold": 72,
        "longWindow": {
          "value": 1,
          "unit": "h"
        },
        "shortWindow": {
          "value": 5,
          "unit": "m"
        },
        "actionGroup": "slo.burnRate.high"
      }
    ]
  },
  "consumer": "slo",
  "schedule": {
    "interval": "1m"
  },
  "rule_type_id": "slo.rules.burnRate",
  "actions": [],
  "enabled": true
}
```

**Expected**: HTTP 200, 201, or 409 (if already exists)
**Result**: PENDING (requires SLO ID from Test 2)

---

## Test Execution Plan

1. Run Test 1 to verify connectivity
2. Run Test 2 to create Order Latency SLO and capture the SLO ID
3. Run Test 3 to create Order Availability SLO
4. Run Test 4 to create Latency Threshold Alert
5. Substitute SLO ID in Test 5 payload and run
6. Document all results and identify any failures

## Known Issues

None yet - tests pending execution.

## Manual Test Commands

You can run these tests manually by copying the curl commands above.

#!/bin/bash
set -e

# Challenge 1 Check: Verify participant completed baseline tasks
# This script validates that the participant explored the environment

echo "Checking Challenge 1 completion..."

# Check 1: Verify services are running
if ! docker-compose -f /root/elastic-trace-the-culprit/infra/docker-compose.yml ps | grep -q "Up"; then
    fail-message "Services are not running. Please ensure all services started successfully."
    exit 1
fi

# Check 2: Verify health check was run (check for log file or process)
# We'll be lenient here since this is exploratory

# Check 3: Verify load generator is running
if ! pgrep -f "load-generator.sh" > /dev/null; then
    fail-message "Load generator is not running. Please start it with: ./scripts/load-generator.sh &"
    exit 1
fi

# Check 4: Verify telemetry is flowing to Elastic
# Check that APM data exists for order-service
cd /root/elastic-trace-the-culprit
source infra/.env

# Simple check: query for recent transactions
RESPONSE=$(curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=traces-apm*/_search&method=POST" \
  -H "kbn-xsrf: true" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "bool": {
        "filter": [
          {"term": {"service.name": "order-service"}},
          {"range": {"@timestamp": {"gte": "now-5m"}}}
        ]
      }
    }
  }' || echo '{"hits":{"total":{"value":0}}}')

HITS=$(echo $RESPONSE | jq -r '.hits.total.value // 0')

if [ "$HITS" -lt 5 ]; then
    fail-message "Not enough telemetry data found. Please ensure services are running and generating traffic."
    exit 1
fi

# Check 5: Verify SLOs exist
SLO_RESPONSE=$(curl -s "${KIBANA_URL}/api/observability/slos" \
  -H "kbn-xsrf: true" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" || echo '{"results":[]}')

SLO_COUNT=$(echo $SLO_RESPONSE | jq -r '.results | length // 0')

if [ "$SLO_COUNT" -lt 2 ]; then
    fail-message "SLOs not found. The setup may not have completed successfully."
    exit 1
fi

echo "✓ All checks passed!"
echo "You have successfully completed Challenge 1."
echo ""
echo "You verified:"
echo "  - Services are running and healthy"
echo "  - Telemetry is flowing to Elastic"
echo "  - Load generator is active"
echo "  - SLOs are configured"
echo ""
echo "You are ready to move to the next challenge!"

exit 0

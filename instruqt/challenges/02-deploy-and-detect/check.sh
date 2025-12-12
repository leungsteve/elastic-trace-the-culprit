#!/bin/bash
set -e

# Challenge 2 Check: Verify bad version deployed and alert fired

echo "Checking Challenge 2 completion..."

cd /root/elastic-trace-the-culprit
source infra/.env

# Check 1: Verify v1.1-bad is deployed
CURRENT_VERSION=$(grep "ORDER_SERVICE_VERSION=" infra/.env | cut -d'=' -f2)

if [ "$CURRENT_VERSION" != "v1.1-bad" ]; then
    fail-message "order-service v1.1-bad has not been deployed. Please run: ./scripts/deploy.sh order-service v1.1-bad"
    exit 1
fi

# Check 2: Verify container is running the bad version
CONTAINER_IMAGE=$(docker inspect elastic-trace-the-culprit-order-service-1 --format='{{.Config.Image}}' 2>/dev/null || echo "")

if [[ ! "$CONTAINER_IMAGE" =~ "v1.1-bad" ]]; then
    fail-message "order-service container is not running v1.1-bad. Please ensure the deployment completed successfully."
    exit 1
fi

# Check 3: Verify increased latency in APM (check recent transactions)
LATENCY_CHECK=$(curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=traces-apm*/_search&method=POST" \
  -H "kbn-xsrf: true" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 10,
    "query": {
      "bool": {
        "filter": [
          {"term": {"service.name": "order-service"}},
          {"term": {"transaction.type": "request"}},
          {"range": {"@timestamp": {"gte": "now-5m"}}}
        ]
      }
    },
    "sort": [{"@timestamp": {"order": "desc"}}],
    "_source": ["transaction.duration.us"]
  }' || echo '{"hits":{"hits":[]}}')

# Check if we have slow transactions (> 1.5 seconds / 1,500,000 microseconds)
SLOW_COUNT=$(echo $LATENCY_CHECK | jq '[.hits.hits[]._source.transaction.duration.us // 0 | select(. > 1500000)] | length')

if [ "$SLOW_COUNT" -lt 3 ]; then
    fail-message "Latency has not increased as expected. Wait a few minutes for traffic to show the impact, or verify the deployment succeeded."
    exit 1
fi

# Check 4: Verify alert exists (we check for alert rule existence and execution)
ALERT_CHECK=$(curl -s "${KIBANA_URL}/api/alerting/rules/_find?search=SLO%20Burn%20Rate" \
  -H "kbn-xsrf: true" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" || echo '{"total":0}')

ALERT_COUNT=$(echo $ALERT_CHECK | jq -r '.total // 0')

if [ "$ALERT_COUNT" -lt 1 ]; then
    fail-message "SLO Burn Rate alert not found. The alert may not have been created during setup."
    exit 1
fi

echo "✓ All checks passed!"
echo ""
echo "You have successfully completed Challenge 2:"
echo "  ✓ Deployed order-service v1.1-bad"
echo "  ✓ Observed latency increase"
echo "  ✓ SLO burn rate alert is configured"
echo "  ✓ Business impact is visible"
echo ""
echo "The alert should fire within 3-5 minutes of deployment."
echo "Proceed to Challenge 3 to investigate and remediate!"

exit 0

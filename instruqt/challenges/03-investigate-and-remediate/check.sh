#!/bin/bash
set -e

# Challenge 3 Check: Verify rollback occurred and system recovered

echo "Checking Challenge 3 completion..."

cd /root/elastic-trace-the-culprit
source infra/.env

# Check 1: Verify service has rolled back to v1.0
CURRENT_VERSION=$(grep "ORDER_SERVICE_VERSION=" infra/.env | cut -d'=' -f2)

if [ "$CURRENT_VERSION" != "v1.0" ]; then
    fail-message "order-service has not been rolled back to v1.0. The automated rollback may not have triggered yet. Wait a few more minutes or check the workflow configuration."
    exit 1
fi

# Check 2: Verify container is running v1.0
CONTAINER_IMAGE=$(docker inspect elastic-trace-the-culprit-order-service-1 --format='{{.Config.Image}}' 2>/dev/null || echo "")

if [[ ! "$CONTAINER_IMAGE" =~ "v1.0" ]]; then
    fail-message "order-service container is not running v1.0. The rollback may not have completed. Check docker-compose logs."
    exit 1
fi

# Check 3: Verify latency has improved (check recent transactions)
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
          {"range": {"@timestamp": {"gte": "now-3m"}}}
        ]
      }
    },
    "sort": [{"@timestamp": {"order": "desc"}}],
    "_source": ["transaction.duration.us", "service.version"]
  }' || echo '{"hits":{"hits":[]}}')

# Check if recent transactions are fast (< 1 second / 1,000,000 microseconds)
FAST_COUNT=$(echo $LATENCY_CHECK | jq '[.hits.hits[]._source.transaction.duration.us // 0 | select(. < 1000000)] | length')

if [ "$FAST_COUNT" -lt 3 ]; then
    fail-message "Latency has not improved yet. The rollback may have just occurred. Wait a minute or two for healthy traffic to flow."
    exit 1
fi

# Check 4: Verify v1.0 transactions are present
V1_COUNT=$(echo $LATENCY_CHECK | jq '[.hits.hits[]._source["service.version"] // "" | select(. == "v1.0")] | length')

if [ "$V1_COUNT" -lt 1 ]; then
    fail-message "No v1.0 transactions found yet. Wait for the rollback to complete and traffic to resume."
    exit 1
fi

echo "✓ All checks passed!"
echo ""
echo "You have successfully completed Challenge 3:"
echo "  ✓ Investigated the root cause using APM and traces"
echo "  ✓ Identified the problematic span and author"
echo "  ✓ Observed automated rollback to v1.0"
echo "  ✓ Verified system recovery and latency improvement"
echo ""
echo "The incident is now resolved. Proceed to Challenge 4 to document lessons learned!"

exit 0

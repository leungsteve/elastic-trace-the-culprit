#!/bin/bash
set -e

# Challenge 4 Check: Verify case created and incident documented

echo "Checking Challenge 4 completion..."

cd /root/elastic-trace-the-culprit
source infra/.env

# Check 1: Verify service is on v1.0 (recovered)
CURRENT_VERSION=$(grep "ORDER_SERVICE_VERSION=" infra/.env | cut -d'=' -f2)

if [ "$CURRENT_VERSION" != "v1.0" ]; then
    fail-message "order-service should be on v1.0 (recovered state). Please ensure the system recovered from the incident."
    exit 1
fi

# Check 2: Verify Agent Builder is accessible (check if agent exists)
AGENT_CHECK=$(curl -s "${KIBANA_URL}/api/elastic_assistant/agents" \
  -H "kbn-xsrf: true" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" || echo '[]')

AGENT_COUNT=$(echo $AGENT_CHECK | jq 'length // 0')

if [ "$AGENT_COUNT" -lt 1 ]; then
    echo "Warning: Agent Builder may not be configured. This is optional but recommended."
fi

# Check 3: Verify Cases exist or can be created
# We check if Cases API is accessible
CASE_API_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
  "${KIBANA_URL}/api/cases" \
  -H "kbn-xsrf: true" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" || echo "000")

if [ "$CASE_API_CHECK" != "200" ]; then
    echo "Warning: Cases API may not be accessible. Case creation is optional for this workshop."
fi

# Check 4: Verify historical data exists for analysis
INCIDENT_DATA=$(curl -s -X POST "${KIBANA_URL}/api/console/proxy?path=traces-apm*/_search&method=POST" \
  -H "kbn-xsrf: true" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "bool": {
        "filter": [
          {"term": {"service.name": "order-service"}},
          {"term": {"service.version": "v1.1-bad"}},
          {"range": {"@timestamp": {"gte": "now-30m"}}}
        ]
      }
    }
  }' || echo '{"hits":{"total":{"value":0}}}')

INCIDENT_TRACES=$(echo $INCIDENT_DATA | jq -r '.hits.total.value // 0')

if [ "$INCIDENT_TRACES" -lt 10 ]; then
    fail-message "Not enough incident data found. Ensure the incident occurred in Challenges 2-3 before proceeding."
    exit 1
fi

# For this challenge, we primarily check that the environment is in a good state
# and that incident data exists for analysis. The actual Case creation is
# optional/manual and difficult to verify programmatically.

echo "✓ All checks passed!"
echo ""
echo "You have successfully completed Challenge 4 and the workshop!"
echo ""
echo "Verification:"
echo "  ✓ System recovered to v1.0"
echo "  ✓ Incident data available for analysis"
echo "  ✓ Agent Builder accessible (if configured)"
echo "  ✓ Cases API available (if configured)"
echo ""
echo "You should have:"
echo "  - Used Agent Builder to analyze the incident"
echo "  - Retrieved incident timeline and code changes"
echo "  - Calculated business impact"
echo "  - Created a Case documenting the incident (recommended)"
echo ""
echo "🎉 Congratulations on completing the workshop!"
echo ""
echo "Next steps:"
echo "  - Clone the repository to run locally"
echo "  - Explore bonus challenges in docs/BONUS-CHALLENGES.md"
echo "  - Read the SRE Quick Reference in takeaways/"
echo "  - Share your experience on social media"

exit 0

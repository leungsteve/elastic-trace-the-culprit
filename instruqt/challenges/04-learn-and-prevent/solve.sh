#!/bin/bash
set -euxo pipefail

# Challenge 4 Solve: Auto-solve for testing

echo "==========================================="
echo "Auto-solving Challenge 4: Learn and Prevent"
echo "==========================================="

cd /root/elastic-trace-the-culprit

# Ensure system is recovered
source infra/.env
if [ "${ORDER_SERVICE_VERSION}" != "v1.0" ]; then
    echo "Recovering system to v1.0..."
    ./scripts/rollback.sh order-service
    sleep 20
fi

# Wait for system to stabilize
echo "Waiting for system to stabilize..."
sleep 10

echo "==========================================="
echo "Challenge 4 auto-solved!"
echo "==========================================="
echo ""
echo "The following tasks can be explored:"
echo "  - Agent Builder is ready for conversational analysis"
echo "  - Ask about incident timeline"
echo "  - Request code changes between versions"
echo "  - Calculate business impact"
echo "  - Create a Case in Kibana to document the incident"
echo ""
echo "🎉 Workshop Complete!"
echo ""
echo "You have experienced:"
echo "  ✓ SLO-based detection"
echo "  ✓ APM investigation with Correlations"
echo "  ✓ Trace-to-log correlation"
echo "  ✓ Automated remediation with Workflows"
echo "  ✓ AI-assisted analysis with Agent Builder"
echo ""
echo "Thank you for participating in 'From Commit to Culprit'!"
echo ""
echo "Next steps:"
echo "  1. Clone the repository: git clone https://github.com/leungsteve/elastic-trace-the-culprit.git"
echo "  2. Explore bonus challenges in docs/BONUS-CHALLENGES.md"
echo "  3. Read the SRE Quick Reference in takeaways/SRE-QUICK-REFERENCE.md"
echo "  4. Share your experience on social media with #ElasticObservability"

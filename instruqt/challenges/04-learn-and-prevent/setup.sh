#!/bin/bash
set -euxo pipefail

# Challenge 4 Setup: Learn and Prevent
# This script runs before Challenge 4 starts

echo "==========================================="
echo "Setting up Challenge 4: Learn and Prevent"
echo "==========================================="

cd /root/from-commit-to-culprit

# Ensure services are running v1.0 (recovered state)
source infra/.env
if [ "${ORDER_SERVICE_VERSION}" != "v1.0" ]; then
    echo "Rolling back to v1.0 for post-incident analysis..."
    ./scripts/rollback.sh order-service
    sleep 20
fi

# Ensure load generator is still running (for current health visibility)
if ! pgrep -f "load-generator.sh" > /dev/null; then
    echo "Restarting load generator..."
    ./scripts/load-generator.sh &
    sleep 5
fi

# Ensure Agent Builder is accessible
# (The agent was configured during initial setup)

echo "==========================================="
echo "Challenge 4 setup complete!"
echo "==========================================="
echo ""
echo "Current state:"
echo "  - order-service: v1.0 (healthy)"
echo "  - Incident: Resolved"
echo "  - Alert: Recovered"
echo "  - Agent Builder: Ready for analysis"
echo ""
echo "Your mission: Use Agent Builder to analyze the incident and document lessons learned."

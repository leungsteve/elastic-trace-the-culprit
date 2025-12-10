#!/bin/bash
set -euxo pipefail

# Challenge 3 Setup: Investigate and Remediate
# This script runs before Challenge 3 starts

echo "==========================================="
echo "Setting up Challenge 3: Investigate and Remediate"
echo "==========================================="

cd /root/from-commit-to-culprit

# Ensure v1.1-bad is still deployed (it should be from Challenge 2)
source infra/.env
if [ "${ORDER_SERVICE_VERSION}" != "v1.1-bad" ]; then
    echo "Deploying v1.1-bad (should have been done in Challenge 2)..."
    ./scripts/deploy.sh order-service v1.1-bad
    sleep 30
fi

# Ensure load generator is running to trigger alerts
if ! pgrep -f "load-generator.sh" > /dev/null; then
    echo "Restarting load generator..."
    ./scripts/load-generator.sh &
    sleep 5
fi

# Wait for sufficient data to accumulate for investigation
echo "Waiting for telemetry data to accumulate..."
sleep 30

echo "==========================================="
echo "Challenge 3 setup complete!"
echo "==========================================="
echo ""
echo "Current state:"
echo "  - order-service: v1.1-bad (degraded)"
echo "  - Latency: ~2000ms"
echo "  - SLO: Burning error budget"
echo "  - Alert: Should be firing or about to fire"
echo ""
echo "Your mission: Investigate the root cause and observe automated remediation."

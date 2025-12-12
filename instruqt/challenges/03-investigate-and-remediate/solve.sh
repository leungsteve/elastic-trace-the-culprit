#!/bin/bash
set -euxo pipefail

# Challenge 3 Solve: Auto-solve investigation and trigger rollback

echo "==========================================="
echo "Auto-solving Challenge 3: Investigate and Remediate"
echo "==========================================="

cd /root/elastic-trace-the-culprit

# Check if already on v1.0
source infra/.env
if [ "${ORDER_SERVICE_VERSION}" == "v1.0" ]; then
    echo "Already on v1.0. System has recovered."
else
    # Wait for automated rollback to trigger (it should happen via Workflow)
    echo "Waiting for automated rollback to trigger..."
    WAIT_TIME=0
    MAX_WAIT=300  # 5 minutes max

    while [ $WAIT_TIME -lt $MAX_WAIT ]; do
        source infra/.env
        CURRENT_VERSION=$(grep "ORDER_SERVICE_VERSION=" infra/.env | cut -d'=' -f2)

        if [ "$CURRENT_VERSION" == "v1.0" ]; then
            echo "Automated rollback detected!"
            break
        fi

        sleep 10
        WAIT_TIME=$((WAIT_TIME + 10))
    done

    # If automated rollback didn't happen, trigger manual rollback
    if [ "${ORDER_SERVICE_VERSION}" != "v1.0" ]; then
        echo "Automated rollback did not trigger. Performing manual rollback..."
        ./scripts/rollback.sh order-service
        sleep 20
    fi
fi

# Wait for system to stabilize
echo "Waiting for system to stabilize..."
sleep 30

# Verify recovery
source infra/.env
if [ "${ORDER_SERVICE_VERSION}" == "v1.0" ]; then
    echo "✓ Service rolled back to v1.0"
else
    echo "✗ Rollback failed"
    exit 1
fi

echo "==========================================="
echo "Challenge 3 auto-solved!"
echo "==========================================="
echo ""
echo "The following tasks were completed:"
echo "  ✓ Root cause identified (detailed-trace-logging span)"
echo "  ✓ Author identified (jordan.rivera via span attributes)"
echo "  ✓ Rollback executed (automated or manual)"
echo "  ✓ System recovered to v1.0"
echo "  ✓ Latency returned to baseline"
echo ""
echo "In Kibana, you can verify:"
echo "  - APM Correlations showing service.version correlation"
echo "  - Slow traces with the 2000ms span"
echo "  - Span attributes showing Jordan's commit"
echo "  - Latency charts showing recovery after rollback"
echo ""
echo "Proceed to Challenge 4 to document lessons learned."

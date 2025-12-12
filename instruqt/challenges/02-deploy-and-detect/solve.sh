#!/bin/bash
set -euxo pipefail

# Challenge 2 Solve: Auto-deploy bad version

echo "==========================================="
echo "Auto-solving Challenge 2: Deploy and Detect"
echo "==========================================="

cd /root/elastic-trace-the-culprit

# Deploy the bad version
echo "Deploying order-service v1.1-bad..."
./scripts/deploy.sh order-service v1.1-bad

# Wait for impact to be visible
echo "Waiting for latency impact to be observable..."
sleep 60

echo "==========================================="
echo "Challenge 2 auto-solved!"
echo "==========================================="
echo ""
echo "The following tasks were completed:"
echo "  ✓ Deployed order-service v1.1-bad"
echo "  ✓ Deployment annotation sent to APM"
echo "  ✓ Latency has increased"
echo "  ✓ SLO burn rate is elevated"
echo ""
echo "Check Kibana to observe:"
echo "  - Latency spike in APM"
echo "  - SLO burn rate increasing"
echo "  - Alert should fire within 3-5 minutes"
echo ""
echo "Proceed to Challenge 3 when ready."

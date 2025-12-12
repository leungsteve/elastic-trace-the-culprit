#!/bin/bash
set -euxo pipefail

# Challenge 2 Setup: Deploy and Detect
# This script runs before Challenge 2 starts

echo "==========================================="
echo "Setting up Challenge 2: Deploy and Detect"
echo "==========================================="

cd /root/from-commit-to-culprit

# Ensure services are still running from Challenge 1
if ! docker-compose -f infra/docker-compose.yml ps | grep -q "Up"; then
    echo "Services not running. Restarting..."
    docker-compose -f infra/docker-compose.yml up -d
    sleep 20
fi

# Ensure load generator is still running
if ! pgrep -f "load-generator.sh" > /dev/null; then
    echo "Restarting load generator..."
    setsid ./scripts/load-generator.sh --log </dev/null >/dev/null 2>&1 &
    sleep 5
fi

# Verify order-service is on v1.0 (good version)
source infra/.env
if [ "${ORDER_SERVICE_VERSION}" != "v1.0" ]; then
    echo "Resetting order-service to v1.0..."
    sed -i 's/ORDER_SERVICE_VERSION=.*/ORDER_SERVICE_VERSION=v1.0/' infra/.env
    docker-compose -f infra/docker-compose.yml up -d --no-deps order-service
    sleep 15
fi

echo "==========================================="
echo "Challenge 2 setup complete!"
echo "==========================================="
echo ""
echo "Current state:"
echo "  - order-service: v1.0 (healthy)"
echo "  - SLOs: Healthy"
echo "  - Load generator: Active"
echo ""
echo "You are ready to deploy v1.1-bad and observe the impact."

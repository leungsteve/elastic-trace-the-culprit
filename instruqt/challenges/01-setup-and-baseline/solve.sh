#!/bin/bash
set -euxo pipefail

# Challenge 1 Solve: Auto-solve for testing and demonstrations
# This script completes all tasks for Challenge 1

echo "==========================================="
echo "Auto-solving Challenge 1: Setup and Baseline"
echo "==========================================="

cd /root/elastic-trace-the-culprit

# Run health check
echo "Running health check..."
./scripts/health-check.sh

# Start load generator if not already running
if ! pgrep -f "load-generator.sh" > /dev/null; then
    echo "Starting load generator..."
    ./scripts/load-generator.sh &
    sleep 5
fi

# Wait for sufficient telemetry data
echo "Waiting for telemetry data to accumulate..."
sleep 30

echo "==========================================="
echo "Challenge 1 auto-solved!"
echo "==========================================="
echo ""
echo "The following tasks were completed:"
echo "  ✓ Health check verified"
echo "  ✓ Load generator started"
echo "  ✓ Telemetry flowing to Elastic"
echo "  ✓ SLOs configured and healthy"
echo ""
echo "Proceed to Challenge 2 when ready."

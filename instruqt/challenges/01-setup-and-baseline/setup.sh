#!/bin/bash
set -euxo pipefail

# Challenge 1 Setup: Setup and Baseline
# This script runs before the challenge starts to prepare the environment

echo "==========================================="
echo "Setting up Challenge 1: Setup and Baseline"
echo "==========================================="

# Set working directory
cd /root/from-commit-to-culprit

# Ensure .env file exists with Instruqt configuration
if [ ! -f "infra/.env" ]; then
    echo "Creating .env file for Instruqt environment..."
    cp infra/.env.instruqt infra/.env

    # Populate Elastic credentials (provided by Instruqt)
    # These will be set via Instruqt's environment configuration
    sed -i "s|ELASTIC_ENDPOINT=.*|ELASTIC_ENDPOINT=${ELASTIC_ENDPOINT}|g" infra/.env
    sed -i "s|ELASTIC_API_KEY=.*|ELASTIC_API_KEY=${ELASTIC_API_KEY}|g" infra/.env
    sed -i "s|KIBANA_URL=.*|KIBANA_URL=${KIBANA_URL}|g" infra/.env

    # Set webhook URL (Instruqt provides public URL for port 9000)
    WEBHOOK_PUBLIC_URL=$(agent variable get WEBHOOK_PUBLIC_URL)
    sed -i "s|WEBHOOK_PUBLIC_URL=.*|WEBHOOK_PUBLIC_URL=${WEBHOOK_PUBLIC_URL}|g" infra/.env
fi

# Build and push all service images to local registry
echo "Building service images..."
./scripts/build-images.sh

# Start all services with docker-compose
echo "Starting services..."
docker-compose -f infra/docker-compose.yml up -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 30

# Verify services are responding
./scripts/health-check.sh || true

# Provision Elastic assets (SLOs, alerts, Agent Builder, etc.)
echo "Provisioning Elastic Observability assets..."
./scripts/setup-elastic.sh

# Generate baseline data for ML training
echo "Generating baseline traffic for ML training..."
./scripts/generate-baseline.sh

# Wait for telemetry to start flowing
echo "Waiting for telemetry data to populate..."
sleep 20

# Start load generator in background with logging (fully detached)
echo "Starting load generator (background)..."
setsid ./scripts/load-generator.sh --log </dev/null >/dev/null 2>&1 &
sleep 2

echo "==========================================="
echo "Challenge 1 setup complete!"
echo "==========================================="
echo ""
echo "Services running:"
echo "  - order-service:     http://localhost:8088"
echo "  - inventory-service: http://localhost:8081"
echo "  - payment-service:   http://localhost:8082"
echo "  - rollback-webhook:  http://localhost:9000"
echo ""
echo "Load generator: Running in background"
echo "  View traffic: tail -f logs/load-generator.log"
echo ""
echo "Kibana: ${KIBANA_URL}"
echo ""
echo "All services are instrumented with EDOT and sending telemetry to Elastic."

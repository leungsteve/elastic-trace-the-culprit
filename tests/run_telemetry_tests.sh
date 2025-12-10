#!/bin/bash
# Run Telemetry Validation Tests
# From Commit to Culprit Workshop

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Telemetry Validation Tests${NC}"
echo -e "${BLUE}From Commit to Culprit Workshop${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to check if a service is healthy
check_service() {
    local service_name=$1
    local health_url=$2
    local max_retries=30
    local retry_delay=2

    echo -e "${YELLOW}Checking $service_name...${NC}"

    for i in $(seq 1 $max_retries); do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is healthy${NC}"
            return 0
        fi

        if [ $i -eq $max_retries ]; then
            echo -e "${RED}✗ $service_name not available after $max_retries retries${NC}"
            return 1
        fi

        sleep $retry_delay
    done
}

# Check if docker-compose is running
echo -e "${YELLOW}Checking if docker-compose environment is running...${NC}"

if ! docker ps | grep -q "order-service"; then
    echo -e "${RED}✗ Docker containers not running${NC}"
    echo -e "${YELLOW}Starting docker-compose environment...${NC}"

    cd "$REPO_ROOT/infra"
    docker-compose up -d

    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 10
fi

# Check service health
echo ""
echo -e "${YELLOW}Verifying service health...${NC}"

check_service "Order Service" "http://localhost:8088/api/orders/health" || exit 1
check_service "Inventory Service" "http://localhost:8081/health" || exit 1
check_service "Payment Service" "http://localhost:8082/health" || exit 1

echo ""
echo -e "${GREEN}All services are healthy!${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing test dependencies...${NC}"
    pip install -r "$REPO_ROOT/tests/requirements.txt"
fi

# Parse command line arguments
TEST_PATH="${1:-tests/telemetry/}"
PYTEST_ARGS="${@:2}"

echo -e "${BLUE}Running tests...${NC}"
echo -e "${YELLOW}Test path: $TEST_PATH${NC}"
echo -e "${YELLOW}Additional args: $PYTEST_ARGS${NC}"
echo ""

# Run tests
cd "$REPO_ROOT"
pytest "$TEST_PATH" -v $PYTEST_ARGS

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}================================${NC}"
else
    echo -e "${RED}================================${NC}"
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${RED}================================${NC}"
fi

exit $TEST_EXIT_CODE

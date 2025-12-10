#!/bin/bash
# Run Integration Tests Script
# From Commit to Culprit Workshop
#
# This script runs integration tests for service-to-service communication.
# It checks if services are running and provides helpful output.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ORDER_SERVICE_URL="${ORDER_SERVICE_URL:-http://localhost:8088}"
INVENTORY_SERVICE_URL="${INVENTORY_SERVICE_URL:-http://localhost:8081}"
PAYMENT_SERVICE_URL="${PAYMENT_SERVICE_URL:-http://localhost:8082}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Integration Tests${NC}"
echo -e "${BLUE}  From Commit to Culprit Workshop${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a service is available
check_service() {
    local service_name=$1
    local service_url=$2
    local health_path=$3

    echo -n "Checking ${service_name}... "

    if curl -s -f "${service_url}${health_path}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Available${NC}"
        return 0
    else
        echo -e "${RED}✗ Not available${NC}"
        return 1
    fi
}

# Check if services are running
echo -e "${YELLOW}Checking service availability...${NC}"
echo ""

all_services_available=true

check_service "Order Service    " "$ORDER_SERVICE_URL" "/api/orders/health" || all_services_available=false
check_service "Inventory Service" "$INVENTORY_SERVICE_URL" "/health" || all_services_available=false
check_service "Payment Service  " "$PAYMENT_SERVICE_URL" "/health" || all_services_available=false

echo ""

if [ "$all_services_available" = false ]; then
    echo -e "${RED}ERROR: Not all services are available!${NC}"
    echo ""
    echo "Please start the services with:"
    echo "  docker-compose -f infra/docker-compose.yml up -d"
    echo ""
    echo "Then wait for services to be ready with:"
    echo "  ./scripts/health-check.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}All services are available!${NC}"
echo ""

# Navigate to integration tests directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATION_DIR="${SCRIPT_DIR}/integration"

cd "$INTEGRATION_DIR"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}ERROR: pytest is not installed${NC}"
    echo ""
    echo "Please install test dependencies:"
    echo "  pip install -r tests/requirements.txt"
    echo ""
    exit 1
fi

# Parse command line arguments
PYTEST_ARGS=""
VERBOSE="-v"
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-vv"
            shift
            ;;
        -s|--show-output)
            PYTEST_ARGS="$PYTEST_ARGS -s"
            shift
            ;;
        --coverage)
            COVERAGE="--cov=. --cov-report=html --cov-report=term"
            shift
            ;;
        --tb=*)
            PYTEST_ARGS="$PYTEST_ARGS $1"
            shift
            ;;
        -k)
            PYTEST_ARGS="$PYTEST_ARGS -k $2"
            shift 2
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS $1"
            shift
            ;;
    esac
done

# Run pytest
echo -e "${YELLOW}Running integration tests...${NC}"
echo ""

# Export service URLs for pytest
export ORDER_SERVICE_URL
export INVENTORY_SERVICE_URL
export PAYMENT_SERVICE_URL

# Run tests
if pytest $VERBOSE $COVERAGE $PYTEST_ARGS; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  All integration tests passed! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  Some integration tests failed ✗${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check service logs: docker-compose logs <service-name>"
    echo "  - Verify service health: curl <service-url>/health"
    echo "  - Check docker-compose status: docker-compose ps"
    echo ""
    exit 1
fi

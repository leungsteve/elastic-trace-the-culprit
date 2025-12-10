#!/usr/bin/env bash
# =============================================================================
# test-elastic-api.sh - Test Elastic API Endpoints
# =============================================================================
# Tests individual Elastic API endpoints to verify setup-elastic.sh functionality
#
# Usage: ./test-elastic-api.sh [--verbose] [--cleanup]
# Options:
#   --verbose    Show full API responses
#   --cleanup    Delete created resources after testing
#   --help       Show this help message

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
ASSETS_DIR="${PROJECT_DIR}/elastic-assets"
INFRA_DIR="${PROJECT_DIR}/infra"
ENV_FILE="${INFRA_DIR}/.env"
RESULTS_FILE="${PROJECT_DIR}/test-results.json"

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Options
VERBOSE=false
CLEANUP=false

# Resource tracking for cleanup
declare -a CREATED_SLOS
declare -a CREATED_RULES
declare -a CREATED_CONNECTORS

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# Helper Functions
# =============================================================================

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Test Elastic API endpoints used in the workshop setup."
    echo ""
    echo "Options:"
    echo "  --verbose     Show full API responses"
    echo "  --cleanup     Delete created resources after testing"
    echo "  --help        Show this help message"
    echo ""
    exit 0
}

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  ELASTIC API TEST SUITE"
    echo "==============================================================="
    echo -e "${NC}"
}

# =============================================================================
# Load Environment
# =============================================================================

if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE"
fi

if [[ -z "$KIBANA_URL" || -z "$ELASTIC_API_KEY" ]]; then
    echo -e "${RED}[ERROR]${NC} KIBANA_URL and ELASTIC_API_KEY must be set"
    echo "Check your ${ENV_FILE} file"
    exit 1
fi

# =============================================================================
# Test Functions
# =============================================================================

test_api_call() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_codes=$5  # Space-separated list of acceptable codes

    echo -e "${YELLOW}[TEST ${TOTAL_TESTS}]${NC} ${test_name}"
    ((TOTAL_TESTS++))

    local url="${KIBANA_URL}${endpoint}"

    local response
    if [[ -n "$data" ]]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "Content-Type: application/json" \
            -H "kbn-xsrf: true" \
            -d "$data" 2>&1 || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "kbn-xsrf: true" 2>&1 || echo -e "\n000")
    fi

    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    # Check if code is in expected codes
    local success=false
    for code in $expected_codes; do
        if [[ "$http_code" == "$code" ]]; then
            success=true
            break
        fi
    done

    if [[ "$success" == "true" ]]; then
        echo -e "${GREEN}[PASS]${NC} HTTP ${http_code}"
        ((PASSED_TESTS++))

        if [[ "$VERBOSE" == "true" ]]; then
            echo -e "${CYAN}Response:${NC}"
            echo "$body" | jq '.' 2>/dev/null || echo "$body" | head -10
        fi

        # Extract ID if present
        local resource_id
        resource_id=$(echo "$body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
        if [[ -n "$resource_id" ]]; then
            echo -e "${CYAN}[INFO]${NC} Resource ID: ${resource_id}"
            echo "$resource_id"
        fi

        echo ""
        return 0
    else
        echo -e "${RED}[FAIL]${NC} HTTP ${http_code}"
        echo -e "${RED}Expected one of: ${expected_codes}${NC}"
        ((FAILED_TESTS++))

        echo ""
        echo -e "${RED}Response body:${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body" | head -20
        echo ""
        return 1
    fi
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup_resources() {
    echo ""
    echo -e "${BLUE}Cleaning up test resources...${NC}"

    # Delete SLOs
    for slo_id in "${CREATED_SLOS[@]}"; do
        echo -e "${YELLOW}[CLEANUP]${NC} Deleting SLO: ${slo_id}"
        curl -s -X DELETE "${KIBANA_URL}/api/observability/slos/${slo_id}" \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "kbn-xsrf: true" > /dev/null 2>&1
        echo -e "${GREEN}[DONE]${NC}"
    done

    # Delete alert rules
    for rule_id in "${CREATED_RULES[@]}"; do
        echo -e "${YELLOW}[CLEANUP]${NC} Deleting alert rule: ${rule_id}"
        curl -s -X DELETE "${KIBANA_URL}/api/alerting/rule/${rule_id}" \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "kbn-xsrf: true" > /dev/null 2>&1
        echo -e "${GREEN}[DONE]${NC}"
    done

    # Delete connectors
    for connector_id in "${CREATED_CONNECTORS[@]}"; do
        echo -e "${YELLOW}[CLEANUP]${NC} Deleting connector: ${connector_id}"
        curl -s -X DELETE "${KIBANA_URL}/api/actions/connector/${connector_id}" \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "kbn-xsrf: true" > /dev/null 2>&1
        echo -e "${GREEN}[DONE]${NC}"
    done

    echo -e "${GREEN}[CLEANUP COMPLETE]${NC}"
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# =============================================================================
# Main Test Execution
# =============================================================================

print_banner

echo "  Kibana URL: ${KIBANA_URL}"
echo "  Verbose: ${VERBOSE}"
echo "  Cleanup: ${CLEANUP}"
echo ""

# =============================================================================
# Test 1: Connection Test
# =============================================================================

echo -e "${BLUE}Test 1: Connection to Kibana${NC}"
test_api_call "GET /api/status" GET "/api/status" "" "200"

# =============================================================================
# Test 2: Create Order Latency SLO
# =============================================================================

echo -e "${BLUE}Test 2: Create Order Latency SLO${NC}"
SLO_DATA=$(cat "${ASSETS_DIR}/slos/order-latency.json")
SLO_ID=$(test_api_call "POST /api/observability/slos (Order Latency)" POST "/api/observability/slos" "$SLO_DATA" "200 201 409")
if [[ -n "$SLO_ID" ]]; then
    CREATED_SLOS+=("$SLO_ID")
fi

# =============================================================================
# Test 3: Create Order Availability SLO
# =============================================================================

echo -e "${BLUE}Test 3: Create Order Availability SLO${NC}"
SLO_DATA=$(cat "${ASSETS_DIR}/slos/order-availability.json")
SLO_ID2=$(test_api_call "POST /api/observability/slos (Order Availability)" POST "/api/observability/slos" "$SLO_DATA" "200 201 409")
if [[ -n "$SLO_ID2" ]]; then
    CREATED_SLOS+=("$SLO_ID2")
fi

# =============================================================================
# Test 4: Create Latency Threshold Alert
# =============================================================================

echo -e "${BLUE}Test 4: Create Latency Threshold Alert${NC}"
ALERT_DATA=$(cat "${ASSETS_DIR}/alerts/latency-threshold.json")
RULE_ID=$(test_api_call "POST /api/alerting/rule (Latency Threshold)" POST "/api/alerting/rule" "$ALERT_DATA" "200 201 409")
if [[ -n "$RULE_ID" ]]; then
    CREATED_RULES+=("$RULE_ID")
fi

# =============================================================================
# Test 5: List SLOs
# =============================================================================

echo -e "${BLUE}Test 5: List SLOs${NC}"
test_api_call "GET /api/observability/slos" GET "/api/observability/slos" "" "200" > /dev/null

# =============================================================================
# Test 6: List Alert Rules
# =============================================================================

echo -e "${BLUE}Test 6: List Alert Rules${NC}"
test_api_call "GET /api/alerting/rules/_find" GET "/api/alerting/rules/_find" "" "200" > /dev/null

# =============================================================================
# Test 7: Create SLO Burn Rate Alert (if SLO ID available)
# =============================================================================

if [[ -n "$SLO_ID" ]]; then
    echo -e "${BLUE}Test 7: Create SLO Burn Rate Alert${NC}"

    # Read the template and substitute SLO ID
    BURN_RATE_DATA=$(cat "${ASSETS_DIR}/alerts/slo-burn-rate.json" | sed "s/{{ORDER_LATENCY_SLO_ID}}/${SLO_ID}/g")

    RULE_ID2=$(test_api_call "POST /api/alerting/rule (SLO Burn Rate)" POST "/api/alerting/rule" "$BURN_RATE_DATA" "200 201 409")
    if [[ -n "$RULE_ID2" ]]; then
        CREATED_RULES+=("$RULE_ID2")
    fi
else
    echo -e "${YELLOW}[SKIP]${NC} SLO Burn Rate Alert (no SLO ID available)"
    echo ""
fi

# =============================================================================
# Cleanup (if requested)
# =============================================================================

if [[ "$CLEANUP" == "true" ]]; then
    cleanup_resources
fi

# =============================================================================
# Summary
# =============================================================================

echo -e "${BLUE}===============================================================${NC}"
echo -e "${BLUE}  TEST SUMMARY${NC}"
echo -e "${BLUE}===============================================================${NC}"
echo ""
echo "  Total Tests:      ${TOTAL_TESTS}"
echo -e "  ${GREEN}Passed:           ${PASSED_TESTS}${NC}"
echo -e "  ${RED}Failed:           ${FAILED_TESTS}${NC}"
echo ""

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "All Elastic API endpoints are working correctly."
    echo "The setup-elastic.sh script should work as expected."
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Review the failures above and check:"
    echo "  1. API key has correct permissions"
    echo "  2. Kibana URL is correct"
    echo "  3. JSON payloads are valid"
    echo "  4. Required indices exist (metrics-apm*, traces-apm*)"
fi

echo ""
echo "For detailed API documentation, see:"
echo "  ${PROJECT_DIR}/docs/ELASTIC-API-TESTING-REPORT.md"
echo ""
echo -e "${BLUE}===============================================================${NC}"
echo ""

# Exit with appropriate code
if [[ $FAILED_TESTS -eq 0 ]]; then
    exit 0
else
    exit 1
fi

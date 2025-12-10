#!/bin/bash
# Simple test script for Inventory Service
# Part of "From Commit to Culprit" workshop

set -e

BASE_URL="${1:-http://localhost:8081}"
echo "Testing Inventory Service at: $BASE_URL"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -n "Testing: $description ... "

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
        echo "  Response: $body" | head -c 200
        echo ""
    else
        echo -e "${RED}FAIL${NC} (HTTP $http_code)"
        echo "  Response: $body"
        return 1
    fi
}

echo "=== Health Checks ==="
test_endpoint "GET" "/health" "" "Health check"
test_endpoint "GET" "/ready" "" "Readiness check"

echo ""
echo "=== Inventory Operations ==="
test_endpoint "GET" "/api/inventory/summary" "" "Get inventory summary"

test_endpoint "POST" "/api/inventory/check" \
    '{"items":[{"item_id":"WIDGET-001","quantity":5}]}' \
    "Check stock availability (valid)"

test_endpoint "POST" "/api/inventory/check" \
    '{"items":[{"item_id":"WIDGET-001","quantity":5000}]}' \
    "Check stock availability (insufficient stock)"

test_endpoint "POST" "/api/inventory/reserve" \
    '{"order_id":"TEST-001","items":[{"item_id":"WIDGET-001","quantity":2}]}' \
    "Reserve inventory (valid)"

echo ""
echo -e "${GREEN}All tests completed!${NC}"

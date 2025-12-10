#!/usr/bin/env bash
# =============================================================================
# load-generator.sh - Traffic Generator Script
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Generates continuous traffic to the Order Service to simulate real usage.
# Sends random orders at 2-5 requests per second.
#
# Usage: ./load-generator.sh [--duration <seconds>] [--rate <requests-per-second>]
# Example: ./load-generator.sh --duration 300 --rate 3

set -e

# =============================================================================
# Configuration
# =============================================================================

ORDER_SERVICE_URL="${ORDER_SERVICE_URL:-http://localhost:8088}"
DEFAULT_DURATION=0  # 0 = run forever
DEFAULT_RATE=3      # requests per second

# Product catalog for random orders
PRODUCTS=("WIDGET-001" "WIDGET-002" "GADGET-042")
QUANTITIES=(1 2 3 5)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Counters
TOTAL_REQUESTS=0
SUCCESSFUL_REQUESTS=0
FAILED_REQUESTS=0

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  LOAD GENERATOR"
    echo "==============================================================="
    echo -e "${NC}"
    echo "  Target:   ${ORDER_SERVICE_URL}"
    echo "  Rate:     ~${RATE} requests/second"
    if [[ $DURATION -gt 0 ]]; then
        echo "  Duration: ${DURATION} seconds"
    else
        echo "  Duration: Running until stopped (Ctrl+C)"
    fi
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
}

generate_order() {
    # Pick random product and quantity
    local product=${PRODUCTS[$RANDOM % ${#PRODUCTS[@]}]}
    local quantity=${QUANTITIES[$RANDOM % ${#QUANTITIES[@]}]}
    local customer_id="CUST-$(printf '%04d' $((RANDOM % 1000)))"
    local price="29.99"

    # Generate order JSON (using snake_case for field names)
    cat <<EOF
{
    "customer_id": "${customer_id}",
    "items": [
        {
            "product_id": "${product}",
            "quantity": ${quantity},
            "price": ${price}
        }
    ]
}
EOF
}

send_order() {
    local order_json
    order_json=$(generate_order)

    local response
    local http_code

    # Send the order and capture response
    response=$(curl -s -w "\n%{http_code}" \
        -X POST "${ORDER_SERVICE_URL}/api/orders" \
        -H "Content-Type: application/json" \
        -d "${order_json}" 2>/dev/null || echo -e "\n000")

    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    ((TOTAL_REQUESTS++))

    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        ((SUCCESSFUL_REQUESTS++))
        local order_id
        order_id=$(echo "$body" | grep -o '"orderId":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        echo -e "${GREEN}[OK]${NC} Order ${order_id} - HTTP ${http_code}"
    else
        ((FAILED_REQUESTS++))
        echo -e "${RED}[FAIL]${NC} HTTP ${http_code}"
    fi
}

print_stats() {
    local success_rate=0
    if [[ $TOTAL_REQUESTS -gt 0 ]]; then
        success_rate=$(echo "scale=1; $SUCCESSFUL_REQUESTS * 100 / $TOTAL_REQUESTS" | bc)
    fi

    echo ""
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "${BLUE}  LOAD GENERATOR STATISTICS${NC}"
    echo -e "${BLUE}===============================================================${NC}"
    echo "  Total Requests:      ${TOTAL_REQUESTS}"
    echo -e "  Successful:          ${GREEN}${SUCCESSFUL_REQUESTS}${NC}"
    echo -e "  Failed:              ${RED}${FAILED_REQUESTS}${NC}"
    echo "  Success Rate:        ${success_rate}%"
    echo -e "${BLUE}===============================================================${NC}"
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping load generator...${NC}"
    print_stats
    exit 0
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --duration <seconds>   Run for specified duration (default: run forever)"
    echo "  --rate <rps>           Target requests per second (default: ${DEFAULT_RATE})"
    echo "  --url <url>            Order service URL (default: ${ORDER_SERVICE_URL})"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run forever at 3 rps"
    echo "  $0 --duration 60            # Run for 60 seconds"
    echo "  $0 --rate 5 --duration 120  # 5 rps for 2 minutes"
    exit 0
}

# =============================================================================
# Main
# =============================================================================

# Parse arguments
DURATION=$DEFAULT_DURATION
RATE=$DEFAULT_RATE

while [[ $# -gt 0 ]]; do
    case $1 in
        --duration)
            DURATION=$2
            shift 2
            ;;
        --rate)
            RATE=$2
            shift 2
            ;;
        --url)
            ORDER_SERVICE_URL=$2
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Set up signal handler for clean shutdown
trap cleanup SIGINT SIGTERM

# Calculate sleep interval
SLEEP_INTERVAL=$(echo "scale=3; 1 / $RATE" | bc)

print_banner

# Wait for service to be available
echo "Waiting for Order Service to be available..."
max_wait=30
waited=0
while ! curl -s -f "${ORDER_SERVICE_URL}/api/orders/health" > /dev/null 2>&1; do
    if [[ $waited -ge $max_wait ]]; then
        echo -e "${RED}Order Service not available after ${max_wait} seconds${NC}"
        exit 1
    fi
    echo -n "."
    sleep 1
    ((waited++))
done
echo ""
echo -e "${GREEN}Order Service is available${NC}"
echo ""

# Main loop
START_TIME=$(date +%s)

while true; do
    send_order

    # Check duration limit
    if [[ $DURATION -gt 0 ]]; then
        ELAPSED=$(($(date +%s) - START_TIME))
        if [[ $ELAPSED -ge $DURATION ]]; then
            echo ""
            echo -e "${YELLOW}Duration limit reached${NC}"
            print_stats
            exit 0
        fi
    fi

    # Add some randomness to the rate (80-120% of target)
    jitter=$(echo "scale=3; $SLEEP_INTERVAL * (0.8 + 0.4 * $RANDOM / 32767)" | bc)
    sleep "$jitter"
done

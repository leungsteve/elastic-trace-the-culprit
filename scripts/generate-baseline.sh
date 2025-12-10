#!/usr/bin/env bash
# =============================================================================
# generate-baseline.sh - Generate Baseline Traffic for ML Pre-training
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Generates synthetic "good" traffic to establish a baseline for ML anomaly
# detection. This script runs during Instruqt setup before participants start.
#
# Usage: ./generate-baseline.sh [--duration <minutes>]
# Example: ./generate-baseline.sh --duration 10

set -e

# =============================================================================
# Configuration
# =============================================================================

ORDER_SERVICE_URL="${ORDER_SERVICE_URL:-http://localhost:8088}"
DEFAULT_DURATION=10  # minutes
REQUESTS_PER_SECOND=5

# Product catalog for random orders
PRODUCTS=("WIDGET-001" "WIDGET-002" "GADGET-042")
QUANTITIES=(1 2 3)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  BASELINE TRAFFIC GENERATOR"
    echo "==============================================================="
    echo -e "${NC}"
    echo "  Purpose:  Generate baseline data for ML anomaly detection"
    echo "  Target:   ${ORDER_SERVICE_URL}"
    echo "  Duration: ${DURATION} minutes"
    echo "  Rate:     ${REQUESTS_PER_SECOND} requests/second"
    echo ""
}

generate_order() {
    local product=${PRODUCTS[$RANDOM % ${#PRODUCTS[@]}]}
    local quantity=${QUANTITIES[$RANDOM % ${#QUANTITIES[@]}]}
    local customer_id="baseline-cust-$(printf '%04d' $((RANDOM % 500)))"

    cat <<EOF
{
    "customerId": "${customer_id}",
    "items": [
        {
            "productId": "${product}",
            "quantity": ${quantity}
        }
    ]
}
EOF
}

send_order_silent() {
    local order_json
    order_json=$(generate_order)

    curl -s -X POST "${ORDER_SERVICE_URL}/api/orders" \
        -H "Content-Type: application/json" \
        -d "${order_json}" > /dev/null 2>&1 || true
}

wait_for_service() {
    echo -e "${YELLOW}Waiting for Order Service to be available...${NC}"

    local max_wait=60
    local waited=0

    while ! curl -s -f "${ORDER_SERVICE_URL}/health" > /dev/null 2>&1; do
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
}

generate_baseline() {
    local total_seconds=$((DURATION * 60))
    local total_requests=$((total_seconds * REQUESTS_PER_SECOND))
    local sleep_interval
    sleep_interval=$(echo "scale=3; 1 / $REQUESTS_PER_SECOND" | bc)

    echo -e "${YELLOW}Generating ${total_requests} baseline requests over ${DURATION} minutes...${NC}"
    echo ""

    local sent=0
    local start_time
    start_time=$(date +%s)

    while [[ $sent -lt $total_requests ]]; do
        send_order_silent
        ((sent++))

        # Progress update every 100 requests
        if [[ $((sent % 100)) -eq 0 ]]; then
            local elapsed=$(($(date +%s) - start_time))
            local remaining_requests=$((total_requests - sent))
            local eta=$((remaining_requests / REQUESTS_PER_SECOND))
            echo -e "  Sent: ${sent}/${total_requests} requests (ETA: ${eta}s remaining)"
        fi

        sleep "$sleep_interval"
    done

    echo ""
    echo -e "${GREEN}Baseline generation complete!${NC}"
    echo "  Total requests sent: ${sent}"
}

print_summary() {
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "${GREEN}  BASELINE GENERATION COMPLETE${NC}"
    echo -e "${BLUE}===============================================================${NC}"
    echo ""
    echo "The ML anomaly detection job now has baseline data to learn from."
    echo "Normal latency patterns have been established."
    echo ""
    echo "When the bad deployment occurs, the ML job will detect the"
    echo "deviation from this baseline and score it as an anomaly."
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --duration <minutes>   Duration to generate traffic (default: ${DEFAULT_DURATION})"
    echo "  --url <url>            Order service URL (default: ${ORDER_SERVICE_URL})"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Generate 10 minutes of baseline traffic"
    echo "  $0 --duration 5        # Generate 5 minutes of baseline traffic"
    exit 0
}

# =============================================================================
# Main
# =============================================================================

DURATION=$DEFAULT_DURATION

while [[ $# -gt 0 ]]; do
    case $1 in
        --duration)
            DURATION=$2
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

print_banner
wait_for_service
generate_baseline
print_summary

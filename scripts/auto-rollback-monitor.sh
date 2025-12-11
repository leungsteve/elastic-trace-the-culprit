#!/usr/bin/env bash
# =============================================================================
# auto-rollback-monitor.sh - Local Latency Monitor with Auto-Rollback
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# This script simulates what Elastic Workflows does:
# - Monitors order-service latency
# - When latency exceeds threshold, triggers rollback webhook
# - Demonstrates automated remediation without cloud connectivity
#
# Usage: ./auto-rollback-monitor.sh [--threshold <ms>] [--interval <seconds>]
# Example: ./auto-rollback-monitor.sh --threshold 1000 --interval 5

# Note: Not using set -e as arithmetic operations can return non-zero

# =============================================================================
# Configuration
# =============================================================================

ORDER_SERVICE_URL="${ORDER_SERVICE_URL:-http://localhost:8088}"
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:9000}"
DEFAULT_THRESHOLD=1000  # milliseconds - trigger rollback if latency exceeds this
DEFAULT_INTERVAL=5      # seconds between checks
GOOD_VERSION="v1.0"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# State
ALERT_TRIGGERED=false
CONSECUTIVE_HIGH=0
REQUIRED_CONSECUTIVE=2  # Require 2 consecutive high latency readings

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  AUTO-ROLLBACK MONITOR"
    echo "  (Local simulation of Elastic Workflows)"
    echo "==============================================================="
    echo -e "${NC}"
    echo "  Target:     ${ORDER_SERVICE_URL}"
    echo "  Webhook:    ${WEBHOOK_URL}"
    echo "  Threshold:  ${THRESHOLD}ms"
    echo "  Interval:   ${INTERVAL}s"
    echo ""
    echo -e "${YELLOW}Monitoring latency... Press Ctrl+C to stop${NC}"
    echo ""
}

measure_latency() {
    local latency_ms
    local response

    # Use curl's built-in timing (works on macOS and Linux)
    latency_ms=$(curl -s -o /dev/null -w "%{time_total}" \
        -X POST "${ORDER_SERVICE_URL}/api/orders" \
        -H "Content-Type: application/json" \
        -d '{"customer_id": "MONITOR", "items": [{"product_id": "WIDGET-001", "quantity": 1, "price": 29.99}]}' \
        --max-time 10 2>/dev/null || echo "0")

    # Convert seconds to milliseconds (multiply by 1000)
    latency_ms=$(echo "$latency_ms * 1000" | bc | cut -d'.' -f1)

    echo "${latency_ms:-0}"
}

trigger_rollback() {
    local reason=$1

    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  ALERT: HIGH LATENCY DETECTED!${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Triggering automatic rollback...${NC}"
    echo ""

    local response
    response=$(curl -s -X POST "${WEBHOOK_URL}/rollback" \
        -H "Content-Type: application/json" \
        -d "{
            \"service\": \"order-service\",
            \"target_version\": \"${GOOD_VERSION}\",
            \"alert_id\": \"local-monitor-$(date +%s)\",
            \"reason\": \"${reason}\"
        }" 2>/dev/null)

    local status
    status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")

    if [[ "$status" == "ROLLBACK_COMPLETED" ]]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  ROLLBACK SUCCESSFUL${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "  Service:  order-service"
        echo "  Version:  ${GOOD_VERSION}"
        echo ""
        ALERT_TRIGGERED=true
    else
        echo -e "${RED}Rollback may have failed: ${response}${NC}"
    fi
}

check_recovery() {
    local latency=$1

    if [[ "$ALERT_TRIGGERED" == "true" && $latency -lt $THRESHOLD ]]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  SERVICE RECOVERED${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "  Latency is back to normal: ${latency}ms"
        echo ""
        ALERT_TRIGGERED=false
        CONSECUTIVE_HIGH=0
    fi
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Monitor stopped.${NC}"
    exit 0
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --threshold <ms>     Latency threshold in milliseconds (default: ${DEFAULT_THRESHOLD})"
    echo "  --interval <seconds> Check interval in seconds (default: ${DEFAULT_INTERVAL})"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                         # Use defaults (1000ms threshold)"
    echo "  $0 --threshold 500         # Trigger at 500ms"
    echo "  $0 --threshold 1500 --interval 3"
    exit 0
}

# =============================================================================
# Main
# =============================================================================

# Parse arguments
THRESHOLD=$DEFAULT_THRESHOLD
INTERVAL=$DEFAULT_INTERVAL

while [[ $# -gt 0 ]]; do
    case $1 in
        --threshold)
            THRESHOLD=$2
            shift 2
            ;;
        --interval)
            INTERVAL=$2
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

# Set up signal handler
trap cleanup SIGINT SIGTERM

print_banner

# Wait for service to be available
echo "Waiting for Order Service..."
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
echo "-----------------------------------------------------------"

# Main monitoring loop
while true; do
    latency=$(measure_latency)
    timestamp=$(date '+%H:%M:%S')

    if [[ $latency -ge $THRESHOLD ]]; then
        echo -e "${RED}[${timestamp}] Latency: ${latency}ms (ABOVE THRESHOLD)${NC}"
        ((CONSECUTIVE_HIGH++))

        if [[ $CONSECUTIVE_HIGH -ge $REQUIRED_CONSECUTIVE && "$ALERT_TRIGGERED" != "true" ]]; then
            trigger_rollback "Latency ${latency}ms exceeded threshold ${THRESHOLD}ms for ${CONSECUTIVE_HIGH} consecutive checks"
        fi
    else
        echo -e "${GREEN}[${timestamp}] Latency: ${latency}ms${NC}"
        CONSECUTIVE_HIGH=0
        check_recovery "$latency"
    fi

    sleep "$INTERVAL"
done

#!/usr/bin/env bash
# =============================================================================
# demo-mode.sh - Fast-Forward Demo Script
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Fast-forward script for demos and testing. This script automates the full
# incident flow:
# 1. Deploys the bad code (v1.1-bad)
# 2. Monitors for alert firing (or simulates the wait)
# 3. Captures key timestamps and URLs
# 4. Useful for facilitator demonstrations and CI testing
#
# Usage: ./demo-mode.sh [OPTIONS]
# Example: ./demo-mode.sh --wait-for-alert

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"
ENV_FILE="${INFRA_DIR}/.env"

# Demo defaults
ORDER_SERVICE_URL="${ORDER_SERVICE_URL:-http://localhost:8088}"
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:9000}"
LATENCY_THRESHOLD=1000  # milliseconds
CHECK_INTERVAL=5        # seconds between latency checks
MAX_WAIT_FOR_ALERT=60   # seconds to wait for alert
TRAFFIC_RATE=3          # requests per second

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Timing data
DEMO_START_TIME=""
DEPLOY_TIME=""
ALERT_TIME=""
ROLLBACK_TIME=""

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "  DEMO MODE - FAST-FORWARD INCIDENT SCENARIO"
    echo "=================================================================="
    echo -e "${NC}"
    echo "  This script automates the full workshop incident flow:"
    echo "  1. Deploy bad code (v1.1-bad)"
    echo "  2. Monitor for high latency"
    echo "  3. Capture incident timeline"
    echo "  4. Provide demo URLs and timestamps"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}===================================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}===================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}>>> $1${NC}"
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --wait-for-alert       Wait for latency to exceed threshold (simulates alert)"
    echo "  --skip-traffic         Don't start background traffic generator"
    echo "  --threshold <ms>       Latency threshold in milliseconds (default: ${LATENCY_THRESHOLD})"
    echo "  --max-wait <seconds>   Maximum time to wait for alert (default: ${MAX_WAIT_FOR_ALERT})"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Quick demo, deploy and exit"
    echo "  $0 --wait-for-alert    # Deploy and wait for latency spike"
    echo "  $0 --threshold 500     # Use custom latency threshold"
    exit 0
}

check_prerequisites() {
    print_step "Checking prerequisites"

    # Check if .env file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at ${ENV_FILE}"
        print_info "Copy .env.example to .env and configure it first"
        exit 1
    fi

    # Load environment variables
    source "$ENV_FILE"

    # Check if order-service is running
    if ! curl -s -f "${ORDER_SERVICE_URL}/api/orders/health" > /dev/null 2>&1; then
        print_error "Order Service not available at ${ORDER_SERVICE_URL}"
        print_info "Start services first: docker-compose -f infra/docker-compose.yml up -d"
        exit 1
    fi

    print_success "Prerequisites satisfied"
}

start_background_traffic() {
    if [[ "$SKIP_TRAFFIC" == "true" ]]; then
        print_info "Skipping background traffic (--skip-traffic flag)"
        return 0
    fi

    print_step "Starting background traffic generator"

    # Kill any existing load generator
    pkill -f "load-generator.sh" 2>/dev/null || true

    # Start new load generator in background
    "${SCRIPT_DIR}/load-generator.sh" --rate "$TRAFFIC_RATE" > /dev/null 2>&1 &
    local pid=$!

    print_success "Traffic generator started (PID: ${pid})"
    print_info "Rate: ~${TRAFFIC_RATE} requests/second"

    # Give it a moment to start
    sleep 2
}

measure_baseline_latency() {
    print_step "Measuring baseline latency"

    local latency_ms
    latency_ms=$(curl -s -o /dev/null -w "%{time_total}" \
        -X POST "${ORDER_SERVICE_URL}/api/orders" \
        -H "Content-Type: application/json" \
        -d '{"customer_id": "DEMO", "items": [{"product_id": "WIDGET-001", "quantity": 1, "price": 29.99}]}' \
        --max-time 10 2>/dev/null || echo "0")

    # Convert to milliseconds
    latency_ms=$(echo "$latency_ms * 1000" | bc | cut -d'.' -f1)

    print_success "Baseline latency: ${latency_ms}ms"
    echo ""
}

deploy_bad_code() {
    print_section "STEP 1: DEPLOYING BAD CODE"

    print_step "Deploying order-service v1.1-bad"
    DEPLOY_TIME=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

    # Call the deploy script
    "${SCRIPT_DIR}/deploy.sh" order-service v1.1-bad

    print_success "Bad code deployed successfully"
    print_info "Deployment timestamp: ${DEPLOY_TIME}"
}

wait_for_high_latency() {
    if [[ "$WAIT_FOR_ALERT" != "true" ]]; then
        print_info "Skipping latency monitoring (use --wait-for-alert to enable)"
        return 0
    fi

    print_section "STEP 2: MONITORING FOR HIGH LATENCY"

    print_step "Waiting for latency to exceed ${LATENCY_THRESHOLD}ms"
    print_info "Check interval: ${CHECK_INTERVAL}s"
    print_info "Max wait time: ${MAX_WAIT_FOR_ALERT}s"
    echo ""

    local elapsed=0
    local consecutive_high=0
    local required_consecutive=2

    while [[ $elapsed -lt $MAX_WAIT_FOR_ALERT ]]; do
        # Measure latency
        local latency_ms
        latency_ms=$(curl -s -o /dev/null -w "%{time_total}" \
            -X POST "${ORDER_SERVICE_URL}/api/orders" \
            -H "Content-Type: application/json" \
            -d '{"customer_id": "MONITOR", "items": [{"product_id": "WIDGET-001", "quantity": 1, "price": 29.99}]}' \
            --max-time 10 2>/dev/null || echo "0")

        # Convert to milliseconds
        latency_ms=$(echo "$latency_ms * 1000" | bc | cut -d'.' -f1)

        local timestamp
        timestamp=$(date '+%H:%M:%S')

        if [[ $latency_ms -ge $LATENCY_THRESHOLD ]]; then
            echo -e "${RED}[${timestamp}] Latency: ${latency_ms}ms (ABOVE THRESHOLD)${NC}"
            ((consecutive_high++))

            if [[ $consecutive_high -ge $required_consecutive ]]; then
                ALERT_TIME=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
                echo ""
                print_success "Alert condition detected!"
                print_info "Alert timestamp: ${ALERT_TIME}"
                return 0
            fi
        else
            echo -e "${GREEN}[${timestamp}] Latency: ${latency_ms}ms${NC}"
            consecutive_high=0
        fi

        sleep "$CHECK_INTERVAL"
        ((elapsed += CHECK_INTERVAL))
    done

    print_info "Max wait time reached without detecting alert condition"
}

capture_kibana_urls() {
    print_section "STEP 3: CAPTURING KIBANA URLS"

    source "$ENV_FILE"

    if [[ -z "$KIBANA_URL" ]]; then
        print_info "KIBANA_URL not configured, skipping URL generation"
        return 0
    fi

    print_step "Generating useful Kibana URLs"

    # Calculate time range (last 15 minutes)
    local now_ms=$(($(date +%s) * 1000))
    local fifteen_min_ago_ms=$((now_ms - 900000))

    # APM URL
    local apm_url="${KIBANA_URL}/app/apm/services/order-service/overview?rangeFrom=now-15m&rangeTo=now"

    # Service Map URL
    local service_map_url="${KIBANA_URL}/app/apm/service-map?rangeFrom=now-15m&rangeTo=now"

    # Alerts URL
    local alerts_url="${KIBANA_URL}/app/observability/alerts?rangeFrom=now-15m&rangeTo=now"

    # Logs URL
    local logs_url="${KIBANA_URL}/app/logs/stream?logPosition=(end:now,start:now-15m)&logFilter=(expression:'service.name:order-service',kind:kuery)"

    echo ""
    print_success "Kibana URLs ready"
    echo ""
    echo "  APM Service Overview:"
    echo "    ${apm_url}"
    echo ""
    echo "  Service Map:"
    echo "    ${service_map_url}"
    echo ""
    echo "  Alerts:"
    echo "    ${alerts_url}"
    echo ""
    echo "  Logs:"
    echo "    ${logs_url}"
    echo ""
}

print_demo_summary() {
    print_section "DEMO SUMMARY"

    local now
    now=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

    echo "Timeline:"
    echo "  Demo Started:        ${DEMO_START_TIME}"
    echo "  Deployment:          ${DEPLOY_TIME}"
    if [[ -n "$ALERT_TIME" ]]; then
        echo "  Alert Detected:      ${ALERT_TIME}"
    fi
    echo "  Current Time:        ${now}"
    echo ""

    echo "Service Status:"
    echo "  Order Service:       ${ORDER_SERVICE_URL}"
    echo "  Current Version:     v1.1-bad"
    echo "  Expected Latency:    ~2000ms (due to bug)"
    echo ""

    echo "What to demonstrate in Kibana:"
    echo "  1. APM Service Overview - observe latency spike"
    echo "  2. Trace Timeline - find the 'detailed-trace-logging' span"
    echo "  3. Span Attributes - see Jordan Rivera's metadata"
    echo "  4. Log Correlation - trace ID in logs"
    echo "  5. Deployment Annotation - vertical line on charts"
    if [[ -n "$WEBHOOK_PUBLIC_URL" ]]; then
        echo "  6. Alert Rule - check if SLO burn rate fired"
        echo "  7. Workflow Execution - automated rollback"
    fi
    echo ""

    print_success "Demo environment ready!"
    echo ""
    echo -e "${YELLOW}NEXT STEPS:${NC}"
    echo "  1. Open Kibana and show the latency spike"
    echo "  2. Click into a slow trace to find the bug"
    echo "  3. Show Jordan's span attributes (author, commit, PR)"
    echo ""
    if [[ "$WAIT_FOR_ALERT" != "true" ]]; then
        echo -e "${YELLOW}TIP:${NC} Run with --wait-for-alert to see simulated alert detection"
    fi
    echo ""
}

cleanup() {
    echo ""
    print_info "Demo mode stopped"

    # Stop background traffic if we started it
    if [[ "$SKIP_TRAFFIC" != "true" ]]; then
        pkill -f "load-generator.sh" 2>/dev/null || true
        print_info "Background traffic stopped"
    fi

    exit 0
}

# =============================================================================
# Main
# =============================================================================

main() {
    # Record start time
    DEMO_START_TIME=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

    # Set up signal handler
    trap cleanup SIGINT SIGTERM

    # Parse arguments
    WAIT_FOR_ALERT=false
    SKIP_TRAFFIC=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --wait-for-alert)
                WAIT_FOR_ALERT=true
                shift
                ;;
            --skip-traffic)
                SKIP_TRAFFIC=true
                shift
                ;;
            --threshold)
                LATENCY_THRESHOLD=$2
                shift 2
                ;;
            --max-wait)
                MAX_WAIT_FOR_ALERT=$2
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

    # Execute demo steps
    print_banner
    check_prerequisites
    measure_baseline_latency
    start_background_traffic
    deploy_bad_code
    wait_for_high_latency
    capture_kibana_urls
    print_demo_summary
}

main "$@"

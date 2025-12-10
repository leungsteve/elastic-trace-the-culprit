#!/usr/bin/env bash
# =============================================================================
# workshop-test.sh - Workshop Flow Test Script
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Automated test script that walks through the full workshop flow:
# 1. Health check all services
# 2. Verify baseline latency is healthy (<100ms)
# 3. Deploy v1.1-bad
# 4. Verify latency increases (>2000ms)
# 5. Trigger rollback (either via webhook or manual)
# 6. Verify recovery (<100ms)
# 7. Report pass/fail for each step
#
# Usage: ./workshop-test.sh [--skip-baseline] [--manual-rollback]
# Example: ./workshop-test.sh

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
INFRA_DIR="${PROJECT_ROOT}/infra"
ENV_FILE="${INFRA_DIR}/.env"

# Test configuration
ORDER_SERVICE_URL="${ORDER_SERVICE_URL:-http://localhost:8088}"
BASELINE_LATENCY_THRESHOLD=500  # ms - should be well below this
BAD_LATENCY_THRESHOLD=1500      # ms - should be well above this after v1.1-bad
RECOVERY_LATENCY_THRESHOLD=500  # ms - should return below this after rollback
NUM_TEST_REQUESTS=10            # Number of requests to average for latency check
ROLLBACK_WAIT_TIME=120          # seconds to wait for automated rollback
RECOVERY_WAIT_TIME=60           # seconds to wait for recovery after rollback

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Flags
SKIP_BASELINE=false
MANUAL_ROLLBACK=false

# =============================================================================
# Helper Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "================================================================================"
    echo "  WORKSHOP FLOW TEST"
    echo "  From Commit to Culprit: An Observability Mystery"
    echo "================================================================================"
    echo -e "${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
    ((TOTAL_TESTS++))
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Test Functions
# =============================================================================

# Measure average latency by sending multiple requests
measure_latency() {
    local num_requests=${1:-$NUM_TEST_REQUESTS}
    local total_time=0
    local successful_requests=0

    print_info "Measuring latency over ${num_requests} requests..."

    for ((i=1; i<=num_requests; i++)); do
        local start_time=$(date +%s%3N)

        # Send a test order
        local response
        response=$(curl -s -w "\n%{http_code}" \
            -X POST "${ORDER_SERVICE_URL}/api/orders" \
            -H "Content-Type: application/json" \
            -d '{
                "customer_id": "TEST-CUST-001",
                "items": [
                    {
                        "product_id": "WIDGET-001",
                        "quantity": 1,
                        "price": 29.99
                    }
                ]
            }' 2>/dev/null || echo -e "\n000")

        local http_code=$(echo "$response" | tail -n1)
        local end_time=$(date +%s%3N)

        if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
            local duration=$((end_time - start_time))
            total_time=$((total_time + duration))
            ((successful_requests++))
            echo -n "."
        else
            echo -n "x"
        fi

        # Small delay between requests
        sleep 0.2
    done

    echo ""

    if [[ $successful_requests -eq 0 ]]; then
        echo "-1"
        return 1
    fi

    local avg_latency=$((total_time / successful_requests))
    echo "$avg_latency"
}

# Get current service version from .env file
get_current_version() {
    if [[ -f "$ENV_FILE" ]]; then
        grep "^ORDER_SERVICE_VERSION=" "$ENV_FILE" | cut -d'=' -f2
    else
        echo "unknown"
    fi
}

# Check if a service is healthy
check_service_health() {
    local service_name=$1
    local health_url=$2

    local response
    response=$(curl -s -w "\n%{http_code}" -m 5 "${health_url}" 2>/dev/null || echo -e "\n000")
    local http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" ]]; then
        return 0
    else
        return 1
    fi
}

# =============================================================================
# Test Steps
# =============================================================================

# Challenge 1: Setup and Baseline
test_step_1_health_checks() {
    print_section "Challenge 1: Setup and Baseline"

    print_step "Checking all services are healthy"

    # Test order-service
    print_test "Order Service health check"
    if check_service_health "order-service" "${ORDER_SERVICE_URL}/api/orders/health"; then
        print_pass "Order Service is healthy"
    else
        print_fail "Order Service is not responding"
        return 1
    fi

    # Test inventory-service
    print_test "Inventory Service health check"
    if check_service_health "inventory-service" "http://localhost:8081/health"; then
        print_pass "Inventory Service is healthy"
    else
        print_fail "Inventory Service is not responding"
        return 1
    fi

    # Test payment-service
    print_test "Payment Service health check"
    if check_service_health "payment-service" "http://localhost:8082/health"; then
        print_pass "Payment Service is healthy"
    else
        print_fail "Payment Service is not responding"
        return 1
    fi

    # Test rollback-webhook
    print_test "Rollback Webhook health check"
    if check_service_health "rollback-webhook" "http://localhost:9000/health"; then
        print_pass "Rollback Webhook is healthy"
    else
        print_warn "Rollback Webhook is not responding (may affect automated rollback test)"
    fi

    # Test OTEL collector
    print_test "OTEL Collector health check"
    if check_service_health "otel-collector" "http://localhost:13133"; then
        print_pass "OTEL Collector is healthy"
    else
        print_warn "OTEL Collector is not responding (telemetry may not be sent)"
    fi

    return 0
}

test_step_2_baseline_latency() {
    if [[ "$SKIP_BASELINE" == true ]]; then
        print_info "Skipping baseline latency check (--skip-baseline flag)"
        return 0
    fi

    print_step "Verifying baseline latency is healthy"

    # Check current version
    local current_version
    current_version=$(get_current_version)
    print_info "Current order-service version: ${current_version}"

    if [[ "$current_version" != "v1.0" ]]; then
        print_warn "Expected version v1.0, found ${current_version}. Ensure v1.0 is deployed for baseline."
    fi

    # Measure latency
    print_test "Baseline latency measurement (target: <${BASELINE_LATENCY_THRESHOLD}ms)"
    local avg_latency
    avg_latency=$(measure_latency)

    if [[ "$avg_latency" == "-1" ]]; then
        print_fail "Could not measure latency (all requests failed)"
        return 1
    fi

    print_info "Average latency: ${avg_latency}ms"

    if [[ $avg_latency -lt $BASELINE_LATENCY_THRESHOLD ]]; then
        print_pass "Baseline latency is healthy (${avg_latency}ms < ${BASELINE_LATENCY_THRESHOLD}ms)"
    else
        print_fail "Baseline latency is too high (${avg_latency}ms >= ${BASELINE_LATENCY_THRESHOLD}ms)"
        return 1
    fi

    return 0
}

# Challenge 2: Deploy and Detect
test_step_3_deploy_bad_version() {
    print_section "Challenge 2: Deploy and Detect"

    print_step "Deploying v1.1-bad to order-service"

    print_test "Execute deployment of v1.1-bad"

    cd "$SCRIPT_DIR"
    if ./deploy.sh order-service v1.1-bad > /dev/null 2>&1; then
        print_pass "Deployment script executed successfully"
    else
        print_fail "Deployment script failed"
        return 1
    fi

    # Verify version was updated
    local new_version
    new_version=$(get_current_version)

    print_test "Verify version updated to v1.1-bad"
    if [[ "$new_version" == "v1.1-bad" ]]; then
        print_pass "Version updated to v1.1-bad"
    else
        print_fail "Version not updated correctly (found: ${new_version})"
        return 1
    fi

    # Wait for service to restart
    print_info "Waiting for service to restart and stabilize (30 seconds)..."
    sleep 30

    return 0
}

test_step_4_verify_degradation() {
    print_step "Verifying latency degradation"

    print_test "Latency after v1.1-bad deployment (target: >${BAD_LATENCY_THRESHOLD}ms)"

    local avg_latency
    avg_latency=$(measure_latency)

    if [[ "$avg_latency" == "-1" ]]; then
        print_fail "Could not measure latency (all requests failed)"
        return 1
    fi

    print_info "Average latency: ${avg_latency}ms"

    if [[ $avg_latency -gt $BAD_LATENCY_THRESHOLD ]]; then
        print_pass "Latency degraded as expected (${avg_latency}ms > ${BAD_LATENCY_THRESHOLD}ms)"
    else
        print_fail "Latency did not degrade sufficiently (${avg_latency}ms <= ${BAD_LATENCY_THRESHOLD}ms)"
        print_warn "The bad version may not be exhibiting the expected behavior"
        return 1
    fi

    return 0
}

# Challenge 3: Investigate and Remediate
test_step_5_rollback() {
    print_section "Challenge 3: Investigate and Remediate"

    if [[ "$MANUAL_ROLLBACK" == true ]]; then
        print_step "Executing manual rollback"

        print_test "Manual rollback to v1.0"
        cd "$SCRIPT_DIR"
        if ./rollback.sh order-service > /dev/null 2>&1; then
            print_pass "Manual rollback executed successfully"
        else
            print_fail "Manual rollback script failed"
            return 1
        fi

        # Wait for service to restart
        print_info "Waiting for service to restart (30 seconds)..."
        sleep 30
    else
        print_step "Waiting for automated rollback"

        print_info "Monitoring for automated rollback (timeout: ${ROLLBACK_WAIT_TIME}s)..."
        print_info "The Elastic Workflow should trigger a rollback when SLO burn rate exceeds threshold"

        local waited=0
        local rollback_detected=false

        while [[ $waited -lt $ROLLBACK_WAIT_TIME ]]; do
            local current_version
            current_version=$(get_current_version)

            if [[ "$current_version" == "v1.0" ]]; then
                print_pass "Automated rollback detected after ${waited} seconds"
                rollback_detected=true
                break
            fi

            echo -n "."
            sleep 5
            waited=$((waited + 5))
        done

        echo ""

        if [[ "$rollback_detected" == false ]]; then
            print_warn "Automated rollback not detected within ${ROLLBACK_WAIT_TIME}s"
            print_info "This may be due to:"
            print_info "  - Webhook not configured or not accessible"
            print_info "  - Alert rule not firing"
            print_info "  - Workflow not configured correctly"
            print_info "Proceeding with manual rollback for testing purposes..."

            cd "$SCRIPT_DIR"
            if ./rollback.sh order-service > /dev/null 2>&1; then
                print_info "Manual rollback executed successfully"
            else
                print_fail "Manual rollback also failed"
                return 1
            fi

            sleep 30
        fi
    fi

    # Verify rollback
    print_test "Verify service rolled back to v1.0"
    local final_version
    final_version=$(get_current_version)

    if [[ "$final_version" == "v1.0" ]]; then
        print_pass "Service successfully rolled back to v1.0"
    else
        print_fail "Service not on v1.0 (found: ${final_version})"
        return 1
    fi

    return 0
}

test_step_6_verify_recovery() {
    print_step "Verifying system recovery"

    print_info "Waiting for system to stabilize after rollback (${RECOVERY_WAIT_TIME}s)..."
    sleep "$RECOVERY_WAIT_TIME"

    print_test "Latency after recovery (target: <${RECOVERY_LATENCY_THRESHOLD}ms)"

    local avg_latency
    avg_latency=$(measure_latency)

    if [[ "$avg_latency" == "-1" ]]; then
        print_fail "Could not measure latency (all requests failed)"
        return 1
    fi

    print_info "Average latency: ${avg_latency}ms"

    if [[ $avg_latency -lt $RECOVERY_LATENCY_THRESHOLD ]]; then
        print_pass "System recovered successfully (${avg_latency}ms < ${RECOVERY_LATENCY_THRESHOLD}ms)"
    else
        print_fail "System did not fully recover (${avg_latency}ms >= ${RECOVERY_LATENCY_THRESHOLD}ms)"
        return 1
    fi

    return 0
}

# Challenge 4: Learn and Prevent
test_step_7_final_checks() {
    print_section "Challenge 4: Learn and Prevent"

    print_step "Running final validation checks"

    # Verify all services still healthy
    print_test "All services healthy after full test cycle"

    local all_healthy=true

    if ! check_service_health "order-service" "${ORDER_SERVICE_URL}/api/orders/health"; then
        print_error "Order Service not healthy"
        all_healthy=false
    fi

    if ! check_service_health "inventory-service" "http://localhost:8081/health"; then
        print_error "Inventory Service not healthy"
        all_healthy=false
    fi

    if ! check_service_health "payment-service" "http://localhost:8082/health"; then
        print_error "Payment Service not healthy"
        all_healthy=false
    fi

    if [[ "$all_healthy" == true ]]; then
        print_pass "All services are healthy"
    else
        print_fail "Some services are not healthy"
        return 1
    fi

    # Verify we're back on v1.0
    print_test "Confirm final state is v1.0"
    local final_version
    final_version=$(get_current_version)

    if [[ "$final_version" == "v1.0" ]]; then
        print_pass "System is on stable version v1.0"
    else
        print_fail "System is not on v1.0 (found: ${final_version})"
        return 1
    fi

    return 0
}

# =============================================================================
# Summary and Reporting
# =============================================================================

print_summary() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}  TEST SUMMARY${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
    echo -e "  Total Tests:      ${TOTAL_TESTS}"
    echo -e "  ${GREEN}Passed:           ${PASSED_TESTS}${NC}"
    echo -e "  ${RED}Failed:           ${FAILED_TESTS}${NC}"
    echo -e "  ${YELLOW}Warnings:         ${WARNINGS}${NC}"
    echo ""

    local success_rate=0
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    fi
    echo -e "  Success Rate:     ${success_rate}%"
    echo ""

    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ ALL TESTS PASSED${NC}"
        echo ""
        echo -e "${GREEN}  The workshop flow is working correctly!${NC}"
        echo -e "${GREEN}  Participants should be able to complete all challenges successfully.${NC}"
    else
        echo -e "${RED}${BOLD}  ✗ SOME TESTS FAILED${NC}"
        echo ""
        echo -e "${RED}  The workshop flow has issues that need to be addressed.${NC}"
        echo -e "${RED}  Review the failed tests above and fix the issues.${NC}"
    fi

    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

# =============================================================================
# Usage and Argument Parsing
# =============================================================================

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Automated test script for the complete workshop flow."
    echo ""
    echo "Options:"
    echo "  --skip-baseline       Skip baseline latency verification"
    echo "  --manual-rollback     Use manual rollback instead of waiting for automated"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run full test with automated rollback"
    echo "  $0 --manual-rollback    # Run test with manual rollback trigger"
    echo "  $0 --skip-baseline      # Skip baseline check (faster for repeated testing)"
    echo ""
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-baseline)
            SKIP_BASELINE=true
            shift
            ;;
        --manual-rollback)
            MANUAL_ROLLBACK=true
            shift
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

# =============================================================================
# Main Execution
# =============================================================================

main() {
    print_banner

    print_info "Starting workshop flow test..."
    print_info "This will test the complete participant journey:"
    print_info "  1. Health checks and baseline latency"
    print_info "  2. Deploy bad version (v1.1-bad)"
    print_info "  3. Verify degradation"
    print_info "  4. Trigger rollback"
    print_info "  5. Verify recovery"
    print_info "  6. Final validation"
    echo ""

    if [[ "$MANUAL_ROLLBACK" == true ]]; then
        print_info "Using manual rollback mode"
    else
        print_info "Will wait for automated rollback (${ROLLBACK_WAIT_TIME}s timeout)"
    fi
    echo ""

    # Challenge 1: Setup and Baseline
    test_step_1_health_checks || true
    test_step_2_baseline_latency || true

    # Challenge 2: Deploy and Detect
    test_step_3_deploy_bad_version || true
    test_step_4_verify_degradation || true

    # Challenge 3: Investigate and Remediate
    test_step_5_rollback || true
    test_step_6_verify_recovery || true

    # Challenge 4: Learn and Prevent
    test_step_7_final_checks || true

    # Print summary
    print_summary

    # Exit with appropriate code
    if [[ $FAILED_TESTS -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

main "$@"

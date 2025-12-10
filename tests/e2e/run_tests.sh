#!/usr/bin/env bash
# =============================================================================
# run_tests.sh - E2E Test Runner
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Convenience script to run E2E tests with proper setup and cleanup.
#
# Usage: ./run_tests.sh [OPTIONS]
# Example: ./run_tests.sh --verify --test-all

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/../.."
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"
INFRA_DIR="${PROJECT_ROOT}/infra"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Flags
VERIFY_SERVICES=false
CLEANUP_AFTER=false
TEST_TARGET="all"

# =============================================================================
# Helper Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "================================================================================"
    echo "  E2E TEST RUNNER"
    echo "  From Commit to Culprit: An Observability Mystery"
    echo "================================================================================"
    echo -e "${NC}"
}

print_section() {
    echo ""
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --verify              Verify services are healthy before running tests"
    echo "  --cleanup             Clean up test artifacts after running"
    echo "  --test-all            Run all E2E tests (default)"
    echo "  --test-scenario       Run workshop scenario tests only"
    echo "  --test-webhook        Run webhook tests only"
    echo "  --test-fast           Run fast tests only (skip slow tests)"
    echo "  --verbose             Run tests with verbose output"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Run all tests"
    echo "  $0 --verify --test-all          # Verify services then run all tests"
    echo "  $0 --test-fast --cleanup        # Run fast tests and cleanup after"
    echo "  $0 --test-scenario --verbose    # Run scenario tests with verbose output"
    echo ""
    exit 0
}

# =============================================================================
# Verification Functions
# =============================================================================

verify_services() {
    print_section "Verifying Services"

    if [[ ! -f "${SCRIPTS_DIR}/health-check.sh" ]]; then
        print_error "health-check.sh not found. Please ensure you're running from the correct directory."
        exit 1
    fi

    print_info "Running health checks..."
    if "${SCRIPTS_DIR}/health-check.sh"; then
        print_success "All services are healthy"
    else
        print_error "Some services are not healthy. Please fix issues before running tests."
        exit 1
    fi
}

check_dependencies() {
    print_section "Checking Dependencies"

    # Check for pytest
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Install with: pip install -r requirements.txt"
        exit 1
    fi

    print_success "pytest found: $(pytest --version)"

    # Check for required Python packages
    if ! python3 -c "import httpx" &> /dev/null; then
        print_error "httpx not found. Install with: pip install -r requirements.txt"
        exit 1
    fi

    print_success "httpx found"

    if ! python3 -c "import pytest_asyncio" &> /dev/null; then
        print_error "pytest-asyncio not found. Install with: pip install -r requirements.txt"
        exit 1
    fi

    print_success "pytest-asyncio found"
}

# =============================================================================
# Test Execution Functions
# =============================================================================

run_tests() {
    print_section "Running E2E Tests"

    cd "$SCRIPT_DIR"

    local pytest_args="-v"

    # Add verbose flag if requested
    if [[ "$VERBOSE" == true ]]; then
        pytest_args="${pytest_args}v -s"
    fi

    # Determine test target
    case $TEST_TARGET in
        all)
            print_info "Running all E2E tests..."
            pytest $pytest_args
            ;;
        scenario)
            print_info "Running workshop scenario tests..."
            pytest $pytest_args test_workshop_scenario.py
            ;;
        webhook)
            print_info "Running webhook tests..."
            pytest $pytest_args test_rollback_webhook.py
            ;;
        fast)
            print_info "Running fast tests (skipping slow tests)..."
            pytest $pytest_args -m "not slow"
            ;;
        *)
            print_error "Unknown test target: $TEST_TARGET"
            exit 1
            ;;
    esac

    if [[ $? -eq 0 ]]; then
        print_success "Tests passed!"
        return 0
    else
        print_error "Tests failed!"
        return 1
    fi
}

cleanup() {
    print_section "Cleanup"

    print_info "Removing test artifacts..."
    cd "$SCRIPT_DIR"
    rm -f e2e_tests.log
    rm -rf .pytest_cache
    rm -rf __pycache__

    print_success "Cleanup complete"
}

# =============================================================================
# Argument Parsing
# =============================================================================

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verify)
            VERIFY_SERVICES=true
            shift
            ;;
        --cleanup)
            CLEANUP_AFTER=true
            shift
            ;;
        --test-all)
            TEST_TARGET="all"
            shift
            ;;
        --test-scenario)
            TEST_TARGET="scenario"
            shift
            ;;
        --test-webhook)
            TEST_TARGET="webhook"
            shift
            ;;
        --test-fast)
            TEST_TARGET="fast"
            shift
            ;;
        --verbose)
            VERBOSE=true
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

    # Check dependencies
    check_dependencies

    # Verify services if requested
    if [[ "$VERIFY_SERVICES" == true ]]; then
        verify_services
    fi

    # Run tests
    local test_result=0
    run_tests || test_result=$?

    # Cleanup if requested
    if [[ "$CLEANUP_AFTER" == true ]]; then
        cleanup
    fi

    # Print final result
    echo ""
    if [[ $test_result -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}✓ E2E Tests Completed Successfully${NC}"
    else
        echo -e "${RED}${BOLD}✗ E2E Tests Failed${NC}"
    fi
    echo ""

    exit $test_result
}

main "$@"

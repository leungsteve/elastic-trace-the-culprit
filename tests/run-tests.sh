#!/bin/bash

# Test runner script for From Commit to Culprit workshop
# This script runs all unit tests for all services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     From Commit to Culprit - Workshop Test Runner             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW} $1${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Parse command line arguments
RUN_JAVA=true
RUN_PYTHON=true
VERBOSE=false
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --java-only)
            RUN_PYTHON=false
            shift
            ;;
        --python-only)
            RUN_JAVA=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --java-only       Run only Java tests"
            echo "  --python-only     Run only Python tests"
            echo "  --verbose, -v     Run tests with verbose output"
            echo "  --coverage, -c    Generate coverage reports"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Run all tests"
            echo "  $0 --java-only        # Run only Java tests"
            echo "  $0 --coverage         # Run all tests with coverage"
            echo "  $0 --python-only -v   # Run Python tests verbosely"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Track overall success
OVERALL_SUCCESS=true

# Run Java tests (Order Service)
if [ "$RUN_JAVA" = true ]; then
    print_section "Running Order Service Tests (Java/JUnit)"

    if [ -d "$PROJECT_ROOT/services/order-service" ]; then
        cd "$PROJECT_ROOT/services/order-service"

        if [ "$COVERAGE" = true ]; then
            if mvn test jacoco:report; then
                print_success "Order Service tests passed with coverage"
                echo "Coverage report: services/order-service/target/site/jacoco/index.html"
            else
                print_error "Order Service tests failed"
                OVERALL_SUCCESS=false
            fi
        else
            if [ "$VERBOSE" = true ]; then
                if mvn test; then
                    print_success "Order Service tests passed"
                else
                    print_error "Order Service tests failed"
                    OVERALL_SUCCESS=false
                fi
            else
                if mvn test -q; then
                    print_success "Order Service tests passed"
                else
                    print_error "Order Service tests failed"
                    OVERALL_SUCCESS=false
                fi
            fi
        fi
    else
        print_error "Order Service directory not found"
        OVERALL_SUCCESS=false
    fi
fi

# Run Python tests
if [ "$RUN_PYTHON" = true ]; then
    print_section "Running Python Service Tests (pytest)"

    if [ -d "$PROJECT_ROOT/tests/unit" ]; then
        cd "$PROJECT_ROOT/tests/unit"

        # Build pytest command
        PYTEST_CMD="pytest"

        if [ "$VERBOSE" = true ]; then
            PYTEST_CMD="$PYTEST_CMD -v"
        fi

        if [ "$COVERAGE" = true ]; then
            PYTEST_CMD="$PYTEST_CMD --cov=inventory --cov=payment --cov=webhook --cov-report=html --cov-report=term"
        fi

        # Run inventory service tests
        echo "Testing Inventory Service..."
        if $PYTEST_CMD inventory-service/; then
            print_success "Inventory Service tests passed"
        else
            print_error "Inventory Service tests failed"
            OVERALL_SUCCESS=false
        fi

        # Run payment service tests
        echo ""
        echo "Testing Payment Service..."
        if $PYTEST_CMD payment-service/; then
            print_success "Payment Service tests passed"
        else
            print_error "Payment Service tests failed"
            OVERALL_SUCCESS=false
        fi

        # Run rollback webhook tests
        echo ""
        echo "Testing Rollback Webhook Service..."
        if $PYTEST_CMD rollback-webhook/; then
            print_success "Rollback Webhook tests passed"
        else
            print_error "Rollback Webhook tests failed"
            OVERALL_SUCCESS=false
        fi

        if [ "$COVERAGE" = true ]; then
            echo ""
            print_success "Python coverage report: tests/unit/htmlcov/index.html"
        fi
    else
        print_error "Python tests directory not found"
        OVERALL_SUCCESS=false
    fi
fi

# Print final summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
if [ "$OVERALL_SUCCESS" = true ]; then
    echo -e "${GREEN}✓ All tests passed successfully!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    exit 1
fi

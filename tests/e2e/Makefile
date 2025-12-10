# Makefile for E2E Tests
# From Commit to Culprit Workshop
#
# Quick commands for running E2E tests with common configurations

.PHONY: help test test-all test-scenario test-webhook test-fast test-slow clean setup verify

# Default target
help:
	@echo "E2E Test Commands"
	@echo "================="
	@echo ""
	@echo "Setup & Verification:"
	@echo "  make setup          - Build images and start services"
	@echo "  make verify         - Verify all services are healthy"
	@echo ""
	@echo "Running Tests:"
	@echo "  make test           - Run all E2E tests"
	@echo "  make test-scenario  - Run workshop scenario tests only"
	@echo "  make test-webhook   - Run rollback webhook tests only"
	@echo "  make test-fast      - Run tests, skip slow ones"
	@echo "  make test-slow      - Run only slow tests"
	@echo ""
	@echo "Specific Test Classes:"
	@echo "  make test-baseline       - Test Challenge 1: Baseline"
	@echo "  make test-deploy-detect  - Test Challenge 2: Deploy & Detect"
	@echo "  make test-remediate      - Test Challenge 3: Remediate"
	@echo "  make test-learn          - Test Challenge 4: Learn & Prevent"
	@echo "  make test-complete-flow  - Test complete workshop flow (master test)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean test artifacts and logs"
	@echo "  make reset          - Reset to v1.0 (good version)"
	@echo ""

# Project paths
PROJECT_ROOT := ../..
SCRIPTS_DIR := $(PROJECT_ROOT)/scripts
INFRA_DIR := $(PROJECT_ROOT)/infra

# Setup commands
setup:
	@echo "Building images..."
	@cd $(PROJECT_ROOT) && ./scripts/build-images.sh
	@echo "Starting services..."
	@cd $(INFRA_DIR) && docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 30
	@cd $(PROJECT_ROOT) && ./scripts/health-check.sh

verify:
	@echo "Verifying service health..."
	@cd $(PROJECT_ROOT) && ./scripts/health-check.sh

# Main test targets
test: test-all

test-all:
	@echo "Running all E2E tests..."
	pytest -v

test-scenario:
	@echo "Running workshop scenario tests..."
	pytest test_workshop_scenario.py -v

test-webhook:
	@echo "Running rollback webhook tests..."
	pytest test_rollback_webhook.py -v

test-fast:
	@echo "Running fast tests (skipping slow tests)..."
	pytest -v -m "not slow"

test-slow:
	@echo "Running slow tests only..."
	pytest -v -m "slow"

# Specific challenge tests
test-baseline:
	@echo "Testing Challenge 1: Setup and Baseline..."
	pytest test_workshop_scenario.py::TestChallenge1Baseline -v

test-deploy-detect:
	@echo "Testing Challenge 2: Deploy and Detect..."
	pytest test_workshop_scenario.py::TestChallenge2DeployDetect -v

test-remediate:
	@echo "Testing Challenge 3: Investigate and Remediate..."
	pytest test_workshop_scenario.py::TestChallenge3InvestigateRemediate -v

test-learn:
	@echo "Testing Challenge 4: Learn and Prevent..."
	pytest test_workshop_scenario.py::TestChallenge4LearnPrevent -v

# Master E2E test
test-complete-flow:
	@echo "Running complete workshop flow test..."
	pytest test_workshop_scenario.py::TestWorkshopScenario::test_complete_workshop_flow -v -s

# Webhook-specific tests
test-webhook-health:
	@echo "Testing webhook health endpoints..."
	pytest test_rollback_webhook.py::TestRollbackWebhookHealth -v

test-webhook-functionality:
	@echo "Testing webhook rollback functionality..."
	pytest test_rollback_webhook.py::TestRollbackWebhookFunctionality -v

test-webhook-integration:
	@echo "Testing webhook integration scenarios..."
	pytest test_rollback_webhook.py::TestWebhookIntegrationScenarios -v

# Advanced test options
test-verbose:
	@echo "Running tests with verbose output..."
	pytest -vv -s

test-quiet:
	@echo "Running tests in quiet mode..."
	pytest -q

test-failfast:
	@echo "Running tests, stop on first failure..."
	pytest -v -x

test-lastfailed:
	@echo "Re-running only failed tests from last run..."
	pytest -v --lf

test-debug:
	@echo "Running tests with debug output..."
	pytest -vv -s --log-cli-level=DEBUG

# Cleanup commands
clean:
	@echo "Cleaning test artifacts..."
	@rm -f e2e_tests.log
	@rm -rf .pytest_cache
	@rm -rf __pycache__
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete"

reset:
	@echo "Resetting to v1.0 (good version)..."
	@cd $(PROJECT_ROOT) && ./scripts/rollback.sh order-service
	@echo "System reset to v1.0"

# Full reset (cleanup + reset services)
reset-all: clean reset
	@echo "Full reset complete"

# Run tests with coverage (requires pytest-cov)
test-coverage:
	@echo "Running tests with coverage report..."
	pytest -v --cov=. --cov-report=html --cov-report=term

# Run tests in parallel (requires pytest-xdist)
test-parallel:
	@echo "Running tests in parallel..."
	pytest -v -n auto

# Generate test report (requires pytest-html)
test-report:
	@echo "Running tests and generating HTML report..."
	pytest -v --html=report.html --self-contained-html

# Development convenience targets
dev-setup: setup verify
	@echo "Development environment ready!"

dev-test: clean test-fast
	@echo "Fast development tests complete!"

# CI/CD target
ci: clean setup verify test-all
	@echo "CI test suite complete!"

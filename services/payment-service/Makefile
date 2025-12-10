# Makefile for Payment Service
# From Commit to Culprit Workshop

.PHONY: help install install-dev test lint format run build clean docker-build docker-run

# Default target
help:
	@echo "Payment Service - Available targets:"
	@echo "  install       - Install production dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  lint          - Run linters (flake8, mypy)"
	@echo "  format        - Format code with black and isort"
	@echo "  run           - Run service locally with auto-reload"
	@echo "  build         - Build Docker image"
	@echo "  clean         - Remove build artifacts and cache"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container locally"

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=payment --cov-report=term-missing --cov-report=html

# Run linters
lint:
	flake8 src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Run service locally
run:
	./run-local.sh

# Build Docker image
docker-build:
	docker build -t payment-service:v1.0 .

# Run Docker container locally
docker-run: docker-build
	docker run -p 8082:8082 \
		-e OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318 \
		payment-service:v1.0

# Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

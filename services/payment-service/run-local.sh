#!/bin/bash
# Local development runner for Payment Service
# From Commit to Culprit Workshop

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Payment Service locally...${NC}"

# Set environment variables for local development
export SERVICE_NAME=payment-service
export SERVICE_VERSION=v1.0
export ENVIRONMENT=local
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=payment-service
export OTEL_RESOURCE_ATTRIBUTES=service.version=v1.0,deployment.environment=local

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Run with OpenTelemetry auto-instrumentation
echo -e "${GREEN}Payment Service starting on http://localhost:8082${NC}"
echo -e "${GREEN}API docs available at http://localhost:8082/api/docs${NC}"

opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    uvicorn payment.main:app \
    --host 0.0.0.0 \
    --port 8082 \
    --reload

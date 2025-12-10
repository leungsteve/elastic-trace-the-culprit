# Payment Service Dockerfile
# From Commit to Culprit Workshop
# Python 3.11 with FastAPI and EDOT Python auto-instrumentation

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV SERVICE_NAME=payment-service
ENV SERVICE_VERSION=v1.0
ENV OTEL_SERVICE_NAME=payment-service
ENV OTEL_RESOURCE_ATTRIBUTES=service.version=v1.0,deployment.environment=production

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Run with OpenTelemetry auto-instrumentation
CMD ["opentelemetry-instrument", \
     "--traces_exporter", "otlp", \
     "--metrics_exporter", "otlp", \
     "--logs_exporter", "otlp", \
     "--exporter_otlp_endpoint", "${OTEL_EXPORTER_OTLP_ENDPOINT}", \
     "uvicorn", "payment.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8082"]

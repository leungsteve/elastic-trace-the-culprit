# Inventory Service Dockerfile
# Python FastAPI microservice with EDOT auto-instrumentation
# Part of "From Commit to Culprit" workshop

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source code
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Set environment variables for OpenTelemetry
ENV OTEL_SERVICE_NAME=inventory-service
ENV OTEL_RESOURCE_ATTRIBUTES="service.name=inventory-service,service.version=1.0.0"
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_PYTHON_LOG_CORRELATION=true
ENV OTEL_PYTHON_LOG_LEVEL=info

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run with OpenTelemetry auto-instrumentation
CMD ["opentelemetry-instrument", \
     "--traces_exporter", "otlp", \
     "--metrics_exporter", "otlp", \
     "--logs_exporter", "otlp", \
     "uvicorn", "inventory.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8081"]

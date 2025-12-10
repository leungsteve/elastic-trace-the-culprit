# =============================================================================
# Rollback Webhook Service Dockerfile
# From Commit to Culprit Workshop
# =============================================================================
# SECURITY WARNING: This service requires access to the Docker socket to perform
# rollbacks via docker-compose. This is intentional for the workshop but should
# be carefully reviewed in production environments.
#
# The service will:
# 1. Receive webhook calls from Elastic Alerting
# 2. Modify .env files to change service versions
# 3. Execute docker-compose commands to restart services
# =============================================================================

FROM python:3.11-slim

# Install system dependencies and Docker CLI
# We need Docker CLI to run docker-compose commands for rollbacks
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN pip install --no-cache-dir poetry==1.7.1

WORKDIR /app

# Copy dependency files and source code
COPY pyproject.toml ./
COPY src/ ./src/

# Configure Poetry to not create virtual environments (we're in a container)
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN poetry install --only main

# Create directory for runtime data
RUN mkdir -p /app/data

# Expose webhook port
EXPOSE 9000

# Environment variables with defaults
ENV ENVIRONMENT=local \
    COMPOSE_FILE=/app/infra/docker-compose.yml \
    ENV_FILE=/app/infra/.env \
    WEBHOOK_PORT=9000 \
    LOG_LEVEL=info \
    OTEL_SERVICE_NAME=rollback-webhook \
    OTEL_RESOURCE_ATTRIBUTES="service.version=1.0.0,deployment.environment=local" \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Run with OpenTelemetry auto-instrumentation
# This wraps the FastAPI app with EDOT Python instrumentation
CMD ["sh", "-c", "opentelemetry-instrument uvicorn src.webhook.main:app --host 0.0.0.0 --port ${WEBHOOK_PORT} --log-level ${LOG_LEVEL}"]

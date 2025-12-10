"""
FastAPI application for the Rollback Webhook Service.

From Commit to Culprit Workshop - Rollback Webhook Service

This service receives webhook calls from Elastic Alerting and performs
automated rollbacks by modifying .env files and restarting services.

Endpoints:
- POST /rollback: Trigger a rollback (called by Elastic Alerting)
- GET /health: Health check
- GET /ready: Readiness check
- GET /status: Get last rollback status
- GET /: Root endpoint with service info

SECURITY NOTE: This service has access to the Docker socket and can modify
.env files and restart services. Use with appropriate access controls.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace

from .models import (
    HealthResponse,
    ReadyResponse,
    RollbackRequest,
    RollbackResponse,
    RollbackStatus,
    StatusResponse,
)
from .rollback import RollbackExecutor

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - trace_id=%(otelTraceID)s span_id=%(otelSpanID)s',
)

# Add trace context to logs
class TraceContextFilter(logging.Filter):
    """Add OpenTelemetry trace context to log records."""

    def filter(self, record):
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            record.otelTraceID = format(ctx.trace_id, "032x")
            record.otelSpanID = format(ctx.span_id, "016x")
        else:
            record.otelTraceID = "0" * 32
            record.otelSpanID = "0" * 16
        return True


# Add the filter to the root logger
logging.getLogger().addFilter(TraceContextFilter())

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Service metadata
SERVICE_NAME = "rollback-webhook"
SERVICE_VERSION = "1.0.0"
START_TIME = time.time()

# Global rollback executor (initialized in lifespan)
rollback_executor: RollbackExecutor = None


def print_startup_banner():
    """
    Print a startup banner showing service configuration.

    This helps workshop participants understand the service state.
    """
    banner = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                   ROLLBACK WEBHOOK SERVICE                                ║
║                   From Commit to Culprit Workshop                         ║
║                                                                           ║
╟───────────────────────────────────────────────────────────────────────────╢
║                                                                           ║
║  Service:     {SERVICE_NAME:<59} ║
║  Version:     {SERVICE_VERSION:<59} ║
║  Environment: {os.getenv('ENVIRONMENT', 'local'):<59} ║
║  Port:        {os.getenv('WEBHOOK_PORT', '9000'):<59} ║
║                                                                           ║
╟───────────────────────────────────────────────────────────────────────────╢
║                                                                           ║
║  Configuration:                                                           ║
║    Compose File:  {os.getenv('COMPOSE_FILE', '/app/infra/docker-compose.yml'):<55} ║
║    Env File:      {os.getenv('ENV_FILE', '/app/infra/.env'):<55} ║
║                                                                           ║
╟───────────────────────────────────────────────────────────────────────────╢
║                                                                           ║
║  Elastic Observability:                                                   ║
║    Endpoint:      {os.getenv('ELASTIC_ENDPOINT', 'Not configured'):<55} ║
║    API Key:       {'Configured' if os.getenv('ELASTIC_API_KEY') else 'Not configured':<55} ║
║                                                                           ║
╟───────────────────────────────────────────────────────────────────────────╢
║                                                                           ║
║  OpenTelemetry:                                                           ║
║    Service Name:  {os.getenv('OTEL_SERVICE_NAME', SERVICE_NAME):<55} ║
║    Protocol:      {os.getenv('OTEL_EXPORTER_OTLP_PROTOCOL', 'http/protobuf'):<55} ║
║                                                                           ║
╟───────────────────────────────────────────────────────────────────────────╢
║                                                                           ║
║  Security Notice:                                                         ║
║    This service has access to the Docker socket and can modify .env      ║
║    files and restart services. This is intentional for the workshop      ║
║    but requires careful security review in production.                   ║
║                                                                           ║
╟───────────────────────────────────────────────────────────────────────────╢
║                                                                           ║
║  Endpoints:                                                               ║
║    POST /rollback   - Trigger rollback (called by Elastic Alerting)      ║
║    GET  /health     - Health check                                       ║
║    GET  /ready      - Readiness check                                    ║
║    GET  /status     - Last rollback status                               ║
║    GET  /           - Service information                                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup/shutdown.

    This prints the startup banner and initializes the rollback executor.
    """
    # Startup
    print_startup_banner()

    # Initialize rollback executor
    global rollback_executor
    rollback_executor = RollbackExecutor(
        compose_file=os.getenv("COMPOSE_FILE", "/app/infra/docker-compose.yml"),
        env_file=os.getenv("ENV_FILE", "/app/infra/.env"),
    )

    # Validate environment on startup
    is_valid, error_msg = rollback_executor.validate_environment()
    if is_valid:
        logger.info("Rollback webhook service started successfully")
        logger.info("Environment validation: PASSED")
    else:
        logger.warning(f"Environment validation: FAILED - {error_msg}")
        logger.warning("Service will start but rollbacks may fail")

    yield

    # Shutdown
    logger.info("Rollback webhook service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Rollback Webhook Service",
    description="Automated rollback service for From Commit to Culprit workshop",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """
    Root endpoint with service information.

    Returns:
        Service metadata and available endpoints
    """
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "environment": os.getenv("ENVIRONMENT", "local"),
        "uptime_seconds": time.time() - START_TIME,
        "endpoints": {
            "POST /rollback": "Trigger a rollback",
            "GET /health": "Health check",
            "GET /ready": "Readiness check",
            "GET /status": "Last rollback status",
        },
        "documentation": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.

    This endpoint checks if the service is running and if Docker is available.
    Used by container orchestration for health monitoring.

    Returns:
        HealthResponse with health status
    """
    with tracer.start_as_current_span("health_check") as span:
        # Check if Docker is available
        docker_available = False
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=2,
            )
            docker_available = result.returncode == 0
        except Exception:
            pass

        span.set_attribute("health.docker_available", docker_available)

        return HealthResponse(
            status="healthy",
            version=SERVICE_VERSION,
            environment=os.getenv("ENVIRONMENT", "local"),
            docker_available=docker_available,
        )


@app.get("/ready", response_model=ReadyResponse)
async def ready():
    """
    Readiness check endpoint.

    This endpoint checks if the service is ready to handle rollback requests.
    It validates that Docker, .env file, and docker-compose.yml are accessible.

    Returns:
        ReadyResponse with readiness status and individual checks
    """
    with tracer.start_as_current_span("readiness_check") as span:
        checks = {
            "docker": False,
            "env_file": False,
            "compose_file": False,
        }

        # Check Docker
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=2,
            )
            checks["docker"] = result.returncode == 0
        except Exception:
            pass

        # Check env file
        env_file = os.getenv("ENV_FILE", "/app/infra/.env")
        checks["env_file"] = os.path.exists(env_file)

        # Check compose file
        compose_file = os.getenv("COMPOSE_FILE", "/app/infra/docker-compose.yml")
        checks["compose_file"] = os.path.exists(compose_file)

        all_ready = all(checks.values())

        span.set_attribute("readiness.status", all_ready)
        for check, status in checks.items():
            span.set_attribute(f"readiness.{check}", status)

        return ReadyResponse(
            ready=all_ready,
            checks=checks,
        )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get the status of the last rollback operation.

    This endpoint is useful for debugging and monitoring rollback operations.

    Returns:
        StatusResponse with last rollback details
    """
    with tracer.start_as_current_span("get_status") as span:
        uptime = time.time() - START_TIME

        if rollback_executor.last_rollback:
            span.set_attribute("status.has_last_rollback", True)
            span.set_attribute(
                "status.last_rollback_status",
                rollback_executor.last_rollback.status.value,
            )
        else:
            span.set_attribute("status.has_last_rollback", False)

        span.set_attribute("status.total_rollbacks", rollback_executor.total_rollbacks)

        return StatusResponse(
            last_rollback=rollback_executor.last_rollback,
            total_rollbacks=rollback_executor.total_rollbacks,
            service_uptime_seconds=uptime,
        )


@app.post("/rollback", response_model=RollbackResponse)
async def trigger_rollback(request: RollbackRequest):
    """
    Trigger a rollback operation.

    This endpoint is called by Elastic Alerting workflows when an SLO burn rate
    or latency threshold alert fires. It performs the following steps:

    1. Validates the environment
    2. Gets the current service version
    3. Updates the .env file with the target version
    4. Restarts the service using docker-compose

    All steps are instrumented with OpenTelemetry spans and correlated logs.

    Args:
        request: RollbackRequest with service and target version

    Returns:
        RollbackResponse with detailed rollback status

    Raises:
        HTTPException: If the rollback fails
    """
    with tracer.start_as_current_span("rollback_webhook") as span:
        span.set_attribute("webhook.service", request.service.value)
        span.set_attribute("webhook.target_version", request.target_version)
        span.set_attribute("webhook.alert_id", request.alert_id)
        span.set_attribute("webhook.reason", request.reason)

        logger.info(
            f"Received rollback request for {request.service.value} -> {request.target_version}",
            extra={
                "service": request.service.value,
                "target_version": request.target_version,
                "alert_id": request.alert_id,
                "alert_name": request.alert_name,
                "reason": request.reason,
            },
        )

        # Execute the rollback
        response = rollback_executor.execute_rollback(request)

        span.set_attribute("rollback.status", response.status.value)
        span.set_attribute("rollback.id", response.rollback_id)

        if response.status == RollbackStatus.ROLLBACK_FAILED:
            logger.error(
                f"Rollback failed: {response.error}",
                extra={
                    "rollback_id": response.rollback_id,
                    "service": response.service.value,
                    "error": response.error,
                },
            )
            # Still return the response (don't raise exception)
            # The caller can check the status field
        else:
            logger.info(
                f"Rollback completed successfully: {response.message}",
                extra={
                    "rollback_id": response.rollback_id,
                    "service": response.service.value,
                    "previous_version": response.previous_version,
                    "target_version": response.target_version,
                },
            )

        return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    This ensures all errors are logged with trace context and returned
    in a consistent format.

    Args:
        request: FastAPI request
        exc: Exception that was raised

    Returns:
        JSONResponse with error details
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        span.record_exception(exc)

    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    # This is for local development only
    # In production, use the Dockerfile CMD with opentelemetry-instrument
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("WEBHOOK_PORT", "9000")),
        log_level=LOG_LEVEL.lower(),
        reload=True,
    )

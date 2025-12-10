"""
Payment Service - Main Application
From Commit to Culprit Workshop

FastAPI application for payment processing with EDOT Python auto-instrumentation.
Simulates payment gateway interactions with realistic success/failure rates.
"""

import hashlib
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from opentelemetry import trace

from payment.models import (
    HealthResponse,
    PaymentMethod,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
)

# Configure logging with trace correlation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] "
    "%(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

# Environment configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "payment-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "v1.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

# In-memory payment storage (stateless, thread-safe)
# In production, this would be a database
payments_store: Dict[UUID, PaymentResponse] = {}

# Create FastAPI application
app = FastAPI(
    title="Payment Service",
    description="Payment processing service for NovaMart - From Commit to Culprit Workshop",
    version=SERVICE_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


def print_startup_banner() -> None:
    """Print startup banner with environment information."""
    banner = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                          PAYMENT SERVICE                                    ║
║                    From Commit to Culprit Workshop                         ║
╠════════════════════════════════════════════════════════════════════════════╣
║ Service:      {SERVICE_NAME:<60} ║
║ Version:      {SERVICE_VERSION:<60} ║
║ Environment:  {ENVIRONMENT:<60} ║
║ OTEL Endpoint: {OTEL_ENDPOINT:<57} ║
║ Python:       {sys.version.split()[0]:<60} ║
║ Status:       READY                                                        ║
╚════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    print_startup_banner()
    logger.info(
        f"Payment Service starting - version={SERVICE_VERSION}, environment={ENVIRONMENT}"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Payment Service shutting down")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with trace context."""
    request_id = str(uuid4())
    logger.info(
        f"Incoming request: method={request.method} path={request.url.path} "
        f"request_id={request_id}"
    )

    response = await call_next(request)

    logger.info(
        f"Request completed: method={request.method} path={request.url.path} "
        f"status={response.status_code} request_id={request_id}"
    )

    return response


def calculate_failure_probability(order_id: str) -> bool:
    """
    Deterministic random failure simulation based on order_id.

    Uses hash of order_id to determine if payment should fail.
    This provides reproducibility for testing while maintaining
    approximately 1% failure rate across different order IDs.

    Args:
        order_id: The order identifier

    Returns:
        True if payment should fail, False otherwise
    """
    # Create deterministic hash from order_id
    hash_value = int(hashlib.sha256(order_id.encode()).hexdigest(), 16)

    # 1% failure rate: fail if hash mod 100 equals 0
    should_fail = (hash_value % 100) == 0

    return should_fail


@app.post(
    "/api/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["payments"],
)
async def process_payment(payment_request: PaymentRequest) -> PaymentResponse:
    """
    Process a payment for an order.

    Simulates payment gateway interaction with:
    - 99% success rate (1% deterministic failures for realism)
    - Transaction ID generation
    - Payment processing latency simulation
    - Trace correlation for observability

    Args:
        payment_request: Payment details including order_id, amount, and method

    Returns:
        PaymentResponse with payment status and details

    Raises:
        HTTPException: If payment fails or validation errors occur
    """
    with tracer.start_as_current_span("process_payment") as span:
        span.set_attribute("payment.order_id", payment_request.order_id)
        span.set_attribute("payment.amount", float(payment_request.amount))
        span.set_attribute("payment.currency", payment_request.currency)
        span.set_attribute("payment.method", payment_request.payment_method.value)
        span.set_attribute("payment.customer_id", payment_request.customer_id)

        logger.info(
            f"Processing payment for order_id={payment_request.order_id} "
            f"amount={payment_request.amount} {payment_request.currency} "
            f"method={payment_request.payment_method.value}"
        )

        # Check for idempotency (prevent duplicate payments)
        if payment_request.idempotency_key:
            for payment in payments_store.values():
                if (
                    payment.order_id == payment_request.order_id
                    and payment.status == PaymentStatus.COMPLETED
                ):
                    logger.info(
                        f"Idempotent payment request detected for order_id={payment_request.order_id}"
                    )
                    span.set_attribute("payment.idempotent", True)
                    return payment

        # Simulate payment gateway interaction
        payment_id = uuid4()
        should_fail = calculate_failure_probability(payment_request.order_id)

        with tracer.start_as_current_span("payment_gateway_request") as gateway_span:
            gateway_span.set_attribute("gateway.provider", "mock_gateway")
            gateway_span.set_attribute("gateway.order_id", payment_request.order_id)

            if should_fail:
                # Simulate payment failure (1% of requests)
                gateway_span.set_attribute("gateway.result", "failed")
                logger.warning(
                    f"Payment gateway declined payment for order_id={payment_request.order_id}"
                )

                payment = PaymentResponse(
                    payment_id=payment_id,
                    order_id=payment_request.order_id,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    status=PaymentStatus.FAILED,
                    payment_method=payment_request.payment_method,
                    failure_reason="Payment declined by gateway - insufficient funds",
                )

                payments_store[payment_id] = payment
                span.set_attribute("payment.status", "failed")

                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "Payment declined",
                        "reason": payment.failure_reason,
                        "payment_id": str(payment_id),
                    },
                )
            else:
                # Successful payment (99% of requests)
                transaction_id = f"TXN-{payment_id.hex[:16].upper()}"
                gateway_span.set_attribute("gateway.result", "success")
                gateway_span.set_attribute("gateway.transaction_id", transaction_id)

                logger.info(
                    f"Payment gateway approved payment for order_id={payment_request.order_id} "
                    f"transaction_id={transaction_id}"
                )

                payment = PaymentResponse(
                    payment_id=payment_id,
                    order_id=payment_request.order_id,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    status=PaymentStatus.COMPLETED,
                    payment_method=payment_request.payment_method,
                    transaction_id=transaction_id,
                )

                payments_store[payment_id] = payment
                span.set_attribute("payment.status", "completed")
                span.set_attribute("payment.transaction_id", transaction_id)

                logger.info(
                    f"Payment processed successfully: payment_id={payment_id} "
                    f"order_id={payment_request.order_id} transaction_id={transaction_id}"
                )

                return payment


@app.get(
    "/api/payments/{payment_id}",
    response_model=PaymentResponse,
    tags=["payments"],
)
async def get_payment(payment_id: UUID) -> PaymentResponse:
    """
    Retrieve payment details by payment ID.

    Args:
        payment_id: The unique payment identifier

    Returns:
        PaymentResponse with payment details

    Raises:
        HTTPException: If payment not found
    """
    with tracer.start_as_current_span("get_payment") as span:
        span.set_attribute("payment.id", str(payment_id))

        logger.info(f"Retrieving payment: payment_id={payment_id}")

        payment = payments_store.get(payment_id)
        if not payment:
            logger.warning(f"Payment not found: payment_id={payment_id}")
            span.set_attribute("payment.found", False)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found",
            )

        span.set_attribute("payment.found", True)
        span.set_attribute("payment.status", payment.status.value)
        logger.info(f"Payment retrieved: payment_id={payment_id} status={payment.status.value}")

        return payment


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint for container orchestration.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        environment=ENVIRONMENT,
    )


@app.get("/ready", response_model=HealthResponse, tags=["health"])
async def readiness_check() -> HealthResponse:
    """
    Readiness check endpoint for container orchestration.

    Verifies that the service is ready to accept traffic.

    Returns:
        HealthResponse with service status
    """
    # In a real service, this would check dependencies (database, cache, etc.)
    # For this workshop, the service is always ready since it's stateless
    return HealthResponse(
        status="ready",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        environment=ENVIRONMENT,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for uncaught exceptions.

    Ensures all errors are logged with trace correlation.
    """
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "service": SERVICE_NAME,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "payment.main:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        log_level="info",
    )

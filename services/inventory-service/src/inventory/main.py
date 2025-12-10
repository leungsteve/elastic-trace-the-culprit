"""
Inventory Service - FastAPI Application
========================================

NovaMart's inventory management microservice for the
"From Commit to Culprit" Elastic Observability workshop.

This service handles:
- Stock availability checking
- Inventory reservation for orders
- Instrumented with EDOT (Elastic Distribution of OpenTelemetry)

Author: NovaMart Platform Team
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from inventory import __version__
from inventory.models import (
    StockCheckRequest,
    StockCheckResponse,
    ReservationRequest,
    ReservationResponse,
    HealthResponse,
    ReadinessResponse,
)
from inventory.data import (
    get_item,
    check_availability,
    reserve_items,
    get_inventory_summary,
)

# Configure logging with correlation support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)


def print_startup_banner():
    """
    Print a startup banner showing service configuration.
    Helps workshop participants verify their environment.
    """
    environment = os.getenv("ENVIRONMENT", "unknown")
    service_version = os.getenv("SERVICE_VERSION", __version__)
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "not configured")

    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                   INVENTORY SERVICE                          ║
║              NovaMart Stock Management System                ║
╠══════════════════════════════════════════════════════════════╣
║  Version:      {service_version:<45} ║
║  Environment:  {environment:<45} ║
║  Port:         8081                                          ║
╠══════════════════════════════════════════════════════════════╣
║  OpenTelemetry Configuration:                                ║
║  Endpoint:     {otel_endpoint:<45} ║
║  Service Name: inventory-service                             ║
╠══════════════════════════════════════════════════════════════╣
║  Workshop: From Commit to Culprit                            ║
║  Elastic Observability Training                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    logger.info("Inventory Service starting up")
    logger.info(f"Environment: {environment}")
    logger.info(f"Version: {service_version}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Prints startup banner and handles shutdown.
    """
    # Startup
    print_startup_banner()

    # Log initial inventory state
    summary = get_inventory_summary()
    logger.info(f"Inventory initialized with {summary['total_items']} items, "
                f"{summary['total_stock']} units, ${summary['total_value']:.2f} value")

    yield

    # Shutdown
    logger.info("Inventory Service shutting down")


# Create FastAPI application
app = FastAPI(
    title="Inventory Service",
    description="NovaMart inventory management microservice with EDOT instrumentation",
    version=__version__,
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all requests with trace context.
    The trace ID is automatically injected by EDOT instrumentation.
    """
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}")
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns basic service status - used by Docker HEALTHCHECK and Kubernetes liveness probes.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        service="inventory-service",
        version=__version__
    )


@app.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check endpoint.
    Verifies the service is ready to accept traffic.

    In a real service, this would check dependencies like databases,
    but for this workshop we keep it simple.

    Returns:
        ReadinessResponse with readiness status
    """
    # Check if inventory is loaded
    summary = get_inventory_summary()
    inventory_ready = summary["total_items"] > 0

    checks = {
        "inventory_loaded": inventory_ready,
        "service_initialized": True
    }

    ready = all(checks.values())

    return ReadinessResponse(
        ready=ready,
        service="inventory-service",
        checks=checks
    )


@app.post("/api/inventory/check", response_model=StockCheckResponse)
async def check_stock(request: StockCheckRequest):
    """
    Check stock availability for multiple items.

    This endpoint is called by the order service to verify items are in stock
    before accepting an order.

    Args:
        request: StockCheckRequest with list of items and quantities

    Returns:
        StockCheckResponse indicating availability of all items

    Example:
        POST /api/inventory/check
        {
            "items": [
                {"item_id": "WIDGET-001", "quantity": 5},
                {"item_id": "GADGET-042", "quantity": 2}
            ]
        }
    """
    logger.info(f"Stock check requested for {len(request.items)} items")

    item_results = []
    all_available = True

    for item in request.items:
        logger.info(f"Processing item: {item}")  # Debug logging
        item_id = item.get("item_id")
        quantity = item.get("quantity", 0)

        if not item_id:
            logger.warning(f"Stock check received item without item_id: {item}")
            raise HTTPException(status_code=400, detail="Each item must have an item_id")

        # Get item details
        inventory_item = get_item(item_id)
        if not inventory_item:
            logger.warning(f"Stock check for unknown item: {item_id}")
            item_results.append({
                "item_id": item_id,
                "requested": quantity,
                "available": 0,
                "in_stock": False,
                "error": "Item not found"
            })
            all_available = False
            continue

        # Check availability
        available, current_stock = check_availability(item_id, quantity)

        logger.debug(f"Stock check: {item_id} - requested: {quantity}, available: {current_stock}, in_stock: {available}")

        item_results.append({
            "item_id": item_id,
            "requested": quantity,
            "available": current_stock,
            "in_stock": available,
            "price": inventory_item["price"]
        })

        if not available:
            all_available = False

    message = "All items available" if all_available else "Some items unavailable"
    logger.info(f"Stock check complete: {message}")

    return StockCheckResponse(
        available=all_available,
        items=item_results,
        message=message
    )


@app.post("/api/inventory/reserve", response_model=ReservationResponse)
async def reserve_inventory(request: ReservationRequest):
    """
    Reserve inventory items for an order.

    This is an atomic operation - either all items are reserved or none.
    Called by the order service after payment is confirmed.

    Args:
        request: ReservationRequest with order_id and items

    Returns:
        ReservationResponse with reservation status

    Raises:
        HTTPException: If reservation fails (insufficient stock, etc.)

    Example:
        POST /api/inventory/reserve
        {
            "order_id": "ORD-12345",
            "items": [
                {"item_id": "WIDGET-001", "quantity": 5},
                {"item_id": "GADGET-042", "quantity": 2}
            ]
        }
    """
    logger.info(f"Reservation request for order: {request.order_id}")

    # Validate request
    if not request.items:
        logger.warning(f"Reservation request {request.order_id} has no items")
        raise HTTPException(status_code=400, detail="No items provided for reservation")

    # Attempt reservation (atomic operation)
    success, message, reserved_items = reserve_items(request.order_id, request.items)

    if not success:
        logger.warning(f"Reservation failed for order {request.order_id}: {message}")
        return ReservationResponse(
            success=False,
            order_id=request.order_id,
            reservation_id=None,
            items_reserved=[],
            message=message
        )

    # Generate reservation ID
    reservation_id = f"RES-{request.order_id}"

    logger.info(f"Reservation successful for order {request.order_id}: {reservation_id}")

    return ReservationResponse(
        success=True,
        order_id=request.order_id,
        reservation_id=reservation_id,
        items_reserved=reserved_items,
        message=message
    )


@app.get("/api/inventory/summary")
async def inventory_summary() -> Dict:
    """
    Get current inventory summary.

    This is a diagnostic endpoint useful for workshop participants
    to verify inventory state.

    Returns:
        Dict with inventory statistics and current stock levels
    """
    logger.debug("Inventory summary requested")
    summary = get_inventory_summary()
    return summary


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler to ensure exceptions are logged with trace context.
    """
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unexpected errors.
    Ensures all errors are logged with trace context.
    """
    logger.exception(f"Unexpected error processing request: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "inventory.main:app",
        host="0.0.0.0",
        port=8081,
        reload=True
    )

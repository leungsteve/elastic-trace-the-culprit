"""
Pytest Configuration and Shared Fixtures for Telemetry Tests
From Commit to Culprit Workshop

Provides fixtures for HTTP clients, mock OTEL receivers, and test data.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# Service URLs - can be overridden via environment variables
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8088")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8081")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8082")
OTEL_COLLECTOR_URL = os.getenv("OTEL_COLLECTOR_URL", "http://localhost:4318")
OTEL_COLLECTOR_GRPC_URL = os.getenv("OTEL_COLLECTOR_GRPC_URL", "http://localhost:4317")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client():
    """Provide an async HTTP client for making requests to services."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def order_service_url() -> str:
    """URL for the order service."""
    return ORDER_SERVICE_URL


@pytest.fixture
def inventory_service_url() -> str:
    """URL for the inventory service."""
    return INVENTORY_SERVICE_URL


@pytest.fixture
def payment_service_url() -> str:
    """URL for the payment service."""
    return PAYMENT_SERVICE_URL


@pytest.fixture
def otel_collector_url() -> str:
    """URL for the OTEL collector HTTP endpoint."""
    return OTEL_COLLECTOR_URL


@pytest.fixture
def sample_order_request() -> Dict[str, Any]:
    """
    Sample order request payload for testing.

    Uses a deterministic order_id to avoid payment failures in tests.
    """
    return {
        "customer_id": "test-customer-123",
        "items": [
            {
                "product_id": "LAPTOP-001",
                "quantity": 1,
                "price": 999.99
            },
            {
                "product_id": "MOUSE-002",
                "quantity": 2,
                "price": 24.99
            }
        ]
    }


@pytest.fixture
def w3c_traceparent() -> str:
    """
    Generate a valid W3C traceparent header for testing trace propagation.

    Format: version-trace_id-parent_id-trace_flags
    Example: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
    """
    trace_id = "0af7651916cd43dd8448eb211c80319c"
    parent_id = "b7ad6b7169203331"
    trace_flags = "01"  # sampled
    return f"00-{trace_id}-{parent_id}-{trace_flags}"


@pytest.fixture
def mock_otel_receiver():
    """
    Mock OTEL receiver that collects telemetry data.

    Simulates the OTEL collector's behavior for testing without
    requiring a full Elastic backend.
    """
    receiver = {
        "traces": [],
        "metrics": [],
        "logs": [],
    }

    def add_trace(trace_data: Dict[str, Any]):
        receiver["traces"].append(trace_data)

    def add_metric(metric_data: Dict[str, Any]):
        receiver["metrics"].append(metric_data)

    def add_log(log_data: Dict[str, Any]):
        receiver["logs"].append(log_data)

    def get_traces() -> List[Dict[str, Any]]:
        return receiver["traces"]

    def get_metrics() -> List[Dict[str, Any]]:
        return receiver["metrics"]

    def get_logs() -> List[Dict[str, Any]]:
        return receiver["logs"]

    def clear():
        receiver["traces"].clear()
        receiver["metrics"].clear()
        receiver["logs"].clear()

    def find_span_by_name(name: str) -> Dict[str, Any] | None:
        """Find the first span with the given name."""
        for trace in receiver["traces"]:
            if isinstance(trace, dict) and trace.get("name") == name:
                return trace
        return None

    return {
        "add_trace": add_trace,
        "add_metric": add_metric,
        "add_log": add_log,
        "get_traces": get_traces,
        "get_metrics": get_metrics,
        "get_logs": get_logs,
        "clear": clear,
        "find_span_by_name": find_span_by_name,
    }


@pytest.fixture
async def wait_for_services(http_client: httpx.AsyncClient):
    """
    Wait for all services to be healthy before running tests.

    This fixture ensures that the docker-compose environment is fully started
    and ready to accept requests.
    """
    services = [
        (ORDER_SERVICE_URL, "/api/orders/health"),
        (INVENTORY_SERVICE_URL, "/health"),
        (PAYMENT_SERVICE_URL, "/health"),
    ]

    max_retries = 30
    retry_delay = 2

    for base_url, health_path in services:
        url = f"{base_url}{health_path}"

        for attempt in range(max_retries):
            try:
                response = await http_client.get(url)
                if response.status_code == 200:
                    print(f"Service healthy: {base_url}")
                    break
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt == max_retries - 1:
                    pytest.skip(
                        f"Service not available after {max_retries} retries: {base_url}. "
                        f"Make sure docker-compose is running."
                    )
                time.sleep(retry_delay)

    yield


@pytest.fixture
def trace_id_extractor():
    """
    Utility function to extract trace_id from various formats.

    Handles extraction from:
    - W3C traceparent headers
    - JSON log messages
    - Span attributes
    """
    def extract(source: str | Dict[str, Any]) -> str | None:
        if isinstance(source, str):
            # Extract from W3C traceparent: 00-{trace_id}-{parent_id}-{flags}
            if source.startswith("00-"):
                parts = source.split("-")
                if len(parts) >= 2:
                    return parts[1]
        elif isinstance(source, dict):
            # Extract from various dict formats
            return (
                source.get("trace_id") or
                source.get("traceId") or
                source.get("otelTraceID")
            )
        return None

    return extract


@pytest.fixture
def span_validator():
    """
    Utility for validating span attributes and structure.

    Provides helper methods to check span correctness.
    """
    def validate_span(span: Dict[str, Any], expected_attributes: Dict[str, Any] = None) -> bool:
        """Validate that a span has the expected structure and attributes."""
        required_fields = ["name", "trace_id", "span_id"]

        for field in required_fields:
            if field not in span:
                return False

        if expected_attributes:
            span_attrs = span.get("attributes", {})
            for key, value in expected_attributes.items():
                if span_attrs.get(key) != value:
                    return False

        return True

    def has_parent_child_relationship(parent_span: Dict[str, Any], child_span: Dict[str, Any]) -> bool:
        """Check if two spans have a parent-child relationship."""
        return (
            parent_span.get("trace_id") == child_span.get("trace_id") and
            parent_span.get("span_id") == child_span.get("parent_span_id")
        )

    return {
        "validate_span": validate_span,
        "has_parent_child_relationship": has_parent_child_relationship,
    }

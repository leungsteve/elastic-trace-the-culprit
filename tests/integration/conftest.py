"""
Pytest Configuration and Shared Fixtures for Integration Tests
From Commit to Culprit Workshop

Provides fixtures for HTTP clients and service health checks for integration testing.
"""

import asyncio
import os
import time
from typing import Dict, Any

import httpx
import pytest


# Service URLs - can be overridden via environment variables
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8088")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8081")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8082")


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
async def check_services_available(http_client: httpx.AsyncClient) -> bool:
    """
    Check if all services are running before tests.

    Returns:
        bool: True if all services are available, False otherwise
    """
    services = [
        (ORDER_SERVICE_URL, "/api/orders/health"),
        (INVENTORY_SERVICE_URL, "/health"),
        (PAYMENT_SERVICE_URL, "/health"),
    ]

    all_available = True
    for base_url, health_path in services:
        url = f"{base_url}{health_path}"
        try:
            response = await http_client.get(url)
            if response.status_code != 200:
                all_available = False
                print(f"Service not healthy: {base_url} - Status: {response.status_code}")
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            all_available = False
            print(f"Service not available: {base_url} - Error: {e}")

    return all_available


@pytest.fixture
async def ensure_services_running(http_client: httpx.AsyncClient):
    """
    Ensure all services are healthy before running tests.

    This fixture will skip tests if services are not available,
    allowing tests to be run only when the docker-compose environment is up.
    """
    services = [
        (ORDER_SERVICE_URL, "/api/orders/health"),
        (INVENTORY_SERVICE_URL, "/health"),
        (PAYMENT_SERVICE_URL, "/health"),
    ]

    max_retries = 5
    retry_delay = 1

    for base_url, health_path in services:
        url = f"{base_url}{health_path}"
        service_available = False

        for attempt in range(max_retries):
            try:
                response = await http_client.get(url)
                if response.status_code == 200:
                    print(f"Service available: {base_url}")
                    service_available = True
                    break
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        if not service_available:
            pytest.skip(
                f"Service not available: {base_url}. "
                f"Please ensure docker-compose is running before executing integration tests."
            )

    yield


@pytest.fixture
def sample_order_request() -> Dict[str, Any]:
    """
    Sample order request payload for testing full order flow.

    Uses known product IDs that exist in the inventory service.
    """
    return {
        "customer_id": "integration-test-customer",
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
def sample_inventory_check_request() -> Dict[str, Any]:
    """
    Sample inventory check request payload.

    Format matches what the inventory service expects.
    """
    return {
        "items": [
            {"item_id": "LAPTOP-001", "quantity": 1},
            {"item_id": "MOUSE-002", "quantity": 2}
        ]
    }


@pytest.fixture
def sample_payment_request() -> Dict[str, Any]:
    """
    Sample payment request payload.

    Format matches what the payment service expects.
    """
    return {
        "order_id": "test-order-123",
        "customer_id": "integration-test-customer",
        "amount": 1049.97,
        "currency": "USD",
        "payment_method": "credit_card"
    }


@pytest.fixture
def unavailable_product_order() -> Dict[str, Any]:
    """
    Order request with a product that doesn't exist in inventory.

    This will cause the inventory check to fail.
    """
    return {
        "customer_id": "integration-test-customer",
        "items": [
            {
                "product_id": "NONEXISTENT-PRODUCT-999",
                "quantity": 1,
                "price": 99.99
            }
        ]
    }


@pytest.fixture
def payment_failure_order() -> Dict[str, Any]:
    """
    Order request that will deterministically fail payment processing.

    The payment service uses a hash-based failure simulation.
    This order_id is crafted to trigger a payment failure.
    """
    return {
        "customer_id": "integration-test-customer",
        "items": [
            {
                "product_id": "LAPTOP-001",
                "quantity": 1,
                "price": 999.99
            }
        ]
    }

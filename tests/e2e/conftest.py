"""
Pytest Configuration and Shared Fixtures for E2E Tests
From Commit to Culprit Workshop

Provides fixtures for service health checks, latency measurement,
deployment management, and test cleanup.
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple

import httpx
import pytest

# =============================================================================
# Path Configuration
# =============================================================================

# Get project root (tests/e2e -> tests -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
INFRA_DIR = PROJECT_ROOT / "infra"
ENV_FILE = INFRA_DIR / ".env"

# =============================================================================
# Service URLs - can be overridden via environment variables
# =============================================================================

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8088")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8081")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8082")
ROLLBACK_WEBHOOK_URL = os.getenv("ROLLBACK_WEBHOOK_URL", "http://localhost:9000")
OTEL_COLLECTOR_URL = os.getenv("OTEL_COLLECTOR_URL", "http://localhost:13133")

# =============================================================================
# Test Configuration
# =============================================================================

BASELINE_LATENCY_THRESHOLD = 500  # ms - healthy latency should be well below this
BAD_LATENCY_THRESHOLD = 1500  # ms - degraded latency should be well above this
RECOVERY_LATENCY_THRESHOLD = 500  # ms - recovered latency should return below this
NUM_LATENCY_SAMPLES = 10  # Number of requests to average for latency measurement
SERVICE_RESTART_WAIT_TIME = 30  # seconds to wait for service restart
STABILIZATION_WAIT_TIME = 10  # seconds to wait for metrics to stabilize


# =============================================================================
# Event Loop Fixture
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# HTTP Client Fixtures
# =============================================================================


@pytest.fixture
async def http_client():
    """Provide an async HTTP client for making requests to services."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


# =============================================================================
# Service URL Fixtures
# =============================================================================


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
def rollback_webhook_url() -> str:
    """URL for the rollback webhook service."""
    return ROLLBACK_WEBHOOK_URL


@pytest.fixture
def otel_collector_url() -> str:
    """URL for the OTEL collector health endpoint."""
    return OTEL_COLLECTOR_URL


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_order_request() -> Dict:
    """
    Sample order request payload for testing.

    Returns a deterministic order that should succeed in all services.
    """
    return {
        "customer_id": "test-customer-e2e-123",
        "items": [
            {
                "product_id": "WIDGET-001",
                "quantity": 1,
                "price": 29.99,
            }
        ],
    }


# =============================================================================
# Service Health Check Helpers
# =============================================================================


async def check_service_health(
    http_client: httpx.AsyncClient, service_url: str, health_path: str = "/health"
) -> Tuple[bool, int]:
    """
    Check if a service is healthy.

    Args:
        http_client: HTTP client to use
        service_url: Base URL of the service
        health_path: Path to the health endpoint

    Returns:
        Tuple of (is_healthy, status_code)
    """
    try:
        response = await http_client.get(f"{service_url}{health_path}", timeout=5.0)
        return response.status_code == 200, response.status_code
    except Exception:
        return False, 0


@pytest.fixture
async def wait_for_services(http_client: httpx.AsyncClient):
    """
    Wait for all services to be healthy before running tests.

    This fixture ensures that the docker-compose environment is fully started
    and ready to accept requests. It will skip tests if services don't come up.
    """
    services = [
        (ORDER_SERVICE_URL, "/api/orders/health", "Order Service"),
        (INVENTORY_SERVICE_URL, "/health", "Inventory Service"),
        (PAYMENT_SERVICE_URL, "/health", "Payment Service"),
        (ROLLBACK_WEBHOOK_URL, "/health", "Rollback Webhook"),
    ]

    max_retries = 30
    retry_delay = 2

    for base_url, health_path, service_name in services:
        for attempt in range(max_retries):
            is_healthy, status_code = await check_service_health(
                http_client, base_url, health_path
            )

            if is_healthy:
                print(f"✓ {service_name} is healthy")
                break

            if attempt == max_retries - 1:
                pytest.skip(
                    f"{service_name} not available after {max_retries} retries. "
                    f"Make sure docker-compose is running: cd infra && docker-compose up -d"
                )

            await asyncio.sleep(retry_delay)

    yield


# =============================================================================
# Latency Measurement Helpers
# =============================================================================


@pytest.fixture
def latency_measurer(http_client: httpx.AsyncClient, sample_order_request: Dict):
    """
    Fixture that provides a function to measure average latency.

    Returns a function that sends multiple requests and returns average latency in ms.
    """

    async def measure_latency(num_samples: int = NUM_LATENCY_SAMPLES) -> float:
        """
        Measure average latency by sending multiple order requests.

        Args:
            num_samples: Number of requests to send

        Returns:
            Average latency in milliseconds, or -1 if all requests failed
        """
        total_time = 0.0
        successful_requests = 0

        for _ in range(num_samples):
            start_time = time.time()

            try:
                response = await http_client.post(
                    f"{ORDER_SERVICE_URL}/api/orders",
                    json=sample_order_request,
                    timeout=10.0,
                )

                if response.status_code in [200, 201]:
                    duration_ms = (time.time() - start_time) * 1000
                    total_time += duration_ms
                    successful_requests += 1

            except Exception:
                # Request failed, don't count it
                pass

            # Small delay between requests
            await asyncio.sleep(0.2)

        if successful_requests == 0:
            return -1.0

        return total_time / successful_requests

    return measure_latency


# =============================================================================
# Version Management Helpers
# =============================================================================


def get_current_version() -> str:
    """
    Get the current order-service version from the .env file.

    Returns:
        Version string (e.g., "v1.0", "v1.1-bad"), or "unknown" if not found
    """
    if not ENV_FILE.exists():
        return "unknown"

    with open(ENV_FILE, "r") as f:
        for line in f:
            if line.strip().startswith("ORDER_SERVICE_VERSION="):
                return line.strip().split("=", 1)[1]

    return "unknown"


@pytest.fixture
def version_manager():
    """
    Fixture that provides functions to get and verify service versions.
    """

    def get_version() -> str:
        """Get current order-service version."""
        return get_current_version()

    def wait_for_version(
        target_version: str, timeout: int = 60, check_interval: int = 2
    ) -> bool:
        """
        Wait for the service to reach a specific version.

        Args:
            target_version: Expected version
            timeout: Max seconds to wait
            check_interval: Seconds between checks

        Returns:
            True if version reached, False if timeout
        """
        elapsed = 0
        while elapsed < timeout:
            if get_current_version() == target_version:
                return True
            time.sleep(check_interval)
            elapsed += check_interval

        return False

    return {
        "get_version": get_version,
        "wait_for_version": wait_for_version,
    }


# =============================================================================
# Script Execution Helpers
# =============================================================================


def run_script(script_name: str, *args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    """
    Run a script from the scripts/ directory.

    Args:
        script_name: Name of the script (e.g., "deploy.sh")
        *args: Arguments to pass to the script
        timeout: Max seconds to wait for script completion

    Returns:
        CompletedProcess with returncode, stdout, stderr

    Raises:
        subprocess.TimeoutExpired: If script takes longer than timeout
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    result = subprocess.run(
        [str(script_path), *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    return result


@pytest.fixture
def script_runner():
    """
    Fixture that provides a function to run scripts.

    Returns a function that runs scripts and returns the result.
    """
    return run_script


# =============================================================================
# State Cleanup Fixtures
# =============================================================================


@pytest.fixture
def initial_state():
    """
    Capture the initial state before test and provide cleanup.

    This fixture records the initial service version and restores it
    after the test completes, ensuring tests are idempotent.
    """
    # Capture initial state
    initial_version = get_current_version()

    yield {
        "initial_version": initial_version,
    }

    # Restore initial state after test
    current_version = get_current_version()

    if current_version != initial_version:
        print(f"\nRestoring initial state: {current_version} -> {initial_version}")

        # Use deploy.sh to restore version
        try:
            run_script("deploy.sh", "order-service", initial_version, timeout=90)
            # Wait for service to stabilize
            time.sleep(SERVICE_RESTART_WAIT_TIME)
        except Exception as e:
            print(f"Warning: Failed to restore initial state: {e}")


# =============================================================================
# Rollback Webhook Helpers
# =============================================================================


@pytest.fixture
def webhook_client(http_client: httpx.AsyncClient):
    """
    Fixture that provides helper functions for interacting with the rollback webhook.
    """

    async def trigger_rollback(
        service: str = "order-service",
        target_version: str = "v1.0",
        alert_id: str = "test-alert-e2e",
        reason: str = "E2E test rollback",
    ) -> Dict:
        """
        Trigger a rollback via the webhook.

        Args:
            service: Service to rollback
            target_version: Version to rollback to
            alert_id: Alert identifier
            reason: Reason for rollback

        Returns:
            Response JSON from webhook

        Raises:
            httpx.HTTPStatusError: If webhook returns error
        """
        response = await http_client.post(
            f"{ROLLBACK_WEBHOOK_URL}/rollback",
            json={
                "service": service,
                "target_version": target_version,
                "alert_id": alert_id,
                "reason": reason,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()

    async def get_webhook_status() -> Dict:
        """
        Get the status of the last rollback from the webhook.

        Returns:
            Status JSON from webhook
        """
        response = await http_client.get(
            f"{ROLLBACK_WEBHOOK_URL}/status",
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    return {
        "trigger_rollback": trigger_rollback,
        "get_status": get_webhook_status,
    }


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line(
        "markers", "requires_docker: marks tests that require Docker to be running"
    )
    config.addinivalue_line(
        "markers", "requires_services: marks tests that require all services to be healthy"
    )


# =============================================================================
# Session-Level Logging
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def print_test_environment():
    """Print test environment information at the start of the session."""
    print("\n" + "=" * 80)
    print("E2E Test Environment Configuration")
    print("=" * 80)
    print(f"Project Root:         {PROJECT_ROOT}")
    print(f"Scripts Directory:    {SCRIPTS_DIR}")
    print(f"Infra Directory:      {INFRA_DIR}")
    print(f"Environment File:     {ENV_FILE}")
    print()
    print("Service URLs:")
    print(f"  Order Service:      {ORDER_SERVICE_URL}")
    print(f"  Inventory Service:  {INVENTORY_SERVICE_URL}")
    print(f"  Payment Service:    {PAYMENT_SERVICE_URL}")
    print(f"  Rollback Webhook:   {ROLLBACK_WEBHOOK_URL}")
    print(f"  OTEL Collector:     {OTEL_COLLECTOR_URL}")
    print()
    print("Test Configuration:")
    print(f"  Baseline Latency Threshold:  < {BASELINE_LATENCY_THRESHOLD}ms")
    print(f"  Bad Latency Threshold:       > {BAD_LATENCY_THRESHOLD}ms")
    print(f"  Recovery Latency Threshold:  < {RECOVERY_LATENCY_THRESHOLD}ms")
    print(f"  Latency Samples:             {NUM_LATENCY_SAMPLES}")
    print("=" * 80 + "\n")

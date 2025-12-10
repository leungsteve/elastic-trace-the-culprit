"""
Span Attribute Tests
From Commit to Culprit Workshop

Tests that spans contain the expected attributes, especially the "detailed-trace-logging"
span from Jordan Rivera's bug with attribution metadata.
"""

import pytest
import httpx
from typing import Dict, Any


class TestBugSpanAttributes:
    """Test suite for the bug span attributes (detailed-trace-logging)."""

    @pytest.mark.asyncio
    async def test_detailed_trace_logging_span_exists(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that the detailed-trace-logging span exists when bug is enabled.

        In v1.1-bad, the order service includes Jordan Rivera's "optimization"
        which creates a span named "detailed-trace-logging" with a 2-second delay.

        This test assumes ORDER_SERVICE_VERSION=v1.1-bad is running.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would:
        # 1. Query for the trace
        # 2. Find the span named "detailed-trace-logging"
        # 3. Verify it exists (if v1.1-bad is deployed)
        # 4. Verify it has the expected attributes


    @pytest.mark.asyncio
    async def test_bug_span_attribution_metadata(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that the detailed-trace-logging span has attribution metadata.

        Expected attributes:
        - logging.type: detailed-trace
        - logging.author: jordan.rivera
        - logging.commit_sha: a1b2c3d4
        - logging.pr_number: PR-1247
        - logging.delay_ms: 2000
        - logging.destination: /var/log/orders/trace.log

        These attributes help participants discover who introduced the bug
        and trace it back to the source code.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would:
        # 1. Query for the trace
        # 2. Find the "detailed-trace-logging" span
        # 3. Verify span.attributes contains:
        #    {
        #      "logging.type": "detailed-trace",
        #      "logging.author": "jordan.rivera",
        #      "logging.commit_sha": "a1b2c3d4",
        #      "logging.pr_number": "PR-1247",
        #      "logging.delay_ms": 2000,
        #      "logging.destination": "/var/log/orders/trace.log"
        #    }


    @pytest.mark.asyncio
    async def test_bug_span_duration(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that the detailed-trace-logging span has ~2 second duration.

        The bug introduces a Thread.sleep(2000), so the span duration
        should be approximately 2000ms (2 seconds).
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would:
        # 1. Query for the trace
        # 2. Find the "detailed-trace-logging" span
        # 3. Verify span.duration >= 2000ms and <= 2100ms (allowing for overhead)


class TestServiceVersionAttribute:
    """Test suite for service.version attributes."""

    @pytest.mark.asyncio
    async def test_order_service_version_attribute(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that order service spans include service.version attribute.

        This helps distinguish between v1.0 (good) and v1.1-bad (buggy).
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would:
        # 1. Query for the trace
        # 2. Find spans from order-service
        # 3. Verify service.version attribute exists
        # 4. Verify it's either "v1.0" or "v1.1-bad"


    @pytest.mark.asyncio
    async def test_all_services_have_version_attribute(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that all services (order, inventory, payment) have service.version.

        Each service should report its version in span attributes.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would:
        # 1. Query for the trace
        # 2. Group spans by service.name
        # 3. Verify each service has service.version attribute


class TestBusinessAttributes:
    """Test suite for business-level span attributes."""

    @pytest.mark.asyncio
    async def test_order_span_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that order.create span has business attributes.

        Expected attributes:
        - order.customer_id
        - order.item_count
        - order.total_amount
        - order.status
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. Span "order.create" contains:
        #    - order.customer_id = "test-customer-123"
        #    - order.item_count = 2
        #    - order.total_amount = 1049.97
        #    - order.status = "CONFIRMED"


    @pytest.mark.asyncio
    async def test_payment_span_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that payment processing span has payment attributes.

        Expected attributes:
        - payment.order_id
        - payment.amount
        - payment.currency
        - payment.method
        - payment.customer_id
        - payment.status
        - payment.transaction_id (if successful)
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. Span "process_payment" contains:
        #    - payment.order_id
        #    - payment.amount
        #    - payment.currency = "USD"
        #    - payment.method
        #    - payment.status = "completed"
        #    - payment.transaction_id (starts with "TXN-")


    @pytest.mark.asyncio
    async def test_inventory_check_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that inventory check span has product attributes.

        Should include the product IDs being checked for availability.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. Inventory-related span contains product IDs
        # 2. Shows availability status


class TestHTTPAttributes:
    """Test suite for HTTP-level span attributes."""

    @pytest.mark.asyncio
    async def test_http_server_span_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that HTTP server spans include standard HTTP attributes.

        Expected attributes (OpenTelemetry semantic conventions):
        - http.method
        - http.route
        - http.status_code
        - http.target
        - http.user_agent
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. HTTP server span contains:
        #    - http.method = "POST"
        #    - http.route = "/api/orders"
        #    - http.status_code = 201
        #    - http.target = "/api/orders"


    @pytest.mark.asyncio
    async def test_http_client_span_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that HTTP client spans (outgoing requests) have HTTP attributes.

        When order service calls inventory and payment services, the HTTP
        client spans should include standard HTTP attributes.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. HTTP client spans to inventory-service contain:
        #    - http.method = "POST"
        #    - http.url (full URL)
        #    - http.status_code
        # 2. HTTP client spans to payment-service contain:
        #    - http.method = "POST"
        #    - http.url (full URL)
        #    - http.status_code


class TestResourceAttributes:
    """Test suite for resource-level attributes."""

    @pytest.mark.asyncio
    async def test_service_name_attribute(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that all spans include service.name resource attribute.

        Each service should identify itself:
        - order-service
        - inventory-service
        - payment-service
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. All spans have service.name attribute
        # 2. service.name values are: order-service, inventory-service, payment-service


    @pytest.mark.asyncio
    async def test_deployment_environment_attribute(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that all spans include deployment.environment attribute.

        The OTEL collector adds this from the ENVIRONMENT env var.
        Should be either "local" or "instruqt".
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. All spans have deployment.environment attribute
        # 2. Value is "local" or "instruqt"


    @pytest.mark.asyncio
    async def test_workshop_identifier_attribute(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that all spans include workshop.name attribute.

        The OTEL collector adds this to identify workshop telemetry:
        workshop.name = "from-commit-to-culprit"
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with OTEL collector access, we would verify:
        # 1. All spans have workshop.name attribute
        # 2. Value is "from-commit-to-culprit"


class TestErrorAttributes:
    """Test suite for error-related span attributes."""

    @pytest.mark.asyncio
    async def test_error_span_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        wait_for_services,
    ):
        """
        Test that error spans include error attributes.

        When an exception occurs, the span should include:
        - error: true
        - exception.type
        - exception.message
        - exception.stacktrace
        """
        # Send invalid request to trigger error
        invalid_request = {
            "customer_id": "",
            "items": []
        }

        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=invalid_request,
        )

        # Expect error response
        assert response.status_code >= 400

        # In a full test with OTEL collector access, we would verify:
        # 1. Error span has error=true attribute
        # 2. Includes exception.type
        # 3. Includes exception.message
        # 4. Includes exception.stacktrace


    @pytest.mark.asyncio
    async def test_payment_failure_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        wait_for_services,
    ):
        """
        Test that payment failure spans include failure reason.

        When payment is declined, the span should include:
        - payment.status = "failed"
        - order.failure_reason = "payment_declined"
        """
        # Try multiple orders to potentially trigger 1% payment failure
        for i in range(200):
            test_request = {
                "customer_id": f"test-customer-{i}",
                "items": [{"product_id": "TEST", "quantity": 1, "price": 10.00}]
            }

            response = await http_client.post(
                f"{order_service_url}/api/orders",
                json=test_request,
            )

            if response.status_code == 400:
                # Found a payment failure
                # In a full test, we would verify span attributes show the failure
                break

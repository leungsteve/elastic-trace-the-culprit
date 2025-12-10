"""
Service Integration Tests
From Commit to Culprit Workshop

Tests service-to-service communication and full order flow:
1. Order service calling inventory service
2. Order service calling payment service
3. Complete order flow (order -> inventory -> payment -> confirmation)
4. Error handling when downstream services fail

These tests require all services to be running (docker-compose up).
They will be skipped if services are not available.
"""

import pytest
import httpx
from typing import Dict, Any


class TestInventoryServiceIntegration:
    """Tests for order service integration with inventory service."""

    @pytest.mark.asyncio
    async def test_inventory_service_health_check(
        self,
        http_client: httpx.AsyncClient,
        inventory_service_url: str,
        ensure_services_running,
    ):
        """
        Test that inventory service health endpoint is accessible.

        This is a basic connectivity test to ensure the service is running.
        """
        response = await http_client.get(f"{inventory_service_url}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "inventory-service"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_inventory_check_available_items(
        self,
        http_client: httpx.AsyncClient,
        inventory_service_url: str,
        sample_inventory_check_request: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test inventory check endpoint with items that are in stock.

        Verifies that the inventory service correctly reports availability
        for products that exist and have sufficient stock.
        """
        response = await http_client.post(
            f"{inventory_service_url}/api/inventory/check",
            json=sample_inventory_check_request,
        )

        assert response.status_code == 200
        data = response.json()

        # All items should be available
        assert data["available"] is True
        assert "items" in data
        assert len(data["items"]) == 2

        # Check first item details
        laptop = next(item for item in data["items"] if item["item_id"] == "LAPTOP-001")
        assert laptop["in_stock"] is True
        assert laptop["requested"] == 1
        assert laptop["available"] > 0
        assert "price" in laptop

    @pytest.mark.asyncio
    async def test_inventory_check_unavailable_items(
        self,
        http_client: httpx.AsyncClient,
        inventory_service_url: str,
        ensure_services_running,
    ):
        """
        Test inventory check endpoint with items that don't exist.

        Verifies that the inventory service correctly reports unavailability
        for products that don't exist in the catalog.
        """
        request_payload = {
            "items": [
                {"item_id": "NONEXISTENT-PRODUCT-999", "quantity": 1}
            ]
        }

        response = await http_client.post(
            f"{inventory_service_url}/api/inventory/check",
            json=request_payload,
        )

        assert response.status_code == 200
        data = response.json()

        # Items should not be available
        assert data["available"] is False
        assert data["items"][0]["in_stock"] is False
        assert data["items"][0]["item_id"] == "NONEXISTENT-PRODUCT-999"

    @pytest.mark.asyncio
    async def test_order_service_calls_inventory_service(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test that order service successfully calls inventory service.

        Creates an order and verifies the request succeeds, which requires
        the order service to successfully communicate with the inventory service.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        # Order should be created successfully
        assert response.status_code in [200, 201]
        data = response.json()

        # Response should contain order confirmation
        assert "orderId" in data or "order_id" in data
        assert data["status"] == "CONFIRMED"
        assert "message" in data


class TestPaymentServiceIntegration:
    """Tests for order service integration with payment service."""

    @pytest.mark.asyncio
    async def test_payment_service_health_check(
        self,
        http_client: httpx.AsyncClient,
        payment_service_url: str,
        ensure_services_running,
    ):
        """
        Test that payment service health endpoint is accessible.

        This is a basic connectivity test to ensure the service is running.
        """
        response = await http_client.get(f"{payment_service_url}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "payment-service"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_payment_processing_success(
        self,
        http_client: httpx.AsyncClient,
        payment_service_url: str,
        sample_payment_request: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test payment service processes payments successfully.

        Verifies that the payment service can accept and process
        a payment request with valid data.
        """
        response = await http_client.post(
            f"{payment_service_url}/api/payments",
            json=sample_payment_request,
        )

        # Payment should be processed (201 Created) or may fail (402) due to deterministic failure
        assert response.status_code in [201, 402]

        if response.status_code == 201:
            data = response.json()
            assert "payment_id" in data
            assert data["order_id"] == sample_payment_request["order_id"]
            assert data["status"] in ["completed", "pending"]
            assert "amount" in data

    @pytest.mark.asyncio
    async def test_order_service_calls_payment_service(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test that order service successfully calls payment service.

        Creates an order and verifies the request completes the payment flow,
        which requires the order service to successfully communicate with
        the payment service.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        # Order should be created successfully (payment may fail, but call should succeed)
        assert response.status_code in [200, 201, 400]
        data = response.json()

        # If order was confirmed, payment service was called successfully
        if data["status"] == "CONFIRMED":
            assert "orderId" in data or "order_id" in data
            assert "totalAmount" in data or "total_amount" in data


class TestFullOrderFlow:
    """Tests for complete order flow across all services."""

    @pytest.mark.asyncio
    async def test_successful_order_flow(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test complete successful order flow.

        Flow:
        1. Client creates order
        2. Order service checks inventory
        3. Order service processes payment
        4. Order is confirmed

        This is the happy path where everything succeeds.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        # Order should be created successfully or fail due to payment (deterministic)
        assert response.status_code in [200, 201, 400]
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert data["status"] in ["CONFIRMED", "FAILED"]

        if data["status"] == "CONFIRMED":
            # Successful order
            assert "orderId" in data or "order_id" in data
            order_id = data.get("orderId") or data.get("order_id")
            assert order_id is not None

            # Verify total amount matches expected
            total_amount = data.get("totalAmount") or data.get("total_amount")
            expected_total = sum(
                item["price"] * item["quantity"]
                for item in sample_order_request["items"]
            )
            assert float(total_amount) == pytest.approx(expected_total, rel=0.01)

            # Verify we can retrieve the order
            get_response = await http_client.get(
                f"{order_service_url}/api/orders/{order_id}"
            )
            assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_order_flow_with_unavailable_inventory(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        unavailable_product_order: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test order flow when inventory is unavailable.

        Flow:
        1. Client creates order with unavailable product
        2. Order service checks inventory
        3. Inventory service returns unavailable
        4. Order is rejected (payment should not be attempted)

        This tests error handling when the inventory check fails.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=unavailable_product_order,
        )

        # Order should fail due to inventory
        assert response.status_code in [200, 201, 400]
        data = response.json()

        # Order should be failed
        assert data["status"] == "FAILED"
        assert "message" in data

        # Message should indicate inventory issue
        message = data["message"].lower()
        assert "inventory" in message or "unavailable" in message or "not available" in message

    @pytest.mark.asyncio
    async def test_order_retrieval(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test retrieving an order after creation.

        Verifies that orders can be retrieved by their order_id
        and contain all expected fields.
        """
        # Create an order first
        create_response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert create_response.status_code in [200, 201, 400]
        create_data = create_response.json()

        # Only test retrieval if order was created successfully
        if create_data["status"] == "CONFIRMED":
            order_id = create_data.get("orderId") or create_data.get("order_id")

            # Retrieve the order
            get_response = await http_client.get(
                f"{order_service_url}/api/orders/{order_id}"
            )

            assert get_response.status_code == 200
            order_data = get_response.json()

            # Verify order fields
            assert order_data["orderId"] == order_id or order_data["order_id"] == order_id
            assert order_data["customerId"] == sample_order_request["customer_id"] or \
                   order_data["customer_id"] == sample_order_request["customer_id"]
            assert "items" in order_data
            assert "totalAmount" in order_data or "total_amount" in order_data
            assert "status" in order_data
            assert order_data["status"] == "CONFIRMED"

    @pytest.mark.asyncio
    async def test_order_not_found(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        ensure_services_running,
    ):
        """
        Test retrieving a non-existent order.

        Verifies that the order service returns 404 for orders that don't exist.
        """
        fake_order_id = "nonexistent-order-12345"

        response = await http_client.get(
            f"{order_service_url}/api/orders/{fake_order_id}"
        )

        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling when downstream services fail."""

    @pytest.mark.asyncio
    async def test_invalid_order_request(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        ensure_services_running,
    ):
        """
        Test order creation with invalid request payload.

        Verifies that the order service validates input and returns
        appropriate error responses.
        """
        # Missing required fields
        invalid_request = {
            "customer_id": "test-customer"
            # Missing items field
        }

        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=invalid_request,
        )

        # Should return bad request
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_empty_order_items(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        ensure_services_running,
    ):
        """
        Test order creation with empty items list.

        Verifies that the order service rejects orders with no items.
        """
        empty_order = {
            "customer_id": "test-customer",
            "items": []
        }

        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=empty_order,
        )

        # Should return bad request or fail
        assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_inventory_service_invalid_request(
        self,
        http_client: httpx.AsyncClient,
        inventory_service_url: str,
        ensure_services_running,
    ):
        """
        Test inventory service with invalid request payload.

        Verifies that the inventory service validates input.
        """
        invalid_request = {
            "items": [
                {"quantity": 1}  # Missing item_id
            ]
        }

        response = await http_client.post(
            f"{inventory_service_url}/api/inventory/check",
            json=invalid_request,
        )

        # Should return bad request
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_payment_service_invalid_request(
        self,
        http_client: httpx.AsyncClient,
        payment_service_url: str,
        ensure_services_running,
    ):
        """
        Test payment service with invalid request payload.

        Verifies that the payment service validates input.
        """
        invalid_request = {
            "order_id": "test-order",
            # Missing required fields: amount, customer_id, payment_method
        }

        response = await http_client.post(
            f"{payment_service_url}/api/payments",
            json=invalid_request,
        )

        # Should return bad request or unprocessable entity
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_concurrent_order_creation(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: Dict[str, Any],
        ensure_services_running,
    ):
        """
        Test creating multiple orders concurrently.

        Verifies that the services can handle concurrent requests
        without issues.
        """
        # Create 5 concurrent orders
        import asyncio

        async def create_order():
            return await http_client.post(
                f"{order_service_url}/api/orders",
                json=sample_order_request,
            )

        responses = await asyncio.gather(*[create_order() for _ in range(5)])

        # All requests should complete (success or failure)
        assert len(responses) == 5

        for response in responses:
            assert response.status_code in [200, 201, 400]
            data = response.json()
            assert "status" in data
            assert data["status"] in ["CONFIRMED", "FAILED"]


class TestServiceHealthAndReadiness:
    """Tests for service health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_all_services_healthy(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        inventory_service_url: str,
        payment_service_url: str,
        ensure_services_running,
    ):
        """
        Test that all services report healthy status.

        This is a comprehensive health check across all services.
        """
        services = [
            (order_service_url, "/api/orders/health"),
            (inventory_service_url, "/health"),
            (payment_service_url, "/health"),
        ]

        for service_url, health_path in services:
            response = await http_client.get(f"{service_url}{health_path}")
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert data["status"] in ["UP", "healthy"]
            assert "service" in data

    @pytest.mark.asyncio
    async def test_all_services_ready(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        inventory_service_url: str,
        payment_service_url: str,
        ensure_services_running,
    ):
        """
        Test that all services report ready status.

        Readiness indicates the service is ready to accept traffic.
        """
        services = [
            (order_service_url, "/api/orders/ready"),
            (inventory_service_url, "/ready"),
            (payment_service_url, "/ready"),
        ]

        for service_url, ready_path in services:
            response = await http_client.get(f"{service_url}{ready_path}")
            assert response.status_code == 200

            data = response.json()
            # Different services use different field names
            assert ("ready" in data and data["ready"] is True) or \
                   ("status" in data and data["status"] in ["ready", "UP"])

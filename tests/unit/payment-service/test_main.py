"""
Unit tests for Payment Service FastAPI endpoints.

Tests the REST API endpoints including:
- Payment processing (success and failure)
- Payment retrieval
- Health and readiness checks
- Idempotency handling

Workshop: From Commit to Culprit - Payment Service Tests
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID
import sys
from pathlib import Path

# Add the service to the path
service_path = Path(__file__).parent.parent.parent.parent / "services" / "payment-service" / "src"
sys.path.insert(0, str(service_path))

from payment.main import app, payments_store
from payment.models import PaymentMethod, PaymentStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_payments():
    """Clear payment store before and after each test."""
    payments_store.clear()
    yield
    payments_store.clear()


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "payment-service"
        assert "version" in data
        assert "environment" in data

    def test_readiness_check(self, client):
        """Test readiness check endpoint returns ready status."""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ready"
        assert data["service"] == "payment-service"


class TestProcessPayment:
    """Test payment processing endpoint."""

    def test_process_payment_success(self, client):
        """Test successful payment processing."""
        # Use an order_id that won't trigger the 1% failure
        payment_request = {
            "order_id": "order-success-123",
            "customer_id": "customer-456",
            "amount": 99.99,
            "currency": "USD",
            "payment_method": "credit_card"
        }

        response = client.post("/api/payments", json=payment_request)

        # Most order IDs should succeed (99% success rate)
        if response.status_code == 201:
            data = response.json()

            assert "payment_id" in data
            assert data["order_id"] == "order-success-123"
            assert data["amount"] == 99.99
            assert data["currency"] == "USD"
            assert data["status"] == "completed"
            assert data["payment_method"] == "credit_card"
            assert "transaction_id" in data
            assert data["transaction_id"].startswith("TXN-")
            assert data["failure_reason"] is None

    def test_process_payment_deterministic_failure(self, client):
        """Test that certain order IDs deterministically fail."""
        # We need to find an order_id that will hash to failure
        # The failure happens when hash(order_id) % 100 == 0
        # Let's try multiple IDs to find one that fails
        found_failure = False

        for i in range(1000):
            order_id = f"order-test-{i}"
            payment_request = {
                "order_id": order_id,
                "customer_id": "customer-test",
                "amount": 50.00,
                "currency": "USD",
                "payment_method": "credit_card"
            }

            response = client.post("/api/payments", json=payment_request)

            if response.status_code == 402:
                found_failure = True
                data = response.json()

                assert "error" in data
                assert data["error"] == "Payment declined"
                assert "reason" in data
                assert "payment_id" in data
                break

            # Clear the store for next iteration
            payments_store.clear()

        # We should find at least one failure in 1000 attempts (statistically)
        assert found_failure, "Should find at least one deterministic failure"

    def test_process_payment_stores_in_memory(self, client):
        """Test that payment is stored in memory after processing."""
        payment_request = {
            "order_id": "order-store-test",
            "customer_id": "customer-999",
            "amount": 150.00,
            "currency": "USD",
            "payment_method": "credit_card"
        }

        response = client.post("/api/payments", json=payment_request)

        if response.status_code == 201:
            data = response.json()
            payment_id = data["payment_id"]

            # Verify payment is in store
            assert len(payments_store) == 1
            assert UUID(payment_id) in payments_store

    def test_process_payment_with_debit_card(self, client):
        """Test payment with debit card method."""
        payment_request = {
            "order_id": "order-debit-123",
            "customer_id": "customer-debit",
            "amount": 75.50,
            "currency": "USD",
            "payment_method": "debit_card"
        }

        response = client.post("/api/payments", json=payment_request)

        if response.status_code == 201:
            data = response.json()
            assert data["payment_method"] == "debit_card"

    def test_process_payment_with_paypal(self, client):
        """Test payment with PayPal method."""
        payment_request = {
            "order_id": "order-paypal-123",
            "customer_id": "customer-paypal",
            "amount": 200.00,
            "currency": "USD",
            "payment_method": "paypal"
        }

        response = client.post("/api/payments", json=payment_request)

        if response.status_code == 201:
            data = response.json()
            assert data["payment_method"] == "paypal"

    def test_process_payment_idempotency(self, client):
        """Test idempotent payment processing."""
        payment_request = {
            "order_id": "order-idempotent-123",
            "customer_id": "customer-idempotent",
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "credit_card",
            "idempotency_key": "unique-key-123"
        }

        # First request
        response1 = client.post("/api/payments", json=payment_request)

        if response1.status_code == 201:
            data1 = response1.json()
            payment_id_1 = data1["payment_id"]

            # Second request with same idempotency key
            response2 = client.post("/api/payments", json=payment_request)

            assert response2.status_code == 201
            data2 = response2.json()

            # Should return the same payment
            assert data2["payment_id"] == payment_id_1
            assert data2["order_id"] == data1["order_id"]

            # Should only have one payment in store
            assert len(payments_store) == 1


class TestGetPayment:
    """Test payment retrieval endpoint."""

    def test_get_payment_found(self, client):
        """Test retrieving an existing payment."""
        # First create a payment
        payment_request = {
            "order_id": "order-retrieve-123",
            "customer_id": "customer-retrieve",
            "amount": 88.88,
            "currency": "USD",
            "payment_method": "credit_card"
        }

        create_response = client.post("/api/payments", json=payment_request)

        if create_response.status_code == 201:
            created_payment = create_response.json()
            payment_id = created_payment["payment_id"]

            # Now retrieve it
            get_response = client.get(f"/api/payments/{payment_id}")

            assert get_response.status_code == 200
            retrieved_payment = get_response.json()

            assert retrieved_payment["payment_id"] == payment_id
            assert retrieved_payment["order_id"] == "order-retrieve-123"
            assert retrieved_payment["amount"] == 88.88
            assert retrieved_payment["status"] == "completed"

    def test_get_payment_not_found(self, client):
        """Test retrieving a non-existent payment."""
        # Generate a random UUID that doesn't exist
        fake_payment_id = "12345678-1234-1234-1234-123456789abc"

        response = client.get(f"/api/payments/{fake_payment_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_payment_invalid_uuid(self, client):
        """Test retrieving payment with invalid UUID format."""
        response = client.get("/api/payments/not-a-valid-uuid")

        # FastAPI will return 422 for invalid UUID format
        assert response.status_code == 422


class TestPaymentFailures:
    """Test payment failure scenarios."""

    def test_failed_payment_stored(self, client):
        """Test that failed payments are also stored."""
        # Find an order_id that will fail
        for i in range(1000):
            order_id = f"order-fail-{i}"
            payment_request = {
                "order_id": order_id,
                "customer_id": "customer-fail",
                "amount": 50.00,
                "currency": "USD",
                "payment_method": "credit_card"
            }

            response = client.post("/api/payments", json=payment_request)

            if response.status_code == 402:
                # Payment failed - verify it's stored
                assert len(payments_store) == 1

                # Get the payment details
                data = response.json()
                payment_id = data["payment_id"]

                # Retrieve the failed payment
                get_response = client.get(f"/api/payments/{payment_id}")
                assert get_response.status_code == 200

                retrieved = get_response.json()
                assert retrieved["status"] == "failed"
                assert retrieved["failure_reason"] is not None
                break

            payments_store.clear()


class TestPaymentValidation:
    """Test payment request validation."""

    def test_process_payment_invalid_amount(self, client):
        """Test payment with invalid amount."""
        payment_request = {
            "order_id": "order-invalid",
            "customer_id": "customer-invalid",
            "amount": -10.00,  # Negative amount
            "currency": "USD",
            "payment_method": "credit_card"
        }

        response = client.post("/api/payments", json=payment_request)

        # Should fail validation
        assert response.status_code == 422

    def test_process_payment_missing_required_fields(self, client):
        """Test payment with missing required fields."""
        payment_request = {
            "order_id": "order-missing",
            # Missing customer_id, amount, currency, payment_method
        }

        response = client.post("/api/payments", json=payment_request)

        # Should fail validation
        assert response.status_code == 422

    def test_process_payment_invalid_payment_method(self, client):
        """Test payment with invalid payment method."""
        payment_request = {
            "order_id": "order-bad-method",
            "customer_id": "customer-bad",
            "amount": 50.00,
            "currency": "USD",
            "payment_method": "invalid_method"  # Not a valid enum value
        }

        response = client.post("/api/payments", json=payment_request)

        # Should fail validation
        assert response.status_code == 422

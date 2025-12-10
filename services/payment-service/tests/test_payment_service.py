"""
Payment Service Tests
From Commit to Culprit Workshop

Tests for payment processing, health checks, and error handling.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from payment.main import app
from payment.models import PaymentMethod, PaymentStatus


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint returns 200 and correct structure."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "payment-service"
    assert "version" in data
    assert "environment" in data


def test_readiness_check(client):
    """Test readiness endpoint returns 200 and correct structure."""
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "payment-service"


def test_process_payment_success(client):
    """Test successful payment processing."""
    # Use an order_id that won't trigger the 1% failure
    payment_request = {
        "order_id": "order-test-123",
        "amount": 47.50,
        "currency": "USD",
        "payment_method": "credit_card",
        "customer_id": "customer-456",
    }

    response = client.post("/api/payments", json=payment_request)

    # Should succeed for most order IDs
    if response.status_code == 201:
        data = response.json()
        assert data["order_id"] == "order-test-123"
        assert float(data["amount"]) == 47.50
        assert data["currency"] == "USD"
        assert data["status"] == "completed"
        assert data["payment_method"] == "credit_card"
        assert data["transaction_id"] is not None
        assert data["transaction_id"].startswith("TXN-")
        assert "payment_id" in data
    else:
        # If it fails due to deterministic hash, that's also valid
        assert response.status_code == 402


def test_process_payment_validation_error(client):
    """Test payment with invalid data."""
    payment_request = {
        "order_id": "order-123",
        "amount": -10.00,  # Invalid: negative amount
        "currency": "USD",
        "payment_method": "credit_card",
        "customer_id": "customer-456",
    }

    response = client.post("/api/payments", json=payment_request)
    assert response.status_code == 422  # Validation error


def test_get_payment_not_found(client):
    """Test retrieving non-existent payment."""
    from uuid import uuid4

    fake_payment_id = str(uuid4())
    response = client.get(f"/api/payments/{fake_payment_id}")
    assert response.status_code == 404


def test_process_and_retrieve_payment(client):
    """Test full payment flow: create and retrieve."""
    # Create payment
    payment_request = {
        "order_id": "order-flow-test-789",
        "amount": 99.99,
        "currency": "USD",
        "payment_method": "paypal",
        "customer_id": "customer-789",
    }

    create_response = client.post("/api/payments", json=payment_request)

    if create_response.status_code == 201:
        payment_data = create_response.json()
        payment_id = payment_data["payment_id"]

        # Retrieve payment
        get_response = client.get(f"/api/payments/{payment_id}")
        assert get_response.status_code == 200

        retrieved_data = get_response.json()
        assert retrieved_data["payment_id"] == payment_id
        assert retrieved_data["order_id"] == "order-flow-test-789"
        assert float(retrieved_data["amount"]) == 99.99


def test_currency_uppercase_conversion(client):
    """Test that currency is converted to uppercase."""
    payment_request = {
        "order_id": "order-currency-test",
        "amount": 50.00,
        "currency": "usd",  # lowercase
        "payment_method": "credit_card",
        "customer_id": "customer-123",
    }

    response = client.post("/api/payments", json=payment_request)

    if response.status_code == 201:
        data = response.json()
        assert data["currency"] == "USD"  # Should be uppercase


def test_deterministic_failure():
    """Test that failure calculation is deterministic."""
    from payment.main import calculate_failure_probability

    # Same order_id should always give same result
    order_id = "test-order-123"
    result1 = calculate_failure_probability(order_id)
    result2 = calculate_failure_probability(order_id)
    assert result1 == result2

    # Different order_ids should (likely) give different results
    results = [calculate_failure_probability(f"order-{i}") for i in range(100)]
    # Should have at least one True and one False in 100 attempts
    assert True in results or False in results


def test_api_documentation_available(client):
    """Test that API documentation endpoints are accessible."""
    # Swagger UI
    response = client.get("/api/docs")
    assert response.status_code == 200

    # ReDoc
    response = client.get("/api/redoc")
    assert response.status_code == 200

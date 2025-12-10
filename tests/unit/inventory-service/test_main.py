"""
Unit tests for Inventory Service FastAPI endpoints.

Tests the REST API endpoints including:
- Stock checking
- Inventory reservation
- Health and readiness checks
- Summary endpoint

Workshop: From Commit to Culprit - Inventory Service Tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the app
import sys
from pathlib import Path

# Add the service to the path
service_path = Path(__file__).parent.parent.parent.parent / "services" / "inventory-service" / "src"
sys.path.insert(0, str(service_path))

from inventory.main import app
from inventory.data import reset_inventory


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_inventory_state():
    """Reset inventory to initial state before each test."""
    reset_inventory()
    yield
    reset_inventory()


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "inventory-service"
        assert "version" in data

    def test_readiness_check(self, client):
        """Test readiness check endpoint returns ready status."""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()

        assert data["ready"] is True
        assert data["service"] == "inventory-service"
        assert "checks" in data
        assert data["checks"]["inventory_loaded"] is True
        assert data["checks"]["service_initialized"] is True


class TestStockCheck:
    """Test stock availability checking endpoint."""

    def test_check_stock_available(self, client):
        """Test checking stock for available items."""
        request_data = {
            "items": [
                {"item_id": "WIDGET-001", "quantity": 5},
                {"item_id": "GADGET-042", "quantity": 2}
            ]
        }

        response = client.post("/api/inventory/check", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["available"] is True
        assert data["message"] == "All items available"
        assert len(data["items"]) == 2

        # Check first item details
        widget_item = next(item for item in data["items"] if item["item_id"] == "WIDGET-001")
        assert widget_item["requested"] == 5
        assert widget_item["available"] == 1000
        assert widget_item["in_stock"] is True
        assert widget_item["price"] == 29.99

    def test_check_stock_insufficient(self, client):
        """Test checking stock when quantity exceeds available stock."""
        request_data = {
            "items": [
                {"item_id": "WIDGET-001", "quantity": 5000}  # More than available (1000)
            ]
        }

        response = client.post("/api/inventory/check", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["available"] is False
        assert data["message"] == "Some items unavailable"
        assert len(data["items"]) == 1

        widget_item = data["items"][0]
        assert widget_item["requested"] == 5000
        assert widget_item["available"] == 1000
        assert widget_item["in_stock"] is False

    def test_check_stock_item_not_found(self, client):
        """Test checking stock for non-existent item."""
        request_data = {
            "items": [
                {"item_id": "NON-EXISTENT-ITEM", "quantity": 1}
            ]
        }

        response = client.post("/api/inventory/check", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["available"] is False
        assert data["message"] == "Some items unavailable"
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert item["item_id"] == "NON-EXISTENT-ITEM"
        assert item["available"] == 0
        assert item["in_stock"] is False
        assert "error" in item

    def test_check_stock_missing_item_id(self, client):
        """Test checking stock with missing item_id."""
        request_data = {
            "items": [
                {"quantity": 5}  # Missing item_id
            ]
        }

        response = client.post("/api/inventory/check", json=request_data)

        assert response.status_code == 400
        assert "item_id" in response.json()["detail"].lower()

    def test_check_stock_mixed_availability(self, client):
        """Test checking stock with some available and some unavailable items."""
        request_data = {
            "items": [
                {"item_id": "WIDGET-001", "quantity": 5},
                {"item_id": "WIDGET-002", "quantity": 600}  # More than available (500)
            ]
        }

        response = client.post("/api/inventory/check", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["available"] is False
        assert data["message"] == "Some items unavailable"
        assert len(data["items"]) == 2


class TestInventoryReservation:
    """Test inventory reservation endpoint."""

    def test_reserve_items_success(self, client):
        """Test successful inventory reservation."""
        request_data = {
            "order_id": "order-12345",
            "items": [
                {"item_id": "WIDGET-001", "quantity": 10},
                {"item_id": "GADGET-042", "quantity": 5}
            ]
        }

        response = client.post("/api/inventory/reserve", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["order_id"] == "order-12345"
        assert data["reservation_id"] is not None
        assert data["reservation_id"].startswith("RES-")
        assert len(data["items_reserved"]) == 2

        # Verify stock was deducted
        summary_response = client.get("/api/inventory/summary")
        summary = summary_response.json()

        # WIDGET-001 should now have 990 (1000 - 10)
        assert summary["items"]["WIDGET-001"]["stock"] == 990
        # GADGET-042 should now have 245 (250 - 5)
        assert summary["items"]["GADGET-042"]["stock"] == 245

    def test_reserve_items_insufficient_stock(self, client):
        """Test reservation fails when stock is insufficient."""
        request_data = {
            "order_id": "order-99999",
            "items": [
                {"item_id": "WIDGET-001", "quantity": 5000}  # More than available
            ]
        }

        response = client.post("/api/inventory/reserve", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["order_id"] == "order-99999"
        assert data["reservation_id"] is None
        assert len(data["items_reserved"]) == 0
        assert "insufficient stock" in data["message"].lower()

    def test_reserve_items_no_items(self, client):
        """Test reservation fails when no items provided."""
        request_data = {
            "order_id": "order-00000",
            "items": []
        }

        response = client.post("/api/inventory/reserve", json=request_data)

        assert response.status_code == 400
        assert "no items" in response.json()["detail"].lower()

    def test_reserve_items_atomic_operation(self, client):
        """Test that reservation is atomic - all or nothing."""
        # Get initial stock levels
        summary_before = client.get("/api/inventory/summary").json()
        widget_stock_before = summary_before["items"]["WIDGET-001"]["stock"]
        gadget_stock_before = summary_before["items"]["GADGET-042"]["stock"]

        request_data = {
            "order_id": "order-atomic-test",
            "items": [
                {"item_id": "WIDGET-001", "quantity": 10},
                {"item_id": "GADGET-042", "quantity": 5000}  # Too many - will fail
            ]
        }

        response = client.post("/api/inventory/reserve", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

        # Verify NO stock was deducted (atomic operation)
        summary_after = client.get("/api/inventory/summary").json()
        assert summary_after["items"]["WIDGET-001"]["stock"] == widget_stock_before
        assert summary_after["items"]["GADGET-042"]["stock"] == gadget_stock_before


class TestInventorySummary:
    """Test inventory summary endpoint."""

    def test_get_inventory_summary(self, client):
        """Test retrieving inventory summary."""
        response = client.get("/api/inventory/summary")

        assert response.status_code == 200
        data = response.json()

        assert "total_items" in data
        assert "total_stock" in data
        assert "total_value" in data
        assert "items" in data

        assert data["total_items"] == 3
        assert data["total_stock"] == 1750  # 1000 + 500 + 250

        # Verify individual items
        assert "WIDGET-001" in data["items"]
        assert "WIDGET-002" in data["items"]
        assert "GADGET-042" in data["items"]

        # Check WIDGET-001 details
        widget = data["items"]["WIDGET-001"]
        assert widget["name"] == "Standard Widget"
        assert widget["stock"] == 1000
        assert widget["price"] == 29.99

    def test_inventory_summary_after_reservation(self, client):
        """Test summary reflects stock changes after reservation."""
        # Reserve some items
        reserve_request = {
            "order_id": "order-summary-test",
            "items": [
                {"item_id": "WIDGET-001", "quantity": 100}
            ]
        }
        client.post("/api/inventory/reserve", json=reserve_request)

        # Get summary
        response = client.get("/api/inventory/summary")
        data = response.json()

        # Stock should be reduced
        assert data["items"]["WIDGET-001"]["stock"] == 900  # 1000 - 100

        # Total stock should also be reduced
        assert data["total_stock"] == 1650  # 1750 - 100

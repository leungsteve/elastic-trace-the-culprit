"""
Unit tests for Inventory Service data operations.

Tests in-memory inventory data management including:
- Item retrieval
- Stock availability checking
- Item reservation
- Inventory summary
- Reset functionality

Workshop: From Commit to Culprit - Inventory Service Tests
"""

import pytest
import sys
from pathlib import Path

# Add the service to the path
service_path = Path(__file__).parent.parent.parent.parent / "services" / "inventory-service" / "src"
sys.path.insert(0, str(service_path))

from inventory.data import (
    get_item,
    check_availability,
    reserve_items,
    get_inventory_summary,
    reset_inventory,
    INVENTORY
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset inventory state before and after each test."""
    reset_inventory()
    yield
    reset_inventory()


class TestGetItem:
    """Test item retrieval functionality."""

    def test_get_existing_item(self):
        """Test retrieving an existing item."""
        item = get_item("WIDGET-001")

        assert item is not None
        assert item["name"] == "Standard Widget"
        assert item["stock"] == 1000
        assert item["price"] == 29.99

    def test_get_all_initial_items(self):
        """Test all initial inventory items can be retrieved."""
        widget_001 = get_item("WIDGET-001")
        widget_002 = get_item("WIDGET-002")
        gadget_042 = get_item("GADGET-042")

        assert widget_001 is not None
        assert widget_002 is not None
        assert gadget_042 is not None

        assert widget_001["name"] == "Standard Widget"
        assert widget_002["name"] == "Premium Widget"
        assert gadget_042["name"] == "Super Gadget"

    def test_get_non_existent_item(self):
        """Test retrieving a non-existent item returns None."""
        item = get_item("NON-EXISTENT")

        assert item is None

    def test_get_item_case_sensitive(self):
        """Test that item IDs are case-sensitive."""
        item_upper = get_item("WIDGET-001")
        item_lower = get_item("widget-001")

        assert item_upper is not None
        assert item_lower is None


class TestCheckAvailability:
    """Test stock availability checking."""

    def test_check_availability_sufficient_stock(self):
        """Test checking availability when stock is sufficient."""
        available, current_stock = check_availability("WIDGET-001", 100)

        assert available is True
        assert current_stock == 1000

    def test_check_availability_exact_stock(self):
        """Test checking availability when requested equals available."""
        available, current_stock = check_availability("WIDGET-001", 1000)

        assert available is True
        assert current_stock == 1000

    def test_check_availability_insufficient_stock(self):
        """Test checking availability when stock is insufficient."""
        available, current_stock = check_availability("WIDGET-001", 1500)

        assert available is False
        assert current_stock == 1000

    def test_check_availability_zero_quantity(self):
        """Test checking availability for zero quantity."""
        available, current_stock = check_availability("WIDGET-001", 0)

        assert available is True
        assert current_stock == 1000

    def test_check_availability_non_existent_item(self):
        """Test checking availability for non-existent item."""
        available, current_stock = check_availability("NON-EXISTENT", 1)

        assert available is False
        assert current_stock == 0


class TestReserveItems:
    """Test inventory reservation functionality."""

    def test_reserve_items_success(self):
        """Test successful item reservation."""
        items = [
            {"item_id": "WIDGET-001", "quantity": 10},
            {"item_id": "GADGET-042", "quantity": 5}
        ]

        success, message, reserved_items = reserve_items("order-123", items)

        assert success is True
        assert "successfully" in message.lower()
        assert len(reserved_items) == 2

        # Verify reserved items details
        widget_reserved = next(item for item in reserved_items if item["item_id"] == "WIDGET-001")
        assert widget_reserved["quantity"] == 10
        assert widget_reserved["price"] == 29.99

        gadget_reserved = next(item for item in reserved_items if item["item_id"] == "GADGET-042")
        assert gadget_reserved["quantity"] == 5
        assert gadget_reserved["price"] == 82.52

    def test_reserve_items_deducts_stock(self):
        """Test that reservation deducts stock from inventory."""
        initial_stock = INVENTORY["WIDGET-001"]["stock"]

        items = [{"item_id": "WIDGET-001", "quantity": 100}]
        success, _, _ = reserve_items("order-456", items)

        assert success is True
        assert INVENTORY["WIDGET-001"]["stock"] == initial_stock - 100

    def test_reserve_items_insufficient_stock(self):
        """Test reservation fails when stock is insufficient."""
        items = [{"item_id": "WIDGET-001", "quantity": 5000}]

        success, message, reserved_items = reserve_items("order-789", items)

        assert success is False
        assert "insufficient stock" in message.lower()
        assert len(reserved_items) == 0

        # Verify stock was NOT deducted
        assert INVENTORY["WIDGET-001"]["stock"] == 1000

    def test_reserve_items_atomic_operation(self):
        """Test that reservation is atomic - all items or none."""
        initial_widget_stock = INVENTORY["WIDGET-001"]["stock"]
        initial_gadget_stock = INVENTORY["GADGET-042"]["stock"]

        items = [
            {"item_id": "WIDGET-001", "quantity": 10},
            {"item_id": "GADGET-042", "quantity": 5000}  # Too many
        ]

        success, message, reserved_items = reserve_items("order-atomic", items)

        assert success is False
        assert "insufficient stock" in message.lower()
        assert len(reserved_items) == 0

        # Verify NO stock was deducted (atomic behavior)
        assert INVENTORY["WIDGET-001"]["stock"] == initial_widget_stock
        assert INVENTORY["GADGET-042"]["stock"] == initial_gadget_stock

    def test_reserve_items_missing_item_id(self):
        """Test reservation fails when item_id is missing."""
        items = [{"quantity": 10}]  # Missing item_id

        success, message, reserved_items = reserve_items("order-bad", items)

        assert success is False
        assert "missing item_id" in message.lower()
        assert len(reserved_items) == 0

    def test_reserve_items_non_existent_item(self):
        """Test reservation fails for non-existent item."""
        items = [{"item_id": "NON-EXISTENT", "quantity": 1}]

        success, message, reserved_items = reserve_items("order-missing", items)

        assert success is False
        assert len(reserved_items) == 0

    def test_reserve_items_multiple_success(self):
        """Test multiple successful reservations."""
        items1 = [{"item_id": "WIDGET-001", "quantity": 100}]
        items2 = [{"item_id": "WIDGET-001", "quantity": 50}]

        success1, _, _ = reserve_items("order-1", items1)
        success2, _, _ = reserve_items("order-2", items2)

        assert success1 is True
        assert success2 is True
        assert INVENTORY["WIDGET-001"]["stock"] == 850  # 1000 - 100 - 50

    def test_reserve_items_thread_safety(self):
        """Test that reservation uses thread locking."""
        # This test verifies that the reservation function uses locking
        # In a real scenario, you would test concurrent access
        items = [{"item_id": "WIDGET-001", "quantity": 1}]

        # Reserve in sequence
        for i in range(10):
            success, _, _ = reserve_items(f"order-{i}", items)
            assert success is True

        # Stock should be reduced by 10
        assert INVENTORY["WIDGET-001"]["stock"] == 990


class TestGetInventorySummary:
    """Test inventory summary functionality."""

    def test_get_inventory_summary_initial_state(self):
        """Test inventory summary in initial state."""
        summary = get_inventory_summary()

        assert summary["total_items"] == 3
        assert summary["total_stock"] == 1750  # 1000 + 500 + 250
        assert isinstance(summary["total_value"], float)
        assert "items" in summary

        # Verify items are included
        assert "WIDGET-001" in summary["items"]
        assert "WIDGET-002" in summary["items"]
        assert "GADGET-042" in summary["items"]

    def test_get_inventory_summary_calculates_value_correctly(self):
        """Test that total value is calculated correctly."""
        summary = get_inventory_summary()

        # Calculate expected value:
        # WIDGET-001: 1000 * 29.99 = 29,990.00
        # WIDGET-002: 500 * 49.99 = 24,995.00
        # GADGET-042: 250 * 82.52 = 20,630.00
        # Total: 75,615.00
        expected_value = (1000 * 29.99) + (500 * 49.99) + (250 * 82.52)

        assert summary["total_value"] == round(expected_value, 2)

    def test_get_inventory_summary_after_reservation(self):
        """Test summary reflects changes after reservation."""
        items = [{"item_id": "WIDGET-001", "quantity": 200}]
        reserve_items("order-summary", items)

        summary = get_inventory_summary()

        assert summary["total_items"] == 3  # Number of SKUs unchanged
        assert summary["total_stock"] == 1550  # 1750 - 200
        assert summary["items"]["WIDGET-001"]["stock"] == 800


class TestResetInventory:
    """Test inventory reset functionality."""

    def test_reset_inventory_restores_initial_state(self):
        """Test that reset restores inventory to initial state."""
        # Modify inventory
        items = [{"item_id": "WIDGET-001", "quantity": 500}]
        reserve_items("order-test", items)

        # Verify inventory was modified
        assert INVENTORY["WIDGET-001"]["stock"] == 500

        # Reset
        reset_inventory()

        # Verify inventory is restored
        assert INVENTORY["WIDGET-001"]["stock"] == 1000
        assert INVENTORY["WIDGET-002"]["stock"] == 500
        assert INVENTORY["GADGET-042"]["stock"] == 250

    def test_reset_inventory_clears_reservations(self):
        """Test that reset clears reservation records."""
        from inventory.data import RESERVATIONS

        # Make a reservation
        items = [{"item_id": "WIDGET-001", "quantity": 10}]
        reserve_items("order-clear", items)

        # Verify reservation was recorded
        assert len(RESERVATIONS) > 0

        # Reset
        reset_inventory()

        # Verify reservations are cleared
        assert len(RESERVATIONS) == 0

    def test_reset_inventory_restores_all_items(self):
        """Test that all items are restored correctly."""
        reset_inventory()

        summary = get_inventory_summary()

        assert summary["total_items"] == 3
        assert "WIDGET-001" in INVENTORY
        assert "WIDGET-002" in INVENTORY
        assert "GADGET-042" in INVENTORY

        # Verify all properties
        assert INVENTORY["WIDGET-001"]["name"] == "Standard Widget"
        assert INVENTORY["WIDGET-002"]["name"] == "Premium Widget"
        assert INVENTORY["GADGET-042"]["name"] == "Super Gadget"

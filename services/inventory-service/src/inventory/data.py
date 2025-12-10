"""
In-memory inventory data store
-------------------------------
This module provides the inventory database (in-memory) for the workshop.
In a real application, this would be backed by a persistent database.
"""

import threading
from typing import Dict, Optional
from datetime import datetime


# In-memory inventory store
# This is stateless across restarts (intentionally for workshop simplicity)
INVENTORY: Dict[str, dict] = {
    "WIDGET-001": {
        "name": "Standard Widget",
        "stock": 1000,
        "price": 29.99
    },
    "WIDGET-002": {
        "name": "Premium Widget",
        "stock": 500,
        "price": 49.99
    },
    "GADGET-042": {
        "name": "Super Gadget",
        "stock": 250,
        "price": 82.52
    },
}

# Thread lock for inventory operations (simulate database transactions)
inventory_lock = threading.Lock()

# In-memory reservation store (order_id -> reservation details)
RESERVATIONS: Dict[str, dict] = {}


def get_item(item_id: str) -> Optional[dict]:
    """
    Retrieve an inventory item by ID.

    Args:
        item_id: The item SKU/ID

    Returns:
        Item details dict or None if not found
    """
    return INVENTORY.get(item_id)


def check_availability(item_id: str, quantity: int) -> tuple[bool, int]:
    """
    Check if requested quantity is available for an item.

    Args:
        item_id: The item SKU/ID
        quantity: Requested quantity

    Returns:
        Tuple of (is_available: bool, current_stock: int)
    """
    item = INVENTORY.get(item_id)
    if not item:
        return False, 0

    current_stock = item.get("stock", 0)
    return current_stock >= quantity, current_stock


def reserve_items(order_id: str, items: list[dict]) -> tuple[bool, str, list[dict]]:
    """
    Reserve inventory items for an order.

    This is an atomic operation - either all items are reserved or none.
    In a real system, this would use database transactions.

    Args:
        order_id: The order ID
        items: List of dicts with 'item_id' and 'quantity'

    Returns:
        Tuple of (success: bool, message: str, reserved_items: list)
    """
    with inventory_lock:
        # First, verify all items are available
        for item in items:
            item_id = item.get("item_id")
            quantity = item.get("quantity", 0)

            if not item_id:
                return False, "Invalid item: missing item_id", []

            available, current_stock = check_availability(item_id, quantity)
            if not available:
                return False, f"Insufficient stock for {item_id}: requested {quantity}, available {current_stock}", []

        # All items available - proceed with reservation
        reserved = []
        for item in items:
            item_id = item["item_id"]
            quantity = item["quantity"]

            # Deduct from inventory
            INVENTORY[item_id]["stock"] -= quantity

            reserved.append({
                "item_id": item_id,
                "quantity": quantity,
                "price": INVENTORY[item_id]["price"]
            })

        # Store reservation
        reservation_id = f"RES-{order_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        RESERVATIONS[order_id] = {
            "reservation_id": reservation_id,
            "order_id": order_id,
            "items": reserved,
            "timestamp": datetime.now().isoformat()
        }

        return True, "Inventory reserved successfully", reserved


def get_inventory_summary() -> dict:
    """
    Get a summary of current inventory levels.

    Returns:
        Dict with inventory statistics
    """
    total_items = len(INVENTORY)
    total_stock = sum(item["stock"] for item in INVENTORY.values())
    total_value = sum(item["stock"] * item["price"] for item in INVENTORY.values())

    return {
        "total_items": total_items,
        "total_stock": total_stock,
        "total_value": round(total_value, 2),
        "items": INVENTORY
    }


def reset_inventory():
    """
    Reset inventory to initial state.
    Useful for testing and workshop scenarios.
    """
    global INVENTORY, RESERVATIONS

    with inventory_lock:
        INVENTORY = {
            "WIDGET-001": {
                "name": "Standard Widget",
                "stock": 1000,
                "price": 29.99
            },
            "WIDGET-002": {
                "name": "Premium Widget",
                "stock": 500,
                "price": 49.99
            },
            "GADGET-042": {
                "name": "Super Gadget",
                "stock": 250,
                "price": 82.52
            },
        }
        RESERVATIONS = {}

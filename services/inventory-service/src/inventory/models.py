"""
Pydantic models for Inventory Service API
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    """
    Represents an inventory item with stock and pricing information.
    """
    item_id: str = Field(..., description="Unique item identifier (SKU)")
    name: str = Field(..., description="Item display name")
    stock: int = Field(..., ge=0, description="Available stock quantity")
    price: float = Field(..., gt=0, description="Item price in USD")


class StockCheckRequest(BaseModel):
    """
    Request to check stock availability for multiple items.
    """
    items: List[dict] = Field(..., description="List of items with item_id and quantity")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"item_id": "WIDGET-001", "quantity": 5},
                    {"item_id": "GADGET-042", "quantity": 2}
                ]
            }
        }


class StockCheckResponse(BaseModel):
    """
    Response indicating stock availability for requested items.
    """
    available: bool = Field(..., description="Whether all items are in stock")
    items: List[dict] = Field(..., description="Item availability details")
    message: Optional[str] = Field(None, description="Additional information")

    class Config:
        json_schema_extra = {
            "example": {
                "available": True,
                "items": [
                    {"item_id": "WIDGET-001", "requested": 5, "available": 1000, "in_stock": True},
                    {"item_id": "GADGET-042", "requested": 2, "available": 250, "in_stock": True}
                ],
                "message": "All items available"
            }
        }


class ReservationRequest(BaseModel):
    """
    Request to reserve inventory items for an order.
    """
    order_id: str = Field(..., description="Order ID for tracking")
    items: List[dict] = Field(..., description="List of items with item_id and quantity")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD-12345",
                "items": [
                    {"item_id": "WIDGET-001", "quantity": 5},
                    {"item_id": "GADGET-042", "quantity": 2}
                ]
            }
        }


class ReservationResponse(BaseModel):
    """
    Response for inventory reservation request.
    """
    success: bool = Field(..., description="Whether reservation succeeded")
    order_id: str = Field(..., description="Order ID")
    reservation_id: Optional[str] = Field(None, description="Reservation ID if successful")
    items_reserved: List[dict] = Field(default_factory=list, description="Successfully reserved items")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "order_id": "ORD-12345",
                "reservation_id": "RES-67890",
                "items_reserved": [
                    {"item_id": "WIDGET-001", "quantity": 5},
                    {"item_id": "GADGET-042", "quantity": 2}
                ],
                "message": "Inventory reserved successfully"
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response.
    """
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")


class ReadinessResponse(BaseModel):
    """
    Readiness check response.
    """
    ready: bool = Field(..., description="Whether service is ready to accept traffic")
    service: str = Field(..., description="Service name")
    checks: dict = Field(..., description="Individual readiness checks")

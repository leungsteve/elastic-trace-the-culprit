"""
Payment Service Models
From Commit to Culprit Workshop

Pydantic models for payment processing requests and responses.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PaymentMethod(str, Enum):
    """Supported payment methods."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(str, Enum):
    """Payment processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentRequest(BaseModel):
    """Request to process a payment."""

    order_id: str = Field(..., description="The order ID from the Order Service")
    amount: Decimal = Field(..., gt=0, description="Payment amount in USD")
    currency: str = Field(default="USD", description="Currency code")
    payment_method: PaymentMethod = Field(..., description="Payment method to use")
    customer_id: str = Field(..., description="Customer identifier")
    idempotency_key: Optional[str] = Field(
        default=None, description="Client-provided idempotency key"
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount has max 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency is uppercase."""
        return v.upper()


class PaymentResponse(BaseModel):
    """Response from payment processing."""

    payment_id: UUID = Field(default_factory=uuid4, description="Unique payment identifier")
    order_id: str = Field(..., description="Associated order ID")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    status: PaymentStatus = Field(..., description="Current payment status")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    transaction_id: Optional[str] = Field(
        default=None, description="External transaction ID from payment gateway"
    )
    failure_reason: Optional[str] = Field(default=None, description="Reason for failure if any")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        json_encoders = {
            UUID: str,
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Deployment environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

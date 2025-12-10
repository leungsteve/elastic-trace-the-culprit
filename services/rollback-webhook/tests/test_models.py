"""
Tests for Pydantic models.

From Commit to Culprit Workshop - Rollback Webhook Service
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.webhook.models import (
    RollbackRequest,
    RollbackResponse,
    RollbackStatus,
    ServiceName,
)


def test_rollback_request_valid():
    """Test creating a valid RollbackRequest."""
    request = RollbackRequest(
        service=ServiceName.ORDER_SERVICE,
        target_version="v1.0",
        alert_id="test-alert-123",
        reason="Test rollback",
    )

    assert request.service == ServiceName.ORDER_SERVICE
    assert request.target_version == "v1.0"
    assert request.alert_id == "test-alert-123"
    assert request.reason == "Test rollback"


def test_rollback_request_with_optional_fields():
    """Test RollbackRequest with optional fields."""
    request = RollbackRequest(
        service=ServiceName.INVENTORY_SERVICE,
        target_version="v2.0",
        alert_id="alert-456",
        alert_name="Inventory Alert",
        reason="Performance degradation",
        triggered_at=datetime.utcnow(),
        additional_context={"metric": "latency", "value": 500},
    )

    assert request.alert_name == "Inventory Alert"
    assert request.additional_context["metric"] == "latency"


def test_rollback_request_invalid_service():
    """Test that invalid service names are rejected."""
    with pytest.raises(ValidationError):
        RollbackRequest(
            service="invalid-service",  # Not a valid ServiceName
            target_version="v1.0",
            alert_id="test",
            reason="Test",
        )


def test_rollback_response_completed():
    """Test creating a successful RollbackResponse."""
    response = RollbackResponse(
        status=RollbackStatus.ROLLBACK_COMPLETED,
        message="Rollback completed successfully",
        service=ServiceName.ORDER_SERVICE,
        previous_version="v1.1-bad",
        target_version="v1.0",
        rollback_id="rb-test-123",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        trace_id="abc123",
    )

    assert response.status == RollbackStatus.ROLLBACK_COMPLETED
    assert response.previous_version == "v1.1-bad"
    assert response.target_version == "v1.0"
    assert response.error is None


def test_rollback_response_failed():
    """Test creating a failed RollbackResponse."""
    response = RollbackResponse(
        status=RollbackStatus.ROLLBACK_FAILED,
        message="Rollback failed",
        service=ServiceName.PAYMENT_SERVICE,
        target_version="v1.0",
        rollback_id="rb-fail-456",
        started_at=datetime.utcnow(),
        error="Docker not available",
    )

    assert response.status == RollbackStatus.ROLLBACK_FAILED
    assert response.error == "Docker not available"
    assert response.completed_at is None


def test_service_name_enum():
    """Test ServiceName enum values."""
    assert ServiceName.ORDER_SERVICE.value == "order-service"
    assert ServiceName.INVENTORY_SERVICE.value == "inventory-service"
    assert ServiceName.PAYMENT_SERVICE.value == "payment-service"


def test_rollback_status_enum():
    """Test RollbackStatus enum values."""
    assert RollbackStatus.ROLLBACK_INITIATED.value == "ROLLBACK_INITIATED"
    assert RollbackStatus.ROLLBACK_COMPLETED.value == "ROLLBACK_COMPLETED"
    assert RollbackStatus.ROLLBACK_FAILED.value == "ROLLBACK_FAILED"

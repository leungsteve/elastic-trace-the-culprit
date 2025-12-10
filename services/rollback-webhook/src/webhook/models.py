"""
Pydantic models for rollback webhook requests and responses.

From Commit to Culprit Workshop - Rollback Webhook Service
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RollbackStatus(str, Enum):
    """Status of a rollback operation."""

    ROLLBACK_INITIATED = "ROLLBACK_INITIATED"
    ROLLBACK_IN_PROGRESS = "ROLLBACK_IN_PROGRESS"
    ROLLBACK_COMPLETED = "ROLLBACK_COMPLETED"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"


class ServiceName(str, Enum):
    """Valid service names that can be rolled back."""

    ORDER_SERVICE = "order-service"
    INVENTORY_SERVICE = "inventory-service"
    PAYMENT_SERVICE = "payment-service"


class RollbackRequest(BaseModel):
    """
    Webhook request from Elastic Alerting to trigger a rollback.

    This is sent by the Elastic Alerting workflow when an SLO burn rate
    or latency threshold alert fires.
    """

    service: ServiceName = Field(
        ..., description="Name of the service to rollback (e.g., 'order-service')"
    )
    target_version: str = Field(
        ..., description="Target version to rollback to (e.g., 'v1.0')"
    )
    alert_id: str = Field(..., description="Elastic alert rule ID that triggered this rollback")
    alert_name: Optional[str] = Field(
        None, description="Human-readable alert name for logging"
    )
    reason: str = Field(..., description="Reason for rollback (e.g., 'SLO burn rate exceeded')")
    triggered_at: Optional[datetime] = Field(
        None, description="When the alert was triggered (ISO 8601)"
    )
    additional_context: Optional[dict] = Field(
        None, description="Additional context from the alert (SLO values, error rates, etc.)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "service": "order-service",
                    "target_version": "v1.0",
                    "alert_id": "slo-burn-rate-order-service",
                    "alert_name": "Order Service SLO Burn Rate Alert",
                    "reason": "SLO burn rate exceeded threshold",
                    "triggered_at": "2025-12-09T15:30:45Z",
                    "additional_context": {
                        "slo_name": "order-service-latency",
                        "burn_rate": 14.5,
                        "threshold": 10.0,
                        "current_latency_p95": 2500,
                        "baseline_latency_p95": 250,
                    },
                }
            ]
        }
    }


class RollbackResponse(BaseModel):
    """
    Response from the rollback webhook.

    Sent back to Elastic (and stored for the /status endpoint).
    """

    status: RollbackStatus = Field(..., description="Current status of the rollback operation")
    message: str = Field(..., description="Human-readable message about the rollback")
    service: ServiceName = Field(..., description="Service that was rolled back")
    previous_version: Optional[str] = Field(None, description="Version before rollback")
    target_version: str = Field(..., description="Version after rollback")
    rollback_id: str = Field(..., description="Unique ID for this rollback operation")
    started_at: datetime = Field(..., description="When the rollback started")
    completed_at: Optional[datetime] = Field(None, description="When the rollback completed")
    error: Optional[str] = Field(None, description="Error message if rollback failed")
    trace_id: Optional[str] = Field(
        None, description="OpenTelemetry trace ID for correlation with logs"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ROLLBACK_COMPLETED",
                    "message": "Successfully rolled back order-service from v1.1-bad to v1.0",
                    "service": "order-service",
                    "previous_version": "v1.1-bad",
                    "target_version": "v1.0",
                    "rollback_id": "rb-20251209-153045-abc123",
                    "started_at": "2025-12-09T15:30:45Z",
                    "completed_at": "2025-12-09T15:31:12Z",
                    "trace_id": "4a8d3f6b2e1c9a7b5d3e1f9c8a6b4d2e",
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service health status")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Deployment environment (local or instruqt)")
    docker_available: bool = Field(..., description="Whether Docker CLI is accessible")


class ReadyResponse(BaseModel):
    """Readiness check response."""

    ready: bool = Field(..., description="Whether the service is ready to accept requests")
    checks: dict = Field(
        ..., description="Individual readiness checks (docker, env_file, compose_file)"
    )


class StatusResponse(BaseModel):
    """Status response showing the last rollback operation."""

    last_rollback: Optional[RollbackResponse] = Field(
        None, description="Details of the last rollback, if any"
    )
    total_rollbacks: int = Field(default=0, description="Total number of rollbacks performed")
    service_uptime_seconds: float = Field(..., description="Service uptime in seconds")

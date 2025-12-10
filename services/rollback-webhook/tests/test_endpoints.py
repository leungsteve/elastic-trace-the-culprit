"""
Tests for FastAPI endpoints.

From Commit to Culprit Workshop - Rollback Webhook Service
"""

import pytest
from fastapi.testclient import TestClient

from src.webhook.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns service information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "rollback-webhook"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data
    assert "uptime_seconds" in data


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "docker_available" in data


def test_ready_endpoint():
    """Test the readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert "ready" in data
    assert "checks" in data
    assert "docker" in data["checks"]
    assert "env_file" in data["checks"]
    assert "compose_file" in data["checks"]


def test_status_endpoint_no_rollbacks():
    """Test the status endpoint when no rollbacks have occurred."""
    response = client.get("/status")
    assert response.status_code == 200

    data = response.json()
    assert data["total_rollbacks"] == 0
    assert data["last_rollback"] is None
    assert "service_uptime_seconds" in data


def test_rollback_endpoint_invalid_service():
    """Test the rollback endpoint with invalid service name."""
    response = client.post(
        "/rollback",
        json={
            "service": "invalid-service",
            "target_version": "v1.0",
            "alert_id": "test",
            "reason": "test",
        },
    )
    assert response.status_code == 422  # Validation error


def test_rollback_endpoint_missing_fields():
    """Test the rollback endpoint with missing required fields."""
    response = client.post(
        "/rollback",
        json={
            "service": "order-service",
            # Missing target_version, alert_id, reason
        },
    )
    assert response.status_code == 422  # Validation error


def test_docs_endpoint():
    """Test that the OpenAPI docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that the OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "Rollback Webhook Service"
    assert schema["info"]["version"] == "1.0.0"

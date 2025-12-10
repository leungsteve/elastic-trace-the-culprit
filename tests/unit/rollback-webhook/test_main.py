"""
Unit tests for Rollback Webhook Service FastAPI endpoints.

Tests the REST API endpoints including:
- Rollback trigger endpoint
- Health and readiness checks
- Status endpoint
- Root endpoint

Workshop: From Commit to Culprit - Rollback Webhook Service Tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the service to the path
service_path = Path(__file__).parent.parent.parent.parent / "services" / "rollback-webhook" / "src"
sys.path.insert(0, str(service_path))

from webhook.main import app
from webhook.models import ServiceName, RollbackStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "rollback-webhook"
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "endpoints" in data

        # Verify endpoints documentation
        endpoints = data["endpoints"]
        assert "POST /rollback" in endpoints
        assert "GET /health" in endpoints
        assert "GET /ready" in endpoints
        assert "GET /status" in endpoints


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_check_without_docker(self, client):
        """Test health check when Docker is not available."""
        with patch("subprocess.run") as mock_run:
            # Simulate Docker not available
            mock_run.return_value = MagicMock(returncode=1)

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["version"] is not None
            assert data["docker_available"] is False

    def test_health_check_with_docker(self, client):
        """Test health check when Docker is available."""
        with patch("subprocess.run") as mock_run:
            # Simulate Docker available
            mock_run.return_value = MagicMock(returncode=0)

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["docker_available"] is True

    def test_health_check_docker_exception(self, client):
        """Test health check when Docker check raises exception."""
        with patch("subprocess.run") as mock_run:
            # Simulate exception
            mock_run.side_effect = Exception("Docker error")

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["docker_available"] is False

    def test_readiness_check_all_ready(self, client):
        """Test readiness check when all dependencies are ready."""
        with patch("subprocess.run") as mock_run, \
             patch("os.path.exists") as mock_exists:

            # Simulate all checks pass
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = True

            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()

            assert data["ready"] is True
            assert data["checks"]["docker"] is True
            assert data["checks"]["env_file"] is True
            assert data["checks"]["compose_file"] is True

    def test_readiness_check_docker_not_ready(self, client):
        """Test readiness check when Docker is not ready."""
        with patch("subprocess.run") as mock_run, \
             patch("os.path.exists") as mock_exists:

            # Simulate Docker not ready
            mock_run.return_value = MagicMock(returncode=1)
            mock_exists.return_value = True

            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()

            assert data["ready"] is False
            assert data["checks"]["docker"] is False
            assert data["checks"]["env_file"] is True
            assert data["checks"]["compose_file"] is True

    def test_readiness_check_files_not_ready(self, client):
        """Test readiness check when required files are missing."""
        with patch("subprocess.run") as mock_run, \
             patch("os.path.exists") as mock_exists:

            # Simulate files not found
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = False

            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()

            assert data["ready"] is False
            assert data["checks"]["docker"] is True
            assert data["checks"]["env_file"] is False
            assert data["checks"]["compose_file"] is False


class TestStatusEndpoint:
    """Test status endpoint."""

    def test_status_no_rollbacks(self, client):
        """Test status endpoint when no rollbacks have been performed."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()

        assert data["total_rollbacks"] == 0
        assert data["last_rollback"] is None
        assert "service_uptime_seconds" in data
        assert data["service_uptime_seconds"] >= 0

    @patch("webhook.main.rollback_executor")
    def test_status_with_rollback_history(self, mock_executor, client):
        """Test status endpoint after a rollback has been performed."""
        # Mock last rollback
        mock_last_rollback = MagicMock()
        mock_last_rollback.status = RollbackStatus.ROLLBACK_COMPLETED

        mock_executor.last_rollback = mock_last_rollback
        mock_executor.total_rollbacks = 3

        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()

        assert data["total_rollbacks"] == 3


class TestRollbackEndpoint:
    """Test rollback trigger endpoint."""

    @patch("webhook.main.rollback_executor")
    def test_trigger_rollback_success(self, mock_executor, client):
        """Test successful rollback trigger."""
        # Mock successful rollback
        mock_response = MagicMock()
        mock_response.status = RollbackStatus.ROLLBACK_COMPLETED
        mock_response.rollback_id = "rb-20250101-120000-order-service"
        mock_response.service = ServiceName.ORDER_SERVICE
        mock_response.target_version = "v1.0"
        mock_response.previous_version = "v1.1-bad"
        mock_response.message = "Rollback completed successfully"
        mock_response.error = None
        mock_response.trace_id = None

        mock_executor.execute_rollback.return_value = mock_response

        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "alert-123",
            "alert_name": "SLO Burn Rate",
            "reason": "High latency detected"
        }

        response = client.post("/rollback", json=rollback_request)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rollback_completed"
        assert data["rollback_id"] == "rb-20250101-120000-order-service"
        assert data["service"] == "order-service"
        assert data["target_version"] == "v1.0"
        assert data["previous_version"] == "v1.1-bad"

    @patch("webhook.main.rollback_executor")
    def test_trigger_rollback_failure(self, mock_executor, client):
        """Test rollback trigger when rollback fails."""
        # Mock failed rollback
        mock_response = MagicMock()
        mock_response.status = RollbackStatus.ROLLBACK_FAILED
        mock_response.rollback_id = "rb-20250101-120001-order-service"
        mock_response.service = ServiceName.ORDER_SERVICE
        mock_response.target_version = "v1.0"
        mock_response.error = "Docker not available"
        mock_response.message = "Rollback failed"

        mock_executor.execute_rollback.return_value = mock_response

        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "alert-456",
            "alert_name": "SLO Burn Rate",
            "reason": "High latency detected"
        }

        response = client.post("/rollback", json=rollback_request)

        # Even on failure, endpoint returns 200 with error details in response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rollback_failed"
        assert data["error"] == "Docker not available"

    def test_trigger_rollback_invalid_service(self, client):
        """Test rollback with invalid service name."""
        rollback_request = {
            "service": "invalid-service",
            "target_version": "v1.0",
            "alert_id": "alert-789",
            "alert_name": "Test Alert",
            "reason": "Testing"
        }

        response = client.post("/rollback", json=rollback_request)

        # Should fail validation
        assert response.status_code == 422

    def test_trigger_rollback_missing_fields(self, client):
        """Test rollback with missing required fields."""
        rollback_request = {
            "service": "order-service"
            # Missing target_version, alert_id, etc.
        }

        response = client.post("/rollback", json=rollback_request)

        # Should fail validation
        assert response.status_code == 422

    @patch("webhook.main.rollback_executor")
    def test_trigger_rollback_for_inventory_service(self, mock_executor, client):
        """Test rollback for inventory service."""
        mock_response = MagicMock()
        mock_response.status = RollbackStatus.ROLLBACK_COMPLETED
        mock_response.rollback_id = "rb-20250101-120002-inventory-service"
        mock_response.service = ServiceName.INVENTORY_SERVICE
        mock_response.target_version = "v1.0"

        mock_executor.execute_rollback.return_value = mock_response

        rollback_request = {
            "service": "inventory-service",
            "target_version": "v1.0",
            "alert_id": "alert-inventory",
            "alert_name": "Inventory Alert",
            "reason": "Inventory service degradation"
        }

        response = client.post("/rollback", json=rollback_request)

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "inventory-service"

    @patch("webhook.main.rollback_executor")
    def test_trigger_rollback_for_payment_service(self, mock_executor, client):
        """Test rollback for payment service."""
        mock_response = MagicMock()
        mock_response.status = RollbackStatus.ROLLBACK_COMPLETED
        mock_response.rollback_id = "rb-20250101-120003-payment-service"
        mock_response.service = ServiceName.PAYMENT_SERVICE
        mock_response.target_version = "v1.0"

        mock_executor.execute_rollback.return_value = mock_response

        rollback_request = {
            "service": "payment-service",
            "target_version": "v1.0",
            "alert_id": "alert-payment",
            "alert_name": "Payment Alert",
            "reason": "Payment service issues"
        }

        response = client.post("/rollback", json=rollback_request)

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "payment-service"


class TestExceptionHandling:
    """Test global exception handling."""

    @patch("webhook.main.rollback_executor")
    def test_unhandled_exception(self, mock_executor, client):
        """Test that unhandled exceptions are caught and logged."""
        # Make execute_rollback raise an exception
        mock_executor.execute_rollback.side_effect = Exception("Unexpected error")

        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "alert-exception",
            "alert_name": "Test Alert",
            "reason": "Testing exception handling"
        }

        response = client.post("/rollback", json=rollback_request)

        # Global exception handler should catch it
        assert response.status_code == 500
        data = response.json()

        assert "error" in data
        assert data["error"] == "Internal server error"

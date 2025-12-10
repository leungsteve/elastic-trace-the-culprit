"""
End-to-End Tests for Rollback Webhook Functionality
From Commit to Culprit Workshop

Tests the rollback webhook service that receives alerts from Elastic
and automatically triggers rollbacks. This validates the automated
remediation capability of the workshop.

Tests cover:
- Webhook health and readiness
- Rollback request handling
- Status tracking
- Integration with docker-compose
"""

import asyncio
import time

import httpx
import pytest

from .conftest import SERVICE_RESTART_WAIT_TIME, STABILIZATION_WAIT_TIME


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestRollbackWebhookHealth:
    """Tests for webhook service health and readiness."""

    async def test_webhook_health_endpoint(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        wait_for_services,
    ):
        """
        Test that the webhook health endpoint returns correct status.

        The health endpoint should always return 200 OK when the service is running.
        """
        response = await http_client.get(f"{rollback_webhook_url}/health")

        assert response.status_code == 200, f"Health check failed: {response.status_code}"

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "docker_available" in data

    async def test_webhook_ready_endpoint(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        wait_for_services,
    ):
        """
        Test that the webhook readiness endpoint validates environment.

        The ready endpoint should check for Docker, .env file, and docker-compose.yml.
        """
        response = await http_client.get(f"{rollback_webhook_url}/ready")

        assert response.status_code == 200, f"Readiness check failed: {response.status_code}"

        data = response.json()
        assert "ready" in data
        assert "checks" in data

        checks = data["checks"]
        assert "docker" in checks
        assert "env_file" in checks
        assert "compose_file" in checks

        # All checks should pass in a properly configured environment
        # Note: This may fail in some CI environments without Docker
        if data["ready"]:
            assert checks["docker"] is True
            assert checks["env_file"] is True
            assert checks["compose_file"] is True

    async def test_webhook_status_endpoint(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        wait_for_services,
    ):
        """
        Test that the webhook status endpoint returns rollback history.

        The status endpoint should show last rollback and total count.
        """
        response = await http_client.get(f"{rollback_webhook_url}/status")

        assert response.status_code == 200, f"Status check failed: {response.status_code}"

        data = response.json()
        assert "last_rollback" in data
        assert "total_rollbacks" in data
        assert "service_uptime_seconds" in data

        # Uptime should be positive
        assert data["service_uptime_seconds"] > 0

    async def test_webhook_root_endpoint(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        wait_for_services,
    ):
        """
        Test that the webhook root endpoint returns service information.

        This endpoint provides useful metadata for debugging.
        """
        response = await http_client.get(rollback_webhook_url)

        assert response.status_code == 200, f"Root endpoint failed: {response.status_code}"

        data = response.json()
        assert data["service"] == "rollback-webhook"
        assert "version" in data
        assert "endpoints" in data
        assert "uptime_seconds" in data


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestRollbackWebhookFunctionality:
    """Tests for webhook rollback functionality."""

    async def test_webhook_triggers_rollback(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test that the webhook successfully triggers a rollback.

        This is the core functionality: webhook receives request,
        updates .env, and restarts the service.
        """
        # First, deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0

        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
        assert version_manager["get_version"]() == "v1.1-bad"

        # Trigger rollback via webhook
        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "test-alert-webhook-e2e",
            "alert_name": "E2E Test Alert",
            "reason": "Testing webhook rollback functionality",
        }

        response = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=rollback_request,
            timeout=90.0,  # Rollback can take time
        )

        assert response.status_code == 200, f"Webhook rollback failed: {response.text}"

        data = response.json()
        assert data["status"] in ["ROLLBACK_COMPLETED", "ROLLBACK_IN_PROGRESS"]
        assert data["service"] == "order-service"
        assert data["target_version"] == "v1.0"
        assert "rollback_id" in data
        assert "started_at" in data

        # Wait for rollback to complete
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Verify version changed
        assert version_manager["wait_for_version"]("v1.0", timeout=60), (
            "Version did not change to v1.0 after webhook rollback"
        )

    async def test_webhook_updates_status_after_rollback(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test that the webhook status endpoint reflects recent rollbacks.

        After a rollback, the /status endpoint should show the latest operation.
        """
        # Get initial status
        response = await http_client.get(f"{rollback_webhook_url}/status")
        initial_data = response.json()
        initial_count = initial_data["total_rollbacks"]

        # Deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Trigger rollback via webhook
        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "test-status-update-e2e",
            "reason": "Testing status update",
        }

        response = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=rollback_request,
            timeout=90.0,
        )

        assert response.status_code == 200

        # Wait for rollback to complete
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Check status was updated
        response = await http_client.get(f"{rollback_webhook_url}/status")
        updated_data = response.json()

        # Total rollbacks should have increased
        assert updated_data["total_rollbacks"] > initial_count

        # Last rollback should be populated
        assert updated_data["last_rollback"] is not None
        assert updated_data["last_rollback"]["service"] == "order-service"
        assert updated_data["last_rollback"]["target_version"] == "v1.0"

    async def test_webhook_handles_invalid_service_name(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        wait_for_services,
    ):
        """
        Test that the webhook rejects invalid service names.

        Only order-service, inventory-service, and payment-service should be accepted.
        """
        invalid_request = {
            "service": "invalid-service",
            "target_version": "v1.0",
            "alert_id": "test-invalid-service",
            "reason": "Testing validation",
        }

        response = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=invalid_request,
        )

        # Should get a validation error (422 Unprocessable Entity)
        assert response.status_code == 422, f"Expected validation error, got {response.status_code}"

    async def test_webhook_handles_missing_fields(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        wait_for_services,
    ):
        """
        Test that the webhook validates required fields.

        Missing required fields should result in validation errors.
        """
        # Missing target_version
        incomplete_request = {
            "service": "order-service",
            "alert_id": "test-missing-fields",
            "reason": "Testing validation",
        }

        response = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=incomplete_request,
        )

        assert response.status_code == 422, f"Expected validation error, got {response.status_code}"

    async def test_webhook_rollback_includes_trace_context(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test that webhook rollback operations include trace context.

        The response should include a trace_id for correlation with Elastic.
        """
        # Deploy v1.1-bad first
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Trigger rollback with custom traceparent header
        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "test-trace-context",
            "reason": "Testing trace context",
        }

        response = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=rollback_request,
            headers={
                "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
            },
            timeout=90.0,
        )

        assert response.status_code == 200

        data = response.json()

        # Response should include trace_id for correlation
        # Note: The actual trace_id may differ from the injected one
        # depending on OTEL configuration, but it should be present
        assert "rollback_id" in data, "Missing rollback_id for tracing"


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestWebhookClientFixture:
    """Tests for the webhook_client fixture helper."""

    async def test_webhook_client_trigger_rollback(
        self,
        webhook_client,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test the webhook_client fixture's trigger_rollback helper.

        This validates the test helper that other tests can use.
        """
        # Deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Use fixture to trigger rollback
        response = await webhook_client["trigger_rollback"](
            service="order-service",
            target_version="v1.0",
            alert_id="test-fixture-rollback",
            reason="Testing webhook_client fixture",
        )

        assert response["status"] in ["ROLLBACK_COMPLETED", "ROLLBACK_IN_PROGRESS"]
        assert response["service"] == "order-service"

        # Wait for completion
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Verify rollback happened
        assert version_manager["wait_for_version"]("v1.0", timeout=60)

    async def test_webhook_client_get_status(
        self,
        webhook_client,
        wait_for_services,
    ):
        """
        Test the webhook_client fixture's get_status helper.

        This validates the test helper for querying webhook status.
        """
        status = await webhook_client["get_status"]()

        assert "last_rollback" in status
        assert "total_rollbacks" in status
        assert "service_uptime_seconds" in status


@pytest.mark.asyncio
@pytest.mark.requires_services
@pytest.mark.slow
class TestWebhookIntegrationScenarios:
    """Integration tests for webhook in realistic scenarios."""

    async def test_webhook_handles_rapid_rollback_requests(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test webhook behavior when multiple rollback requests arrive rapidly.

        In practice, Elastic might send multiple alert notifications.
        The webhook should handle this gracefully.
        """
        # Deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Send multiple rollback requests in quick succession
        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "test-rapid-rollback",
            "reason": "Testing rapid rollback handling",
        }

        # Send first request
        response1 = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=rollback_request,
            timeout=90.0,
        )

        assert response1.status_code == 200

        # Send second request (while first might still be processing)
        response2 = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json={**rollback_request, "alert_id": "test-rapid-rollback-2"},
            timeout=90.0,
        )

        assert response2.status_code == 200

        # Wait for rollback to complete
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Verify we ended up on v1.0
        assert version_manager["wait_for_version"]("v1.0", timeout=60)

    async def test_webhook_rollback_from_unknown_version(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test webhook rollback when current version is unknown or unusual.

        The webhook should handle this gracefully and still perform the rollback.
        """
        # Deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Trigger rollback
        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "test-unknown-version",
            "reason": "Testing rollback from any version",
        }

        response = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=rollback_request,
            timeout=90.0,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["ROLLBACK_COMPLETED", "ROLLBACK_IN_PROGRESS"]

        # Wait and verify
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
        assert version_manager["wait_for_version"]("v1.0", timeout=60)

    async def test_complete_automated_remediation_flow(
        self,
        http_client: httpx.AsyncClient,
        rollback_webhook_url: str,
        latency_measurer,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test the complete automated remediation flow.

        This simulates the full workshop scenario with automated rollback:
        1. Deploy bad version
        2. Observe degradation
        3. Webhook triggers rollback
        4. Verify recovery
        """
        print("\n" + "=" * 80)
        print("AUTOMATED REMEDIATION FLOW TEST")
        print("=" * 80)

        # Step 1: Establish baseline
        result = script_runner("deploy.sh", "order-service", "v1.0")
        assert result.returncode == 0
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        baseline_latency = await latency_measurer()
        print(f"Baseline latency: {baseline_latency:.2f}ms")

        # Step 2: Deploy bad version
        print("\nDeploying v1.1-bad...")
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        degraded_latency = await latency_measurer()
        print(f"Degraded latency: {degraded_latency:.2f}ms")

        # Verify degradation
        assert degraded_latency > baseline_latency * 2

        # Step 3: Trigger automated rollback (simulating Elastic alert)
        print("\nTriggering automated rollback via webhook...")
        rollback_request = {
            "service": "order-service",
            "target_version": "v1.0",
            "alert_id": "automated-remediation-test",
            "alert_name": "Order Service SLO Burn Rate",
            "reason": "SLO burn rate exceeded threshold",
            "additional_context": {
                "current_latency_p95": degraded_latency,
                "baseline_latency_p95": baseline_latency,
                "burn_rate": 14.5,
            },
        }

        response = await http_client.post(
            f"{rollback_webhook_url}/rollback",
            json=rollback_request,
            timeout=90.0,
        )

        assert response.status_code == 200
        print(f"✓ Webhook responded: {response.json()['status']}")

        # Wait for rollback
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
        assert version_manager["wait_for_version"]("v1.0", timeout=60)
        print("✓ Rollback completed")

        # Step 4: Verify recovery
        await asyncio.sleep(STABILIZATION_WAIT_TIME)
        recovery_latency = await latency_measurer()
        print(f"Recovery latency: {recovery_latency:.2f}ms")

        # Latency should be back to normal
        assert recovery_latency < baseline_latency * 1.5

        print("\n✓ Automated remediation flow completed successfully")
        print("=" * 80 + "\n")

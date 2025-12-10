"""
End-to-End Tests for Complete Workshop Scenario
From Commit to Culprit Workshop

Tests the full workshop flow:
1. Baseline state (v1.0 healthy, latency < 500ms)
2. Deploy bad version (v1.1-bad)
3. Verify degradation (latency > 2000ms)
4. Trigger rollback
5. Verify recovery (latency back to normal)

These tests validate that the workshop experience works correctly
for participants going through all four challenges.
"""

import asyncio
import time

import httpx
import pytest

from .conftest import (
    BASELINE_LATENCY_THRESHOLD,
    BAD_LATENCY_THRESHOLD,
    RECOVERY_LATENCY_THRESHOLD,
    SERVICE_RESTART_WAIT_TIME,
    STABILIZATION_WAIT_TIME,
)


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestWorkshopScenario:
    """
    Complete end-to-end test of the workshop scenario.

    This test class follows the participant journey through all four
    challenges, validating each step along the way.
    """

    async def test_complete_workshop_flow(
        self,
        http_client: httpx.AsyncClient,
        wait_for_services,
        latency_measurer,
        version_manager,
        script_runner,
        initial_state,
    ):
        """
        Test the complete workshop flow from start to finish.

        This is the master E2E test that validates the entire workshop experience.

        Flow:
        1. Challenge 1: Verify baseline health and latency
        2. Challenge 2: Deploy bad version and detect degradation
        3. Challenge 3: Perform rollback and verify recovery
        4. Challenge 4: Verify final state is healthy

        This test is idempotent - it restores the initial state after completion.
        """

        # =====================================================================
        # Challenge 1: Setup and Baseline
        # =====================================================================

        print("\n" + "=" * 80)
        print("CHALLENGE 1: Setup and Baseline")
        print("=" * 80)

        # Verify we're starting on v1.0
        current_version = version_manager["get_version"]()
        print(f"Current version: {current_version}")

        if current_version != "v1.0":
            print(f"Deploying v1.0 to establish baseline...")
            result = script_runner("deploy.sh", "order-service", "v1.0")
            assert result.returncode == 0, f"Failed to deploy v1.0: {result.stderr}"

            # Wait for service to restart
            await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

            # Verify version changed
            assert version_manager["wait_for_version"]("v1.0", timeout=30)

        # Wait for metrics to stabilize
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        # Measure baseline latency
        print("Measuring baseline latency...")
        baseline_latency = await latency_measurer()

        assert baseline_latency != -1, "Failed to measure baseline latency (all requests failed)"

        print(f"Baseline latency: {baseline_latency:.2f}ms")

        assert (
            baseline_latency < BASELINE_LATENCY_THRESHOLD
        ), f"Baseline latency too high: {baseline_latency:.2f}ms >= {BASELINE_LATENCY_THRESHOLD}ms"

        print(f"✓ Baseline health verified (latency: {baseline_latency:.2f}ms)")

        # =====================================================================
        # Challenge 2: Deploy and Detect
        # =====================================================================

        print("\n" + "=" * 80)
        print("CHALLENGE 2: Deploy and Detect")
        print("=" * 80)

        # Deploy the bad version
        print("Deploying v1.1-bad...")
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")

        assert result.returncode == 0, f"Failed to deploy v1.1-bad: {result.stderr}"

        # Wait for service to restart
        print(f"Waiting {SERVICE_RESTART_WAIT_TIME}s for service to restart...")
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Verify version changed
        assert version_manager["wait_for_version"]("v1.1-bad", timeout=30), (
            "Service did not switch to v1.1-bad"
        )

        print(f"✓ Service deployed to v1.1-bad")

        # Wait for metrics to stabilize
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        # Measure degraded latency
        print("Measuring degraded latency...")
        degraded_latency = await latency_measurer()

        assert degraded_latency != -1, "Failed to measure degraded latency (all requests failed)"

        print(f"Degraded latency: {degraded_latency:.2f}ms")

        assert (
            degraded_latency > BAD_LATENCY_THRESHOLD
        ), f"Latency did not degrade as expected: {degraded_latency:.2f}ms <= {BAD_LATENCY_THRESHOLD}ms"

        print(f"✓ Degradation detected (latency: {degraded_latency:.2f}ms)")

        # Calculate the latency increase
        latency_increase_pct = ((degraded_latency - baseline_latency) / baseline_latency) * 100
        print(f"  Latency increased by {latency_increase_pct:.1f}%")

        # =====================================================================
        # Challenge 3: Investigate and Remediate
        # =====================================================================

        print("\n" + "=" * 80)
        print("CHALLENGE 3: Investigate and Remediate")
        print("=" * 80)

        # Perform rollback using the rollback script
        print("Executing rollback to v1.0...")
        result = script_runner("rollback.sh", "order-service")

        assert result.returncode == 0, f"Rollback failed: {result.stderr}"

        # Wait for service to restart
        print(f"Waiting {SERVICE_RESTART_WAIT_TIME}s for service to restart...")
        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Verify version changed back
        assert version_manager["wait_for_version"]("v1.0", timeout=30), (
            "Service did not rollback to v1.0"
        )

        print(f"✓ Service rolled back to v1.0")

        # Wait for metrics to stabilize
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        # Measure recovery latency
        print("Measuring recovery latency...")
        recovery_latency = await latency_measurer()

        assert recovery_latency != -1, "Failed to measure recovery latency (all requests failed)"

        print(f"Recovery latency: {recovery_latency:.2f}ms")

        assert (
            recovery_latency < RECOVERY_LATENCY_THRESHOLD
        ), f"System did not recover: {recovery_latency:.2f}ms >= {RECOVERY_LATENCY_THRESHOLD}ms"

        print(f"✓ System recovered (latency: {recovery_latency:.2f}ms)")

        # =====================================================================
        # Challenge 4: Learn and Prevent
        # =====================================================================

        print("\n" + "=" * 80)
        print("CHALLENGE 4: Learn and Prevent")
        print("=" * 80)

        # Verify final state is healthy
        final_version = version_manager["get_version"]()
        assert final_version == "v1.0", f"Final version is not v1.0: {final_version}"

        print(f"✓ Final state verified (version: {final_version})")

        # =====================================================================
        # Test Summary
        # =====================================================================

        print("\n" + "=" * 80)
        print("WORKSHOP SCENARIO TEST SUMMARY")
        print("=" * 80)
        print(f"Baseline Latency:  {baseline_latency:.2f}ms")
        print(f"Degraded Latency:  {degraded_latency:.2f}ms (↑ {latency_increase_pct:.1f}%)")
        print(f"Recovery Latency:  {recovery_latency:.2f}ms")
        print()
        print("✓ All challenges passed successfully")
        print("✓ Workshop flow is working correctly")
        print("=" * 80 + "\n")


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestChallenge1Baseline:
    """Tests specific to Challenge 1: Setup and Baseline."""

    async def test_all_services_healthy(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        inventory_service_url: str,
        payment_service_url: str,
        rollback_webhook_url: str,
        wait_for_services,
    ):
        """
        Test that all services are healthy and responding.

        This validates the setup step where participants verify
        their environment is correctly configured.
        """
        # Check order-service health
        response = await http_client.get(f"{order_service_url}/api/orders/health")
        assert response.status_code == 200, f"Order service not healthy: {response.status_code}"

        # Check inventory-service health
        response = await http_client.get(f"{inventory_service_url}/health")
        assert response.status_code == 200, f"Inventory service not healthy: {response.status_code}"

        # Check payment-service health
        response = await http_client.get(f"{payment_service_url}/health")
        assert response.status_code == 200, f"Payment service not healthy: {response.status_code}"

        # Check rollback-webhook health
        response = await http_client.get(f"{rollback_webhook_url}/health")
        assert response.status_code == 200, f"Rollback webhook not healthy: {response.status_code}"

    async def test_baseline_latency_is_healthy(
        self,
        wait_for_services,
        latency_measurer,
        version_manager,
        script_runner,
    ):
        """
        Test that baseline latency (v1.0) is within healthy thresholds.

        This ensures participants start with a healthy baseline before
        introducing the bad version.
        """
        # Ensure we're on v1.0
        current_version = version_manager["get_version"]()

        if current_version != "v1.0":
            result = script_runner("deploy.sh", "order-service", "v1.0")
            assert result.returncode == 0

            await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
            assert version_manager["wait_for_version"]("v1.0", timeout=30)

        # Wait for stabilization
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        # Measure latency
        latency = await latency_measurer()

        assert latency != -1, "Failed to measure latency"
        assert latency < BASELINE_LATENCY_THRESHOLD, (
            f"Baseline latency too high: {latency:.2f}ms >= {BASELINE_LATENCY_THRESHOLD}ms"
        )

    async def test_order_creation_succeeds(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that order creation works correctly in baseline state.

        This validates the happy path flow before introducing issues.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        data = response.json()
        assert "orderId" in data or "order_id" in data, "Response missing order_id"


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestChallenge2DeployDetect:
    """Tests specific to Challenge 2: Deploy and Detect."""

    async def test_deploy_bad_version(
        self,
        version_manager,
        script_runner,
        initial_state,
    ):
        """
        Test that deploying v1.1-bad succeeds and updates the version.

        This validates the deployment mechanism used in the workshop.
        """
        # Deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0, f"Deployment failed: {result.stderr}"

        # Verify version changed
        time.sleep(5)  # Give it a moment to update .env
        new_version = version_manager["get_version"]()
        assert new_version == "v1.1-bad", f"Version not updated: {new_version}"

    async def test_latency_degrades_after_bad_deployment(
        self,
        wait_for_services,
        latency_measurer,
        version_manager,
        script_runner,
        initial_state,
    ):
        """
        Test that latency significantly increases after deploying v1.1-bad.

        This validates that the bad version exhibits the expected behavior
        that participants will investigate.
        """
        # Deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0

        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
        assert version_manager["wait_for_version"]("v1.1-bad", timeout=30)

        # Wait for stabilization
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        # Measure degraded latency
        latency = await latency_measurer()

        assert latency != -1, "Failed to measure latency"
        assert latency > BAD_LATENCY_THRESHOLD, (
            f"Latency did not degrade: {latency:.2f}ms <= {BAD_LATENCY_THRESHOLD}ms"
        )

    async def test_bad_version_still_processes_orders(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        version_manager,
        script_runner,
        wait_for_services,
        initial_state,
    ):
        """
        Test that the bad version still successfully processes orders.

        The bug introduces latency but doesn't break functionality.
        Participants should see slow but successful requests.
        """
        # Ensure we're on v1.1-bad
        current_version = version_manager["get_version"]()

        if current_version != "v1.1-bad":
            result = script_runner("deploy.sh", "order-service", "v1.1-bad")
            assert result.returncode == 0
            await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Create an order (should succeed but be slow)
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
            timeout=15.0,  # Longer timeout for slow requests
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestChallenge3InvestigateRemediate:
    """Tests specific to Challenge 3: Investigate and Remediate."""

    async def test_manual_rollback_succeeds(
        self,
        version_manager,
        script_runner,
        initial_state,
    ):
        """
        Test that manual rollback using rollback.sh works correctly.

        This validates the manual remediation path that participants
        can use if automated rollback doesn't work.
        """
        # First deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0

        time.sleep(5)
        assert version_manager["get_version"]() == "v1.1-bad"

        # Now rollback
        result = script_runner("rollback.sh", "order-service")
        assert result.returncode == 0, f"Rollback failed: {result.stderr}"

        # Verify rollback succeeded
        time.sleep(5)
        assert version_manager["get_version"]() == "v1.0"

    async def test_system_recovers_after_rollback(
        self,
        wait_for_services,
        latency_measurer,
        version_manager,
        script_runner,
        initial_state,
    ):
        """
        Test that system performance recovers after rollback.

        This validates that rolling back actually fixes the performance issue.
        """
        # Deploy bad version
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0

        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Rollback
        result = script_runner("rollback.sh", "order-service")
        assert result.returncode == 0

        await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)
        assert version_manager["wait_for_version"]("v1.0", timeout=30)

        # Wait for stabilization
        await asyncio.sleep(STABILIZATION_WAIT_TIME)

        # Verify latency recovered
        latency = await latency_measurer()

        assert latency != -1, "Failed to measure latency"
        assert latency < RECOVERY_LATENCY_THRESHOLD, (
            f"Latency did not recover: {latency:.2f}ms >= {RECOVERY_LATENCY_THRESHOLD}ms"
        )


@pytest.mark.asyncio
@pytest.mark.requires_services
class TestChallenge4LearnPrevent:
    """Tests specific to Challenge 4: Learn and Prevent."""

    async def test_final_state_is_stable(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        version_manager,
        script_runner,
        wait_for_services,
    ):
        """
        Test that the final state (after completing all challenges) is stable.

        This ensures participants end with a healthy system.
        """
        # Ensure we're on v1.0
        current_version = version_manager["get_version"]()

        if current_version != "v1.0":
            result = script_runner("rollback.sh", "order-service")
            assert result.returncode == 0
            await asyncio.sleep(SERVICE_RESTART_WAIT_TIME)

        # Verify health
        response = await http_client.get(f"{order_service_url}/api/orders/health")
        assert response.status_code == 200

    async def test_version_persistence_across_multiple_deployments(
        self,
        version_manager,
        script_runner,
        initial_state,
    ):
        """
        Test that version changes persist correctly across multiple deployments.

        This validates that the .env file mechanism works reliably.
        """
        # Deploy v1.0
        result = script_runner("deploy.sh", "order-service", "v1.0")
        assert result.returncode == 0
        time.sleep(5)
        assert version_manager["get_version"]() == "v1.0"

        # Deploy v1.1-bad
        result = script_runner("deploy.sh", "order-service", "v1.1-bad")
        assert result.returncode == 0
        time.sleep(5)
        assert version_manager["get_version"]() == "v1.1-bad"

        # Rollback to v1.0
        result = script_runner("rollback.sh", "order-service")
        assert result.returncode == 0
        time.sleep(5)
        assert version_manager["get_version"]() == "v1.0"

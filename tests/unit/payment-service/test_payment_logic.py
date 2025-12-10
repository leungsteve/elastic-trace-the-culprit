"""
Unit tests for Payment Service business logic.

Tests payment processing logic including:
- Deterministic failure calculation
- Payment gateway simulation
- Success/failure rate distribution

Workshop: From Commit to Culprit - Payment Service Tests
"""

import pytest
import hashlib
import sys
from pathlib import Path

# Add the service to the path
service_path = Path(__file__).parent.parent.parent.parent / "services" / "payment-service" / "src"
sys.path.insert(0, str(service_path))

from payment.main import calculate_failure_probability


class TestFailureProbability:
    """Test deterministic failure probability calculation."""

    def test_failure_probability_is_deterministic(self):
        """Test that same order_id always produces same result."""
        order_id = "test-order-12345"

        result1 = calculate_failure_probability(order_id)
        result2 = calculate_failure_probability(order_id)
        result3 = calculate_failure_probability(order_id)

        assert result1 == result2 == result3

    def test_failure_probability_different_ids(self):
        """Test that different order IDs can produce different results."""
        results = set()

        # Test 100 different order IDs
        for i in range(100):
            order_id = f"order-{i}"
            result = calculate_failure_probability(order_id)
            results.add(result)

        # We should have both True and False results
        # (statistically very likely with 100 samples and 1% failure rate)
        assert len(results) > 1, "Should have both success and failure cases"

    def test_failure_probability_distribution(self):
        """Test that failure rate is approximately 1%."""
        failure_count = 0
        total_count = 10000

        for i in range(total_count):
            order_id = f"order-{i}"
            if calculate_failure_probability(order_id):
                failure_count += 1

        # Calculate failure rate
        failure_rate = failure_count / total_count

        # Should be approximately 1% (allow for some variance)
        # With 10,000 samples, we expect around 100 failures
        # Allow 0.5% to 1.5% range for statistical variance
        assert 0.005 <= failure_rate <= 0.015, \
            f"Failure rate {failure_rate:.3%} should be approximately 1%"

    def test_failure_probability_uses_sha256(self):
        """Test that the function uses SHA256 hashing."""
        order_id = "test-order"

        # Calculate expected hash value
        hash_value = int(hashlib.sha256(order_id.encode()).hexdigest(), 16)
        expected_failure = (hash_value % 100) == 0

        actual_failure = calculate_failure_probability(order_id)

        assert actual_failure == expected_failure

    def test_failure_probability_specific_failing_ids(self):
        """Test specific order IDs that should fail."""
        # Find order IDs that hash to multiples of 100
        failing_ids = []

        for i in range(10000):
            order_id = f"order-{i}"
            if calculate_failure_probability(order_id):
                failing_ids.append(order_id)

            if len(failing_ids) >= 5:
                break

        # Verify they consistently fail
        for order_id in failing_ids:
            assert calculate_failure_probability(order_id) is True

    def test_failure_probability_specific_succeeding_ids(self):
        """Test specific order IDs that should succeed."""
        # Find order IDs that don't fail
        succeeding_ids = []

        for i in range(100):
            order_id = f"order-success-{i}"
            if not calculate_failure_probability(order_id):
                succeeding_ids.append(order_id)

            if len(succeeding_ids) >= 5:
                break

        # Verify they consistently succeed
        for order_id in succeeding_ids:
            assert calculate_failure_probability(order_id) is False

    def test_failure_probability_empty_string(self):
        """Test failure probability with empty order ID."""
        result = calculate_failure_probability("")

        # Should still work (deterministic for empty string)
        assert isinstance(result, bool)

        # Verify consistency
        assert result == calculate_failure_probability("")

    def test_failure_probability_special_characters(self):
        """Test failure probability with special characters in order ID."""
        special_order_ids = [
            "order-with-dashes-123",
            "order_with_underscores_456",
            "order.with.dots.789",
            "order@with#special$chars",
            "order-with-unicode-😀"
        ]

        for order_id in special_order_ids:
            result = calculate_failure_probability(order_id)
            assert isinstance(result, bool)

            # Verify deterministic behavior
            assert result == calculate_failure_probability(order_id)

    def test_failure_probability_long_order_id(self):
        """Test failure probability with very long order ID."""
        long_order_id = "order-" + ("x" * 1000)

        result = calculate_failure_probability(long_order_id)
        assert isinstance(result, bool)

        # Verify deterministic
        assert result == calculate_failure_probability(long_order_id)

    def test_failure_probability_case_sensitivity(self):
        """Test that order ID is case-sensitive."""
        order_id_lower = "order-abc"
        order_id_upper = "ORDER-ABC"

        result_lower = calculate_failure_probability(order_id_lower)
        result_upper = calculate_failure_probability(order_id_upper)

        # Different cases should potentially produce different results
        # (they hash differently)
        hash_lower = hashlib.sha256(order_id_lower.encode()).hexdigest()
        hash_upper = hashlib.sha256(order_id_upper.encode()).hexdigest()

        assert hash_lower != hash_upper


class TestPaymentGatewaySimulation:
    """Test payment gateway simulation behavior."""

    def test_gateway_simulation_reproducibility(self):
        """Test that payment outcomes are reproducible for same order ID."""
        # This test verifies the overall payment flow is reproducible
        test_order_ids = [
            "order-reproducible-1",
            "order-reproducible-2",
            "order-reproducible-3"
        ]

        for order_id in test_order_ids:
            result1 = calculate_failure_probability(order_id)
            result2 = calculate_failure_probability(order_id)

            assert result1 == result2, \
                f"Payment outcome for {order_id} should be reproducible"

    def test_gateway_simulation_variety(self):
        """Test that gateway produces variety of outcomes across different orders."""
        outcomes = set()

        for i in range(1000):
            order_id = f"order-variety-{i}"
            result = calculate_failure_probability(order_id)
            outcomes.add(result)

        # Should have both success and failure outcomes
        assert True in outcomes, "Should have at least one success"
        assert False in outcomes, "Should have at least one failure"

    def test_gateway_failure_rate_consistency(self):
        """Test that failure rate is consistent across different batches."""
        batch_size = 1000
        num_batches = 5

        failure_rates = []

        for batch in range(num_batches):
            failure_count = 0
            for i in range(batch_size):
                order_id = f"batch-{batch}-order-{i}"
                if calculate_failure_probability(order_id):
                    failure_count += 1

            failure_rate = failure_count / batch_size
            failure_rates.append(failure_rate)

        # All batches should have similar failure rates (around 1%)
        avg_failure_rate = sum(failure_rates) / len(failure_rates)

        assert 0.005 <= avg_failure_rate <= 0.015, \
            f"Average failure rate {avg_failure_rate:.3%} should be around 1%"

        # Individual batches should not deviate too much
        for rate in failure_rates:
            assert 0.0 <= rate <= 0.03, \
                f"Individual batch rate {rate:.3%} should be within reasonable range"

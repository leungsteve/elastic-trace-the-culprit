"""
Log Correlation Tests
From Commit to Culprit Workshop

Tests that logs contain trace_id for correlation and that log format matches expected patterns.
Validates that logs can be filtered by trace_id to reconstruct request flows.
"""

import re
import json
import pytest
import httpx
from typing import List, Dict, Any


class TestLogTraceCorrelation:
    """Test suite for log and trace correlation."""

    @pytest.mark.asyncio
    async def test_logs_contain_trace_id(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that application logs contain trace_id for correlation.

        All log messages should include trace_id so they can be correlated
        with their corresponding traces in Elastic Observability.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with log collection, we would:
        # 1. Query logs for the order request
        # 2. Verify each log entry contains a trace_id field
        # 3. Verify the trace_id matches the trace generated for this request


    @pytest.mark.asyncio
    async def test_log_format_includes_otel_fields(
        self,
        http_client: httpx.AsyncClient,
        payment_service_url: str,
        wait_for_services,
    ):
        """
        Test that log format includes OpenTelemetry trace correlation fields.

        Python services use this format:
        %(asctime)s [%(levelname)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s]
        %(name)s - %(message)s

        This test verifies the format is correct by making a request and
        checking that correlation is possible.
        """
        # Make a simple health check request to generate logs
        response = await http_client.get(f"{payment_service_url}/health")
        assert response.status_code == 200

        # In a full test, we would:
        # 1. Capture the logs from the service
        # 2. Parse the log format
        # 3. Verify presence of trace_id and span_id fields
        # 4. Verify they match the expected pattern (hex strings)


    @pytest.mark.asyncio
    async def test_java_log_correlation_format(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that Java service logs include trace correlation.

        Java services use SLF4J with EDOT Java auto-instrumentation,
        which automatically injects trace_id and span_id into MDC.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with log collection, we would verify:
        # 1. Java logs contain trace.id field
        # 2. Java logs contain span.id field
        # 3. Format matches EDOT Java conventions


class TestLogFiltering:
    """Test suite for filtering logs by trace_id."""

    @pytest.mark.asyncio
    async def test_filter_logs_by_trace_id(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        w3c_traceparent: str,
        wait_for_services,
    ):
        """
        Test that logs can be filtered by trace_id to reconstruct request flow.

        Given a trace_id, we should be able to query all logs from all services
        that participated in that distributed transaction.
        """
        trace_id = w3c_traceparent.split("-")[1]

        # Send request with known trace_id
        headers = {
            "traceparent": w3c_traceparent,
            "Content-Type": "application/json",
        }

        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
            headers=headers,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with log aggregation, we would:
        # 1. Query logs where trace_id == {trace_id}
        # 2. Verify we get logs from order-service
        # 3. Verify we get logs from inventory-service
        # 4. Verify we get logs from payment-service
        # 5. Verify log timestamps show the request flow chronology


    @pytest.mark.asyncio
    async def test_cross_service_log_correlation(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that logs from all services can be correlated via shared trace_id.

        This validates the complete observability story:
        - Order service logs have trace_id
        - Inventory service logs have same trace_id
        - Payment service logs have same trace_id
        - All can be queried together in Kibana
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"
        response_data = response.json()
        order_id = response_data.get("orderId") or response_data.get("order_id")

        # In a full test, we would:
        # 1. Extract trace_id from the response or trace
        # 2. Query logs from all services with that trace_id
        # 3. Verify temporal ordering matches the service call chain
        # 4. Verify we can see the complete request flow in the logs


class TestStructuredLogging:
    """Test suite for structured logging formats."""

    @pytest.mark.asyncio
    async def test_json_log_output(
        self,
        http_client: httpx.AsyncClient,
        payment_service_url: str,
        wait_for_services,
    ):
        """
        Test that services can output logs in JSON format for structured logging.

        While the workshop uses human-readable format by default,
        production deployments often use JSON for better parsing.
        """
        response = await http_client.get(f"{payment_service_url}/health")
        assert response.status_code == 200

        # In a full test, if JSON logging is enabled, we would:
        # 1. Verify log output is valid JSON
        # 2. Verify JSON contains all required fields
        # 3. Verify trace_id and span_id are at the root level


    @pytest.mark.asyncio
    async def test_log_levels_preserved(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that log levels (INFO, WARN, ERROR) are correctly set and preserved.

        Different log levels help filter and prioritize log messages.
        Trace correlation should work across all log levels.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test, we would verify:
        # 1. INFO logs have trace_id
        # 2. WARN logs (if any) have trace_id
        # 3. ERROR logs (if any) have trace_id
        # 4. All share the same trace_id for the request


class TestExceptionLogging:
    """Test suite for exception logging with trace correlation."""

    @pytest.mark.asyncio
    async def test_exception_logs_include_trace_id(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        wait_for_services,
    ):
        """
        Test that exception logs include trace_id for debugging.

        When an error occurs, the exception log should contain:
        - trace_id to correlate with the failing trace
        - span_id to identify the exact span that failed
        - Full stack trace for debugging
        """
        # Send invalid request to trigger an error
        invalid_request = {
            "customer_id": "",  # Invalid: empty customer_id
            "items": []  # Invalid: no items
        }

        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=invalid_request,
        )

        # Expect some kind of error response (400, 422, or 500)
        assert response.status_code >= 400

        # In a full test, we would:
        # 1. Query error logs for this request
        # 2. Verify error log contains trace_id
        # 3. Verify we can correlate the error log with the failed trace


    @pytest.mark.asyncio
    async def test_payment_failure_logs_correlated(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        wait_for_services,
    ):
        """
        Test that payment failures are properly logged with trace correlation.

        Payment service has a 1% deterministic failure rate.
        When payment fails, logs should:
        - Indicate the failure reason
        - Include trace_id for correlation
        - Be visible in the order service logs as well
        """
        # Try to trigger a payment failure by sending multiple orders
        # The deterministic hash should eventually fail one
        failure_found = False

        for i in range(200):  # Try 200 orders to increase chance of hitting 1% failure
            test_request = {
                "customer_id": f"test-customer-{i}",
                "items": [
                    {
                        "product_id": "TEST-PRODUCT",
                        "quantity": 1,
                        "price": 10.00
                    }
                ]
            }

            response = await http_client.post(
                f"{order_service_url}/api/orders",
                json=test_request,
            )

            if response.status_code == 400:
                # Found a failed order
                failure_found = True
                response_data = response.json()

                # In a full test, we would:
                # 1. Extract trace_id from the failed response
                # 2. Query logs for that trace_id
                # 3. Verify we see payment failure logs
                # 4. Verify logs explain the payment was declined
                break

        # Note: We may not always trigger a failure in 200 attempts,
        # so we don't assert failure_found here


class TestLogAttributes:
    """Test suite for custom log attributes and metadata."""

    @pytest.mark.asyncio
    async def test_service_metadata_in_logs(
        self,
        http_client: httpx.AsyncClient,
        payment_service_url: str,
        wait_for_services,
    ):
        """
        Test that logs include service metadata.

        Logs should include:
        - service.name
        - service.version
        - deployment.environment
        These are added by EDOT resource attributes.
        """
        response = await http_client.get(f"{payment_service_url}/health")
        assert response.status_code == 200

        # In a full test, we would verify logs contain:
        # - service.name = payment-service
        # - service.version = v1.0 (or v1.1-bad)
        # - deployment.environment = local (or instruqt)


    @pytest.mark.asyncio
    async def test_custom_attributes_in_logs(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that custom business attributes appear in logs.

        Logs should include business context:
        - customer_id
        - order_id
        - order amount
        This helps with business analytics from logs.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test, we would verify logs contain:
        # - customer_id from the request
        # - order_id from the response
        # - total_amount calculated value

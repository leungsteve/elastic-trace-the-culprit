"""
Example Telemetry Test
From Commit to Culprit Workshop

This example demonstrates how to write telemetry tests using the provided fixtures.
Use this as a template for creating additional tests.
"""

import pytest
import httpx


class TestExampleTelemetry:
    """Example test class showing fixture usage."""

    @pytest.mark.asyncio
    async def test_complete_order_flow(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        w3c_traceparent: str,
        wait_for_services,
    ):
        """
        Example test demonstrating a complete order flow with trace context.

        This test shows:
        1. How to use fixtures
        2. How to send requests with trace context
        3. How to validate responses
        4. How to handle errors gracefully
        """
        # Extract trace_id from the traceparent for logging
        trace_id = w3c_traceparent.split("-")[1]
        print(f"\nTest trace_id: {trace_id}")

        # Set up headers with trace context
        headers = {
            "traceparent": w3c_traceparent,
            "Content-Type": "application/json",
        }

        # Send order request
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
            headers=headers,
        )

        # Validate response
        assert response.status_code in [200, 201], (
            f"Order creation failed with status {response.status_code}: {response.text}"
        )

        # Parse response data
        response_data = response.json()
        print(f"Order created: {response_data}")

        # Validate response structure
        assert "orderId" in response_data or "order_id" in response_data
        assert response_data.get("status") == "CONFIRMED"

        # In a full test with Elastic access, you would:
        # 1. Query Elastic APM for the trace with this trace_id
        # 2. Verify all three services appear in the trace
        # 3. Verify span attributes are correct
        # 4. Query logs by trace_id
        # 5. Verify log messages match expected flow


    @pytest.mark.asyncio
    async def test_with_mock_receiver(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        mock_otel_receiver: dict,
        wait_for_services,
    ):
        """
        Example test using the mock OTEL receiver fixture.

        This demonstrates how to use the mock receiver to collect
        and validate telemetry data in tests.
        """
        # Clear any previous data
        mock_otel_receiver["clear"]()

        # Send request
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201]

        # In a real implementation with receiver integration:
        # traces = mock_otel_receiver["get_traces"]()
        # assert len(traces) > 0
        #
        # order_span = mock_otel_receiver["find_span_by_name"]("order.create")
        # assert order_span is not None
        # assert order_span["attributes"]["order.customer_id"] == "test-customer-123"


    @pytest.mark.asyncio
    async def test_trace_id_extraction(
        self,
        w3c_traceparent: str,
        trace_id_extractor: callable,
    ):
        """
        Example test demonstrating the trace_id_extractor utility.

        This shows how to extract trace_id from various formats.
        """
        # Extract from W3C traceparent
        trace_id = trace_id_extractor(w3c_traceparent)
        assert trace_id is not None
        assert len(trace_id) == 32  # 128-bit trace_id in hex

        # Extract from dict (simulating a log message)
        log_message = {
            "message": "Order created",
            "trace_id": trace_id,
            "level": "INFO"
        }
        extracted_id = trace_id_extractor(log_message)
        assert extracted_id == trace_id

        # Handle different field names
        span_data = {
            "name": "order.create",
            "traceId": trace_id,
            "spanId": "b7ad6b7169203331"
        }
        extracted_id = trace_id_extractor(span_data)
        assert extracted_id == trace_id


    @pytest.mark.asyncio
    async def test_span_validation(
        self,
        span_validator: dict,
    ):
        """
        Example test demonstrating the span_validator utility.

        This shows how to validate span structure and attributes.
        """
        # Create a mock span for validation
        mock_span = {
            "name": "order.create",
            "trace_id": "0af7651916cd43dd8448eb211c80319c",
            "span_id": "b7ad6b7169203331",
            "attributes": {
                "order.customer_id": "test-customer-123",
                "order.total_amount": 1049.97,
                "service.name": "order-service"
            }
        }

        # Validate basic span structure
        is_valid = span_validator["validate_span"](mock_span)
        assert is_valid

        # Validate with expected attributes
        expected_attrs = {
            "order.customer_id": "test-customer-123"
        }
        is_valid = span_validator["validate_span"](mock_span, expected_attrs)
        assert is_valid

        # Test parent-child relationship
        parent_span = {
            "name": "parent",
            "trace_id": "0af7651916cd43dd8448eb211c80319c",
            "span_id": "parent123456789abc",
        }
        child_span = {
            "name": "child",
            "trace_id": "0af7651916cd43dd8448eb211c80319c",
            "span_id": "child123456789abc",
            "parent_span_id": "parent123456789abc",
        }

        has_relationship = span_validator["has_parent_child_relationship"](
            parent_span, child_span
        )
        assert has_relationship


    @pytest.mark.asyncio
    async def test_error_handling_example(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        wait_for_services,
    ):
        """
        Example test showing how to test error scenarios with trace context.

        This demonstrates testing error paths while maintaining trace correlation.
        """
        # Send invalid request
        invalid_request = {
            "customer_id": "",  # Invalid: empty
            "items": []  # Invalid: no items
        }

        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=invalid_request,
        )

        # Expect error response
        assert response.status_code >= 400

        # In a full test with Elastic access, you would:
        # 1. Extract trace_id from response or headers
        # 2. Query error logs by trace_id
        # 3. Verify error span has error=true attribute
        # 4. Verify exception details are captured


# Note: This file is for demonstration purposes.
# You can run it with: pytest tests/telemetry/example_test.py -v

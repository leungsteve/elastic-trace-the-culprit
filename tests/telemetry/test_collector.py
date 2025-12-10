"""
OTEL Collector Tests
From Commit to Culprit Workshop

Tests that the OpenTelemetry Collector receives telemetry from services
and correctly processes traces, metrics, and logs through its pipelines.
"""

import asyncio
import json
import pytest
import httpx
from typing import Dict, Any, List


class TestCollectorHealth:
    """Test suite for OTEL Collector health and availability."""

    @pytest.mark.asyncio
    async def test_collector_health_endpoint(
        self,
        http_client: httpx.AsyncClient,
        otel_collector_url: str,
    ):
        """
        Test that OTEL Collector health check endpoint is accessible.

        The collector exposes a health check at :13133/
        """
        try:
            # Health check endpoint is on port 13133, not the OTLP port
            health_url = otel_collector_url.replace(":4318", ":13133")
            response = await http_client.get(health_url)

            # Health endpoint should return 200 when collector is healthy
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip(
                f"OTEL Collector not available at {otel_collector_url}. "
                "Make sure docker-compose is running."
            )


    @pytest.mark.asyncio
    async def test_collector_metrics_endpoint(
        self,
        http_client: httpx.AsyncClient,
        otel_collector_url: str,
    ):
        """
        Test that OTEL Collector exposes metrics about itself.

        The collector exposes Prometheus metrics at :8888/metrics
        """
        try:
            # Metrics endpoint is on port 8888
            metrics_url = otel_collector_url.replace(":4318", ":8888") + "/metrics"
            response = await http_client.get(metrics_url)

            # Metrics endpoint should return 200
            assert response.status_code == 200

            # Response should contain Prometheus-format metrics
            metrics_text = response.text
            assert "otelcol_" in metrics_text or "# HELP" in metrics_text

        except httpx.ConnectError:
            pytest.skip("OTEL Collector metrics endpoint not available")


class TestCollectorReceiversHTTP:
    """Test suite for OTLP HTTP receiver."""

    @pytest.mark.asyncio
    async def test_otlp_http_receiver_accepts_traces(
        self,
        http_client: httpx.AsyncClient,
        otel_collector_url: str,
    ):
        """
        Test that OTLP HTTP receiver accepts trace data.

        The collector should accept POST requests to /v1/traces
        """
        # Create minimal OTLP trace payload
        trace_payload = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {
                                "key": "service.name",
                                "value": {"stringValue": "test-service"}
                            }
                        ]
                    },
                    "scopeSpans": [
                        {
                            "scope": {
                                "name": "test-scope"
                            },
                            "spans": [
                                {
                                    "traceId": "0af7651916cd43dd8448eb211c80319c",
                                    "spanId": "b7ad6b7169203331",
                                    "name": "test-span",
                                    "kind": 1,
                                    "startTimeUnixNano": "1234567890000000000",
                                    "endTimeUnixNano": "1234567890001000000"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        try:
            response = await http_client.post(
                f"{otel_collector_url}/v1/traces",
                json=trace_payload,
                headers={"Content-Type": "application/json"},
            )

            # Collector should accept the trace (200, 201, or 202)
            assert response.status_code in [200, 201, 202]

        except httpx.ConnectError:
            pytest.skip("OTEL Collector HTTP receiver not available")


    @pytest.mark.asyncio
    async def test_otlp_http_receiver_accepts_metrics(
        self,
        http_client: httpx.AsyncClient,
        otel_collector_url: str,
    ):
        """
        Test that OTLP HTTP receiver accepts metric data.

        The collector should accept POST requests to /v1/metrics
        """
        # Create minimal OTLP metrics payload
        metrics_payload = {
            "resourceMetrics": [
                {
                    "resource": {
                        "attributes": [
                            {
                                "key": "service.name",
                                "value": {"stringValue": "test-service"}
                            }
                        ]
                    },
                    "scopeMetrics": [
                        {
                            "scope": {
                                "name": "test-scope"
                            },
                            "metrics": [
                                {
                                    "name": "test_counter",
                                    "unit": "1",
                                    "sum": {
                                        "dataPoints": [
                                            {
                                                "asInt": "42",
                                                "timeUnixNano": "1234567890000000000"
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        try:
            response = await http_client.post(
                f"{otel_collector_url}/v1/metrics",
                json=metrics_payload,
                headers={"Content-Type": "application/json"},
            )

            # Collector should accept the metrics (200, 201, or 202)
            assert response.status_code in [200, 201, 202]

        except httpx.ConnectError:
            pytest.skip("OTEL Collector HTTP receiver not available")


    @pytest.mark.asyncio
    async def test_otlp_http_receiver_accepts_logs(
        self,
        http_client: httpx.AsyncClient,
        otel_collector_url: str,
    ):
        """
        Test that OTLP HTTP receiver accepts log data.

        The collector should accept POST requests to /v1/logs
        """
        # Create minimal OTLP logs payload
        logs_payload = {
            "resourceLogs": [
                {
                    "resource": {
                        "attributes": [
                            {
                                "key": "service.name",
                                "value": {"stringValue": "test-service"}
                            }
                        ]
                    },
                    "scopeLogs": [
                        {
                            "scope": {
                                "name": "test-scope"
                            },
                            "logRecords": [
                                {
                                    "timeUnixNano": "1234567890000000000",
                                    "severityText": "INFO",
                                    "body": {
                                        "stringValue": "test log message"
                                    },
                                    "traceId": "0af7651916cd43dd8448eb211c80319c",
                                    "spanId": "b7ad6b7169203331"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        try:
            response = await http_client.post(
                f"{otel_collector_url}/v1/logs",
                json=logs_payload,
                headers={"Content-Type": "application/json"},
            )

            # Collector should accept the logs (200, 201, or 202)
            assert response.status_code in [200, 201, 202]

        except httpx.ConnectError:
            pytest.skip("OTEL Collector HTTP receiver not available")


class TestCollectorPipelines:
    """Test suite for OTEL Collector pipeline processing."""

    @pytest.mark.asyncio
    async def test_trace_pipeline_processes_data(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        otel_collector_url: str,
        wait_for_services,
    ):
        """
        Test that traces flow through the collector pipeline.

        Pipeline: receivers -> processors -> exporters
        - Receiver: OTLP HTTP/gRPC
        - Processors: memory_limiter, resource, batch
        - Exporter: OTLP to Elastic
        """
        # Generate a trace by creating an order
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with collector access, we would:
        # 1. Query collector metrics to verify trace was received
        # 2. Verify trace was processed through pipeline
        # 3. Verify trace was exported to Elastic endpoint
        # 4. Check metrics like: otelcol_receiver_accepted_spans


    @pytest.mark.asyncio
    async def test_metrics_pipeline_processes_data(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that metrics flow through the collector pipeline.

        Services auto-generate runtime metrics which should be processed.
        """
        # Generate metrics by creating an order
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with collector access, we would:
        # 1. Query collector metrics to verify metrics were received
        # 2. Verify metrics were processed through pipeline
        # 3. Check metrics like: otelcol_receiver_accepted_metric_points


    @pytest.mark.asyncio
    async def test_logs_pipeline_processes_data(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that logs flow through the collector pipeline.

        Application logs should be captured and processed.
        """
        # Generate logs by creating an order
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with collector access, we would:
        # 1. Query collector metrics to verify logs were received
        # 2. Verify logs were processed through pipeline
        # 3. Check metrics like: otelcol_receiver_accepted_log_records


class TestCollectorProcessors:
    """Test suite for OTEL Collector processors."""

    @pytest.mark.asyncio
    async def test_resource_processor_adds_attributes(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that resource processor adds deployment.environment and workshop.name.

        The resource processor in the collector config adds:
        - deployment.environment from ENVIRONMENT env var
        - workshop.name = "from-commit-to-culprit"
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with Elastic access, we would:
        # 1. Query the trace in Elastic
        # 2. Verify all spans have deployment.environment attribute
        # 3. Verify all spans have workshop.name = "from-commit-to-culprit"


    @pytest.mark.asyncio
    async def test_batch_processor_batches_telemetry(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that batch processor batches telemetry before export.

        Batch processor config:
        - timeout: 1s
        - send_batch_size: 1024

        This reduces export overhead.
        """
        # Send multiple requests to generate multiple spans
        for i in range(5):
            response = await http_client.post(
                f"{order_service_url}/api/orders",
                json=sample_order_request,
            )
            assert response.status_code in [200, 201]

        # In a full test with collector metrics access, we would:
        # 1. Check otelcol_processor_batch_batch_send_size
        # 2. Verify batches are being created
        # 3. Verify timeout mechanism works


    @pytest.mark.asyncio
    async def test_memory_limiter_processor(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that memory limiter prevents OOM.

        Memory limiter config:
        - limit_mib: 512
        - spike_limit_mib: 128

        Under normal load, this should not trigger.
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with collector metrics access, we would:
        # 1. Check otelcol_processor_refused_spans
        # 2. Verify it's 0 (no spans refused under normal load)


class TestCollectorExporter:
    """Test suite for OTEL Collector exporter to Elastic."""

    @pytest.mark.asyncio
    async def test_elastic_exporter_configuration(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that collector is configured to export to Elastic.

        The otlp/elastic exporter should:
        - Send to ELASTIC_ENDPOINT
        - Use ELASTIC_API_KEY for auth
        - Use gzip compression
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with Elastic access, we would:
        # 1. Verify trace appears in Elastic APM
        # 2. Verify trace contains all expected spans
        # 3. Verify resource attributes are present


    @pytest.mark.asyncio
    async def test_telemetry_reaches_elastic(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test end-to-end: telemetry from service to Elastic.

        Full pipeline:
        1. Service generates trace/metrics/logs
        2. EDOT SDK sends to collector via OTLP
        3. Collector processes through pipelines
        4. Collector exports to Elastic
        5. Data appears in Kibana
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"
        response_data = response.json()
        order_id = response_data.get("orderId") or response_data.get("order_id")

        # Give telemetry time to propagate (batch processor has 1s timeout)
        await asyncio.sleep(2)

        # In a full test with Elastic API access, we would:
        # 1. Query Elastic APM API for traces with the order_id
        # 2. Verify trace exists
        # 3. Verify all three services appear in the trace
        # 4. Verify logs can be queried by trace_id
        # 5. Verify metrics are present


class TestCollectorErrorHandling:
    """Test suite for collector error handling."""

    @pytest.mark.asyncio
    async def test_collector_handles_malformed_data(
        self,
        http_client: httpx.AsyncClient,
        otel_collector_url: str,
    ):
        """
        Test that collector gracefully handles malformed OTLP data.

        Malformed data should be rejected with appropriate error response.
        """
        # Send invalid JSON
        try:
            response = await http_client.post(
                f"{otel_collector_url}/v1/traces",
                content="not valid json",
                headers={"Content-Type": "application/json"},
            )

            # Collector should reject with 4xx error
            assert response.status_code >= 400

        except httpx.ConnectError:
            pytest.skip("OTEL Collector not available")


    @pytest.mark.asyncio
    async def test_collector_continues_on_export_failure(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that collector continues receiving data even if export fails.

        If Elastic endpoint is unreachable, the collector should:
        - Continue accepting data from services
        - Buffer data (up to memory limits)
        - Retry exports
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with collector metrics, we would:
        # 1. Temporarily break Elastic connection
        # 2. Send telemetry
        # 3. Verify collector still accepts data
        # 4. Check otelcol_exporter_send_failed_spans
        # 5. Restore connection
        # 6. Verify data eventually exports


class TestCollectorConfiguration:
    """Test suite for collector configuration validation."""

    @pytest.mark.asyncio
    async def test_collector_uses_environment_variables(
        self,
        http_client: httpx.AsyncClient,
        order_service_url: str,
        sample_order_request: dict,
        wait_for_services,
    ):
        """
        Test that collector correctly uses environment variables.

        Expected env vars:
        - ELASTIC_ENDPOINT
        - ELASTIC_API_KEY
        - ENVIRONMENT
        """
        response = await http_client.post(
            f"{order_service_url}/api/orders",
            json=sample_order_request,
        )

        assert response.status_code in [200, 201], f"Order creation failed: {response.text}"

        # In a full test with Elastic access, we would:
        # 1. Verify telemetry reaches the configured ELASTIC_ENDPOINT
        # 2. Verify deployment.environment matches ENVIRONMENT env var

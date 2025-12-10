"""
Rollback execution logic for the webhook service.

From Commit to Culprit Workshop - Rollback Webhook Service

This module handles the actual rollback process:
1. Validates the rollback request
2. Updates the .env file with the new service version
3. Executes docker-compose to restart the service
4. Tracks rollback status and provides detailed logging

SECURITY NOTE: This service requires access to the Docker socket and filesystem
to perform rollbacks. In production, this would require careful security review.
"""

import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from opentelemetry import trace

from .models import RollbackRequest, RollbackResponse, RollbackStatus, ServiceName

# Get OpenTelemetry tracer
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class RollbackExecutor:
    """
    Executes rollback operations by modifying .env and restarting services.

    This class is responsible for the core rollback logic used in the workshop
    to demonstrate automated remediation via Elastic Alerting workflows.
    """

    def __init__(
        self,
        compose_file: str = "/app/infra/docker-compose.yml",
        env_file: str = "/app/infra/.env",
    ):
        """
        Initialize the rollback executor.

        Args:
            compose_file: Path to docker-compose.yml
            env_file: Path to .env file containing service versions
        """
        self.compose_file = Path(compose_file)
        self.env_file = Path(env_file)
        self.last_rollback: Optional[RollbackResponse] = None
        self.total_rollbacks: int = 0

        logger.info(
            f"RollbackExecutor initialized with compose_file={compose_file}, env_file={env_file}"
        )

    def validate_environment(self) -> Tuple[bool, str]:
        """
        Validate that the required files and Docker are accessible.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if env file exists
        if not self.env_file.exists():
            return False, f"Environment file not found: {self.env_file}"

        # Check if compose file exists
        if not self.compose_file.exists():
            return False, f"Docker Compose file not found: {self.compose_file}"

        # Check if Docker is available
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return False, f"Docker not available: {result.stderr}"
        except Exception as e:
            return False, f"Docker not available: {str(e)}"

        return True, ""

    def get_current_version(self, service: ServiceName) -> Optional[str]:
        """
        Get the current version of a service from the .env file.

        Args:
            service: Service name (e.g., ServiceName.ORDER_SERVICE)

        Returns:
            Current version string or None if not found
        """
        env_var = self._get_env_var_name(service)

        try:
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{env_var}="):
                        version = line.split("=", 1)[1].strip()
                        logger.debug(f"Found current version for {service}: {version}")
                        return version
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")

        return None

    def update_service_version(self, service: ServiceName, version: str) -> bool:
        """
        Update the service version in the .env file.

        Args:
            service: Service name
            version: New version to set

        Returns:
            True if successful, False otherwise
        """
        env_var = self._get_env_var_name(service)

        try:
            # Read the current .env file
            with open(self.env_file, "r") as f:
                lines = f.readlines()

            # Update the version line
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{env_var}="):
                    lines[i] = f"{env_var}={version}\n"
                    updated = True
                    logger.info(f"Updated {env_var} to {version} in .env file")
                    break

            if not updated:
                logger.warning(f"{env_var} not found in .env, appending")
                lines.append(f"{env_var}={version}\n")

            # Write back to the file
            with open(self.env_file, "w") as f:
                f.writelines(lines)

            return True

        except Exception as e:
            logger.error(f"Error updating .env file: {e}")
            return False

    def restart_service(self, service: ServiceName) -> Tuple[bool, str]:
        """
        Restart the service using docker-compose.

        Args:
            service: Service name to restart

        Returns:
            Tuple of (success, output/error message)
        """
        try:
            # Use docker compose (v2) or docker-compose (v1)
            # Try docker compose first (newer)
            compose_cmd = ["docker", "compose"]
            test_result = subprocess.run(
                compose_cmd + ["version"],
                capture_output=True,
                timeout=5,
            )

            if test_result.returncode != 0:
                # Fall back to docker-compose v1
                compose_cmd = ["docker-compose"]

            # Build the restart command
            # Using up -d --no-deps to restart only this service
            cmd = compose_cmd + [
                "-f",
                str(self.compose_file),
                "--env-file",
                str(self.env_file),
                "up",
                "-d",
                "--no-deps",
                service.value,
            ]

            logger.info(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                logger.info(f"Successfully restarted {service}")
                return True, result.stdout
            else:
                logger.error(f"Failed to restart {service}: {result.stderr}")
                return False, result.stderr

        except subprocess.TimeoutExpired:
            error_msg = f"Timeout while restarting {service}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error restarting {service}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def execute_rollback(self, request: RollbackRequest) -> RollbackResponse:
        """
        Execute a complete rollback operation.

        This is the main entry point for rollback operations. It:
        1. Validates the environment
        2. Gets the current version
        3. Updates the .env file
        4. Restarts the service
        5. Returns detailed status

        Args:
            request: RollbackRequest with service and target version

        Returns:
            RollbackResponse with detailed status
        """
        # Generate a unique rollback ID
        rollback_id = f"rb-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{request.service.value}"
        started_at = datetime.utcnow()

        # Get the current trace context
        current_span = trace.get_current_span()
        trace_id = None
        if current_span and current_span.get_span_context().is_valid:
            trace_id = format(current_span.get_span_context().trace_id, "032x")

        logger.info(
            f"Starting rollback {rollback_id}: {request.service} -> {request.target_version}",
            extra={
                "rollback_id": rollback_id,
                "service": request.service.value,
                "target_version": request.target_version,
                "alert_id": request.alert_id,
                "reason": request.reason,
                "trace_id": trace_id,
            },
        )

        # Create a span for the entire rollback operation
        with tracer.start_as_current_span("execute_rollback") as span:
            span.set_attribute("rollback.id", rollback_id)
            span.set_attribute("rollback.service", request.service.value)
            span.set_attribute("rollback.target_version", request.target_version)
            span.set_attribute("rollback.alert_id", request.alert_id)
            span.set_attribute("rollback.reason", request.reason)

            # Step 1: Validate environment
            is_valid, error_msg = self.validate_environment()
            if not is_valid:
                logger.error(f"Environment validation failed: {error_msg}")
                span.set_attribute("rollback.status", "FAILED")
                span.set_attribute("rollback.error", error_msg)

                response = RollbackResponse(
                    status=RollbackStatus.ROLLBACK_FAILED,
                    message=f"Rollback validation failed: {error_msg}",
                    service=request.service,
                    target_version=request.target_version,
                    rollback_id=rollback_id,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    error=error_msg,
                    trace_id=trace_id,
                )
                self.last_rollback = response
                return response

            # Step 2: Get current version
            previous_version = self.get_current_version(request.service)
            if previous_version:
                logger.info(f"Current version of {request.service}: {previous_version}")
                span.set_attribute("rollback.previous_version", previous_version)

            # Step 3: Update .env file
            with tracer.start_as_current_span("update_env_file") as env_span:
                env_span.set_attribute("env_file", str(self.env_file))
                env_span.set_attribute("service", request.service.value)
                env_span.set_attribute("new_version", request.target_version)

                if not self.update_service_version(request.service, request.target_version):
                    error_msg = "Failed to update .env file"
                    logger.error(error_msg)
                    span.set_attribute("rollback.status", "FAILED")
                    span.set_attribute("rollback.error", error_msg)

                    response = RollbackResponse(
                        status=RollbackStatus.ROLLBACK_FAILED,
                        message=f"Rollback failed: {error_msg}",
                        service=request.service,
                        previous_version=previous_version,
                        target_version=request.target_version,
                        rollback_id=rollback_id,
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                        error=error_msg,
                        trace_id=trace_id,
                    )
                    self.last_rollback = response
                    return response

            # Step 4: Restart the service
            with tracer.start_as_current_span("restart_service") as restart_span:
                restart_span.set_attribute("service", request.service.value)
                restart_span.set_attribute("compose_file", str(self.compose_file))

                success, output = self.restart_service(request.service)

                if not success:
                    error_msg = f"Failed to restart service: {output}"
                    logger.error(error_msg)
                    span.set_attribute("rollback.status", "FAILED")
                    span.set_attribute("rollback.error", error_msg)

                    response = RollbackResponse(
                        status=RollbackStatus.ROLLBACK_FAILED,
                        message=f"Rollback failed during service restart: {output}",
                        service=request.service,
                        previous_version=previous_version,
                        target_version=request.target_version,
                        rollback_id=rollback_id,
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                        error=error_msg,
                        trace_id=trace_id,
                    )
                    self.last_rollback = response
                    return response

                restart_span.set_attribute("restart.success", True)
                restart_span.set_attribute("restart.output", output[:500])  # Truncate

            # Success!
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()

            span.set_attribute("rollback.status", "COMPLETED")
            span.set_attribute("rollback.duration_seconds", duration_seconds)

            message = (
                f"Successfully rolled back {request.service.value} from "
                f"{previous_version or 'unknown'} to {request.target_version} "
                f"in {duration_seconds:.2f} seconds"
            )

            logger.info(
                message,
                extra={
                    "rollback_id": rollback_id,
                    "service": request.service.value,
                    "previous_version": previous_version,
                    "target_version": request.target_version,
                    "duration_seconds": duration_seconds,
                    "trace_id": trace_id,
                },
            )

            response = RollbackResponse(
                status=RollbackStatus.ROLLBACK_COMPLETED,
                message=message,
                service=request.service,
                previous_version=previous_version,
                target_version=request.target_version,
                rollback_id=rollback_id,
                started_at=started_at,
                completed_at=completed_at,
                trace_id=trace_id,
            )

            self.last_rollback = response
            self.total_rollbacks += 1

            return response

    @staticmethod
    def _get_env_var_name(service: ServiceName) -> str:
        """
        Get the environment variable name for a service version.

        Args:
            service: ServiceName enum

        Returns:
            Environment variable name (e.g., 'ORDER_SERVICE_VERSION')
        """
        # Convert order-service to ORDER_SERVICE_VERSION
        service_upper = service.value.upper().replace("-", "_")
        return f"{service_upper}_VERSION"

"""
Unit tests for Rollback Webhook Service rollback execution logic.

Tests rollback execution including:
- Environment validation
- Version retrieval and updates
- Service restart logic
- Rollback workflow orchestration

Workshop: From Commit to Culprit - Rollback Webhook Service Tests
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
from datetime import datetime

# Add the service to the path
service_path = Path(__file__).parent.parent.parent.parent / "services" / "rollback-webhook" / "src"
sys.path.insert(0, str(service_path))

from webhook.rollback import RollbackExecutor
from webhook.models import RollbackRequest, RollbackStatus, ServiceName


@pytest.fixture
def rollback_executor():
    """Create a RollbackExecutor instance for testing."""
    return RollbackExecutor(
        compose_file="/test/docker-compose.yml",
        env_file="/test/.env"
    )


class TestRollbackExecutorInit:
    """Test RollbackExecutor initialization."""

    def test_init_sets_paths(self):
        """Test that initialization sets correct paths."""
        executor = RollbackExecutor(
            compose_file="/custom/compose.yml",
            env_file="/custom/.env"
        )

        assert executor.compose_file == Path("/custom/compose.yml")
        assert executor.env_file == Path("/custom/.env")

    def test_init_default_values(self):
        """Test initialization with default values."""
        executor = RollbackExecutor()

        assert executor.compose_file == Path("/app/infra/docker-compose.yml")
        assert executor.env_file == Path("/app/infra/.env")
        assert executor.last_rollback is None
        assert executor.total_rollbacks == 0


class TestValidateEnvironment:
    """Test environment validation."""

    @patch("pathlib.Path.exists")
    @patch("subprocess.run")
    def test_validate_environment_all_valid(self, mock_run, mock_exists, rollback_executor):
        """Test validation when all requirements are met."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        is_valid, error_msg = rollback_executor.validate_environment()

        assert is_valid is True
        assert error_msg == ""

    @patch("pathlib.Path.exists")
    def test_validate_environment_env_file_missing(self, mock_exists, rollback_executor):
        """Test validation when env file is missing."""
        # First call (env_file) returns False, second call (compose_file) doesn't matter
        mock_exists.return_value = False

        is_valid, error_msg = rollback_executor.validate_environment()

        assert is_valid is False
        assert "Environment file not found" in error_msg

    @patch("pathlib.Path.exists")
    def test_validate_environment_compose_file_missing(self, mock_exists, rollback_executor):
        """Test validation when compose file is missing."""
        # env_file exists (True), compose_file doesn't (False)
        mock_exists.side_effect = [True, False]

        is_valid, error_msg = rollback_executor.validate_environment()

        assert is_valid is False
        assert "Docker Compose file not found" in error_msg

    @patch("pathlib.Path.exists")
    @patch("subprocess.run")
    def test_validate_environment_docker_not_available(self, mock_run, mock_exists, rollback_executor):
        """Test validation when Docker is not available."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=1, stderr="Docker daemon not running")

        is_valid, error_msg = rollback_executor.validate_environment()

        assert is_valid is False
        assert "Docker not available" in error_msg

    @patch("pathlib.Path.exists")
    @patch("subprocess.run")
    def test_validate_environment_docker_exception(self, mock_run, mock_exists, rollback_executor):
        """Test validation when Docker check raises exception."""
        mock_exists.return_value = True
        mock_run.side_effect = Exception("Connection error")

        is_valid, error_msg = rollback_executor.validate_environment()

        assert is_valid is False
        assert "Docker not available" in error_msg


class TestGetCurrentVersion:
    """Test getting current service version."""

    def test_get_current_version_found(self, rollback_executor):
        """Test getting version when it exists in .env file."""
        env_content = """
ENVIRONMENT=local
ORDER_SERVICE_VERSION=v1.1-bad
INVENTORY_SERVICE_VERSION=v1.0
PAYMENT_SERVICE_VERSION=v1.0
"""
        with patch("builtins.open", mock_open(read_data=env_content)):
            version = rollback_executor.get_current_version(ServiceName.ORDER_SERVICE)

        assert version == "v1.1-bad"

    def test_get_current_version_with_whitespace(self, rollback_executor):
        """Test getting version with extra whitespace."""
        env_content = "ORDER_SERVICE_VERSION = v1.0  \n"

        with patch("builtins.open", mock_open(read_data=env_content)):
            version = rollback_executor.get_current_version(ServiceName.ORDER_SERVICE)

        assert version == "v1.0"

    def test_get_current_version_not_found(self, rollback_executor):
        """Test getting version when it doesn't exist."""
        env_content = "SOME_OTHER_VAR=value\n"

        with patch("builtins.open", mock_open(read_data=env_content)):
            version = rollback_executor.get_current_version(ServiceName.ORDER_SERVICE)

        assert version is None

    def test_get_current_version_file_error(self, rollback_executor):
        """Test getting version when file read fails."""
        with patch("builtins.open", side_effect=IOError("File not found")):
            version = rollback_executor.get_current_version(ServiceName.ORDER_SERVICE)

        assert version is None

    def test_get_current_version_inventory_service(self, rollback_executor):
        """Test getting version for inventory service."""
        env_content = "INVENTORY_SERVICE_VERSION=v2.0\n"

        with patch("builtins.open", mock_open(read_data=env_content)):
            version = rollback_executor.get_current_version(ServiceName.INVENTORY_SERVICE)

        assert version == "v2.0"

    def test_get_current_version_payment_service(self, rollback_executor):
        """Test getting version for payment service."""
        env_content = "PAYMENT_SERVICE_VERSION=v3.0\n"

        with patch("builtins.open", mock_open(read_data=env_content)):
            version = rollback_executor.get_current_version(ServiceName.PAYMENT_SERVICE)

        assert version == "v3.0"


class TestUpdateServiceVersion:
    """Test updating service version in .env file."""

    def test_update_service_version_success(self, rollback_executor):
        """Test successful version update."""
        original_content = "ORDER_SERVICE_VERSION=v1.1-bad\nOTHER_VAR=value\n"

        m = mock_open(read_data=original_content)
        with patch("builtins.open", m):
            result = rollback_executor.update_service_version(ServiceName.ORDER_SERVICE, "v1.0")

        assert result is True

        # Verify the write was called with updated content
        handle = m()
        written_content = "".join([call[0][0] for call in handle.write.call_args_list])
        assert "ORDER_SERVICE_VERSION=v1.0" in written_content
        assert "OTHER_VAR=value" in written_content

    def test_update_service_version_appends_if_not_found(self, rollback_executor):
        """Test that version is appended if not found."""
        original_content = "OTHER_VAR=value\n"

        m = mock_open(read_data=original_content)
        with patch("builtins.open", m):
            result = rollback_executor.update_service_version(ServiceName.ORDER_SERVICE, "v1.0")

        assert result is True

    def test_update_service_version_file_error(self, rollback_executor):
        """Test update when file operations fail."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = rollback_executor.update_service_version(ServiceName.ORDER_SERVICE, "v1.0")

        assert result is False


class TestRestartService:
    """Test service restart logic."""

    @patch("subprocess.run")
    def test_restart_service_success_with_docker_compose_v2(self, mock_run, rollback_executor):
        """Test successful restart using docker compose v2."""
        # Mock docker compose version check (success)
        mock_run.side_effect = [
            MagicMock(returncode=0),  # version check succeeds
            MagicMock(returncode=0, stdout="Service restarted")  # restart succeeds
        ]

        success, output = rollback_executor.restart_service(ServiceName.ORDER_SERVICE)

        assert success is True
        assert "Service restarted" in output

        # Verify docker compose v2 was used
        restart_call = mock_run.call_args_list[1]
        assert "docker" in restart_call[0][0]
        assert "compose" in restart_call[0][0]

    @patch("subprocess.run")
    def test_restart_service_success_with_docker_compose_v1(self, mock_run, rollback_executor):
        """Test successful restart using docker-compose v1."""
        # Mock docker compose version check (fails, falls back to v1)
        mock_run.side_effect = [
            MagicMock(returncode=1),  # version check fails
            MagicMock(returncode=0, stdout="Service restarted")  # restart succeeds
        ]

        success, output = rollback_executor.restart_service(ServiceName.ORDER_SERVICE)

        assert success is True

    @patch("subprocess.run")
    def test_restart_service_failure(self, mock_run, rollback_executor):
        """Test restart when docker compose fails."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # version check succeeds
            MagicMock(returncode=1, stderr="Container not found")  # restart fails
        ]

        success, output = rollback_executor.restart_service(ServiceName.ORDER_SERVICE)

        assert success is False
        assert "Container not found" in output

    @patch("subprocess.run")
    def test_restart_service_timeout(self, mock_run, rollback_executor):
        """Test restart when operation times out."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = [
            MagicMock(returncode=0),  # version check succeeds
            TimeoutExpired("docker", 60)  # restart times out
        ]

        success, output = rollback_executor.restart_service(ServiceName.ORDER_SERVICE)

        assert success is False
        assert "Timeout" in output

    @patch("subprocess.run")
    def test_restart_service_exception(self, mock_run, rollback_executor):
        """Test restart when exception occurs."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # version check succeeds
            Exception("Unexpected error")  # restart raises exception
        ]

        success, output = rollback_executor.restart_service(ServiceName.ORDER_SERVICE)

        assert success is False
        assert "Error restarting" in output


class TestExecuteRollback:
    """Test complete rollback execution."""

    @patch("webhook.rollback.RollbackExecutor.validate_environment")
    @patch("webhook.rollback.RollbackExecutor.get_current_version")
    @patch("webhook.rollback.RollbackExecutor.update_service_version")
    @patch("webhook.rollback.RollbackExecutor.restart_service")
    def test_execute_rollback_success(self, mock_restart, mock_update, mock_get_version,
                                      mock_validate, rollback_executor):
        """Test successful complete rollback."""
        # Setup mocks
        mock_validate.return_value = (True, "")
        mock_get_version.return_value = "v1.1-bad"
        mock_update.return_value = True
        mock_restart.return_value = (True, "Service restarted")

        request = RollbackRequest(
            service=ServiceName.ORDER_SERVICE,
            target_version="v1.0",
            alert_id="alert-123",
            alert_name="SLO Burn Rate",
            reason="High latency"
        )

        response = rollback_executor.execute_rollback(request)

        assert response.status == RollbackStatus.ROLLBACK_COMPLETED
        assert response.service == ServiceName.ORDER_SERVICE
        assert response.target_version == "v1.0"
        assert response.previous_version == "v1.1-bad"
        assert response.error is None
        assert rollback_executor.total_rollbacks == 1

    @patch("webhook.rollback.RollbackExecutor.validate_environment")
    def test_execute_rollback_validation_fails(self, mock_validate, rollback_executor):
        """Test rollback when environment validation fails."""
        mock_validate.return_value = (False, "Docker not available")

        request = RollbackRequest(
            service=ServiceName.ORDER_SERVICE,
            target_version="v1.0",
            alert_id="alert-456",
            alert_name="Test Alert",
            reason="Testing"
        )

        response = rollback_executor.execute_rollback(request)

        assert response.status == RollbackStatus.ROLLBACK_FAILED
        assert "Docker not available" in response.error
        assert rollback_executor.total_rollbacks == 0

    @patch("webhook.rollback.RollbackExecutor.validate_environment")
    @patch("webhook.rollback.RollbackExecutor.get_current_version")
    @patch("webhook.rollback.RollbackExecutor.update_service_version")
    def test_execute_rollback_update_fails(self, mock_update, mock_get_version,
                                           mock_validate, rollback_executor):
        """Test rollback when .env update fails."""
        mock_validate.return_value = (True, "")
        mock_get_version.return_value = "v1.1-bad"
        mock_update.return_value = False

        request = RollbackRequest(
            service=ServiceName.ORDER_SERVICE,
            target_version="v1.0",
            alert_id="alert-789",
            alert_name="Test Alert",
            reason="Testing"
        )

        response = rollback_executor.execute_rollback(request)

        assert response.status == RollbackStatus.ROLLBACK_FAILED
        assert "Failed to update .env file" in response.error

    @patch("webhook.rollback.RollbackExecutor.validate_environment")
    @patch("webhook.rollback.RollbackExecutor.get_current_version")
    @patch("webhook.rollback.RollbackExecutor.update_service_version")
    @patch("webhook.rollback.RollbackExecutor.restart_service")
    def test_execute_rollback_restart_fails(self, mock_restart, mock_update, mock_get_version,
                                            mock_validate, rollback_executor):
        """Test rollback when service restart fails."""
        mock_validate.return_value = (True, "")
        mock_get_version.return_value = "v1.1-bad"
        mock_update.return_value = True
        mock_restart.return_value = (False, "Container not found")

        request = RollbackRequest(
            service=ServiceName.ORDER_SERVICE,
            target_version="v1.0",
            alert_id="alert-restart",
            alert_name="Test Alert",
            reason="Testing"
        )

        response = rollback_executor.execute_rollback(request)

        assert response.status == RollbackStatus.ROLLBACK_FAILED
        assert "Container not found" in response.error


class TestGetEnvVarName:
    """Test environment variable name generation."""

    def test_get_env_var_name_order_service(self):
        """Test env var name for order service."""
        var_name = RollbackExecutor._get_env_var_name(ServiceName.ORDER_SERVICE)
        assert var_name == "ORDER_SERVICE_VERSION"

    def test_get_env_var_name_inventory_service(self):
        """Test env var name for inventory service."""
        var_name = RollbackExecutor._get_env_var_name(ServiceName.INVENTORY_SERVICE)
        assert var_name == "INVENTORY_SERVICE_VERSION"

    def test_get_env_var_name_payment_service(self):
        """Test env var name for payment service."""
        var_name = RollbackExecutor._get_env_var_name(ServiceName.PAYMENT_SERVICE)
        assert var_name == "PAYMENT_SERVICE_VERSION"

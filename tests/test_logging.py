"""
Tests for the logging functionality of the Agent Name Service.
"""
import os
import pytest
import logging
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime

from ans.api.logging import (
    setup_logging,
    log_request,
    log_response,
    log_security_event,
    log_certificate_event,
    log_rate_limit_exceeded
)


class TestLogging:
    """Test the ANS logging functionality."""
    
    @pytest.fixture
    def log_directory(self):
        """Create and return a temporary log directory."""
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
    
    @pytest.fixture
    def server_log_file(self, log_directory):
        """Return the path to the server log file."""
        return os.path.join(log_directory, "ans_server_test.log")
    
    @pytest.fixture
    def audit_log_file(self, log_directory):
        """Return the path to the audit log file."""
        return os.path.join(log_directory, "ans_audit_test.log")
    
    def test_setup_logging(self, server_log_file, audit_log_file):
        """Test that logging setup creates the correct log handlers."""
        # Set up logging with test log files
        with patch("logging.FileHandler") as mock_file_handler:
            setup_logging(server_log_file, audit_log_file)
            
            # Verify two file handlers were created (one for each log file)
            assert mock_file_handler.call_count == 2
            
            # Check the log file paths
            call_args_list = mock_file_handler.call_args_list
            assert server_log_file in str(call_args_list[0])
            assert audit_log_file in str(call_args_list[1])
    
    def test_log_request(self, server_log_file, audit_log_file):
        """Test that requests are logged correctly."""
        # Set up logging with test log files
        setup_logging(server_log_file, audit_log_file)
        
        # Create a mock request
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"User-Agent": "Test Client"}
        
        # Log the request
        with patch("logging.Logger.info") as mock_info:
            log_request(mock_request)
            
            # Verify logging was called
            mock_info.assert_called_once()
            # Check that the log message contains relevant info
            log_msg = mock_info.call_args[0][0]
            assert "GET" in log_msg
            assert "/test" in log_msg
            assert "127.0.0.1" in log_msg
    
    def test_log_response(self, server_log_file, audit_log_file):
        """Test that responses are logged correctly."""
        # Set up logging with test log files
        setup_logging(server_log_file, audit_log_file)
        
        # Create mock request and response
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Log the response
        execution_time = 100.5  # ms
        with patch("logging.Logger.info") as mock_info:
            log_response(mock_request, mock_response, execution_time)
            
            # Verify logging was called
            mock_info.assert_called_once()
            # Check that the log message contains relevant info
            log_msg = mock_info.call_args[0][0]
            assert "GET" in log_msg
            assert "/test" in log_msg
            assert "200" in log_msg
            assert "100.5" in log_msg
    
    def test_log_security_event(self, server_log_file, audit_log_file):
        """Test that security events are logged correctly."""
        # Set up logging with test log files
        setup_logging(server_log_file, audit_log_file)

        # Create a mock request
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # Log a security event
        event_type = "login_failure"
        details = {"username": "test_user", "reason": "invalid_password"}
        source = "auth_api"

        # Since our implementation logs to both audit and server loggers,
        # we need to check that warning was called at least once, not exactly once
        with patch("logging.Logger.warning") as mock_warning:
            log_security_event(event_type, details, source, mock_request)

            # Verify logging was called at least once
            assert mock_warning.call_count >= 1, "Warning was not logged"

            # Check that the log message contains relevant info using the first call
            log_msg = mock_warning.call_args_list[0][0][0]
            assert "login_failure" in log_msg
            assert "test_user" in log_msg
            assert "auth_api" in log_msg
            assert "127.0.0.1" in log_msg
    
    def test_log_certificate_event(self, server_log_file, audit_log_file):
        """Test that certificate events are logged correctly."""
        # Set up logging with test log files
        setup_logging(server_log_file, audit_log_file)

        # Log a certificate event
        event_type = "issued"
        agent_id = "test-agent"
        details = {"cert_serial": "12345", "valid_until": "2025-12-31"}
        source = "ca_service"

        with patch("logging.Logger.info") as mock_info:
            log_certificate_event(event_type, agent_id, details, source)

            # Verify logging was called at least once (we log to both server and audit loggers)
            assert mock_info.call_count >= 1, "Info was not logged"

            # Check that the log message contains relevant info
            log_msg = mock_info.call_args_list[0][0][0]
            assert "issued" in log_msg
            assert "test-agent" in log_msg
            assert "12345" in log_msg
            assert "ca_service" in log_msg
    
    def test_log_rate_limit_exceeded(self, server_log_file, audit_log_file):
        """Test that rate limit exceeded events are logged correctly."""
        # Set up logging with test log files
        setup_logging(server_log_file, audit_log_file)

        # Create a mock request
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/register"
        mock_request.client.host = "127.0.0.1"

        # Log a rate limit exceeded event
        with patch("logging.Logger.warning") as mock_warning:
            log_rate_limit_exceeded(mock_request)

            # Verify logging was called at least once (we log to both server and audit loggers)
            assert mock_warning.call_count >= 1, "Warning was not logged"

            # Check that the log message contains relevant info
            log_msg = mock_warning.call_args_list[0][0][0]
            assert "Rate limit exceeded" in log_msg
            assert "POST" in log_msg
            assert "/register" in log_msg
            assert "127.0.0.1" in log_msg
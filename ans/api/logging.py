"""
Logging configuration for the Agent Name Service.
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response

# Logger instances
server_logger = logging.getLogger("ans.server")
audit_logger = logging.getLogger("ans.audit")

def setup_logging(server_log_path: str = None, audit_log_path: str = None) -> None:
    """
    Set up logging for the ANS service.
    
    Args:
        server_log_path: Path to the server log file (defaults to tests/logs/ans_server.log)
        audit_log_path: Path to the audit log file (defaults to tests/logs/ans_audit.log)
    """
    # Set default log paths if not provided
    if server_log_path is None:
        # Use tests/logs directory by default
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "logs")
        os.makedirs(log_dir, exist_ok=True)
        server_log_path = os.path.join(log_dir, "ans_server.log")
    
    if audit_log_path is None:
        # Use tests/logs directory by default
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "logs")
        os.makedirs(log_dir, exist_ok=True)
        audit_log_path = os.path.join(log_dir, "ans_audit.log")
    
    # Configure server logger
    server_logger.setLevel(logging.INFO)
    server_handler = logging.FileHandler(server_log_path)
    server_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    server_handler.setFormatter(server_formatter)
    server_logger.addHandler(server_handler)
    
    # Configure console handler for server logger
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(server_formatter)
    server_logger.addHandler(console_handler)
    
    # Configure audit logger
    audit_logger.setLevel(logging.INFO)
    audit_handler = logging.FileHandler(audit_log_path)
    audit_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    audit_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_handler)

def log_request(request: Request) -> None:
    """
    Log an incoming request.
    
    Args:
        request: The FastAPI request object
    """
    server_logger.info(
        f"Request: {request.method} {request.url.path} from {request.client.host} "
        f"- User-Agent: {request.headers.get('user-agent', 'Unknown')}"
    )

def log_response(request: Request, response: Response, execution_time: float = None) -> None:
    """
    Log a response to a request.
    
    Args:
        request: The FastAPI request object
        response: The FastAPI response object
        execution_time: The time taken to process the request (in ms)
    """
    log_message = (
        f"Response: {request.method} {request.url.path} from {request.client.host} "
        f"- Status: {response.status_code}"
    )
    
    if execution_time is not None:
        log_message += f" - Time: {execution_time:.2f}ms"
    
    server_logger.info(log_message)

def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    source: str,
    request: Optional[Request] = None
) -> None:
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event (e.g., "access_denied", "invalid_token")
        details: Details of the event
        source: Source of the event (e.g., "auth_service", "public_api")
        request: Associated request object (if any)
    """
    client_ip = request.client.host if request else "unknown"
    
    log_message = (
        f"Security event: {event_type} from {source} - IP: {client_ip} - "
        f"Details: {json.dumps(details)}"
    )
    
    audit_logger.warning(log_message)
    server_logger.warning(log_message)

def log_certificate_event(
    event_type: str,
    agent_id: str,
    details: Dict[str, Any],
    source: str
) -> None:
    """
    Log a certificate-related event.
    
    Args:
        event_type: Type of certificate event (e.g., "issued", "revoked")
        agent_id: ID of the agent the certificate belongs to
        details: Details of the event
        source: Source of the event (e.g., "ca_service", "public_api")
    """
    log_message = (
        f"Certificate event: {event_type} for agent {agent_id} from {source} - "
        f"Details: {json.dumps(details)}"
    )
    
    audit_logger.info(log_message)
    server_logger.info(log_message)

def log_rate_limit_exceeded(request: Request) -> None:
    """
    Log a rate limit exceeded event.
    
    Args:
        request: The FastAPI request object
    """
    log_message = (
        f"Rate limit exceeded: {request.method} {request.url.path} from {request.client.host}"
    )
    
    audit_logger.warning(log_message)
    server_logger.warning(log_message)

# Set up logging on import
setup_logging()
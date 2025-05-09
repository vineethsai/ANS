"""
Security audit logging for the ANS API.
"""
import json
import logging
from datetime import datetime
import os
from typing import Dict, Any, Optional
from fastapi import Request, Response

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = os.environ.get("ANS_LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("ANS_LOG_FILE", "ans_audit.log")

# Create logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ans-audit")

def get_client_info(request: Request) -> Dict[str, Any]:
    """Get client information from the request."""
    return {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "referer": request.headers.get("referer"),
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
    }

def log_request(request: Request, username: Optional[str] = None) -> None:
    """Log an incoming request."""
    client_info = get_client_info(request)
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "request",
        "username": username or "anonymous",
        "client": client_info,
        "headers": dict(request.headers),
    }
    
    # Sanitize sensitive headers
    if "authorization" in log_data["headers"]:
        log_data["headers"]["authorization"] = "REDACTED"
    
    logger.info(f"REQUEST: {json.dumps(log_data)}")

def log_response(request: Request, response: Response, username: Optional[str] = None, execution_time: Optional[float] = None) -> None:
    """Log a response."""
    client_info = get_client_info(request)
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "response",
        "username": username or "anonymous",
        "client": client_info,
        "status_code": response.status_code,
        "execution_time_ms": execution_time,
    }
    
    logger.info(f"RESPONSE: {json.dumps(log_data)}")

def log_auth_success(username: str, request: Request) -> None:
    """Log a successful authentication."""
    client_info = get_client_info(request)
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "auth_success",
        "username": username,
        "client": client_info,
    }
    
    logger.info(f"AUTH SUCCESS: {json.dumps(log_data)}")

def log_auth_failure(username: str, request: Request, reason: str) -> None:
    """Log a failed authentication attempt."""
    client_info = get_client_info(request)
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "auth_failure",
        "username": username,
        "reason": reason,
        "client": client_info,
    }
    
    logger.warning(f"AUTH FAILURE: {json.dumps(log_data)}")

def log_security_event(event_type: str, details: Dict[str, Any], username: Optional[str] = None, request: Optional[Request] = None) -> None:
    """Log a security event."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "username": username or "system",
        "details": details,
    }
    
    if request:
        log_data["client"] = get_client_info(request)
    
    logger.warning(f"SECURITY EVENT: {json.dumps(log_data)}")

def log_certificate_event(event_type: str, agent_id: str, details: Dict[str, Any], username: Optional[str] = None) -> None:
    """Log a certificate-related event."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": f"certificate_{event_type}",
        "username": username or "system",
        "agent_id": agent_id,
        "details": details,
    }
    
    logger.info(f"CERTIFICATE EVENT: {json.dumps(log_data)}")

def log_rate_limit_exceeded(request: Request) -> None:
    """Log a rate limit exceeded event."""
    client_info = get_client_info(request)
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "rate_limit_exceeded",
        "client": client_info,
    }
    
    logger.warning(f"RATE LIMIT EXCEEDED: {json.dumps(log_data)}")

def log_access_denied(request: Request, username: str, required_permission: str) -> None:
    """Log an access denied event."""
    client_info = get_client_info(request)
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "access_denied",
        "username": username,
        "required_permission": required_permission,
        "client": client_info,
    }
    
    logger.warning(f"ACCESS DENIED: {json.dumps(log_data)}") 
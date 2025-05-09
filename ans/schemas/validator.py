"""
Schema validator for ANS requests and responses.
"""
import os
import json
from typing import Dict, Any, Optional
import jsonschema
from jsonschema import validate
import datetime
from cryptography import x509
from cryptography.x509.name import NameAttribute, Name
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization

SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))

# Load schemas
schemas = {}

def _load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema from file."""
    if schema_name in schemas:
        return schemas[schema_name]
    
    schema_path = os.path.join(SCHEMA_DIR, f"{schema_name}.json")
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    schemas[schema_name] = schema
    return schema

def validate_request(request_type: str, request_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate a request against its schema.
    
    Args:
        request_type: Type of request ('registration', 'renewal', 'capability_query')
        request_data: Request data to validate
        
    Returns:
        Error message if validation fails, None if validation succeeds
    """
    schema_name = f"agent_{request_type}_request_schema"
    try:
        schema = _load_schema(schema_name)
        validate(instance=request_data, schema=schema)
        return None
    except FileNotFoundError:
        return f"Schema not found: {schema_name}"
    except jsonschema.exceptions.ValidationError as e:
        return f"Validation error: {e.message}"

def validate_response(response_type: str, response_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate a response against its schema.
    
    Args:
        response_type: Type of response ('registration_response', 'renewal_response', 'capability_response')
        response_data: Response data to validate
        
    Returns:
        Error message if validation fails, None if validation succeeds
    """
    # Map response type to schema name
    type_to_schema = {
        "registration_response": "agent_registration_response_schema",
        "renewal_response": "agent_renewal_response_schema",
        "capability_response": "agent_capability_response_schema"
    }
    
    schema_name = type_to_schema.get(response_type)
    if not schema_name:
        return f"Unknown response type: {response_type}"
    
    try:
        schema = _load_schema(schema_name)
        validate(instance=response_data, schema=schema)
        return None
    except FileNotFoundError:
        return f"Schema not found: {schema_name}"
    except jsonschema.exceptions.ValidationError as e:
        return f"Validation error: {e.message}"

def create_self_signed_cert(agent_id, private_key):
    """Create a self-signed certificate for testing."""
    # Various details about who this certificate belongs to
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, agent_id),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Organization"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
    ])
    
    now = datetime.datetime.utcnow()
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now
    ).not_valid_after(
        # Certificate is valid for 30 days
        now + datetime.timedelta(days=30)
    ).sign(private_key, hashes.SHA256())
    
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    
    return {
        "certificateSubject": "CN=" + agent_id + ", O=Test Organization, C=US",
        "certificateIssuer": "CN=" + agent_id + ", O=Test Organization, C=US",
        "certificateSerialNumber": str(cert.serial_number),
        "certificateValidFrom": now.isoformat(),
        "certificateValidTo": (now + datetime.timedelta(days=30)).isoformat(),
        "certificatePEM": cert_pem.decode('utf-8'),
        "certificatePublicKeyAlgorithm": "RSA",
        "certificateSignatureAlgorithm": "SHA256withRSA"
    }

# Helper function to ensure datetime objects are converted to ISO format strings
def ensure_iso_format(obj):
    """Convert any datetime objects in a dictionary to ISO format strings."""
    if isinstance(obj, dict):
        return {k: ensure_iso_format(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [ensure_iso_format(item) for item in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        return obj

def create_registration_response(agent_data: Dict[str, Any], certificate: str) -> Dict[str, Any]:
    """
    Create a registration response from agent data.
    
    Args:
        agent_data: Agent data from the registry
        certificate: Certificate issued to the agent
        
    Returns:
        Registration response object
    """
    # Ensure any datetime objects are converted to ISO format strings
    agent_data = ensure_iso_format(agent_data)
    
    response = {
        "responseType": "registration_response",
        "status": "success",
        "registeredAgent": {
            "agentID": agent_data["agent_id"],
            "ansName": agent_data["ans_name"],
            "protocol": agent_data["ans_name"].split("://")[0],
            "capabilities": agent_data["capabilities"],
            "protocolExtensions": agent_data.get("protocol_extensions", {}),
            "endpoint": agent_data["endpoint"],
            "certificate": agent_data["certificate"],
            "registrationTime": agent_data["registration_time"],
            "lastRenewalTime": agent_data.get("last_renewal_time"),
            "isActive": agent_data["is_active"]
        },
        "certificate": certificate
    }
    
    # Validate the response
    error = validate_response("registration_response", response)
    if error:
        raise ValueError(f"Invalid registration response: {error}")
    
    return response

def create_renewal_response(agent_data: Dict[str, Any], new_certificate: str) -> Dict[str, Any]:
    """
    Create a renewal response from agent data.
    
    Args:
        agent_data: Agent data from the registry
        new_certificate: New certificate issued to the agent
        
    Returns:
        Renewal response object
    """
    # Ensure any datetime objects are converted to ISO format strings
    agent_data = ensure_iso_format(agent_data)
    
    response = {
        "responseType": "renewal_response",
        "status": "success",
        "renewedAgent": {
            "agentID": agent_data["agent_id"],
            "ansName": agent_data["ans_name"],
            "renewalTime": agent_data["last_renewal_time"],
            "validUntil": agent_data.get("valid_until", "")
        },
        "newCertificate": new_certificate
    }
    
    # Validate the response
    error = validate_response("renewal_response", response)
    if error:
        raise ValueError(f"Invalid renewal response: {error}")
    
    return response

def create_capability_response(
    matching_agents: list, 
    query_params: Dict[str, Any], 
    result_count: int,
    total_count: int
) -> Dict[str, Any]:
    """
    Create a capability response from matching agents.
    
    Args:
        matching_agents: List of agents matching the query
        query_params: Query parameters used
        result_count: Number of results
        total_count: Total number of agents in the registry
        
    Returns:
        Capability response object
    """
    # Ensure any datetime objects are converted to ISO format strings
    matching_agents = ensure_iso_format(matching_agents)
    
    # Transform agent data to response format
    formatted_agents = []
    for agent in matching_agents:
        formatted_agents.append({
            "agentID": agent["agent_id"],
            "ansName": agent["ans_name"],
            "protocol": agent["ans_name"].split("://")[0],
            "agentCategory": agent["ans_name"].split(".")[1],
            "provider": agent["ans_name"].split(".")[2],
            "version": agent["ans_name"].split("v")[1] if "v" in agent["ans_name"] else "",
            "capabilities": agent["capabilities"],
            "protocolExtensions": agent.get("protocol_extensions", {}),
            "endpoint": agent["endpoint"],
            "certificate": agent["certificate"],
            "isActive": agent["is_active"],
            "lastUpdated": agent.get("last_renewal_time") or agent["registration_time"]
        })
    
    response = {
        "responseType": "capability_response",
        "status": "success",
        "matchingAgents": formatted_agents,
        "queryParameters": query_params,
        "resultCount": result_count,
        "totalCount": total_count
    }
    
    # Validate the response
    error = validate_response("capability_response", response)
    if error:
        raise ValueError(f"Invalid capability response: {error}")
    
    return response

def create_error_response(response_type: str, error_message: str) -> Dict[str, Any]:
    """
    Create an error response.
    
    Args:
        response_type: Type of response
        error_message: Error message
        
    Returns:
        Error response object
    """
    response = {
        "responseType": response_type,
        "status": "failure",
        "error": error_message
    }
    
    # Validate the response if possible (might fail if schema not loaded)
    try:
        validate_response(response_type, response)
    except:
        # Fallback to a generic error response
        pass
    
    return response 
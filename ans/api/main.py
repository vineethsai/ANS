"""
FastAPI application for the Agent Name Service.
"""
from typing import Dict, Any, Optional, List
import time
import datetime
import json
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from .logging import (
    log_request, log_response, log_security_event, log_certificate_event, 
    log_rate_limit_exceeded
)
from ..core.agent import Agent
from ..core.ans_name import ANSName
from ..core.agent_registry import AgentRegistry
from ..core.registration_authority import RegistrationAuthority
from ..crypto.certificate import Certificate
from ..crypto.certificate_authority import CertificateAuthority
from ..db.models import init_db
from ..schemas import (
    validate_request,
    validate_response,
    create_registration_response,
    create_renewal_response,
    create_capability_response,
    create_error_response,
    ensure_iso_format,
    generate_model_from_schema
)

# Custom JSON encoder to handle datetime objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

# Custom JSONResponse class that uses our encoder
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=CustomJSONEncoder,
        ).encode("utf-8")

# Initialize FastAPI app
app = FastAPI(
    title="Agent Name Service",
    description="A universal directory for AI agents",
    version="1.0.0",
    docs_url=None,  # Disable automatic Swagger UI
    redoc_url=None,  # Disable ReDoc
    openapi_url=None,  # Disable OpenAPI JSON generation
    default_response_class=CustomJSONResponse
)

# Simple HTML documentation for the API
API_DOC_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ANS API Documentation</title>
    <style>
        body { font-family: sans-serif; margin: 20px; line-height: 1.5; }
        h1, h2 { color: #333; }
        h2 { margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .endpoint { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .method { font-weight: bold; color: #e91e63; }
        .path { font-family: monospace; color: #333; }
        .description { margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Agent Name Service API</h1>
    <p>A universal directory for AI agents</p>
    
    <h2>Registration Endpoints</h2>
    
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/register</span></div>
        <div class="description">Register a new agent in the ANS, providing certificate information, endpoints, capabilities, etc.</div>
    </div>
    
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/renew</span></div>
        <div class="description">Renew an agent's registration by providing a new CSR</div>
    </div>
    
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/revoke</span></div>
        <div class="description">Revoke an agent's registration, optionally providing a reason</div>
    </div>
    
    <h2>Resolution Endpoints</h2>
    
    <div class="endpoint">
        <div><span class="method">POST</span> <span class="path">/resolve</span></div>
        <div class="description">Resolve an agent's ANS name to its endpoint record</div>
    </div>
    
    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/agents</span></div>
        <div class="description">Find agents matching criteria such as protocol, capability, or provider</div>
    </div>
    
    <h2>System Endpoints</h2>
    
    <div class="endpoint">
        <div><span class="method">GET</span> <span class="path">/health</span></div>
        <div class="description">Check the health of the ANS service</div>
    </div>
    
    <p><em>Note: The automatic API documentation (Swagger/ReDoc) is currently disabled. Please refer to the README or contact the administrator for detailed API specifications.</em></p>
</body>
</html>
"""

@app.get("/docs", response_class=HTMLResponse)
async def custom_docs():
    """Serve a simple HTML API documentation page."""
    return API_DOC_HTML

# Rate limiting configuration
RATE_LIMIT = {
    "/register": {"calls": 10, "period": 60},    # 10 registrations per minute
    "/resolve": {"calls": 60, "period": 60},     # 60 resolutions per minute
    "/agents": {"calls": 30, "period": 60},      # 30 list calls per minute
    "default": {"calls": 100, "period": 60}      # 100 calls per minute for other endpoints
}

# Dictionary to store client request data for rate limiting
client_requests = {}

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Get client IP address
    client_ip = request.client.host
    path = request.url.path
    current_time = time.time()
    
    # Determine which rate limit applies
    if path in RATE_LIMIT:
        limit_config = RATE_LIMIT[path]
    else:
        limit_config = RATE_LIMIT["default"]
    
    # Initialize client request tracking if needed
    if client_ip not in client_requests:
        client_requests[client_ip] = {}
    
    if path not in client_requests[client_ip]:
        client_requests[client_ip][path] = []
    
    # Clean old requests
    client_requests[client_ip][path] = [
        timestamp for timestamp in client_requests[client_ip][path]
        if current_time - timestamp < limit_config["period"]
    ]
    
    # Check if rate limit exceeded
    if len(client_requests[client_ip][path]) >= limit_config["calls"]:
        log_rate_limit_exceeded(request)
        return Response(
            content="Rate limit exceeded. Please try again later.",
            status_code=429
        )
    
    # Record this request
    client_requests[client_ip][path].append(current_time)
    
    # Log the request
    log_request(request)
    
    # Process the request
    start_time = time.time()
    response = await call_next(request)
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Log the response
    log_response(request, response, execution_time=execution_time)
    
    return response

# Add CORS middleware with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],  # Allow all origins and our frontend dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Include OPTIONS for CORS preflight
    allow_headers=["Content-Type", "Authorization"],  # Include Authorization for future use
)

# Initialize database
SessionLocal = init_db()

# Generate Pydantic models from JSON schemas
# This avoids manual model definition and keeps models in sync with schemas
try:
    # Generate models from JSON schemas
    RegistrationRequest = generate_model_from_schema("agent_registration_request_schema", "RegistrationRequest")
    RenewalRequest = generate_model_from_schema("agent_renewal_request_schema", "RenewalRequest")
except Exception as e:
    # Fallback to manual models if generation fails
    print(f"Error generating models from schemas: {e}")
    print("Falling back to manual model definitions")
    
    # Pydantic models for request/response validation - these are fallbacks
    class CertificateSchema(BaseModel):
        certificateSubject: str
        certificateIssuer: str
        certificateSerialNumber: str
        certificateValidFrom: datetime.datetime
        certificateValidTo: datetime.datetime
        certificatePEM: str
        certificatePublicKeyAlgorithm: str
        certificateSignatureAlgorithm: str

    class RequestingAgent(BaseModel):
        protocol: str
        agentName: str
        agentCategory: str
        providerName: str
        version: str
        extension: Optional[str] = None
        agentUseJustification: str
        agentCapability: str
        agentEndpoint: str
        agentDID: str
        certificate: CertificateSchema
        csrPEM: str
        agentDNSName: str

    class RegistrationRequest(BaseModel):
        requestType: str = Field(..., pattern="^registration$")
        requestingAgent: RequestingAgent
        
    class CertificateInfoModel(BaseModel):
        certificateSerialNumber: str
        certificatePEM: str

    class RequestingAgentModel(BaseModel):
        agentID: str
        ansName: str
        protocol: str
        csrPEM: str
        currentCertificate: CertificateInfoModel

    class RenewalRequest(BaseModel):
        requestType: str = Field(..., pattern="^renewal$")
        requestingAgent: RequestingAgentModel

# These models aren't yet in JSON schemas, so we keep them manually defined
class RevocationRequest(BaseModel):
    agent_id: str
    reason: Optional[str] = None

class ResolutionRequest(BaseModel):
    ans_name: str
    version_range: Optional[str] = None

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize CA and RA
ca_cert, ca_private_key = Certificate.generate_self_signed_cert("ANS CA")
ca = CertificateAuthority(ca_cert, ca_private_key)
ra = RegistrationAuthority(ca)

# Initialize registry
registry = None

def get_registry(db: Session = Depends(get_db)) -> AgentRegistry:
    global registry
    if registry is None:
        registry = AgentRegistry(ca, db)
        registry.initialize_registry("Main Registry")
    return registry

@app.post("/register", tags=["registration"], summary="Register a new agent", 
         description="Register a new agent in the ANS, providing certificate information, endpoints, capabilities, etc.")
async def register_agent(
    request: Request,
    registration_request: RegistrationRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """
    Register a new agent.
    
    The request format follows the JSON schema defined in `agent_registration_request_schema.json`.
    
    Returns a registration response with agent information and certificate if successful,
    or an error response if the registration fails.
    """
    try:
        # Extract data from the request format
        # The structure may vary slightly depending on whether we're using generated models or fallbacks
        agent_info = registration_request.requestingAgent
        
        # Convert to dictionary for validation
        if hasattr(agent_info, "dict"):
            # Generated model has dict() method
            agent_info_dict = agent_info.dict()
        else:
            # Fallback model has __dict__ attribute
            agent_info_dict = agent_info.__dict__
        
        # Create a compatible format for the registration authority
        # Field names are adjusted based on the actual schema used
        ra_request = {
            "agent_id": agent_info_dict.get("agentName", agent_info_dict.get("agent_name", "")),
            "ans_name": f"{agent_info_dict.get('protocol')}://{agent_info_dict.get('agentName', agent_info_dict.get('agent_name', ''))}.{agent_info_dict.get('agentCapability', agent_info_dict.get('agent_capability', ''))}.{agent_info_dict.get('providerName', agent_info_dict.get('provider_name', ''))}.v{agent_info_dict.get('version', '')}",
            "capabilities": [agent_info_dict.get("agentCapability", agent_info_dict.get("agent_capability", ""))],
            "protocol_extensions": {
                "endpoint": agent_info_dict.get("agentEndpoint", agent_info_dict.get("agent_endpoint", "")),
                "did": agent_info_dict.get("agentDID", agent_info_dict.get("agent_did", "")),
                "use_justification": agent_info_dict.get("agentUseJustification", agent_info_dict.get("agent_use_justification", "")),
                "dns_name": agent_info_dict.get("agentDNSName", agent_info_dict.get("agent_dns_name", ""))
            },
            "endpoint": agent_info_dict.get("agentEndpoint", agent_info_dict.get("agent_endpoint", "")),
            "csr": agent_info_dict.get("csrPEM", agent_info_dict.get("csr_pem", ""))
        }
        
        # Validate the request against the schema
        request_data = {}
        if hasattr(registration_request, "dict"):
            request_data = registration_request.dict()
        else:
            request_data = {
                "requestType": "registration",
                "requestingAgent": agent_info_dict
            }
        
        # Ensure all datetime objects are strings before validation
        request_data = ensure_iso_format(request_data)
        
        error = validate_request("registration", request_data)
        
        if error:
            log_security_event(
                "schema_validation_error", 
                {"agent_id": ra_request["agent_id"], "error": error}, 
                "public_api", 
                request
            )
            return create_error_response("registration_response", error)
        
        response = ra.process_registration_request(ra_request)
        
        # Ensure all datetime objects are converted to ISO strings
        response = ensure_iso_format(response)
        
        # Create Agent object from the response
        agent = Agent.from_dict(response["agent"])
        
        # Register agent in the registry
        registry.register_agent(agent)
        
        # Log the certificate issuance
        log_certificate_event(
            "issued", 
            agent.agent_id, 
            {"ans_name": str(agent.ans_name)}, 
            "public_api"
        )
        
        # Create a standardized response
        return create_registration_response(response["agent"], response["certificate"])
        
    except ValueError as e:
        agent_id = ""
        try:
            agent_id = registration_request.requestingAgent.agentName
        except:
            try:
                agent_id = registration_request.requestingAgent.agent_name
            except:
                pass
                
        log_security_event(
            "registration_error", 
            {"agent_id": agent_id, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("registration_response", str(e))
    except Exception as e:
        agent_id = ""
        try:
            agent_id = registration_request.requestingAgent.agentName
        except:
            try:
                agent_id = registration_request.requestingAgent.agent_name
            except:
                pass
                
        log_security_event(
            "unexpected_error", 
            {"agent_id": agent_id, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("registration_response", f"Unexpected error: {e}")

@app.post("/renew", tags=["registration"], summary="Renew an agent's registration", 
         description="Renew an agent's registration by providing a new CSR")
async def renew_agent(
    request: Request,
    renewal_request: RenewalRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """
    Renew an agent's registration.
    
    The request format follows the JSON schema defined in `agent_renewal_request_schema.json`.
    
    Returns a renewal response with the new certificate if successful,
    or an error response if the renewal fails.
    """
    try:
        # Extract data from the request
        request_dict = {}
        
        # Convert to dictionary for validation
        if hasattr(renewal_request, "dict"):
            # Generated model has dict() method
            request_dict = renewal_request.dict()
            req_agent = renewal_request.requestingAgent
            agent_id = req_agent.agentID if hasattr(req_agent, "agentID") else req_agent.agent_id
            csr = req_agent.csrPEM if hasattr(req_agent, "csrPEM") else req_agent.csr_pem
        else:
            # Fallback model
            request_dict = {
                "requestType": "renewal",
                "requestingAgent": renewal_request.requestingAgent.__dict__
            }
            agent_id = renewal_request.requestingAgent.agentID
            csr = renewal_request.requestingAgent.csrPEM
            
        # Ensure all datetime objects are strings before validation
        request_dict = ensure_iso_format(request_dict)
        
        # Validate the request against the schema
        error = validate_request("renewal", request_dict)
        
        if error:
            log_security_event(
                "schema_validation_error", 
                {"agent_id": agent_id, "error": error}, 
                "public_api", 
                request
            )
            return create_error_response("renewal_response", error)
        
        # Issue new certificate
        ra_response = ra.process_renewal_request(agent_id, csr)
        
        # Update agent in registry
        agent = registry.renew_agent(agent_id)
        
        # Get certificate data for setting valid_until
        cert_data = Certificate(ra_response["certificate"].encode())
        
        # CryptographyDeprecationWarning: Properties that return a naïve datetime object have been deprecated.
        # Switch to not_valid_after_utc when updating dependencies
        valid_until = cert_data.cert.not_valid_after
        
        # Log certificate renewal
        log_certificate_event(
            "renewed", 
            agent_id, 
            {"valid_until": valid_until.isoformat()}, 
            "public_api"
        )
        
        # Add valid_until to agent data for renewal response
        agent_dict = agent.to_dict()
        agent_dict["valid_until"] = valid_until.isoformat()
        
        # Create standardized response
        return create_renewal_response(agent_dict, ra_response["certificate"])
        
    except ValueError as e:
        agent_id = ""
        try:
            if hasattr(renewal_request.requestingAgent, "agentID"):
                agent_id = renewal_request.requestingAgent.agentID
            else:
                agent_id = renewal_request.requestingAgent.agent_id
        except:
            pass
            
        log_security_event(
            "renewal_error", 
            {"agent_id": agent_id, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("renewal_response", str(e))
    except Exception as e:
        agent_id = ""
        try:
            if hasattr(renewal_request.requestingAgent, "agentID"):
                agent_id = renewal_request.requestingAgent.agentID
            else:
                agent_id = renewal_request.requestingAgent.agent_id
        except:
            pass
            
        log_security_event(
            "unexpected_error", 
            {"agent_id": agent_id, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("renewal_response", f"Unexpected error: {e}")

@app.post("/revoke", tags=["registration"], summary="Revoke an agent's registration", 
         description="Revoke an agent's registration, optionally providing a reason")
async def revoke_agent(
    request: Request,
    revocation_request: RevocationRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """
    Revoke an agent's registration.
    
    Returns a success response if the revocation is successful,
    or an error response if the revocation fails.
    """
    try:
        agent_id = revocation_request.agent_id
        reason = revocation_request.reason
        
        # Deactivate agent in registry
        registry.deactivate_agent(agent_id)
        
        # TODO: Add certificate revocation
        
        # Log revocation
        log_certificate_event(
            "revoked", 
            agent_id, 
            {"reason": reason or "No reason provided"}, 
            "public_api"
        )
        
        return {
            "status": "success",
            "message": f"Agent {agent_id} registration revoked"
        }
        
    except ValueError as e:
        log_security_event(
            "revocation_error", 
            {"agent_id": revocation_request.agent_id, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("revocation_response", str(e))
    except Exception as e:
        log_security_event(
            "unexpected_error", 
            {"agent_id": revocation_request.agent_id, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("revocation_response", f"Unexpected error: {e}")

@app.post("/resolve", tags=["resolution"], summary="Resolve an agent's ANS name", 
         description="Resolve an agent's ANS name to its endpoint record")
async def resolve_agent(
    request: Request,
    resolution_request: ResolutionRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """
    Resolve an agent's ANS name.
    
    Returns the endpoint record if the resolution is successful,
    or an error response if the resolution fails.
    """
    try:
        ans_name = resolution_request.ans_name
        version_range = resolution_request.version_range
        
        # Resolve ANS name in registry
        endpoint_record = registry.resolve_ans_name(ans_name, version_range)
        
        # Log resolution
        log_security_event(
            "name_resolution", 
            {"ans_name": ans_name, "version_range": version_range}, 
            "public_api", 
            request
        )
        
        return endpoint_record
        
    except ValueError as e:
        log_security_event(
            "resolution_error", 
            {"ans_name": resolution_request.ans_name, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("resolution_response", str(e))
    except Exception as e:
        log_security_event(
            "unexpected_error", 
            {"ans_name": resolution_request.ans_name, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("resolution_response", f"Unexpected error: {e}")

@app.get("/agents", tags=["resolution"], summary="Find agents matching criteria", 
        description="Find agents matching criteria such as protocol, capability, or provider")
async def list_agents(
    request: Request,
    protocol: Optional[str] = None,
    capability: Optional[str] = None,
    provider: Optional[str] = None,
    registry: AgentRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """
    Find agents matching criteria.
    
    Returns a list of matching agents,
    or an error response if the search fails.
    """
    try:
        # Find agents in registry
        agents = registry.find_agents_by_criteria(protocol, capability, provider)
        
        # Log agent listing
        log_security_event(
            "list_agents", 
            {"protocol": protocol, "capability": capability, "provider": provider, "count": len(agents)}, 
            "public_api", 
            request
        )
        
        return {
            "status": "success",
            "agents": agents
        }
        
    except Exception as e:
        log_security_event(
            "unexpected_error", 
            {"error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("agent_list_response", f"Unexpected error: {e}")

@app.get("/health", tags=["system"], summary="Health check", 
        description="Check the health of the ANS service")
async def health_check() -> Dict[str, str]:
    """
    Check the health of the ANS service.
    """
    return {
        "status": "ok",
        "version": "1.0.0"
    } 
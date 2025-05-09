"""
FastAPI application for the Agent Name Service.
"""
from typing import Dict, Any, Optional, List
import time
import datetime
import json
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    ensure_iso_format
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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "registration",
            "description": "API endpoints for agent registration, renewal, and revocation"
        },
        {
            "name": "resolution",
            "description": "API endpoints for resolving agent names and finding agents"
        },
        {
            "name": "system",
            "description": "System health and status endpoints"
        }
    ],
    default_response_class=CustomJSONResponse
)

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

# Pydantic models for request/response validation
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
        # Extract data from the new request format
        agent_info = registration_request.requestingAgent
        
        # Create a compatible format for the registration authority
        ra_request = {
            "agent_id": agent_info.agentName,
            "ans_name": f"{agent_info.protocol}://{agent_info.agentName}.{agent_info.agentCapability}.{agent_info.providerName}.v{agent_info.version}",
            "capabilities": [agent_info.agentCapability],
            "protocol_extensions": {
                "endpoint": agent_info.agentEndpoint,
                "did": agent_info.agentDID,
                "use_justification": agent_info.agentUseJustification,
                "dns_name": agent_info.agentDNSName
            },
            "endpoint": agent_info.agentEndpoint,
            "csr": agent_info.csrPEM
        }
        
        # Validate the request against the schema
        request_data = {
            "requestType": "registration",
            "requestingAgent": registration_request.requestingAgent.dict()
        }
        
        # Ensure all datetime objects are strings before validation
        request_data = ensure_iso_format(request_data)
        
        error = validate_request("registration", request_data)
        
        if error:
            log_security_event(
                "schema_validation_error", 
                {"agent_id": agent_info.agentName, "error": error}, 
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
        log_security_event(
            "registration_error", 
            {"agent_id": registration_request.requestingAgent.agentName, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("registration_response", str(e))
    except Exception as e:
        log_security_event(
            "unexpected_error", 
            {"agent_id": registration_request.requestingAgent.agentName, "error": str(e)}, 
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
    
    Uses the format defined in `agent_renewal_request_schema.json`.
    
    Returns a renewal response with updated certificate information if successful,
    or an error response if the renewal fails.
    """
    try:
        # Extract required information from the request
        agent_id = renewal_request.requestingAgent.agentID
        csr = renewal_request.requestingAgent.csrPEM
        
        # Process the renewal request
        response = ra.process_renewal_request(agent_id, csr)
        agent = registry.renew_agent(agent_id)
        
        # Get the certificate's details to extract validity information
        cert_data = Certificate(response["certificate"].encode())
        valid_until = cert_data.cert.not_valid_after
        
        # Log the certificate renewal
        log_certificate_event(
            "renewed", 
            agent_id, 
            {"valid_until": valid_until.isoformat()}, 
            "public_api"
        )
        
        # Create a standardized response
        agent_data = agent.to_dict()
        agent_data["last_renewal_time"] = datetime.datetime.now().isoformat()
        agent_data["valid_until"] = valid_until.isoformat()
        
        return create_renewal_response(agent_data, response["certificate"])
    except ValueError as e:
        log_security_event(
            "renewal_error", 
            {"agent_id": renewal_request.requestingAgent.agentID, "error": str(e)}, 
            "public_api", 
            request
        )
        return create_error_response("renewal_response", str(e))
    except Exception as e:
        log_security_event(
            "unexpected_error", 
            {"agent_id": renewal_request.requestingAgent.agentID, "error": str(e)}, 
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
    
    Returns a response indicating whether the revocation was successful,
    or an error response if the revocation fails.
    """
    try:
        response = ra.process_revocation_request(revocation_request.agent_id, revocation_request.reason)
        registry.deactivate_agent(revocation_request.agent_id)
        
        # Log the certificate revocation
        log_certificate_event(
            "revoked", 
            revocation_request.agent_id, 
            {"reason": revocation_request.reason or "No reason provided"}, 
            "public_api"
        )
        
        return response
    except ValueError as e:
        log_security_event(
            "revocation_error", 
            {"agent_id": revocation_request.agent_id, "error": str(e)}, 
            "public_api", 
            request
        )
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/resolve", tags=["resolution"], summary="Resolve an agent's ANS name", 
         description="Resolve an agent's ANS name to its endpoint record")
async def resolve_agent(
    request: Request,
    resolution_request: ResolutionRequest,
    registry: AgentRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    """
    Resolve an agent's ANS name to its endpoint record.
    
    Returns the endpoint record with signature if successful,
    or an error response if the resolution fails.
    """
    try:
        result = registry.resolve_ans_name(resolution_request.ans_name, resolution_request.version_range)
        
        # Log successful resolution
        log_security_event(
            "resolve_success", 
            {"ans_name": resolution_request.ans_name}, 
            "public_api", 
            request
        )
        
        return result
    except ValueError as e:
        log_security_event(
            "resolve_error", 
            {"ans_name": resolution_request.ans_name, "error": str(e)}, 
            "public_api", 
            request
        )
        raise HTTPException(status_code=400, detail=str(e))

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
    List agents matching the given criteria.
    
    Returns a capability response with matching agents if successful,
    or an error response if the query fails.
    
    The response format follows the JSON schema defined in `agent_capability_response_schema.json`.
    """
    try:
        agents = registry.find_agents_by_criteria(protocol, capability, provider)
        
        # Log successful agent listing
        log_security_event(
            "list_agents", 
            {
                "protocol": protocol,
                "capability": capability,
                "provider": provider,
                "count": len(agents)
            }, 
            "public_api", 
            request
        )
        
        # Create a standardized response
        query_params = {
            "protocol": protocol or "*",
            "capability": capability or "*",
            "provider": provider or "*"
        }
        
        # Get the total count of all agents
        all_agents = registry.find_agents_by_criteria(None, None, None)
        
        return create_capability_response(agents, query_params, len(agents), len(all_agents))
    except ValueError as e:
        log_security_event(
            "list_agents_error", 
            {
                "protocol": protocol,
                "capability": capability,
                "provider": provider,
                "error": str(e)
            }, 
            "public_api", 
            request
        )
        return create_error_response("capability_response", str(e))

@app.get("/health", tags=["system"], summary="Health check", 
        description="Check the health of the ANS service")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns a simple status response indicating the service is healthy.
    """
    return {"status": "healthy"} 
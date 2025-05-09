"""
Client for registering and accessing MCP-protocol agents with the Agent Name Service.

This example demonstrates working with agents that implement
Anthropic's Model Context Protocol (MCP).
"""
import sys
import os
import json
import requests
import datetime
from typing import Dict, Any, List, Optional
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

# Add the parent directory to the Python path so we can import ANS modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ans.schemas.validator import ensure_iso_format

# ANS server URL
ANS_URL = "http://localhost:8000"

def generate_key_pair():
    """Generate an RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    return private_key, private_pem

def create_csr(agent_id, private_key):
    """Create a Certificate Signing Request."""
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, agent_id)
        ])
    ).sign(private_key, hashes.SHA256())
    
    csr_pem = csr.public_bytes(serialization.Encoding.PEM)
    return csr_pem

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
    
    cert_info = {
        "certificateSubject": "CN=" + agent_id + ", O=Test Organization, C=US",
        "certificateIssuer": "CN=" + agent_id + ", O=Test Organization, C=US",
        "certificateSerialNumber": str(cert.serial_number),
        "certificateValidFrom": now.strftime("%Y-%m-%dT%H:%M:%SZ"),  # Format for JSON Schema date-time
        "certificateValidTo": (now + datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # Format for JSON Schema date-time
        "certificatePEM": cert_pem.decode('utf-8'),
        "certificatePublicKeyAlgorithm": "RSA",
        "certificateSignatureAlgorithm": "SHA256withRSA"
    }
    
    # Ensure all datetime objects are converted to ISO format strings
    return ensure_iso_format(cert_info)

def register_agent(agent_name, agent_category, provider_name, version, capabilities, context_types, endpoint):
    """Register an MCP agent with the ANS."""
    private_key, private_pem = generate_key_pair()
    csr_pem = create_csr(agent_name, private_key)
    
    # Generate a random DID for this example
    agent_did = f"did:example:{agent_name}"
    
    # Create the DNS-like name
    agent_dns_name = f"{agent_name}.{agent_category}.{provider_name}.ans"
    
    # Generate a self-signed certificate for testing
    cert_info = create_self_signed_cert(agent_name, private_key)
    
    # Create protocol extensions for MCP
    protocol_extensions = {
        "schema_version": "1.0",
        "context_specifications": [
            {
                "context_type": context_type,
                "version": "1.0.0",
                "description": f"{context_type.capitalize()} context for model reasoning",
                "schema": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": f"{context_type.capitalize()} content"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["text", "markdown", "html", "pdf"],
                            "default": "text",
                            "description": f"{context_type.capitalize()} format"
                        }
                    }
                },
                "max_tokens": 100000
            }
            for context_type in context_types
        ],
        "document_types": ["text", "markdown", "html", "pdf"],
        "token_limit": 100000,
        "metadata": {
            "provider": provider_name,
            "description": "Model Context Protocol implementation"
        }
    }
    
    # Create the main capability
    primary_capability = capabilities[0] if capabilities else "context-handling"
    
    request_data = {
        "requestType": "registration",
        "requestingAgent": {
            "protocol": "mcp",
            "agentName": agent_name,
            "agentCategory": agent_category,
            "providerName": provider_name,
            "version": version,
            "extension": "agent",
            "agentUseJustification": f"Providing {primary_capability} capabilities with MCP",
            "agentCapability": primary_capability,
            "agentEndpoint": endpoint,
            "agentDID": agent_did,
            "certificate": cert_info,
            "csrPEM": csr_pem.decode('utf-8'),
            "agentDNSName": agent_dns_name
        }
    }
    
    response = requests.post(
        f"{ANS_URL}/register",
        json=request_data
    )
    
    if response.status_code != 200:
        print(f"Registration failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json(), private_pem, protocol_extensions

def resolve_agent(ans_name, version_range=None):
    """Resolve an agent's ANS name to its endpoint record."""
    request_data = {
        "ans_name": ans_name,
        "version_range": version_range
    }
    
    response = requests.post(
        f"{ANS_URL}/resolve",
        json=request_data
    )
    
    if response.status_code != 200:
        print(f"Resolution failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

def find_mcp_agents(capability=None, provider=None):
    """Find MCP agents matching criteria."""
    params = {"protocol": "mcp"}
    if capability:
        params["capability"] = capability
    if provider:
        params["provider"] = provider
    
    response = requests.get(
        f"{ANS_URL}/agents",
        params=params
    )
    
    if response.status_code != 200:
        print(f"Query failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

def simulate_mcp_client(endpoint_record):
    """
    Simulate an MCP client using the agent's endpoint.
    
    In this example, we just extract and display the context specifications
    that the agent supports from its protocol extensions.
    """
    try:
        agent_data = endpoint_record.get("data", {})
        extensions = agent_data.get("protocol_extensions", {})
        
        print("\nAgent MCP specifications:")
        print(f"Schema version: {extensions.get('schema_version')}")
        
        context_specs = extensions.get("context_specifications", [])
        print(f"Supported context types ({len(context_specs)}):")
        
        for spec in context_specs:
            print(f"- {spec.get('context_type')} (v{spec.get('version')})")
            print(f"  Description: {spec.get('description')}")
            print(f"  Max tokens: {spec.get('max_tokens')}")
        
        print(f"Document types: {extensions.get('document_types')}")
        print(f"Token limit: {extensions.get('token_limit')}")
        
        return True
    except Exception as e:
        print(f"Error processing MCP specifications: {e}")
        return False

def main():
    """Example usage of the MCP client."""
    # Register an MCP-compatible agent
    print("Registering MCP agent...")
    agent_name = "claude-model-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # unique name
    result, private_key, protocol_extensions = register_agent(
        agent_name=agent_name,
        agent_category="context-handling",
        provider_name="anthropic",
        version="1.0.0",
        capabilities=["document", "system_prompt"],
        context_types=["document", "system_prompt"],
        endpoint="https://claude-model.anthropic.com/api"
    )
    
    if not result:
        print("Failed to register MCP agent")
        return
    
    print("Registration successful!")
    if result.get("status") == "success":
        agent_info = result.get("registeredAgent", {})
        agent_id = agent_info.get("agentID")
        ans_name = agent_info.get("ansName")
        print(f"Agent ID: {agent_id}")
        print(f"ANS Name: {ans_name}")
    else:
        print(f"Registration error: {result.get('error')}")
        return
    
    # Resolve the agent
    print("\nResolving MCP agent...")
    endpoint_record = resolve_agent(ans_name)
    
    if not endpoint_record:
        print("Failed to resolve MCP agent")
        return
    
    print("Resolution successful!")
    endpoint = endpoint_record.get("data", {}).get("endpoint")
    print(f"Agent endpoint: {endpoint}")
    
    # Simulate an MCP client using the resolved endpoint
    print("\nSimulating MCP client...")
    simulate_mcp_client(endpoint_record)
    
    # Find MCP agents
    print("\nFinding all MCP agents...")
    agents = find_mcp_agents()
    
    if not agents:
        print("Failed to find MCP agents")
        return
    
    print("Query successful!")
    matching_agents = agents.get("matchingAgents", [])
    print(f"Found {len(matching_agents)} MCP agents")
    for agent in matching_agents:
        print(f"- {agent.get('ansName')}: {agent.get('capabilities')}")

if __name__ == "__main__":
    main() 
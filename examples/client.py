"""
Client for interacting with the Agent Name Service.
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

def register_agent(agent_name, agent_category, provider_name, version, capability, endpoint, protocol="a2a"):
    """Register an agent with the ANS."""
    private_key, private_pem = generate_key_pair()
    csr_pem = create_csr(agent_name, private_key)
    
    # Generate a random DID for this example
    agent_did = f"did:example:{agent_name}"
    
    # Create the DNS-like name
    agent_dns_name = f"{agent_name}.{agent_category}.{provider_name}.ans"
    
    # Generate a self-signed certificate for testing
    cert_info = create_self_signed_cert(agent_name, private_key)
    
    request_data = {
        "requestType": "registration",
        "requestingAgent": {
            "protocol": protocol,
            "agentName": agent_name,
            "agentCategory": agent_category,
            "providerName": provider_name,
            "version": version,
            "extension": "agent",
            "agentUseJustification": f"Providing {capability} capabilities",
            "agentCapability": capability,
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
    
    return response.json(), private_pem

def renew_agent(agent_id, ans_name, protocol, private_pem):
    """Renew an agent's registration."""
    private_key = serialization.load_pem_private_key(
        private_pem,
        password=None
    )
    
    csr_pem = create_csr(agent_id, private_key)
    
    # Create certificate info for the current certificate
    cert_info = create_self_signed_cert(agent_id, private_key)
    
    request_data = {
        "requestType": "renewal",
        "requestingAgent": {
            "agentID": agent_id,
            "ansName": ans_name,
            "protocol": protocol,
            "csrPEM": csr_pem.decode('utf-8'),
            "currentCertificate": {
                "certificateSerialNumber": cert_info["certificateSerialNumber"],
                "certificatePEM": cert_info["certificatePEM"]
            }
        }
    }
    
    response = requests.post(
        f"{ANS_URL}/renew",
        json=request_data
    )
    
    if response.status_code != 200:
        print(f"Renewal failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

def revoke_agent(agent_id, reason=None):
    """Revoke an agent's registration."""
    request_data = {
        "agent_id": agent_id,
        "reason": reason
    }
    
    response = requests.post(
        f"{ANS_URL}/revoke",
        json=request_data
    )
    
    if response.status_code != 200:
        print(f"Revocation failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

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

def find_agents(protocol=None, capability=None, provider=None):
    """Find agents matching criteria."""
    params = {}
    if protocol:
        params["protocol"] = protocol
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

def verify_endpoint_record(endpoint_record):
    """
    Verify the signature on an endpoint record.
    
    In a real implementation, this would verify the signature using
    the registry's public key. For this example, we just return True.
    """
    return True

def main():
    """Example usage of the client."""
    # Register an agent
    print("Registering agent...")
    agent_name = "example-agent-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # unique name
    result, private_key = register_agent(
        agent_name=agent_name,
        agent_category="chat",
        provider_name="example",
        version="1.0.0",
        capability="conversation",
        endpoint="https://example.com/agent"
    )
    
    if result:
        print("Registration successful!")
        if result.get("status") == "success":
            agent_info = result.get("registeredAgent", {})
            agent_id = agent_info.get("agentID")
            ans_name = agent_info.get("ansName")
            print(f"Agent ID: {agent_id}")
            print(f"ANS Name: {ans_name}")
            
            # Resolve the agent
            print("\nResolving agent...")
            endpoint_record = resolve_agent(ans_name)
            
            if endpoint_record and verify_endpoint_record(endpoint_record):
                print("Resolution successful!")
                endpoint = endpoint_record.get("data", {}).get("endpoint")
                print(f"Agent endpoint: {endpoint}")
            
            # Find agents with the same protocol
            print("\nFinding agents with protocol 'a2a'...")
            agents = find_agents(protocol="a2a")
            
            if agents:
                print("Query successful!")
                matching_agents = agents.get("matchingAgents", [])
                print(f"Found {len(matching_agents)} agents")
                for agent in matching_agents[:3]:  # Show at most 3 for brevity
                    print(f"- {agent.get('ansName')}: {agent.get('capabilities')}")
            
            # Renew the agent's registration
            print("\nRenewing agent registration...")
            renewal_result = renew_agent(agent_id, ans_name, "a2a", private_key)
            
            if renewal_result:
                print("Renewal successful!")
                if renewal_result.get("status") == "success":
                    renewed_agent = renewal_result.get("renewedAgent", {})
                    print(f"Renewal time: {renewed_agent.get('renewalTime')}")
                else:
                    print(f"Renewal error: {renewal_result.get('error')}")
            
            # Revoke the agent's registration
            print("\nRevoking agent registration...")
            revocation_result = revoke_agent(agent_id, "Testing revocation")
            
            if revocation_result:
                print("Revocation successful!")
        else:
            print(f"Registration error: {result.get('error')}")
    else:
        print("Registration failed!")

if __name__ == "__main__":
    main() 
"""
Test script for the updated Agent Name Service with the new schema.

This script tests the registration endpoint using the new schema format.
"""
import json
import requests
import datetime
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

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
    
    return private_pem

def create_csr(agent_id, private_key_pem):
    """Create a Certificate Signing Request."""
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None
    )
    
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, agent_id)
        ])
    ).sign(private_key, hashes.SHA256())
    
    return csr.public_bytes(serialization.Encoding.PEM)

def create_self_signed_cert(agent_id, private_key_pem):
    """Create a self-signed certificate for testing."""
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None
    )
    
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

def test_register_agent():
    """Test registering an agent with the new schema."""
    # Agent information
    agent_name = "test-agent-new-schema"
    agent_category = "conversation"
    provider_name = "anthropic"
    version = "1.0.0"
    capability = "chat"
    protocol = "mcp"
    endpoint = "https://test-agent.example.com/api"
    
    # Generate key pair and CSR
    print("Generating key pair and CSR...")
    private_key = generate_key_pair()
    csr = create_csr(agent_name, private_key)
    
    # Create the request data
    agent_did = f"did:example:{agent_name}"
    agent_dns_name = f"{agent_name}.{agent_category}.{provider_name}.ans"
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
            "agentUseJustification": f"Providing {capability} capabilities for testing",
            "agentCapability": capability,
            "agentEndpoint": endpoint,
            "agentDID": agent_did,
            "certificate": cert_info,
            "csrPEM": csr.decode('utf-8'),
            "agentDNSName": agent_dns_name
        }
    }
    
    print(f"Sending registration request for agent: {agent_name}")
    
    response = requests.post(
        f"{ANS_URL}/register",
        json=request_data
    )
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Registration successful!")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"Registration failed: {response.text}")
        return False

def test_resolve_agent():
    """Test resolving an agent."""
    ans_name = "mcp://test-agent-new-schema.chat.anthropic.v1.0.0"
    
    request_data = {
        "ans_name": ans_name,
        "version_range": None
    }
    
    response = requests.post(
        f"{ANS_URL}/resolve",
        json=request_data
    )
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Resolution successful!")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"Resolution failed: {response.text}")
        return False

def test_filter_agents():
    """Test filtering agents by protocol."""
    response = requests.get(f"{ANS_URL}/agents?protocol=mcp")
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        agents = response.json()["agents"]
        print(f"Found {len(agents)} MCP agents")
        print(json.dumps(agents, indent=2))
        return True
    else:
        print(f"Filtering failed: {response.text}")
        return False

def main():
    """Run all tests."""
    print("Testing agent registration with new schema")
    print("=========================================")
    registration_success = test_register_agent()
    
    if registration_success:
        print("\nTesting agent resolution")
        print("======================")
        test_resolve_agent()
        
        print("\nTesting agent filtering")
        print("=====================")
        test_filter_agents()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 
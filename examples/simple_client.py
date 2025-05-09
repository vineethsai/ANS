"""
Simple client for the Agent Name Service.

This is a minimal example focused only on the core registration functionality.
"""
import sys
import os
import json
import requests
import datetime
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

# Add the parent directory to the Python path so we can import ANS modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ans.schemas.validator import create_self_signed_cert, ensure_iso_format

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

def register_agent(agent_name, agent_category, provider_name, version, capability, endpoint, protocol="a2a"):
    """Register an agent with the ANS using the new schema."""
    # Generate a random DID for this example
    agent_did = f"did:example:{agent_name}"
    
    # Create the DNS-like name
    agent_dns_name = f"{agent_name}.{agent_category}.{provider_name}.ans"
    
    # Generate key pair and CSR
    private_key, private_pem = generate_key_pair()
    csr_pem = create_csr(agent_name, private_key)
    
    # Create certificate info manually
    now = datetime.datetime.utcnow()
    valid_to = now + datetime.timedelta(days=30)
    
    # Generate a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, agent_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Organization"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
    ])
    
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
        valid_to
    ).sign(private_key, hashes.SHA256())
    
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    
    # Create certificate info with string dates in ISO-8601 format
    cert_info = {
        "certificateSubject": "CN=" + agent_name + ", O=Test Organization, C=US",
        "certificateIssuer": "CN=" + agent_name + ", O=Test Organization, C=US",
        "certificateSerialNumber": str(cert.serial_number),
        "certificateValidFrom": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "certificateValidTo": valid_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "certificatePEM": cert_pem.decode('utf-8'),
        "certificatePublicKeyAlgorithm": "RSA",
        "certificateSignatureAlgorithm": "SHA256withRSA"
    }
    
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
    
    print(f"Sending registration request for agent: {agent_name}")
    
    # Print the request data for debugging
    print(f"Request data: {json.dumps(request_data, indent=2)}")
    
    response = requests.post(
        f"{ANS_URL}/register",
        json=request_data
    )
    
    if response.status_code != 200:
        print(f"Registration failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

def main():
    """Simple client usage example."""
    # Agent information (minimal setup)
    agent_name = "simple-agent-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # unique name
    agent_category = "basic"
    provider_name = "example"
    version = "1.0.0"
    capability = "basic"
    protocol = "a2a"
    endpoint = "https://example.com/api"
    
    # Register agent
    print("Registering agent...")
    response = register_agent(
        agent_name,
        agent_category,
        provider_name,
        version,
        capability,
        endpoint,
        protocol
    )
    
    if response:
        print("Registration successful!")
        print(json.dumps(response, indent=2))
    else:
        print("Registration failed!")

if __name__ == "__main__":
    main() 
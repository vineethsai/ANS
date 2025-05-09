"""
Test script for the schema validation in the Agent Name Service.

This script tests all schema validation features for registration,
renewal, and capability queries.
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

def test_registration_with_schema_validation():
    """Test agent registration with schema validation."""
    # Agent information
    agent_name = "schema-validation-test"
    agent_category = "testing"
    provider_name = "example"
    version = "1.0.0"
    capability = "validation"
    protocol = "a2a"
    endpoint = "https://schema-validation.example.com/api"
    
    # Generate key pair and CSR
    print("Generating key pair and CSR...")
    private_key = generate_key_pair()
    csr = create_csr(agent_name, private_key)
    
    # Create certificate
    cert_info = create_self_signed_cert(agent_name, private_key)
    
    # Create a valid request first
    agent_did = f"did:example:{agent_name}"
    agent_dns_name = f"{agent_name}.{agent_category}.{provider_name}.ans"
    
    valid_request = {
        "requestType": "registration",
        "requestingAgent": {
            "protocol": protocol,
            "agentName": agent_name,
            "agentCategory": agent_category,
            "providerName": provider_name,
            "version": version,
            "extension": "agent",
            "agentUseJustification": f"Testing schema validation",
            "agentCapability": capability,
            "agentEndpoint": endpoint,
            "agentDID": agent_did,
            "certificate": cert_info,
            "csrPEM": csr.decode('utf-8'),
            "agentDNSName": agent_dns_name
        }
    }
    
    # Test 1: Send a valid request
    print("\nTEST 1: Valid registration request")
    response = requests.post(
        f"{ANS_URL}/register",
        json=valid_request
    )
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        resp_data = response.json()
        print(f"Response type: {resp_data.get('responseType')}")
        print(f"Status: {resp_data.get('status')}")
    else:
        print(f"Error: {response.text}")
    
    # Test 2: Send an invalid request (missing required field)
    print("\nTEST 2: Invalid registration (missing field)")
    invalid_request = valid_request.copy()
    invalid_request["requestingAgent"] = valid_request["requestingAgent"].copy()
    del invalid_request["requestingAgent"]["agentUseJustification"]
    
    response = requests.post(
        f"{ANS_URL}/register",
        json=invalid_request
    )
    
    print(f"Response status code: {response.status_code}")
    resp_data = response.json()
    print(f"Response type: {resp_data.get('responseType')}")
    print(f"Status: {resp_data.get('status')}")
    print(f"Error: {resp_data.get('error')}")
    
    # Test 3: Send an invalid request (invalid protocol)
    print("\nTEST 3: Invalid registration (invalid protocol)")
    invalid_protocol_request = valid_request.copy()
    invalid_protocol_request["requestingAgent"] = valid_request["requestingAgent"].copy()
    invalid_protocol_request["requestingAgent"]["protocol"] = "invalid_protocol"
    
    response = requests.post(
        f"{ANS_URL}/register",
        json=invalid_protocol_request
    )
    
    print(f"Response status code: {response.status_code}")
    resp_data = response.json()
    print(f"Response type: {resp_data.get('responseType')}")
    print(f"Status: {resp_data.get('status')}")
    print(f"Error: {resp_data.get('error')}")
    
    return True

def test_capability_query():
    """Test capability query with schema validation."""
    print("\nTEST 4: Capability query")
    
    # Test capability query
    response = requests.get(f"{ANS_URL}/agents?protocol=a2a")
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        resp_data = response.json()
        print(f"Response type: {resp_data.get('responseType')}")
        print(f"Status: {resp_data.get('status')}")
        print(f"Matching agents: {resp_data.get('resultCount')}")
        print(f"Query parameters: {resp_data.get('queryParameters')}")
    else:
        print(f"Error: {response.text}")
    
    return True

def main():
    """Run the schema validation tests."""
    print("Testing schema validation for ANS")
    print("================================")
    
    # Test registration
    test_registration_with_schema_validation()
    
    # Test capability query
    test_capability_query()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 
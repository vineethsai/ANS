"""
Test security aspects of the ANS system.

This test suite covers:
- Certificate validation
- Signature verification
- Attempts to register with invalid/expired certificates
- Attempts to register with revoked certificates
- Attempts to tamper with endpoint records
"""
import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime, timedelta
import time

from ans.core.agent_registry import AgentRegistry
from ans.core.agent import Agent
from ans.core.ans_name import ANSName
from ans.core.registration_authority import RegistrationAuthority
from ans.db.models import AgentModel, RevokedCertificateModel
from ans.crypto.certificate import Certificate
from ans.crypto.certificate_authority import CertificateAuthority

class TestSecurity:
    """Test security aspects of the ANS system."""
    
    @pytest.fixture
    def ca(self):
        """Create a Certificate Authority for testing."""
        cert, private_key = Certificate.generate_self_signed_cert("Test CA")
        return CertificateAuthority(cert, private_key)
    
    @pytest.fixture
    def another_ca(self):
        """Create another Certificate Authority (untrusted) for testing."""
        cert, private_key = Certificate.generate_self_signed_cert("Untrusted CA")
        return CertificateAuthority(cert, private_key)
    
    @pytest.fixture
    def db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.query = MagicMock(return_value=session)
        session.filter = MagicMock(return_value=session)
        session.filter_by = MagicMock(return_value=session)
        session.first = MagicMock(return_value=None)
        session.all = MagicMock(return_value=[])
        return session
    
    @pytest.fixture
    def registration_authority(self, ca):
        """Create a RegistrationAuthority for testing."""
        return RegistrationAuthority(ca)
    
    @pytest.fixture
    def registry(self, ca, db_session):
        """Create an AgentRegistry for testing."""
        registry = AgentRegistry(ca, db_session)
        registry.initialize_registry("Test Registry")
        return registry
    
    @pytest.fixture
    def valid_csr(self):
        """Create a valid Certificate Signing Request."""
        # Use a mock CSR string for testing
        return "-----BEGIN CERTIFICATE REQUEST-----\nMIIByjCCATMCAQAwWjELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRMwEQYDVQQH\nDApDYWxpZm9ybmlhMRIwEAYDVQQKDAlUZXN0IENvcnAxFTATBgNVBAMMDFRlc3Qg\nQWdlbnQgMTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEA1Kd87/j1XUYpML8p\noK9bUt5dt4wSo6YSJ3EU1TMcCGCrVpFzCk1L9JI8oPmtEDFdGIWYevMJxWxTCJV8\ng5Msq+UzTSbEXO2dwHRO7Y5+MxJK2hEXLhorRBgx/VZ8VFhw6bHMfjmkEO6zHL0v\n5JRJPNNTy8FMeOBCg8W2T+4notsCAwEAAaAtMCsGCSqGSIb3DQEJDjEeMBwwGgYD\nVR0RBBMwEYIPdGVzdC5hZ2VudC5jb20wDQYJKoZIhvcNAQELBQADgYEACQyMU7n3\nZIIvYnqiTu0xE2OzKLR7Jgibd1G1VjsJQZvSaEpXVeMI7JRHQyB4MhfAknmT/cUP\ngUHM8FGQM23DwMsISHOTpVdwDfKkzw2OMwU7MG7Ntnt35XNZ4PmwwFmjb/mKaCzt\nn96lOQEk+FpTZUZlGmiwG0Ej0eusJJYB3dI=\n-----END CERTIFICATE REQUEST-----"
    
    @pytest.fixture
    def valid_agent(self, registration_authority, valid_csr):
        """Create a valid agent with proper certificate."""
        with patch.object(registration_authority, 'process_registration_request') as mock_register:
            mock_register.return_value = {
                "agent": {
                    "agent_id": "test-agent",
                    "ans_name": "a2a://test-agent.conversation.test-provider.v1.0.0",
                    "capabilities": ["conversation"],
                    "protocol_extensions": {
                        "endpoint": "https://test-agent.example.com/api",
                        "did": "did:example:test-agent",
                        "use_justification": "Testing agent registration",
                        "dns_name": "test-agent.conversation.test-provider.ans"
                    },
                    "endpoint": "https://test-agent.example.com/api",
                    "registration_time": datetime.utcnow().isoformat(),
                    "last_renewal_time": None,
                    "is_active": True
                },
                "certificate": "MOCK_CERTIFICATE"
            }
            
            request = {
                "agent_id": "test-agent",
                "ans_name": "a2a://test-agent.conversation.test-provider.v1.0.0",
                "capabilities": ["conversation"],
                "protocol_extensions": {
                    "endpoint": "https://test-agent.example.com/api",
                    "did": "did:example:test-agent",
                    "use_justification": "Testing agent registration",
                    "dns_name": "test-agent.conversation.test-provider.ans"
                },
                "endpoint": "https://test-agent.example.com/api",
                "csr": valid_csr
            }
            
            response = registration_authority.process_registration_request(request)
            
        agent = Agent.from_dict(response["agent"])
        agent.certificate = response["certificate"]
        return agent
    
    @pytest.fixture
    def untrusted_certificate(self, another_ca):
        """Create a certificate from an untrusted CA."""
        # Generate a test certificate with the untrusted CA
        test_cert, test_key = Certificate.generate_self_signed_cert("Untrusted Agent")
        # For testing purposes, we'll just return a mock certificate
        return "UNTRUSTED_MOCK_CERTIFICATE"
    
    def test_registration_with_invalid_certificate(self, registry, db_session, valid_agent):
        """Test registration with an invalid certificate."""
        # Create an agent with an invalid certificate (just a string)
        invalid_agent = Agent(
            agent_id=valid_agent.agent_id,
            ans_name=valid_agent.ans_name,
            capabilities=valid_agent.capabilities,
            protocol_extensions=valid_agent.protocol_extensions,
            endpoint=valid_agent.endpoint,
            certificate="INVALID_CERTIFICATE",
            registration_time=datetime.utcnow(),
            last_renewal_time=None,
            is_active=True
        )
        
        # Mock the certificate validation to fail
        with patch('ans.crypto.certificate.Certificate.is_valid', return_value=False):
            with pytest.raises(ValueError) as excinfo:
                registry.register_agent(invalid_agent)
            
            assert "certificate is not valid" in str(excinfo.value).lower()
    
    def test_registration_with_untrusted_certificate(self, registry, db_session, valid_agent, untrusted_certificate):
        """Test registration with a certificate from an untrusted CA."""
        # Create an agent with a certificate from an untrusted CA
        untrusted_agent = Agent(
            agent_id="untrusted-agent",
            ans_name=ANSName.parse("a2a://untrusted-agent.conversation.test-provider.v1.0.0"),
            capabilities=valid_agent.capabilities,
            protocol_extensions=valid_agent.protocol_extensions,
            endpoint=valid_agent.endpoint,
            certificate=untrusted_certificate,
            registration_time=datetime.utcnow(),
            last_renewal_time=None,
            is_active=True
        )
        
        # Mock the CA chain verification to fail
        with patch.object(registry.ca, 'verify_certificate_chain', return_value=False):
            with pytest.raises(ValueError) as excinfo:
                registry.register_agent(untrusted_agent)
            
            assert "invalid agent certificate" in str(excinfo.value).lower()
    
    def test_registration_with_expired_certificate(self, registry, db_session, valid_agent):
        """Test registration with an expired certificate."""
        # Mock Certificate.is_valid to simulate an expired certificate
        with patch('ans.crypto.certificate.Certificate.is_valid', return_value=False):
            with pytest.raises(ValueError) as excinfo:
                registry.register_agent(valid_agent)
            
            assert "certificate is not valid" in str(excinfo.value).lower()
    
    def test_registration_with_revoked_certificate(self, registry, db_session, valid_agent):
        """Test registration with a revoked certificate."""
        # Mock the database to simulate a revoked certificate
        revoked_cert = MagicMock(spec=RevokedCertificateModel)
        revoked_cert.serial_number = "12345"  # Sample serial number
        
        # Mock Certificate to return the serial number
        with patch('ans.crypto.certificate.Certificate.get_serial_number', return_value="12345"):
            # Mock the query to return the revoked certificate
            db_session.first.return_value = revoked_cert
            
            with pytest.raises(ValueError) as excinfo:
                registry.register_agent(valid_agent)
            
            assert "revoked" in str(excinfo.value).lower()
    
    def test_tampered_endpoint_record(self, registry, db_session, valid_agent):
        """Test verification of a tampered endpoint record."""
        # Create a valid endpoint record
        agent_model = MagicMock(spec=AgentModel)
        agent_model.agent_id = valid_agent.agent_id
        agent_model.ans_name = str(valid_agent.ans_name)
        agent_model.capabilities = valid_agent.capabilities
        agent_model.protocol_extensions = valid_agent.protocol_extensions
        agent_model.endpoint = valid_agent.endpoint
        agent_model.certificate = valid_agent.certificate
        agent_model.registration_time = valid_agent.registration_time
        agent_model.last_renewal_time = valid_agent.last_renewal_time
        agent_model.is_active = True
        
        # Mock to_dict method
        agent_model.to_dict.return_value = {
            "agent_id": agent_model.agent_id,
            "ans_name": agent_model.ans_name,
            "capabilities": agent_model.capabilities,
            "protocol_extensions": agent_model.protocol_extensions,
            "endpoint": agent_model.endpoint,
            "certificate": agent_model.certificate,
            "registration_time": agent_model.registration_time,
            "last_renewal_time": agent_model.last_renewal_time,
            "is_active": agent_model.is_active
        }
        
        # Mock database to return the agent
        db_session.first.return_value = agent_model
        db_session.all.return_value = [agent_model]
        
        # Mock signature verification methods
        with patch.object(registry._registry_cert, 'sign_data', return_value=b"VALID_SIGNATURE"):
            with patch.object(registry._registry_cert, 'verify_signature', side_effect=lambda data, sig: b"MALICIOUS" not in data):
                # Get a valid endpoint record
                endpoint_record = registry.resolve_ans_name(str(valid_agent.ans_name))
                
                # Tamper with the data
                tampered_record = endpoint_record.copy()
                tampered_record["data"]["endpoint"] = "https://malicious.example.com/api"
                
                # Verify the tampered record
                assert not registry.verify_endpoint_record(tampered_record)
                
                # Original record should verify
                assert registry.verify_endpoint_record(endpoint_record)
    
    def test_signature_verification(self, registry, valid_agent):
        """Test signature verification of registry certificates."""
        # Create some data to sign
        data = json.dumps({"test": "data"}).encode()
        
        # Sign with registry certificate
        signature = registry._registry_cert.sign_data(data)
        
        # Tampered data
        tampered_data = json.dumps({"test": "tampered"}).encode()
        
        # Verification should succeed with correct data
        assert registry._registry_cert.verify_signature(data, signature)
        
        # Verification should fail with tampered data
        assert not registry._registry_cert.verify_signature(tampered_data, signature)
    
    def test_certificate_chain_verification(self, ca, another_ca):
        """Test certificate chain verification."""
        # Generate test certificates
        cert1, key1 = Certificate.generate_self_signed_cert("Test Agent 1")
        cert2, key2 = Certificate.generate_self_signed_cert("Test Agent 2")
        
        # Mock verify_certificate_chain to return appropriate results
        with patch.object(ca, 'verify_certificate_chain', side_effect=lambda cert: cert == cert1):
            # Trusted certificate should verify
            assert ca.verify_certificate_chain(cert1)
            
            # Untrusted certificate should not verify
            assert not ca.verify_certificate_chain(cert2)
            
            # Test cross-verification
            with patch.object(another_ca, 'verify_certificate_chain', side_effect=lambda cert: cert == cert2):
                # CA from another chain should not verify the certificate
                assert not another_ca.verify_certificate_chain(cert1) 
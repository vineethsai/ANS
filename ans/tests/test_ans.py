"""
Test script for the Agent Name Service.
"""
import pytest
from datetime import datetime
from ..core.agent import Agent
from ..core.ans_name import ANSName
from ..core.agent_registry import AgentRegistry
from ..core.registration_authority import RegistrationAuthority
from ..crypto.certificate import Certificate
from ..crypto.certificate_authority import CertificateAuthority
from ..db.models import init_db, AgentModel
from sqlalchemy.orm import Session

@pytest.fixture
def db_session():
    """Create a test database session."""
    SessionLocal = init_db("sqlite:///test.db")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def ca():
    """Create a test Certificate Authority."""
    ca_cert, ca_private_key = Certificate.generate_self_signed_cert("Test CA")
    return CertificateAuthority(ca_cert, ca_private_key)

@pytest.fixture
def ra(ca):
    """Create a test Registration Authority."""
    return RegistrationAuthority(ca)

@pytest.fixture
def registry(ca, db_session):
    """Create a test Agent Registry."""
    registry = AgentRegistry(ca, db_session)
    registry.initialize_registry("Test Registry")
    return registry

def test_ans_name_parsing():
    """Test ANS name parsing."""
    # Valid ANS name
    name_str = "a2a://agent1.capability1.provider1.v1.0.0,ext1"
    name = ANSName.parse(name_str)
    assert name.protocol == "a2a"
    assert name.agent_id == "agent1"
    assert name.capability == "capability1"
    assert name.provider == "provider1"
    assert name.version == "1.0.0"
    assert name.extension == "ext1"

    # Invalid ANS name
    with pytest.raises(ValueError):
        ANSName.parse("invalid-name")

def test_agent_registration(registry, ra):
    """Test agent registration."""
    # Create test agent
    ans_name = ANSName.parse("a2a://agent1.capability1.provider1.v1.0.0")
    agent_cert, _ = Certificate.generate_self_signed_cert("agent1")
    
    agent = Agent(
        agent_id="agent1",
        ans_name=ans_name,
        capabilities=["cap1", "cap2"],
        protocol_extensions={"ext1": "value1"},
        endpoint="http://agent1.example.com",
        certificate=agent_cert.get_pem().decode()
    )

    # Register agent
    registry.register_agent(agent)

    # Verify registration
    db_agent = registry.db.query(AgentModel).filter_by(agent_id="agent1").first()
    assert db_agent is not None
    assert db_agent.ans_name == str(ans_name)
    assert db_agent.capabilities == ["cap1", "cap2"]
    assert db_agent.protocol_extensions == {"ext1": "value1"}
    assert db_agent.endpoint == "http://agent1.example.com"

def test_agent_resolution(registry):
    """Test agent resolution."""
    # Register test agent
    ans_name = ANSName.parse("a2a://agent1.capability1.provider1.v1.0.0")
    agent_cert, _ = Certificate.generate_self_signed_cert("agent1")
    
    agent = Agent(
        agent_id="agent1",
        ans_name=ans_name,
        capabilities=["cap1", "cap2"],
        protocol_extensions={"ext1": "value1"},
        endpoint="http://agent1.example.com",
        certificate=agent_cert.get_pem().decode()
    )
    registry.register_agent(agent)

    # Resolve agent
    result = registry.resolve_ans_name(str(ans_name))
    assert result["data"]["agent_id"] == "agent1"
    assert result["data"]["ans_name"] == str(ans_name)
    assert result["data"]["endpoint"] == "http://agent1.example.com"

def test_agent_renewal(registry):
    """Test agent renewal."""
    # Register test agent
    ans_name = ANSName.parse("a2a://agent1.capability1.provider1.v1.0.0")
    agent_cert, _ = Certificate.generate_self_signed_cert("agent1")
    
    agent = Agent(
        agent_id="agent1",
        ans_name=ans_name,
        capabilities=["cap1", "cap2"],
        protocol_extensions={"ext1": "value1"},
        endpoint="http://agent1.example.com",
        certificate=agent_cert.get_pem().decode()
    )
    registry.register_agent(agent)

    # Renew agent
    registry.renew_agent("agent1")

    # Verify renewal
    db_agent = registry.db.query(AgentModel).filter_by(agent_id="agent1").first()
    assert db_agent.last_renewal_time is not None
    assert db_agent.is_active is True

def test_agent_deactivation(registry):
    """Test agent deactivation."""
    # Register test agent
    ans_name = ANSName.parse("a2a://agent1.capability1.provider1.v1.0.0")
    agent_cert, _ = Certificate.generate_self_signed_cert("agent1")
    
    agent = Agent(
        agent_id="agent1",
        ans_name=ans_name,
        capabilities=["cap1", "cap2"],
        protocol_extensions={"ext1": "value1"},
        endpoint="http://agent1.example.com",
        certificate=agent_cert.get_pem().decode()
    )
    registry.register_agent(agent)

    # Deactivate agent
    registry.deactivate_agent("agent1")

    # Verify deactivation
    db_agent = registry.db.query(AgentModel).filter_by(agent_id="agent1").first()
    assert db_agent.is_active is False

def test_certificate_operations(ca):
    """Test certificate operations."""
    # Generate test certificate
    cert, private_key = Certificate.generate_self_signed_cert("test-agent")
    
    # Verify certificate
    assert cert.is_valid()
    assert not ca.is_certificate_revoked(cert.get_serial_number())

    # Revoke certificate
    ca.revoke_certificate(cert.get_serial_number())
    assert ca.is_certificate_revoked(cert.get_serial_number()) 
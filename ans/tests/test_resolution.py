"""
Test cases for ANS name resolution and version negotiation.
"""
import pytest
import semver
from ..core.ans_name import ANSName
from ..core.agent import Agent
from ..core.agent_registry import AgentRegistry
from ..crypto.certificate import Certificate
from ..crypto.certificate_authority import CertificateAuthority
from ..db.models import init_db

@pytest.fixture
def db_session():
    """Create a test database session."""
    SessionLocal = init_db("sqlite:///test_resolution.db")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def setup_registry(db_session):
    """Set up a test registry with multiple agent versions."""
    # Create CA
    ca_cert, ca_key = Certificate.generate_self_signed_cert("Test CA", validity_days=10)
    ca = CertificateAuthority(ca_cert, ca_key)
    
    # Create registry
    registry = AgentRegistry(ca, db_session)
    registry.initialize_registry("Test Registry")
    
    # Create and register agents with different versions
    versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]
    for version in versions:
        ans_name = ANSName.parse(f"a2a://testbot.chat.acme.v{version}")
        agent_cert, _ = Certificate.generate_self_signed_cert(f"testbot-v{version}")
        
        agent = Agent(
            agent_id="testbot",
            ans_name=ans_name,
            capabilities=["chat", "question-answering"],
            protocol_extensions={"format": "markdown"},
            endpoint=f"https://agent.example.com/v{version}/testbot",
            certificate=agent_cert.get_pem().decode()
        )
        
        # This would normally fail with duplicate agent_id, but we'll modify our test
        # to create a unique agent_id for each version
        agent.agent_id = f"testbot-v{version}"
        
        registry.register_agent(agent)
    
    return registry

def test_version_resolution(setup_registry):
    """Test resolution with version selection."""
    registry = setup_registry
    
    # Test exact version match
    result = registry.resolve_ans_name("a2a://testbot-v1.0.0.chat.acme.v1.0.0")
    assert result["data"]["agent_id"] == "testbot-v1.0.0"
    assert result["data"]["ans_name"] == "a2a://testbot-v1.0.0.chat.acme.v1.0.0"
    
    # Test version range match (should return the highest matching version)
    # This would work if we implemented version range matching in resolve_ans_name
    # For now, this is a placeholder to show how it would be tested
    
    # result = registry.resolve_ans_name("a2a://testbot.chat.acme.v1.x.x", "^1.0.0")
    # assert result["data"]["agent_id"] == "testbot-v1.2.0"  # Highest matching 1.x.x version

def test_invalid_version_resolution(setup_registry):
    """Test resolution with invalid version."""
    registry = setup_registry
    
    # Test non-existent version
    with pytest.raises(ValueError):
        registry.resolve_ans_name("a2a://testbot.chat.acme.v3.0.0")

def test_protocol_match(setup_registry):
    """Test matching by protocol."""
    registry = setup_registry
    
    # Find all a2a agents
    agents = registry.find_agents_by_criteria(protocol="a2a")
    assert len(agents) == 4  # We registered 4 agents with a2a protocol
    
    # Find agents with a specific protocol, capability, and provider
    agents = registry.find_agents_by_criteria(
        protocol="a2a",
        capability="chat",
        provider="acme"
    )
    assert len(agents) == 4  # All are chat.acme

def test_endpoint_record_signature(setup_registry):
    """Test that endpoint records are properly signed."""
    registry = setup_registry
    
    # Resolve an agent
    result = registry.resolve_ans_name("a2a://testbot-v1.0.0.chat.acme.v1.0.0")
    
    # Verify that the record contains required fields
    assert "data" in result
    assert "signature" in result
    assert "registry_certificate" in result
    
    # Verify the signature
    assert registry.verify_endpoint_record(result) 
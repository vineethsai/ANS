"""
Tests for the database functionality of the Agent Name Service.
"""
import os
import pytest
import tempfile
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ans.db.models import Base, AgentModel, RevokedCertificateModel
from ans.db.init_db import init_database


class TestDatabase:
    """Test the ANS database functionality."""
    
    @pytest.fixture
    def test_db_path(self):
        """Create a temporary database file for testing."""
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, "test_ans.db")
    
    @pytest.fixture
    def test_db_url(self, test_db_path):
        """Return the database URL for the test database."""
        # Remove the file if it already exists
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)
        
        return f"sqlite:///{test_db_path}"
    
    @pytest.fixture
    def db_session(self, test_db_url):
        """Create and return a database session."""
        engine = create_engine(test_db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        yield session
        
        # Clean up
        session.close()
    
    def test_init_database(self, test_db_url, test_db_path):
        """Test that the database can be initialized."""
        # Initialize the database
        init_database(test_db_url)
        
        # Check that the database file was created
        assert os.path.exists(test_db_path), "Database file was not created"
    
    def test_agent_model_creation(self, db_session):
        """Test that an AgentModel can be created and saved."""
        # Create a test agent
        agent = AgentModel(
            agent_id="test-agent-1",
            ans_name="a2a://test-agent-1.capability.provider.v1.0.0",
            capabilities=["capability1", "capability2"],
            protocol_extensions={"ext1": "value1", "ext2": "value2"},
            endpoint="https://test-agent.example.com/api",
            certificate="MOCK_CERTIFICATE",
            registration_time=datetime.utcnow(),
            is_active=True
        )
        
        # Save the agent to the database
        db_session.add(agent)
        db_session.commit()
        
        # Query the agent from the database
        saved_agent = db_session.query(AgentModel).filter_by(agent_id="test-agent-1").first()
        
        # Verify the agent was saved correctly
        assert saved_agent is not None, "Agent was not saved to the database"
        assert saved_agent.agent_id == "test-agent-1"
        assert saved_agent.ans_name == "a2a://test-agent-1.capability.provider.v1.0.0"
        assert "capability1" in saved_agent.capabilities
        assert "capability2" in saved_agent.capabilities
        assert saved_agent.protocol_extensions["ext1"] == "value1"
        assert saved_agent.endpoint == "https://test-agent.example.com/api"
        assert saved_agent.certificate == "MOCK_CERTIFICATE"
        assert saved_agent.is_active is True
    
    def test_revoked_certificate_model_creation(self, db_session):
        """Test that a RevokedCertificateModel can be created and saved."""
        # Create a test revoked certificate
        revoked_cert = RevokedCertificateModel(
            serial_number=12345,
            revocation_time=datetime.utcnow(),
            reason="compromised"
        )
        
        # Save the revoked certificate to the database
        db_session.add(revoked_cert)
        db_session.commit()
        
        # Query the revoked certificate from the database
        saved_cert = db_session.query(RevokedCertificateModel).filter_by(serial_number=12345).first()
        
        # Verify the revoked certificate was saved correctly
        assert saved_cert is not None, "Revoked certificate was not saved to the database"
        assert saved_cert.serial_number == 12345
        assert saved_cert.reason == "compromised"
    
    def test_agent_model_to_dict(self, db_session):
        """Test that an AgentModel can be converted to a dictionary."""
        # Create a test agent
        registration_time = datetime.utcnow()
        agent = AgentModel(
            agent_id="test-agent-2",
            ans_name="a2a://test-agent-2.capability.provider.v1.0.0",
            capabilities=["capability1"],
            protocol_extensions={"ext1": "value1"},
            endpoint="https://test-agent.example.com/api",
            certificate="MOCK_CERTIFICATE",
            registration_time=registration_time,
            is_active=True
        )
        
        # Convert to dictionary
        agent_dict = agent.to_dict()
        
        # Verify the dictionary contains the correct data
        assert agent_dict["agent_id"] == "test-agent-2"
        assert agent_dict["ans_name"] == "a2a://test-agent-2.capability.provider.v1.0.0"
        assert "capability1" in agent_dict["capabilities"]
        assert agent_dict["protocol_extensions"]["ext1"] == "value1"
        assert agent_dict["endpoint"] == "https://test-agent.example.com/api"
        assert agent_dict["certificate"] == "MOCK_CERTIFICATE"
        assert agent_dict["registration_time"] == registration_time.isoformat()
        assert agent_dict["is_active"] is True
    
    def test_agent_query(self, db_session):
        """Test querying agents from the database."""
        # Create multiple test agents
        agents = [
            AgentModel(
                agent_id=f"test-agent-{i}",
                ans_name=f"a2a://test-agent-{i}.capability.provider.v1.0.0",
                capabilities=["capability1"],
                protocol_extensions={"ext1": "value1"},
                endpoint=f"https://test-agent-{i}.example.com/api",
                certificate="MOCK_CERTIFICATE",
                registration_time=datetime.utcnow(),
                is_active=True
            )
            for i in range(3, 6)  # Create agents 3, 4, 5
        ]
        
        # Save the agents to the database
        for agent in agents:
            db_session.add(agent)
        db_session.commit()
        
        # Query all agents
        all_agents = db_session.query(AgentModel).all()
        
        # Verify that at least 3 agents were added
        assert len(all_agents) >= 3, "Not all agents were saved to the database"
        
        # Query a specific agent
        agent_4 = db_session.query(AgentModel).filter_by(agent_id="test-agent-4").first()
        
        # Verify the specific agent was found
        assert agent_4 is not None, "Specific agent was not found in the database"
        assert agent_4.agent_id == "test-agent-4"
        assert agent_4.ans_name == "a2a://test-agent-4.capability.provider.v1.0.0"
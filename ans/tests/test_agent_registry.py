"""
Test the AgentRegistry class.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from ans.core.agent_registry import AgentRegistry
from ans.core.agent import Agent
from ans.core.ans_name import ANSName
from ans.db.models import AgentModel
from ans.crypto.certificate import Certificate
from ans.crypto.certificate_authority import CertificateAuthority

class TestAgentRegistry:
    """Test the AgentRegistry class."""
    
    @pytest.fixture
    def ca(self):
        """Create a mock Certificate Authority."""
        ca = MagicMock(spec=CertificateAuthority)
        ca.verify_certificate_chain.return_value = True
        return ca
    
    @pytest.fixture
    def db_session(self):
        """Create a mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def registry(self, ca, db_session):
        """Create an AgentRegistry instance with mock dependencies."""
        registry = AgentRegistry(ca, db_session)
        registry._registry_cert = MagicMock(spec=Certificate)
        registry._registry_cert.get_pem.return_value = b"MOCK_CERT"
        registry._registry_cert.sign_data.return_value = b"MOCK_SIGNATURE"
        registry._registry_private_key = b"MOCK_PRIVATE_KEY"
        return registry
    
    @pytest.fixture
    def agent_models(self):
        """Create mock agent models with different versions."""
        agent_v100 = MagicMock(spec=AgentModel)
        agent_v100.agent_id = "test-agent"
        agent_v100.ans_name = "a2a://test-agent.conversation.openai.v1.0.0"
        agent_v100.capabilities = ["conversation"]
        agent_v100.protocol_extensions = {"endpoint": "https://api.example.com/v1"}
        agent_v100.endpoint = "https://api.example.com/v1"
        agent_v100.certificate = "CERT_V1"
        agent_v100.registration_time = datetime.utcnow()
        agent_v100.last_renewal_time = None
        agent_v100.is_active = True
        agent_v100.to_dict.return_value = {
            "agent_id": agent_v100.agent_id,
            "ans_name": agent_v100.ans_name,
            "capabilities": agent_v100.capabilities,
            "protocol_extensions": agent_v100.protocol_extensions,
            "endpoint": agent_v100.endpoint,
            "certificate": agent_v100.certificate,
            "registration_time": agent_v100.registration_time,
            "last_renewal_time": agent_v100.last_renewal_time,
            "is_active": agent_v100.is_active
        }
        
        agent_v110 = MagicMock(spec=AgentModel)
        agent_v110.agent_id = "test-agent"
        agent_v110.ans_name = "a2a://test-agent.conversation.openai.v1.1.0"
        agent_v110.capabilities = ["conversation"]
        agent_v110.protocol_extensions = {"endpoint": "https://api.example.com/v1.1"}
        agent_v110.endpoint = "https://api.example.com/v1.1"
        agent_v110.certificate = "CERT_V1_1"
        agent_v110.registration_time = datetime.utcnow()
        agent_v110.last_renewal_time = None
        agent_v110.is_active = True
        agent_v110.to_dict.return_value = {
            "agent_id": agent_v110.agent_id,
            "ans_name": agent_v110.ans_name,
            "capabilities": agent_v110.capabilities,
            "protocol_extensions": agent_v110.protocol_extensions,
            "endpoint": agent_v110.endpoint,
            "certificate": agent_v110.certificate,
            "registration_time": agent_v110.registration_time,
            "last_renewal_time": agent_v110.last_renewal_time,
            "is_active": agent_v110.is_active
        }
        
        agent_v200 = MagicMock(spec=AgentModel)
        agent_v200.agent_id = "test-agent"
        agent_v200.ans_name = "a2a://test-agent.conversation.openai.v2.0.0"
        agent_v200.capabilities = ["conversation", "enhanced"]
        agent_v200.protocol_extensions = {"endpoint": "https://api.example.com/v2"}
        agent_v200.endpoint = "https://api.example.com/v2"
        agent_v200.certificate = "CERT_V2"
        agent_v200.registration_time = datetime.utcnow()
        agent_v200.last_renewal_time = None
        agent_v200.is_active = True
        agent_v200.to_dict.return_value = {
            "agent_id": agent_v200.agent_id,
            "ans_name": agent_v200.ans_name,
            "capabilities": agent_v200.capabilities,
            "protocol_extensions": agent_v200.protocol_extensions,
            "endpoint": agent_v200.endpoint,
            "certificate": agent_v200.certificate,
            "registration_time": agent_v200.registration_time,
            "last_renewal_time": agent_v200.last_renewal_time,
            "is_active": agent_v200.is_active
        }
        
        return [agent_v100, agent_v110, agent_v200]
    
    def test_resolve_ans_name_exact_version(self, registry, agent_models, db_session):
        """Test resolving an ANS name with exact version."""
        # Mock the database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_by_mock = MagicMock()
        
        db_session.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.filter_by.return_value = filter_by_mock
        filter_by_mock.all.return_value = agent_models
        
        # Request exact version (v1.0.0)
        ans_name = "a2a://test-agent.conversation.openai.v1.0.0"
        result = registry.resolve_ans_name(ans_name)
        
        # Verify the result
        assert result["data"]["agent_id"] == "test-agent"
        assert result["data"]["ans_name"] == "a2a://test-agent.conversation.openai.v1.0.0"
        assert result["data"]["certificate"] == "CERT_V1"
        
        # Verify query was constructed correctly
        db_session.query.assert_called_once_with(AgentModel)
        query_mock.filter.assert_called_once()
        filter_mock.filter_by.assert_called_once_with(is_active=True)
    
    def test_resolve_ans_name_latest_version(self, registry, agent_models, db_session):
        """Test resolving an ANS name with no specific version (gets latest)."""
        # Mock the database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_by_mock = MagicMock()
        
        db_session.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.filter_by.return_value = filter_by_mock
        filter_by_mock.all.return_value = agent_models
        
        # Request without exact version
        ans_name = "a2a://test-agent.conversation.openai.v"
        with patch('semver.VersionInfo.parse') as mock_parse:
            # Ensure we get the version comparison right
            mock_parse.side_effect = lambda v: MagicMock(__gt__=lambda other: v == "2.0.0")
            result = registry.resolve_ans_name(ans_name)
        
        # Verify the result (should be v2.0.0 as it's the latest)
        assert result["data"]["agent_id"] == "test-agent"
        assert result["data"]["ans_name"] == "a2a://test-agent.conversation.openai.v2.0.0"
        assert result["data"]["certificate"] == "CERT_V2"
    
    def test_resolve_ans_name_with_version_range(self, registry, agent_models, db_session):
        """Test resolving an ANS name with a version range."""
        # Mock the database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_by_mock = MagicMock()
        
        db_session.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.filter_by.return_value = filter_by_mock
        filter_by_mock.all.return_value = agent_models
        
        # Request with version range ^1.0.0 (matches 1.0.0 and 1.1.0, but not 2.0.0)
        ans_name = "a2a://test-agent.conversation.openai.v"
        
        # Mock the version range check and sorting
        with patch('ans.core.ans_name.ANSName.satisfies_version_range') as mock_satisfies:
            # Only the v1.x.x versions should match
            mock_satisfies.side_effect = lambda v: "v2.0.0" not in v
            
            # Mock the version parsing and comparison for sorting
            with patch('semver.VersionInfo.parse') as mock_parse:
                mock_v110 = MagicMock()
                mock_v110.__gt__ = lambda other: True
                mock_v100 = MagicMock()
                mock_v100.__gt__ = lambda other: False
                
                # v1.1.0 should be greater than v1.0.0
                mock_parse.side_effect = lambda v: mock_v110 if v == "1.1.0" else mock_v100
                
                result = registry.resolve_ans_name(ans_name, version_range="^1.0.0")
        
        # Verify the result (should be v1.1.0 as it's the highest matching version)
        assert result["data"]["agent_id"] == "test-agent"
        assert result["data"]["ans_name"] == "a2a://test-agent.conversation.openai.v1.1.0"
        assert result["data"]["certificate"] == "CERT_V1_1"
    
    def test_resolve_ans_name_no_matching_version(self, registry, db_session):
        """Test resolving an ANS name with a version range that has no matches."""
        # Mock the database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_by_mock = MagicMock()
        
        db_session.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.filter_by.return_value = filter_by_mock
        filter_by_mock.all.return_value = []  # No matching agents
        
        # Request with version range
        ans_name = "a2a://test-agent.conversation.openai.v"
        
        # Should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            registry.resolve_ans_name(ans_name, version_range="^3.0.0")
        
        assert "No active agent found" in str(excinfo.value)
    
    def test_resolve_ans_name_no_agent_matches_range(self, registry, agent_models, db_session):
        """Test resolving when agents exist but none match the version range."""
        # Mock the database query
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_by_mock = MagicMock()
        
        db_session.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.filter_by.return_value = filter_by_mock
        filter_by_mock.all.return_value = agent_models
        
        # Request with version range that won't match any agent
        ans_name = "a2a://test-agent.conversation.openai.v"
        
        # Mock the version range check to always return False (no matches)
        with patch('ans.core.ans_name.ANSName.satisfies_version_range') as mock_satisfies:
            mock_satisfies.return_value = False
            
            # Should raise ValueError
            with pytest.raises(ValueError) as excinfo:
                registry.resolve_ans_name(ans_name, version_range="^3.0.0")
            
            assert "No agent matches version range" in str(excinfo.value) 
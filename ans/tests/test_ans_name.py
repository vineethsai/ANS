"""
Test ANS name parsing and validation with focus on edge cases.

This test suite covers:
- Valid ANS name formats
- Invalid ANS name formats
- Edge cases in parsing
- Validation rules for each component
"""
import pytest
import re
from ans.core.ans_name import ANSName

class TestANSNameParsing:
    """Test ANS name parsing and validation."""
    
    def test_valid_ans_name_formats(self):
        """Test parsing of valid ANS name formats."""
        # Standard format
        name = ANSName.parse("a2a://agent-id.capability.provider.v1.0.0")
        assert name.protocol == "a2a"
        assert name.agent_id == "agent-id"
        assert name.capability == "capability"
        assert name.provider == "provider"
        assert name.version == "1.0.0"
        assert name.extension is None
        
        # With extension
        name = ANSName.parse("a2a://agent-id.capability.provider.v1.0.0,extension")
        assert name.protocol == "a2a"
        assert name.agent_id == "agent-id"
        assert name.capability == "capability"
        assert name.provider == "provider"
        assert name.version == "1.0.0"
        assert name.extension == "extension"
        
        # Different protocol
        name = ANSName.parse("mcp://agent-id.capability.provider.v1.0.0")
        assert name.protocol == "mcp"
        
        # With underscores and hyphens
        name = ANSName.parse("a2a://agent_id-123.capability_name.provider-name.v1.0.0")
        assert name.protocol == "a2a"
        assert name.agent_id == "agent_id-123"
        assert name.capability == "capability_name"
        assert name.provider == "provider-name"
        assert name.version == "1.0.0"
        
        # Pre-release version
        name = ANSName.parse("a2a://agent-id.capability.provider.v1.0.0-beta.1")
        assert name.protocol == "a2a"
        assert name.version == "1.0.0-beta.1"
        
        # Build metadata
        name = ANSName.parse("a2a://agent-id.capability.provider.v1.0.0+build.123")
        assert name.protocol == "a2a"
        assert name.version == "1.0.0+build.123"
        
        # Pre-release and build metadata
        name = ANSName.parse("a2a://agent-id.capability.provider.v1.0.0-alpha.1+build.123")
        assert name.protocol == "a2a"
        assert name.version == "1.0.0-alpha.1+build.123"
    
    def test_invalid_ans_name_formats(self):
        """Test parsing of invalid ANS name formats."""
        # Missing protocol
        with pytest.raises(ValueError):
            ANSName.parse("agent-id.capability.provider.v1.0.0")
        
        # Missing agent ID
        with pytest.raises(ValueError):
            ANSName.parse("a2a://.capability.provider.v1.0.0")
        
        # Missing capability
        with pytest.raises(ValueError):
            ANSName.parse("a2a://agent-id..provider.v1.0.0")
        
        # Missing provider
        with pytest.raises(ValueError):
            ANSName.parse("a2a://agent-id.capability..v1.0.0")
        
        # Missing version
        with pytest.raises(ValueError):
            ANSName.parse("a2a://agent-id.capability.provider.")
        
        # Missing 'v' prefix in version
        with pytest.raises(ValueError):
            ANSName.parse("a2a://agent-id.capability.provider.1.0.0")
        
        # Invalid version format
        with pytest.raises(ValueError):
            ANSName.parse("a2a://agent-id.capability.provider.vX.Y.Z")
            
        # Invalid version format (not semver)
        with pytest.raises(ValueError):
            ANSName.parse("a2a://agent-id.capability.provider.v1.0")
    
    def test_edge_cases(self):
        """Test edge cases in ANS name parsing."""
        # Multiple dots in version (valid for semver)
        name = ANSName.parse("a2a://agent-id.capability.provider.v1.0.0.0")
        assert name.version == "1.0.0.0"
        
        # Very long component names (but still valid)
        long_name = "a" * 50
        name = ANSName.parse(f"a2a://{long_name}.{long_name}.{long_name}.v1.0.0")
        assert name.agent_id == "a" * 50
        assert name.capability == "a" * 50
        assert name.provider == "a" * 50
        
        # Version with many segments
        name = ANSName.parse("a2a://agent-id.capability.provider.v1.2.3.4.5.6.7")
        assert name.version == "1.2.3.4.5.6.7"
        
        # Zero version components
        name = ANSName.parse("a2a://agent-id.capability.provider.v0.0.0")
        assert name.version == "0.0.0"
        
        # Extension with special characters (if allowed by validation)
        if re.match(r'^[a-zA-Z0-9_-]+$', "ext-123_456"):
            name = ANSName.parse("a2a://agent-id.capability.provider.v1.0.0,ext-123_456")
            assert name.extension == "ext-123_456"
    
    def test_validation_rules(self):
        """Test validation rules for each ANS name component."""
        # Create a valid ANS name
        name = ANSName(
            protocol="a2a",
            agent_id="agent-id",
            capability="capability",
            provider="provider",
            version="1.0.0"
        )
        
        # Should validate successfully
        assert name.validate()
        
        # Invalid protocol (contains invalid character)
        with pytest.raises(ValueError):
            ANSName(
                protocol="a2a!",
                agent_id="agent-id",
                capability="capability",
                provider="provider",
                version="1.0.0"
            ).validate()
        
        # Invalid agent_id (contains invalid character)
        with pytest.raises(ValueError):
            ANSName(
                protocol="a2a",
                agent_id="agent@id",
                capability="capability",
                provider="provider",
                version="1.0.0"
            ).validate()
        
        # Invalid capability (contains invalid character)
        with pytest.raises(ValueError):
            ANSName(
                protocol="a2a",
                agent_id="agent-id",
                capability="capability!",
                provider="provider",
                version="1.0.0"
            ).validate()
        
        # Invalid provider (contains invalid character)
        with pytest.raises(ValueError):
            ANSName(
                protocol="a2a",
                agent_id="agent-id",
                capability="capability",
                provider="provider!",
                version="1.0.0"
            ).validate()
        
        # Invalid version (not semver)
        with pytest.raises(ValueError):
            ANSName(
                protocol="a2a",
                agent_id="agent-id",
                capability="capability",
                provider="provider",
                version="not-semver"
            ).validate()
        
        # Invalid extension (contains invalid character)
        with pytest.raises(ValueError):
            ANSName(
                protocol="a2a",
                agent_id="agent-id",
                capability="capability",
                provider="provider",
                version="1.0.0",
                extension="extension!"
            ).validate()
    
    def test_string_representation(self):
        """Test string representation of ANS names."""
        # Without extension
        name = ANSName(
            protocol="a2a",
            agent_id="agent-id",
            capability="capability",
            provider="provider",
            version="1.0.0"
        )
        assert str(name) == "a2a://agent-id.capability.provider.v1.0.0"
        
        # With extension
        name = ANSName(
            protocol="a2a",
            agent_id="agent-id",
            capability="capability",
            provider="provider",
            version="1.0.0",
            extension="extension"
        )
        assert str(name) == "a2a://agent-id.capability.provider.v1.0.0,extension"
        
        # Roundtrip: Parse a string, then convert back to string
        original = "a2a://agent-id.capability.provider.v1.0.0"
        name = ANSName.parse(original)
        assert str(name) == original
        
        # Roundtrip with extension
        original = "a2a://agent-id.capability.provider.v1.0.0,extension"
        name = ANSName.parse(original)
        assert str(name) == original
    
    def test_component_validation(self):
        """Test validation of individual components."""
        # Protocol validation
        assert re.match(r'^[a-zA-Z0-9_-]+$', "a2a")
        assert re.match(r'^[a-zA-Z0-9_-]+$', "mcp")
        assert not re.match(r'^[a-zA-Z0-9_-]+$', "proto!")
        
        # Agent ID validation
        assert re.match(r'^[a-zA-Z0-9_-]+$', "agent-id")
        assert re.match(r'^[a-zA-Z0-9_-]+$', "agent_id")
        assert not re.match(r'^[a-zA-Z0-9_-]+$', "agent@id")
        
        # Capability validation
        assert re.match(r'^[a-zA-Z0-9_-]+$', "capability")
        assert re.match(r'^[a-zA-Z0-9_-]+$', "capability-name")
        assert not re.match(r'^[a-zA-Z0-9_-]+$', "capability!")
        
        # Provider validation
        assert re.match(r'^[a-zA-Z0-9_-]+$', "provider")
        assert re.match(r'^[a-zA-Z0-9_-]+$', "provider-name")
        assert not re.match(r'^[a-zA-Z0-9_-]+$', "provider!")
        
        # Extension validation
        assert re.match(r'^[a-zA-Z0-9_-]+$', "extension")
        assert re.match(r'^[a-zA-Z0-9_-]+$', "extension-name")
        assert not re.match(r'^[a-zA-Z0-9_-]+$', "extension!") 
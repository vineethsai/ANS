"""
Test version range matching functionality in ANS.
"""
import pytest
from ans.core.ans_name import ANSName

def test_satisfies_version_range():
    """Test version range matching functionality."""
    # Create test ANSName objects with different versions
    ans_v100 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="1.0.0"
    )
    
    ans_v110 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="1.1.0"
    )
    
    ans_v120 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="1.2.0"
    )
    
    ans_v200 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="2.0.0"
    )
    
    ans_v010 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="0.1.0"
    )
    
    ans_v011 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="0.1.1"
    )
    
    # Test exact version matching
    assert ans_v100.satisfies_version_range("1.0.0") is True
    assert ans_v110.satisfies_version_range("1.0.0") is False
    
    # Test operators
    assert ans_v100.satisfies_version_range(">0.9.0") is True
    assert ans_v100.satisfies_version_range("<1.1.0") is True
    assert ans_v100.satisfies_version_range(">=1.0.0") is True
    assert ans_v100.satisfies_version_range("<=1.0.0") is True
    assert ans_v100.satisfies_version_range("==1.0.0") is True
    assert ans_v100.satisfies_version_range("!=1.1.0") is True
    
    # Test caret ranges (^) - compatible with major version
    assert ans_v100.satisfies_version_range("^1.0.0") is True
    assert ans_v110.satisfies_version_range("^1.0.0") is True
    assert ans_v200.satisfies_version_range("^1.0.0") is False
    
    # For 0.x.y versions, ^ only allows changes in the patch version
    assert ans_v010.satisfies_version_range("^0.1.0") is True
    assert ans_v011.satisfies_version_range("^0.1.0") is True
    assert ans_v100.satisfies_version_range("^0.1.0") is False
    
    # Test tilde ranges (~) - compatible with minor version
    assert ans_v100.satisfies_version_range("~1.0.0") is True
    assert ans_v110.satisfies_version_range("~1.0.0") is False
    
    # Test ranges with hyphen (inclusive ranges)
    assert ans_v100.satisfies_version_range("1.0.0 - 2.0.0") is True
    assert ans_v110.satisfies_version_range("1.0.0 - 2.0.0") is True
    assert ans_v200.satisfies_version_range("1.0.0 - 2.0.0") is True
    
    # Test multiple range expressions
    assert ans_v110.satisfies_version_range(">=1.0.0 <2.0.0") is True
    assert ans_v200.satisfies_version_range(">=1.0.0 <2.0.0") is False

def test_is_compatible_with():
    """Test the is_compatible_with method."""
    # Create test ANSName objects with different versions
    ans_v100 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="1.0.0"
    )
    
    ans_v110 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="1.1.0"
    )
    
    ans_v200 = ANSName(
        protocol="a2a",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="2.0.0"
    )
    
    ans_mcp_v100 = ANSName(
        protocol="mcp",
        agent_id="test-agent",
        capability="conversation",
        provider="openai",
        version="1.0.0"
    )
    
    # Test same protocol, agent, capability, provider
    assert ans_v100.is_compatible_with(ans_v100) is True
    
    # Test different protocol
    assert ans_v100.is_compatible_with(ans_mcp_v100) is False
    
    # Test version matching (assuming the current implementation uses match)
    # The match method in semver is expected to match the version specification
    assert ans_v110.is_compatible_with(ans_v100) is False  # 1.1.0 doesn't match "1.0.0"
    assert ans_v100.is_compatible_with(ans_v100) is True   # 1.0.0 matches "1.0.0" 
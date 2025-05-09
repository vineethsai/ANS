"""
Test cases for protocol adapters.
"""
import pytest
from ..adapters.a2a import A2AProtocolAdapter
from ..adapters.base import ProtocolAdapter
from jsonschema import ValidationError

@pytest.fixture
def a2a_adapter():
    """Create an A2A protocol adapter instance."""
    return A2AProtocolAdapter()

def test_a2a_adapter_validate_protocol_data(a2a_adapter):
    """Test validation of A2A protocol data."""
    # Valid A2A protocol data
    valid_data = {
        "spec_version": "1.0.0",
        "capabilities": [
            {
                "name": "text_conversation",
                "version": "1.0.0",
                "description": "Text-based conversation capability",
                "interface": {
                    "inputs": {
                        "message": "string"
                    },
                    "outputs": {
                        "response": "string"
                    }
                }
            }
        ],
        "routing": {
            "protocol": "http",
            "endpoints": [
                {
                    "url": "https://example.com/api/conversation",
                    "capability": "text_conversation"
                }
            ]
        },
        "security": {
            "authentication": "oauth",
            "authorization": "rbac",
            "encryption": "tls"
        },
        "metadata": {
            "description": "Test agent"
        }
    }
    
    # This should not raise an exception
    a2a_adapter.validate_protocol_data(valid_data)
    
    # Invalid data (missing required field)
    invalid_data = {
        "spec_version": "1.0.0",
        "capabilities": [
            {
                "name": "text_conversation",
                "version": "1.0.0",
                "description": "Text-based conversation capability"
            }
        ],
        # Missing routing
        "security": {
            "authentication": "oauth"
        }
    }
    
    with pytest.raises(ValueError):
        a2a_adapter.validate_protocol_data(invalid_data)
    
    # Invalid enum value
    invalid_enum_data = {
        "spec_version": "1.0.0",
        "capabilities": [
            {
                "name": "text_conversation",
                "version": "1.0.0",
                "description": "Text-based conversation capability"
            }
        ],
        "routing": {
            "protocol": "invalid_protocol",  # Invalid value
            "endpoints": []
        },
        "security": {
            "authentication": "oauth"
        }
    }
    
    with pytest.raises(ValueError):
        a2a_adapter.validate_protocol_data(invalid_enum_data)

def test_a2a_adapter_parse_protocol_data(a2a_adapter):
    """Test parsing of A2A protocol data."""
    # A2A protocol data
    a2a_data = {
        "spec_version": "1.0.0",
        "capabilities": [
            {
                "name": "text_conversation",
                "version": "1.0.0",
                "description": "Text-based conversation capability",
                "interface": {
                    "inputs": {
                        "message": "string"
                    },
                    "outputs": {
                        "response": "string"
                    }
                }
            },
            {
                "name": "knowledge_query",
                "version": "2.0.0",
                "description": "Knowledge base query capability"
            }
        ],
        "routing": {
            "protocol": "http",
            "endpoints": [
                {
                    "url": "https://example.com/api/conversation",
                    "capability": "text_conversation"
                },
                {
                    "url": "https://example.com/api/query",
                    "capability": "knowledge_query"
                }
            ]
        },
        "security": {
            "authentication": "jwt",
            "authorization": "capability_based",
            "encryption": "mtls"
        },
        "metadata": {
            "description": "Test agent"
        }
    }
    
    # Parse data
    parsed_data = a2a_adapter.parse_protocol_data(a2a_data)
    
    # Verify parsed data
    assert parsed_data["protocol"] == "a2a"
    assert parsed_data["spec_version"] == "1.0.0"
    assert len(parsed_data["capabilities"]) == 2
    assert parsed_data["capabilities"][0]["name"] == "text_conversation"
    assert parsed_data["capabilities"][0]["version"] == "1.0.0"
    assert parsed_data["capabilities"][0]["parameters"] == {"message": "string"}
    assert parsed_data["capabilities"][0]["returns"] == {"response": "string"}
    assert parsed_data["capabilities"][1]["name"] == "knowledge_query"
    assert parsed_data["routing"]["protocol"] == "http"
    assert len(parsed_data["routing"]["endpoints"]) == 2
    assert parsed_data["security"]["authentication"] == "jwt"
    assert parsed_data["security"]["authorization"] == "capability_based"
    assert parsed_data["security"]["encryption"] == "mtls"
    assert parsed_data["metadata"]["description"] == "Test agent"

def test_a2a_adapter_format_protocol_data(a2a_adapter):
    """Test formatting of standard data to A2A protocol format."""
    # Standard data
    standard_data = {
        "protocol": "a2a",
        "spec_version": "1.0.0",
        "capabilities": [
            {
                "name": "text_conversation",
                "version": "1.0.0",
                "description": "Text-based conversation capability",
                "parameters": {
                    "message": "string"
                },
                "returns": {
                    "response": "string"
                }
            }
        ],
        "routing": {
            "protocol": "http",
            "endpoints": [
                {
                    "url": "https://example.com/api/conversation",
                    "capability": "text_conversation"
                }
            ]
        },
        "security": {
            "authentication": "jwt",
            "authorization": "capability_based",
            "encryption": "tls"
        },
        "metadata": {
            "description": "Test agent"
        }
    }
    
    # Format data
    formatted_data = a2a_adapter.format_protocol_data(standard_data)
    
    # Verify formatted data
    assert formatted_data["spec_version"] == "1.0.0"
    assert len(formatted_data["capabilities"]) == 1
    assert formatted_data["capabilities"][0]["name"] == "text_conversation"
    assert formatted_data["capabilities"][0]["version"] == "1.0.0"
    assert formatted_data["capabilities"][0]["description"] == "Text-based conversation capability"
    assert formatted_data["capabilities"][0]["interface"]["inputs"] == {"message": "string"}
    assert formatted_data["capabilities"][0]["interface"]["outputs"] == {"response": "string"}
    assert formatted_data["routing"]["protocol"] == "http"
    assert formatted_data["security"]["authentication"] == "jwt"
    assert formatted_data["security"]["authorization"] == "capability_based"
    assert formatted_data["security"]["encryption"] == "tls"
    assert formatted_data["metadata"]["description"] == "Test agent"
    
    # Invalid protocol
    invalid_data = {
        "protocol": "invalid",  # Not A2A
        "spec_version": "1.0.0",
        "capabilities": [],
        "routing": {
            "protocol": "http",
            "endpoints": []
        },
        "security": {
            "authentication": "none"
        }
    }
    
    with pytest.raises(ValueError):
        a2a_adapter.format_protocol_data(invalid_data)

def test_a2a_adapter_get_protocol_name(a2a_adapter):
    """Test getting the protocol name."""
    assert a2a_adapter.get_protocol_name() == "a2a" 
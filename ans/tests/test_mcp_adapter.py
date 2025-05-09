"""
Test cases for the MCP (Model Context Protocol) adapter.
"""
import pytest
from ..adapters.mcp import MCPProtocolAdapter
from jsonschema import ValidationError

@pytest.fixture
def mcp_adapter():
    """Create an MCP protocol adapter instance."""
    return MCPProtocolAdapter()

def test_mcp_adapter_validate_protocol_data(mcp_adapter):
    """Test validation of MCP protocol data."""
    # Valid MCP protocol data
    valid_data = {
        "schema_version": "1.0.0",
        "context_specifications": [
            {
                "context_type": "document",
                "version": "1.0.0",
                "description": "Document context for model reasoning",
                "schema": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Document content"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["text", "markdown", "html", "pdf"],
                            "default": "text",
                            "description": "Document format"
                        }
                    }
                },
                "max_tokens": 100000
            }
        ],
        "document_types": ["text", "markdown", "html", "pdf"],
        "token_limit": 100000,
        "metadata": {
            "provider": "anthropic",
            "description": "Model Context Protocol implementation"
        }
    }
    
    # This should not raise an exception
    mcp_adapter.validate_protocol_data(valid_data)
    
    # Invalid data (missing required field)
    invalid_data = {
        "schema_version": "1.0.0",
        # Missing context_specifications
        "document_types": ["text", "markdown"]
    }
    
    with pytest.raises(ValueError):
        mcp_adapter.validate_protocol_data(invalid_data)
    
    # Invalid specification (missing required field)
    invalid_spec_data = {
        "schema_version": "1.0.0",
        "context_specifications": [
            {
                "context_type": "document",
                "version": "1.0.0",
                # Missing description
                "schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }
    
    with pytest.raises(ValueError):
        mcp_adapter.validate_protocol_data(invalid_spec_data)

def test_mcp_adapter_parse_protocol_data(mcp_adapter):
    """Test parsing of MCP protocol data."""
    # MCP protocol data
    mcp_data = {
        "schema_version": "1.0.0",
        "context_specifications": [
            {
                "context_type": "document",
                "version": "1.0.0",
                "description": "Document context for model reasoning",
                "schema": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string"
                        }
                    }
                },
                "max_tokens": 100000
            },
            {
                "context_type": "system_prompt",
                "version": "1.0.0",
                "description": "System prompt for model behavior",
                "schema": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string"
                        }
                    }
                },
                "max_tokens": 10000
            }
        ],
        "document_types": ["text", "markdown", "html", "pdf"],
        "token_limit": 100000,
        "metadata": {
            "provider": "anthropic",
            "model": "claude-3"
        }
    }
    
    # Parse data
    parsed_data = mcp_adapter.parse_protocol_data(mcp_data)
    
    # Verify parsed data
    assert parsed_data["protocol"] == "mcp"
    assert parsed_data["schema_version"] == "1.0.0"
    assert len(parsed_data["capabilities"]) == 2
    assert parsed_data["capabilities"][0]["name"] == "document"
    assert parsed_data["capabilities"][0]["version"] == "1.0.0"
    assert "schema" in parsed_data["capabilities"][0]
    assert parsed_data["capabilities"][0]["max_tokens"] == 100000
    assert parsed_data["capabilities"][1]["name"] == "system_prompt"
    assert len(parsed_data["document_types"]) == 4
    assert parsed_data["token_limit"] == 100000
    assert parsed_data["metadata"]["provider"] == "anthropic"
    assert parsed_data["metadata"]["model"] == "claude-3"

def test_mcp_adapter_format_protocol_data(mcp_adapter):
    """Test formatting of standard data to MCP protocol format."""
    # Standard data
    standard_data = {
        "protocol": "mcp",
        "schema_version": "1.0.0",
        "capabilities": [
            {
                "name": "document",
                "version": "1.0.0",
                "description": "Document context for model reasoning",
                "schema": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string"
                        }
                    }
                },
                "max_tokens": 100000
            }
        ],
        "document_types": ["text", "markdown", "html", "pdf"],
        "token_limit": 100000,
        "metadata": {
            "provider": "anthropic",
            "model": "claude-3"
        }
    }
    
    # Format data
    formatted_data = mcp_adapter.format_protocol_data(standard_data)
    
    # Verify formatted data
    assert formatted_data["schema_version"] == "1.0.0"
    assert len(formatted_data["context_specifications"]) == 1
    assert formatted_data["context_specifications"][0]["context_type"] == "document"
    assert formatted_data["context_specifications"][0]["version"] == "1.0.0"
    assert formatted_data["context_specifications"][0]["description"] == "Document context for model reasoning"
    assert "schema" in formatted_data["context_specifications"][0]
    assert formatted_data["context_specifications"][0]["max_tokens"] == 100000
    assert len(formatted_data["document_types"]) == 4
    assert formatted_data["token_limit"] == 100000
    assert formatted_data["metadata"]["provider"] == "anthropic"
    assert formatted_data["metadata"]["model"] == "claude-3"
    
    # Invalid protocol
    invalid_data = {
        "protocol": "invalid",  # Not MCP
        "schema_version": "1.0.0",
        "capabilities": []
    }
    
    with pytest.raises(ValueError):
        mcp_adapter.format_protocol_data(invalid_data)

def test_mcp_adapter_get_protocol_name(mcp_adapter):
    """Test getting the protocol name."""
    assert mcp_adapter.get_protocol_name() == "mcp" 
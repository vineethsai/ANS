"""
MCP (Model Context Protocol) adapter for the Agent Name Service.

This adapter implements Anthropic's Model Context Protocol for handling
model contexts and prompts.
"""
from typing import Dict, Any
from jsonschema import validate, ValidationError
from .base import ProtocolAdapter

# JSON Schema for Anthropic's Model Context Protocol data
MCP_SCHEMA = {
    "type": "object",
    "required": ["schema_version", "context_specifications"],
    "properties": {
        "schema_version": {
            "type": "string",
            "description": "Version of the MCP schema"
        },
        "context_specifications": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["context_type", "version", "description", "schema"],
                "properties": {
                    "context_type": {
                        "type": "string",
                        "description": "Type of context"
                    },
                    "version": {
                        "type": "string",
                        "description": "Version of this context type specification"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of this context type"
                    },
                    "schema": {
                        "type": "object",
                        "description": "JSON Schema for this context type"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum number of tokens for this context type"
                    }
                }
            }
        },
        "document_types": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "List of supported document types"
        },
        "token_limit": {
            "type": "integer",
            "description": "Total token limit for the model"
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata",
            "additionalProperties": True
        }
    }
}

class MCPProtocolAdapter(ProtocolAdapter):
    """
    Adapter for Anthropic's Model Context Protocol.
    """
    
    def validate_protocol_data(self, data: Dict[str, Any]) -> None:
        """
        Validate MCP protocol-specific data.
        
        Args:
            data: MCP protocol data to validate
            
        Raises:
            ValueError: If the data is invalid
        """
        try:
            validate(instance=data, schema=MCP_SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Invalid Model Context Protocol data: {e}")

    def parse_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse MCP protocol data into a standard format.
        
        Args:
            data: MCP protocol data to parse
            
        Returns:
            Dict containing parsed data
            
        Raises:
            ValueError: If parsing fails
        """
        # Validate data first
        self.validate_protocol_data(data)

        # Extract capabilities from context specifications
        capabilities = []
        for spec in data["context_specifications"]:
            capability = {
                "name": spec["context_type"],
                "version": spec["version"],
                "description": spec["description"],
                "schema": spec["schema"]
            }
            
            if "max_tokens" in spec:
                capability["max_tokens"] = spec["max_tokens"]
                
            capabilities.append(capability)

        # Convert to standard format
        return {
            "protocol": "mcp",
            "schema_version": data["schema_version"],
            "capabilities": capabilities,
            "document_types": data.get("document_types", []),
            "token_limit": data.get("token_limit"),
            "metadata": data.get("metadata", {})
        }

    def format_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format standard data into MCP protocol format.
        
        Args:
            data: Standard data to format
            
        Returns:
            Dict containing MCP protocol data
            
        Raises:
            ValueError: If formatting fails
        """
        if data["protocol"] != "mcp":
            raise ValueError("Data is not in Model Context Protocol format")

        # Convert capabilities to context specifications
        context_specifications = []
        for capability in data["capabilities"]:
            spec = {
                "context_type": capability["name"],
                "version": capability["version"],
                "description": capability["description"],
                "schema": capability.get("schema", {})
            }
            
            if "max_tokens" in capability:
                spec["max_tokens"] = capability["max_tokens"]
                
            context_specifications.append(spec)

        # Build MCP protocol data
        mcp_data = {
            "schema_version": data.get("schema_version", "1.0.0"),
            "context_specifications": context_specifications
        }
        
        if "document_types" in data:
            mcp_data["document_types"] = data["document_types"]
            
        if "token_limit" in data:
            mcp_data["token_limit"] = data["token_limit"]
            
        if "metadata" in data:
            mcp_data["metadata"] = data["metadata"]
            
        return mcp_data

    def get_protocol_name(self) -> str:
        """
        Get the name of the protocol.
        
        Returns:
            Protocol name
        """
        return "mcp" 
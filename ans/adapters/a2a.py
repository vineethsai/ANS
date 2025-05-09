"""
A2A (agent2agent) protocol adapter for the Agent Name Service.

This adapter implements Google's agent2agent protocol for communication
between AI agents.
"""
from typing import Dict, Any
from jsonschema import validate, ValidationError
from .base import ProtocolAdapter

# JSON Schema for Google's agent2agent protocol data
A2A_SCHEMA = {
    "type": "object",
    "required": ["spec_version", "capabilities", "routing", "security"],
    "properties": {
        "spec_version": {
            "type": "string",
            "description": "Version of the agent2agent specification"
        },
        "capabilities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "version", "description"],
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "description": {"type": "string"},
                    "interface": {
                        "type": "object",
                        "properties": {
                            "inputs": {"type": "object"},
                            "outputs": {"type": "object"}
                        }
                    }
                }
            }
        },
        "routing": {
            "type": "object",
            "required": ["protocol"],
            "properties": {
                "protocol": {
                    "type": "string",
                    "enum": ["http", "grpc", "websocket"]
                },
                "endpoints": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["url", "capability"],
                        "properties": {
                            "url": {"type": "string"},
                            "capability": {"type": "string"}
                        }
                    }
                }
            }
        },
        "security": {
            "type": "object",
            "properties": {
                "authentication": {
                    "type": "string",
                    "enum": ["none", "oauth", "api_key", "jwt"]
                },
                "authorization": {
                    "type": "string",
                    "enum": ["none", "rbac", "capability_based"]
                },
                "encryption": {
                    "type": "string",
                    "enum": ["none", "tls", "mtls"]
                }
            }
        },
        "metadata": {
            "type": "object",
            "additionalProperties": True
        }
    }
}

class A2AProtocolAdapter(ProtocolAdapter):
    """
    Adapter for Google's agent2agent protocol.
    """
    def validate_protocol_data(self, data: Dict[str, Any]) -> None:
        """
        Validate agent2agent protocol-specific data.
        
        Args:
            data: agent2agent protocol data to validate
            
        Raises:
            ValueError: If the data is invalid
        """
        try:
            validate(instance=data, schema=A2A_SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Invalid agent2agent protocol data: {e}")

    def parse_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse agent2agent protocol data into a standard format.
        
        Args:
            data: agent2agent protocol data to parse
            
        Returns:
            Dict containing parsed data
            
        Raises:
            ValueError: If parsing fails
        """
        # Validate data first
        self.validate_protocol_data(data)

        # Convert to standard format
        capabilities = []
        for cap in data["capabilities"]:
            capability = {
                "name": cap["name"],
                "version": cap["version"],
                "description": cap.get("description", "")
            }
            
            if "interface" in cap:
                capability["parameters"] = cap["interface"].get("inputs", {})
                capability["returns"] = cap["interface"].get("outputs", {})
                
            capabilities.append(capability)

        return {
            "protocol": "a2a",
            "spec_version": data["spec_version"],
            "capabilities": capabilities,
            "routing": data["routing"],
            "security": {
                "authentication": data["security"].get("authentication", "none"),
                "authorization": data["security"].get("authorization", "none"),
                "encryption": data["security"].get("encryption", "none")
            },
            "metadata": data.get("metadata", {})
        }

    def format_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format standard data into agent2agent protocol format.
        
        Args:
            data: Standard data to format
            
        Returns:
            Dict containing agent2agent protocol data
            
        Raises:
            ValueError: If formatting fails
        """
        if data["protocol"] != "a2a":
            raise ValueError("Data is not in agent2agent protocol format")

        capabilities = []
        for cap in data["capabilities"]:
            capability = {
                "name": cap["name"],
                "version": cap["version"],
                "description": cap.get("description", "")
            }
            
            if "parameters" in cap or "returns" in cap:
                capability["interface"] = {}
                if "parameters" in cap:
                    capability["interface"]["inputs"] = cap["parameters"]
                if "returns" in cap:
                    capability["interface"]["outputs"] = cap["returns"]
                
            capabilities.append(capability)

        return {
            "spec_version": data.get("spec_version", "1.0.0"),
            "capabilities": capabilities,
            "routing": data["routing"],
            "security": {
                "authentication": data["security"].get("authentication", "none"),
                "authorization": data["security"].get("authorization", "none"),
                "encryption": data["security"].get("encryption", "none")
            },
            "metadata": data.get("metadata", {})
        }

    def get_protocol_name(self) -> str:
        """
        Get the name of the protocol.
        
        Returns:
            Protocol name
        """
        return "a2a" 
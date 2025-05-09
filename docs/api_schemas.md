# API Schemas Documentation

This document describes the JSON schemas used in the Agent Name Service (ANS) API.

## Registration Request

Used to register a new agent with the ANS.

```json
{
  "type": "object",
  "required": ["agent_id", "ans_name", "capabilities", "protocol_extensions", "endpoint", "csr"],
  "properties": {
    "agent_id": {
      "type": "string",
      "description": "Unique identifier for the agent"
    },
    "ans_name": {
      "type": "string",
      "description": "ANS name in the format Protocol://AgentID.Capability.Provider.vVersion,Extension",
      "pattern": "^[^:]+://[^.]+\\.[^.]+\\.[^.]+\\.v[^,]+(?:,.+)?$"
    },
    "capabilities": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of capabilities provided by the agent"
    },
    "protocol_extensions": {
      "type": "object",
      "description": "Protocol-specific metadata",
      "additionalProperties": true
    },
    "endpoint": {
      "type": "string",
      "description": "URL endpoint for the agent",
      "format": "uri"
    },
    "csr": {
      "type": "string",
      "description": "PEM-encoded Certificate Signing Request"
    }
  }
}
```

## Registration Response

Returned after successfully registering an agent.

```json
{
  "type": "object",
  "required": ["status", "agent", "certificate"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success"]
    },
    "agent": {
      "type": "object",
      "required": ["agent_id", "ans_name", "capabilities", "protocol_extensions", "endpoint", "certificate", "registration_time"],
      "properties": {
        "agent_id": {
          "type": "string"
        },
        "ans_name": {
          "type": "string"
        },
        "capabilities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "protocol_extensions": {
          "type": "object"
        },
        "endpoint": {
          "type": "string"
        },
        "certificate": {
          "type": "string"
        },
        "registration_time": {
          "type": "string",
          "format": "date-time"
        },
        "last_renewal_time": {
          "type": ["string", "null"],
          "format": "date-time"
        },
        "is_active": {
          "type": "boolean"
        }
      }
    },
    "certificate": {
      "type": "string",
      "description": "PEM-encoded certificate issued by the ANS CA"
    }
  }
}
```

## Renewal Request

Used to renew an agent's registration.

```json
{
  "type": "object",
  "required": ["agent_id", "csr"],
  "properties": {
    "agent_id": {
      "type": "string",
      "description": "ID of the agent to renew"
    },
    "csr": {
      "type": "string",
      "description": "PEM-encoded Certificate Signing Request"
    }
  }
}
```

## Renewal Response

Returned after successfully renewing an agent's registration.

```json
{
  "type": "object",
  "required": ["status", "agent_id", "certificate"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success"]
    },
    "agent_id": {
      "type": "string"
    },
    "certificate": {
      "type": "string",
      "description": "PEM-encoded certificate issued by the ANS CA"
    }
  }
}
```

## Revocation Request

Used to revoke an agent's registration.

```json
{
  "type": "object",
  "required": ["agent_id"],
  "properties": {
    "agent_id": {
      "type": "string",
      "description": "ID of the agent to revoke"
    },
    "reason": {
      "type": "string",
      "description": "Optional reason for revocation"
    }
  }
}
```

## Resolution Request

Used to resolve an ANS name to an agent endpoint.

```json
{
  "type": "object",
  "required": ["ans_name"],
  "properties": {
    "ans_name": {
      "type": "string",
      "description": "ANS name to resolve"
    },
    "version_range": {
      "type": "string",
      "description": "Optional version range (e.g., '^1.0.0', '>=2.0.0')"
    }
  }
}
```

## Endpoint Record Response

Returned after successfully resolving an ANS name.

```json
{
  "type": "object",
  "required": ["data", "signature", "registry_certificate"],
  "properties": {
    "data": {
      "type": "object",
      "required": ["agent_id", "ans_name", "endpoint", "capabilities", "protocol_extensions", "certificate", "is_active"],
      "properties": {
        "agent_id": {
          "type": "string"
        },
        "ans_name": {
          "type": "string"
        },
        "endpoint": {
          "type": "string"
        },
        "capabilities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "protocol_extensions": {
          "type": "object"
        },
        "certificate": {
          "type": "string"
        },
        "is_active": {
          "type": "boolean"
        }
      }
    },
    "signature": {
      "type": "string",
      "description": "Hex-encoded signature of the data field, signed by the registry's private key"
    },
    "registry_certificate": {
      "type": "string",
      "description": "PEM-encoded certificate of the registry"
    }
  }
}
```

## Agent Listing Response

Returned when listing agents matching criteria.

```json
{
  "type": "object",
  "required": ["agents"],
  "properties": {
    "agents": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["agent_id", "ans_name", "capabilities", "protocol_extensions", "endpoint", "certificate", "registration_time", "is_active"],
        "properties": {
          "agent_id": {
            "type": "string"
          },
          "ans_name": {
            "type": "string"
          },
          "capabilities": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "protocol_extensions": {
            "type": "object"
          },
          "endpoint": {
            "type": "string"
          },
          "certificate": {
            "type": "string"
          },
          "registration_time": {
            "type": "string",
            "format": "date-time"
          },
          "last_renewal_time": {
            "type": ["string", "null"],
            "format": "date-time"
          },
          "is_active": {
            "type": "boolean"
          }
        }
      }
    }
  }
}
```

## Protocol-Specific Extension Schemas

### A2A Protocol Extensions

Used for Google's agent2agent protocol.

```json
{
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
          "name": {
            "type": "string",
            "description": "Name of the capability"
          },
          "version": {
            "type": "string",
            "description": "Version of the capability"
          },
          "description": {
            "type": "string",
            "description": "Description of the capability"
          },
          "interface": {
            "type": "object",
            "properties": {
              "inputs": {
                "type": "object",
                "description": "Input schema for the capability"
              },
              "outputs": {
                "type": "object",
                "description": "Output schema for the capability"
              }
            }
          }
        }
      }
    },
    "routing": {
      "type": "object",
      "properties": {
        "protocol": {
          "type": "string",
          "enum": ["http", "grpc", "websocket"],
          "description": "Communication protocol used by the agent"
        },
        "endpoints": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "url": {
                "type": "string",
                "description": "URL for the capability endpoint"
              },
              "capability": {
                "type": "string",
                "description": "Capability name this endpoint serves"
              }
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
          "enum": ["none", "oauth", "api_key", "jwt"],
          "description": "Authentication method"
        },
        "authorization": {
          "type": "string",
          "enum": ["none", "rbac", "capability_based"],
          "description": "Authorization method"
        },
        "encryption": {
          "type": "string",
          "enum": ["none", "tls", "mtls"],
          "description": "Encryption method"
        }
      }
    },
    "metadata": {
      "type": "object",
      "description": "Additional metadata",
      "additionalProperties": true
    }
  }
}
```

### MCP Protocol Extensions

Used for Anthropic's Model Context Protocol.

```json
{
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
            "description": "Type of context (e.g., document, system_prompt)"
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
      },
      "description": "Specifications for different types of context"
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
      "description": "Additional metadata about the model context capabilities",
      "additionalProperties": true
    }
  }
}
```

### Error Response

Returned when an error occurs.

```json
{
  "type": "object",
  "required": ["detail"],
  "properties": {
    "detail": {
      "type": "string",
      "description": "Error description"
    }
  }
}
``` 
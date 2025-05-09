# Agent Name Service (ANS)

A robust and secure implementation of the Agent Name Service, providing a universal directory for AI agents.

## Overview

The Agent Name Service (ANS) is a directory service for AI agents that enables:

1. **Structured agent naming** with protocol support
2. **Secure agent registration and discovery**
3. **Public Key Infrastructure (PKI)** integration
4. **Protocol adapters** for different agent communication protocols
5. **Version negotiation** for agent compatibility

ANS provides a way for agents to register their capabilities and for other agents to discover and securely communicate with them.

## Supported Protocols

ANS is designed to support multiple agent communication protocols:

1. **A2A (Agent2Agent)**: Google's protocol for agent interoperability, enabling agents to discover and communicate with each other in a standardized way.
2. **MCP (Model Context Protocol)**: Anthropic's protocol for model-tool interaction, facilitating integration between foundation models and tools.

The protocol adapter layer allows ANS to be extended to support additional protocols in the future.

## Architecture

The ANS consists of several core components:

### 1. ANSName

The structured naming system for agents follows the format:
```
Protocol://AgentID.agentCapability.Provider.vVersion,Extension
```

For example:
```
a2a://chatbot.conversation.openai.v1.0.0
```

### 2. Certificate Authority (CA)

The CA issues and manages certificates for agents and the ANS registry itself. It:
- Issues certificates based on Certificate Signing Requests (CSRs)
- Maintains a list of revoked certificates
- Verifies certificate chains

### 3. Registration Authority (RA)

The RA manages agent registration by:
- Validating registration requests
- Forwarding CSRs to the CA
- Enforcing naming policies

### 4. Agent Registry

The registry maintains a database of registered agents and handles:
- Storing agent information
- Resolving ANS names to endpoints
- Signing endpoint records
- Finding agents by criteria (protocol, capability, provider)

### 5. Protocol Adapters

Protocol adapters provide a way to handle different agent communication protocols:
- A2A (Agent-to-Agent): For direct agent communication
- MCP (Model Capabilities Protocol): For ML model capabilities

## Features

- **Structured agent naming** with protocol support
- **Secure agent registration and resolution**
- **Public Key Infrastructure (PKI)** integration
- **Protocol adapter layer** for different agent protocols
- **RESTful API** interface
- **Persistent storage** with SQLite (extensible to other databases)
- **Version negotiation** for backward compatibility
- **Certificate revocation** for security

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ans.git
   cd ans
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the ANS Server

1. Initialize the database:
   ```bash
   python -m ans.db.init_db
   ```

2. Start the API server:
   ```bash
   python run_ans.py
   ```

3. Access the API documentation at `http://localhost:8000/docs`

### Example: Registering an Agent

```python
from examples.client import register_agent, create_csr, generate_key_pair

# Generate key pair and CSR
private_key, public_key = generate_key_pair()
csr = create_csr("my-agent", private_key)

# Register agent
response = register_agent(
    agent_id="my-agent",
    ans_name="a2a://my-agent.chat.example.v1.0.0",
    capabilities=["chat", "question-answering"],
    protocol_extensions={
        "message_format": "json",
        "supported_actions": [
            {
                "name": "send_message",
                "version": "1.0.0"
            }
        ],
        "security_level": "basic"
    },
    endpoint="https://my-agent.example.com/api",
    csr_pem=csr
)

# Save certificate
with open("my-agent.cert", "w") as f:
    f.write(response["certificate"])
```

### Example: Resolving an Agent

```python
from examples.client import resolve_agent, verify_endpoint_record

# Resolve agent
endpoint_record = resolve_agent("a2a://my-agent.chat.example.v1.0.0")

# Verify endpoint record signature
if verify_endpoint_record(endpoint_record):
    # Use the agent's endpoint
    endpoint = endpoint_record["data"]["endpoint"]
    print(f"Agent endpoint: {endpoint}")
else:
    print("Invalid endpoint record signature")
```

### Example: Filtering Agents by Protocol

```python
import requests

# Get all agents using the A2A protocol
response = requests.get("http://localhost:8000/agents?protocol=a2a")
a2a_agents = response.json()["agents"]

# Get all agents using the MCP protocol
response = requests.get("http://localhost:8000/agents?protocol=mcp")
mcp_agents = response.json()["agents"]
```

## Project Structure

```
ans/
├── core/           # Core ANS components
│   ├── agent.py           # Agent representation
│   ├── ans_name.py        # ANS name handling
│   ├── agent_registry.py  # Agent registry
│   └── registration_authority.py # Registration authority
├── crypto/         # Cryptographic operations
│   ├── certificate.py       # Certificate operations
│   └── certificate_authority.py # Certificate authority
├── db/            # Database models and operations
│   ├── models.py    # SQLAlchemy models
│   └── init_db.py   # Database initialization
├── api/           # API endpoints
│   └── main.py     # FastAPI application
├── schemas/       # JSON schemas
├── adapters/      # Protocol adapters
│   ├── base.py     # Protocol adapter base class
│   └── a2a.py      # Agent-to-Agent protocol adapter
│   └── mcp.py      # Model Context Protocol adapter
└── tests/         # Test suite
    ├── test_ans.py          # Basic ANS tests
    ├── test_crypto.py       # Cryptography tests
    ├── test_protocol_adapters.py # Protocol adapter tests
    └── test_resolution.py   # ANS resolution tests
```

## API Endpoints

- `POST /register`: Register a new agent
- `POST /renew`: Renew an agent's registration
- `POST /revoke`: Revoke an agent's registration
- `POST /resolve`: Resolve an agent's ANS name to its endpoint
- `GET /agents`: List agents matching criteria
- `GET /health`: Health check endpoint

## Testing

Run the test suite:

```bash
pytest
```

Run specific tests:

```bash
pytest ans/tests/test_crypto.py  # Run cryptography tests
pytest ans/tests/test_protocol_adapters.py  # Run protocol adapter tests
```

## Security Considerations

The ANS implements several security measures while maintaining public access like DNS:

1. **Certificate-based Authentication for Agents**
   - All agents must have valid certificates issued by the ANS CA
   - Certificates are verified during registration and resolution
   - This secures the agent identity without restricting public API access

2. **Signed Endpoint Records**
   - Endpoint records are signed by the ANS registry
   - Signatures are verified by clients to prevent tampering
   - Ensures data integrity across the network

3. **Certificate Revocation**
   - Compromised certificates can be revoked
   - Revocation status is checked during certificate validation
   - Provides ability to remove compromised agents

4. **Input Validation**
   - All API inputs are validated against JSON schemas
   - ANS names are strictly validated for format compliance
   - Prevents injection attacks and malformed data

5. **Rate Limiting**
   - Configurable rate limits per endpoint
   - Prevents abuse while allowing legitimate usage
   - Different limits for different operations based on resource impact

6. **Comprehensive Audit Logging**
   - All API access is logged for auditing purposes
   - Certificate operations (issuance, renewal, revocation) are tracked
   - Security events and errors are documented for incident response

7. **Secure Transport**
   - HTTPS should be used in production
   - TLS configuration should follow best practices
   - Prevents man-in-the-middle attacks

## Development

- Format code: `black ans/`
- Type checking: `mypy ans/`
- Run linting: `pylint ans/`

## License

MIT License
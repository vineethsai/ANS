# ANS Design Document

## Architecture and Design Principles

The Agent Name Service (ANS) is designed with several key principles:

1. **Security-First Approach**
2. **Protocol Adaptability**
3. **Semantic Versioning**
4. **Scalability**
5. **Decentralization Preparation**

### Core Components

![ANS Architecture](architecture.png)

#### ANSName

The structured naming system forms the foundation of ANS, providing:

- **Structured Hierarchy**: Protocol://AgentID.Capability.Provider.vVersion,Extension
- **Semantic Interpretation**: Each part has specific meaning
- **Version Specification**: Explicit version information for compatibility

Example:
```
a2a://chatbot-1.conversation.openai.v1.2.3
```

This represents:
- Protocol: a2a (Google's agent2agent protocol)
- Agent ID: chatbot-1
- Capability: conversation
- Provider: openai
- Version: 1.2.3

#### Certificate Authority (CA)

The CA is responsible for:

- **Issuing Certificates**: Processing CSRs and issuing signed certificates
- **Certificate Revocation**: Maintaining list of revoked certificates
- **Chain Verification**: Verifying certificate chains during validation

The CA uses X.509 certificates with RSA keys, leveraging the cryptography library for all operations.

#### Registration Authority (RA)

The RA acts as a gatekeeper for agent registration:

- **Request Validation**: Validates registration requests against schemas
- **Policy Enforcement**: Ensures naming conventions are followed
- **CA Interface**: Forwards valid CSRs to the CA for certificate issuance

#### Agent Registry

The registry serves as the central database for agents:

- **Storage**: Persistent storage for agent information
- **Resolution**: Primary mechanism for resolving ANS names to endpoints
- **Querying**: Allows searching for agents by various criteria

### Agent Resolution Flow

1. Client requests resolution of an ANS name
2. Registry parses the ANS name
3. Registry searches for agents matching the criteria
4. If version range is provided, registry performs version negotiation
5. Registry creates and signs an endpoint record
6. Client verifies the endpoint record's signature
7. Client verifies the registry's certificate chain

### Protocol Adapter Architecture

Protocol adapters provide a layer of abstraction for different agent protocols:

- **Validation**: Protocol-specific validation of registration data
- **Parsing**: Converting protocol-specific data to standard format
- **Formatting**: Converting standard data to protocol-specific format

The adapter architecture allows:
- Easy addition of new protocols
- Protocol-specific validation and handling
- Standardized interface regardless of protocol

Currently supported protocols include:
- **a2a**: Google's agent2agent protocol for agent communication
- **MCP**: Anthropic's Model Context Protocol for handling model contexts

### Version Negotiation

ANS uses [Semantic Versioning](https://semver.org/) for compatibility checks:

- **Major Version**: Incompatible API changes
- **Minor Version**: Backwards-compatible functionality
- **Patch Version**: Backwards-compatible bug fixes

Resolution requests can specify version ranges:
- `^1.0.0`: Any version compatible with 1.0.0 (1.0.0 to <2.0.0)
- `~1.2.0`: Any version compatible with 1.2.0 (1.2.0 to <1.3.0)
- `>=1.0.0`: Any version greater than or equal to 1.0.0

### Security Architecture

ANS employs multiple layers of security:

1. **Certificate-Based Authentication**:
   - Agents must have valid certificates issued by the ANS CA
   - Certificates contain the agent_id as the subject common name
   - All certificates are X.509 with RSA keys

2. **Endpoint Record Signing**:
   - All endpoint records are signed by the registry
   - Clients verify signatures before trusting endpoint information
   - This prevents tampering with endpoint data

3. **Certificate Revocation**:
   - Compromised certificates can be revoked
   - Revocation status is checked during validation
   - Fully implemented Online Certificate Status Protocol (OCSP)
   - Real-time certificate validation with caching for performance

4. **Input Validation**:
   - All API inputs are validated against JSON schemas
   - ANS names are strictly validated for format compliance
   - Protocol-specific validation occurs through adapters

### Database Architecture

The current implementation uses SQLite for simplicity but is designed for scalability:

- **ORM**: SQLAlchemy provides database abstraction
- **Models**: Clear separation between database models and domain entities
- **Migration Path**: Can be extended to other databases (PostgreSQL, MongoDB, etc.)

### API Design

The REST API follows standard conventions:

- **Resource-Based**: Endpoints represent resources (agents, certificates)
- **JSON**: All requests and responses use JSON
- **Stateless**: Each request contains all information needed for processing
- **HTTPS**: Production deployments should use HTTPS/mTLS

### Scalability Considerations

While the current implementation is single-instance, several paths to scalability exist:

1. **Database Scaling**:
   - Move from SQLite to a distributed database
   - Consider sharding strategies for agent data

2. **Service Scaling**:
   - Separate CA, RA, and Registry services
   - Use load balancers for API endpoints

3. **Caching**:
   - Add caching layer for frequently resolved agents
   - Use distributed cache for multi-instance deployments

4. **Asynchronous Processing**:
   - Make registration process asynchronous
   - Use message queues for communication between components

### OCSP Implementation

The ANS implements the Online Certificate Status Protocol (OCSP) for real-time certificate validation:

1. **OCSP Responder**:
   - Provides real-time certificate status information
   - Generates signed OCSP responses containing:
     - Certificate ID (issuer and serial number)
     - Certificate status (good, revoked, unknown)
     - Response generation time and validity period
   - Implements efficient caching to reduce overhead

2. **OCSP Client**:
   - Verifies certificate status during validation
   - Caches results to reduce request volume
   - Falls back to traditional verification when OCSP is unavailable

3. **Integration Points**:
   - Agent registration: Verifies certificate validity
   - Agent resolution: Ensures endpoints come from valid agents
   - Revocation: Updates status for immediate invalidation
   - API endpoint: Allows direct OCSP queries

4. **Performance Considerations**:
   - Response caching (default 1 hour for responder, 10 minutes for client)
   - Efficient database queries for revocation status
   - Graceful fallback to traditional methods

5. **Security Features**:
   - Signed responses prevent tampering
   - Timestamps prevent replay attacks
   - Complete audit trail of all status checks

### Future Directions

1. **Federation**:
   - Multiple registry instances sharing agent information
   - Decentralized resolution across multiple organizations

2. **Advanced Protocol Adapters**:
   - Enhanced Model Context Protocol (MCP) implementation for Anthropic's models
   - More comprehensive agent2agent (a2a) implementation for Google's protocol
   - New protocols as they emerge

3. **Advanced Security**:
   - Fine-grained authorization policies
   - Distributed OCSP responders for high availability

4. **Metrics and Monitoring**:
   - Telemetry for resolution and registration operations
   - Health monitoring and alerting 
"""
Registration Authority module for handling agent registration requests.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import json
from jsonschema import validate, ValidationError
from .agent import Agent
from .ans_name import ANSName
from ..crypto.certificate import Certificate
from ..crypto.certificate_authority import CertificateAuthority

# JSON Schema for registration requests
REGISTRATION_SCHEMA = {
    "type": "object",
    "required": ["agent_id", "ans_name", "capabilities", "protocol_extensions", "endpoint", "csr"],
    "properties": {
        "agent_id": {"type": "string"},
        "ans_name": {"type": "string"},
        "capabilities": {
            "type": "array",
            "items": {"type": "string"}
        },
        "protocol_extensions": {
            "type": "object",
            "additionalProperties": True
        },
        "endpoint": {"type": "string"},
        "csr": {"type": "string"}  # PEM-encoded CSR
    }
}

class RegistrationAuthority:
    """
    Handles agent registration requests and certificate issuance.
    """
    def __init__(self, ca: CertificateAuthority):
        """
        Initialize the Registration Authority.
        
        Args:
            ca: Certificate Authority instance
        """
        self.ca = ca

    def validate_registration_request(self, request: Dict[str, Any]) -> None:
        """
        Validate a registration request against the schema.
        
        Args:
            request: Registration request to validate
            
        Raises:
            ValidationError: If the request is invalid
        """
        try:
            validate(instance=request, schema=REGISTRATION_SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Invalid registration request: {e}")

    def process_registration_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a registration request and issue a certificate.
        
        Args:
            request: Registration request to process
            
        Returns:
            Dict containing registration response
            
        Raises:
            ValueError: If registration fails
        """
        # Validate request
        try:
            self.validate_registration_request(request)
        except ValueError as e:
            raise

        # Parse ANS name
        try:
            ans_name = ANSName.parse(request["ans_name"])
        except ValueError as e:
            raise ValueError(f"Invalid ANS name: {e}")

        # Verify agent_id matches ANS name
        if request["agent_id"] != ans_name.agent_id:
            error_msg = f"Agent ID '{request['agent_id']}' must match the one in ANS name '{ans_name.agent_id}'"
            raise ValueError(error_msg)

        # Issue certificate
        try:
            cert = self.ca.issue_certificate(request["csr"].encode())
        except Exception as e:
            raise ValueError(f"Certificate issuance failed: {e}")

        # Create agent
        agent = Agent(
            agent_id=request["agent_id"],
            ans_name=ans_name,
            capabilities=request["capabilities"],
            protocol_extensions=request["protocol_extensions"],
            endpoint=request["endpoint"],
            certificate=cert.get_pem().decode()
        )

        return {
            "status": "success",
            "agent": agent.to_dict(),
            "certificate": cert.get_pem().decode()
        }

    def process_renewal_request(self, agent_id: str, csr: str) -> Dict[str, Any]:
        """
        Process a certificate renewal request.
        
        Args:
            agent_id: ID of the agent requesting renewal
            csr: PEM-encoded Certificate Signing Request
            
        Returns:
            Dict containing renewal response
            
        Raises:
            ValueError: If renewal fails
        """
        # Issue new certificate
        try:
            cert = self.ca.issue_certificate(csr.encode())
        except ValueError as e:
            raise ValueError(f"Certificate issuance failed: {e}")

        return {
            "status": "success",
            "agent_id": agent_id,
            "certificate": cert.get_pem().decode()
        }

    def process_revocation_request(self, agent_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a certificate revocation request.
        
        Args:
            agent_id: ID of the agent to revoke
            reason: Optional reason for revocation
            
        Returns:
            Dict containing revocation response
            
        Raises:
            ValueError: If revocation fails
        """
        # TODO: Implement certificate revocation
        # This would involve:
        # 1. Finding the agent's certificate
        # 2. Revoking it in the CA
        # 3. Updating the agent's status
        pass 
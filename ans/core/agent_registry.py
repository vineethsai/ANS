"""
Agent Registry module for managing agent registration and resolution.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import json
from sqlalchemy.orm import Session
from ..db.models import AgentModel, RevokedCertificateModel
from .agent import Agent
from .ans_name import ANSName
from ..crypto.certificate import Certificate
from ..crypto.certificate_authority import CertificateAuthority

class AgentRegistry:
    """
    Manages agent registration and resolution in the Agent Name Service.
    """
    def __init__(self, ca: CertificateAuthority, db_session: Session):
        """
        Initialize the Agent Registry.
        
        Args:
            ca: Certificate Authority instance
            db_session: Database session
        """
        self.ca = ca
        self.db = db_session
        self._registry_cert: Optional[Certificate] = None
        self._registry_private_key: Optional[bytes] = None

    def initialize_registry(self, subject_name: str) -> None:
        """
        Initialize the registry with its own certificate.
        
        Args:
            subject_name: Subject name for the registry's certificate
        """
        self._registry_cert, self._registry_private_key = Certificate.generate_self_signed_cert(
            subject_name=f"ANS Registry - {subject_name}"
        )

    def register_agent(self, agent: Agent) -> None:
        """
        Register a new agent.
        
        Args:
            agent: Agent to register
            
        Raises:
            ValueError: If registration fails
        """
        try:
            # Check if agent ID already exists
            existing_agent = self.db.query(AgentModel).filter_by(agent_id=agent.agent_id).first()
            if existing_agent:
                raise ValueError(f"Agent ID {agent.agent_id} already registered")

            # Check if ANS name already exists
            existing_ans = self.db.query(AgentModel).filter_by(ans_name=str(agent.ans_name)).first()
            if existing_ans:
                raise ValueError(f"ANS name {agent.ans_name} already registered")

            # Verify agent's certificate
            try:
                agent_cert = Certificate(agent.certificate.encode())
                
                if not agent_cert.is_valid():
                    raise ValueError("Agent certificate is not valid (date validation failed)")
                
                if not self.ca.verify_certificate_chain(agent_cert):
                    raise ValueError("Invalid agent certificate (failed chain verification)")
            except Exception as e:
                raise ValueError(f"Invalid agent certificate: {e}")

            # Create database record
            agent_model = AgentModel(
                agent_id=agent.agent_id,
                ans_name=str(agent.ans_name),
                capabilities=agent.capabilities,
                protocol_extensions=agent.protocol_extensions,
                endpoint=agent.endpoint,
                certificate=agent.certificate,
                registration_time=agent.registration_time,
                last_renewal_time=agent.last_renewal_time,
                is_active=agent.is_active
            )

            self.db.add(agent_model)
            self.db.commit()
        except Exception as e:
            raise

    def renew_agent(self, agent_id: str) -> Agent:
        """
        Renew an agent's registration.
        
        Args:
            agent_id: ID of the agent to renew
            
        Returns:
            Agent: The renewed Agent object
            
        Raises:
            ValueError: If agent not found or renewal fails
        """
        agent_model = self.db.query(AgentModel).filter_by(agent_id=agent_id).first()
        if not agent_model:
            raise ValueError(f"Agent {agent_id} not found")

        agent_model.last_renewal_time = datetime.utcnow()
        agent_model.is_active = True
        self.db.commit()
        
        # Convert the model back to an Agent object
        try:
            ans_name = ANSName.parse(agent_model.ans_name)
            agent = Agent(
                agent_id=agent_model.agent_id,
                ans_name=ans_name,
                capabilities=agent_model.capabilities,
                protocol_extensions=agent_model.protocol_extensions,
                endpoint=agent_model.endpoint,
                certificate=agent_model.certificate,
                registration_time=agent_model.registration_time,
                last_renewal_time=agent_model.last_renewal_time,
                is_active=agent_model.is_active
            )
            return agent
        except Exception as e:
            raise ValueError(f"Error creating Agent object: {e}")

    def deactivate_agent(self, agent_id: str) -> None:
        """
        Deactivate an agent.
        
        Args:
            agent_id: ID of the agent to deactivate
            
        Raises:
            ValueError: If agent not found
        """
        agent_model = self.db.query(AgentModel).filter_by(agent_id=agent_id).first()
        if not agent_model:
            raise ValueError(f"Agent {agent_id} not found")

        agent_model.is_active = False
        self.db.commit()

    def resolve_ans_name(self, ans_name: str, version_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve an ANS name to an agent's endpoint record.
        
        Args:
            ans_name: ANS name to resolve
            version_range: Optional version range to match
            
        Returns:
            Dict containing the endpoint record
            
        Raises:
            ValueError: If resolution fails
        """
        try:
            # Parse ANS name
            try:
                name = ANSName.parse(ans_name)
            except ValueError as e:
                raise ValueError(f"Invalid ANS name: {e}")

            # Query database
            query = self.db.query(AgentModel).filter(
                AgentModel.ans_name.like(f"{name.protocol}://{name.agent_id}.{name.capability}.{name.provider}.v%")
            )

            if version_range:
                # TODO: Implement version range matching
                pass

            agent_model = query.filter_by(is_active=True).first()
            if not agent_model:
                raise ValueError(f"No active agent found for {ans_name}")

            # Create endpoint record
            endpoint_record = {
                "agent_id": agent_model.agent_id,
                "ans_name": agent_model.ans_name,
                "endpoint": agent_model.endpoint,
                "capabilities": agent_model.capabilities,
                "protocol_extensions": agent_model.protocol_extensions,
                "certificate": agent_model.certificate,
                "is_active": agent_model.is_active
            }

            # Sign the endpoint record
            if not self._registry_cert or not self._registry_private_key:
                raise ValueError("Registry not initialized")

            # Convert record to bytes for signing
            record_bytes = json.dumps(endpoint_record, sort_keys=True).encode()
            
            # Sign the record
            signature = self._registry_cert.sign_data(record_bytes)

            # Convert binary signature to hex string for JSON serialization
            signature_hex = signature.hex()

            return {
                "data": endpoint_record,
                "signature": signature_hex,
                "registry_certificate": self._registry_cert.get_pem().decode()
            }
        except Exception as e:
            raise

    def find_agents_by_criteria(self, 
                              protocol: Optional[str] = None,
                              capability: Optional[str] = None,
                              provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find agents matching the given criteria.
        
        Args:
            protocol: Optional protocol to match
            capability: Optional capability to match
            provider: Optional provider to match
            
        Returns:
            List of matching agent records
        """
        query = self.db.query(AgentModel).filter_by(is_active=True)

        if protocol:
            query = query.filter(AgentModel.ans_name.like(f"{protocol}://%"))
        if capability:
            query = query.filter(AgentModel.ans_name.like(f"%.{capability}.%"))
        if provider:
            query = query.filter(AgentModel.ans_name.like(f"%.{provider}.v%"))

        return [agent.to_dict() for agent in query.all()]

    def verify_endpoint_record(self, record: Dict[str, Any]) -> bool:
        """
        Verify an endpoint record's signature.
        
        Args:
            record: Endpoint record to verify
            
        Returns:
            bool: True if the record is valid
        """
        try:
            # Extract components
            data = record["data"]
            signature = record["signature"]
            registry_cert = Certificate(record["registry_certificate"].encode())

            # Verify registry certificate
            if not self.ca.verify_certificate_chain(registry_cert):
                return False

            # Verify signature
            data_bytes = json.dumps(data, sort_keys=True).encode()
            return registry_cert.verify_signature(data_bytes, signature)
        except Exception:
            return False 
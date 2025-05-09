"""
Agent module for representing agents in the Agent Name Service.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from .ans_name import ANSName

@dataclass
class Agent:
    """
    Represents an agent in the Agent Name Service.
    """
    agent_id: str
    ans_name: ANSName
    capabilities: List[str]
    protocol_extensions: Dict[str, Any]
    endpoint: str
    certificate: str  # PEM-encoded certificate
    registration_time: datetime = field(default_factory=datetime.utcnow)
    last_renewal_time: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        """Validate agent data after initialization."""
        if not self.agent_id:
            raise ValueError("Agent ID cannot be empty")
        
        if not self.endpoint:
            raise ValueError("Endpoint cannot be empty")
        
        if not self.certificate:
            raise ValueError("Certificate cannot be empty")
        
        # Validate ANS name
        self.ans_name.validate()
        
        # Ensure agent_id matches the one in ANS name
        if self.agent_id != self.ans_name.agent_id:
            raise ValueError("Agent ID must match the one in ANS name")

    def renew(self) -> None:
        """Renew the agent's registration."""
        self.last_renewal_time = datetime.utcnow()
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the agent."""
        self.is_active = False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent to a dictionary representation.
        
        Returns:
            Dict containing agent data
        """
        return {
            "agent_id": self.agent_id,
            "ans_name": str(self.ans_name),
            "capabilities": self.capabilities,
            "protocol_extensions": self.protocol_extensions,
            "endpoint": self.endpoint,
            "certificate": self.certificate,
            "registration_time": self.registration_time.isoformat(),
            "last_renewal_time": self.last_renewal_time.isoformat() if self.last_renewal_time else None,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """
        Create an Agent instance from a dictionary.
        
        Args:
            data: Dictionary containing agent data
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        required_fields = ["agent_id", "ans_name", "capabilities", "protocol_extensions", 
                         "endpoint", "certificate"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Parse ANS name
        ans_name = ANSName.parse(data["ans_name"])
        
        # Parse datetime fields
        registration_time = datetime.fromisoformat(data["registration_time"])
        last_renewal_time = (datetime.fromisoformat(data["last_renewal_time"]) 
                           if data.get("last_renewal_time") else None)

        return cls(
            agent_id=data["agent_id"],
            ans_name=ans_name,
            capabilities=data["capabilities"],
            protocol_extensions=data["protocol_extensions"],
            endpoint=data["endpoint"],
            certificate=data["certificate"],
            registration_time=registration_time,
            last_renewal_time=last_renewal_time,
            is_active=data.get("is_active", True)
        )

    def get_endpoint_record(self) -> Dict[str, Any]:
        """
        Get the agent's endpoint record for resolution.
        
        Returns:
            Dict containing the endpoint record
        """
        return {
            "agent_id": self.agent_id,
            "ans_name": str(self.ans_name),
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "protocol_extensions": self.protocol_extensions,
            "certificate": self.certificate,
            "is_active": self.is_active
        } 
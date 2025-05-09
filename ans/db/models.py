"""
Database models for the Agent Name Service.
"""
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class AgentModel(Base):
    """
    SQLAlchemy model for storing agent information.
    """
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    agent_id = Column(String, unique=True, nullable=False)
    ans_name = Column(String, unique=True, nullable=False)
    capabilities = Column(JSON, nullable=False)
    protocol_extensions = Column(JSON, nullable=False)
    endpoint = Column(String, nullable=False)
    certificate = Column(String, nullable=False)  # PEM-encoded certificate
    registration_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_renewal_time = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            Dict containing agent data
        """
        return {
            "agent_id": self.agent_id,
            "ans_name": self.ans_name,
            "capabilities": self.capabilities,
            "protocol_extensions": self.protocol_extensions,
            "endpoint": self.endpoint,
            "certificate": self.certificate,
            "registration_time": self.registration_time.isoformat(),
            "last_renewal_time": self.last_renewal_time.isoformat() if self.last_renewal_time else None,
            "is_active": self.is_active
        }

class RevokedCertificateModel(Base):
    """
    SQLAlchemy model for storing revoked certificates.
    """
    __tablename__ = 'revoked_certificates'

    id = Column(Integer, primary_key=True)
    serial_number = Column(Integer, unique=True, nullable=False)
    revocation_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(String)

def init_db(db_url: str = "sqlite:///ans.db") -> sessionmaker:
    """
    Initialize the database and create tables.
    
    Args:
        db_url: Database URL
        
    Returns:
        Session factory
    """
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine) 
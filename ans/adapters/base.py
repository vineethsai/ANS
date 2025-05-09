"""
Base protocol adapter module for the Agent Name Service.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ProtocolAdapter(ABC):
    """
    Abstract base class for protocol adapters.
    """
    @abstractmethod
    def validate_protocol_data(self, data: Dict[str, Any]) -> None:
        """
        Validate protocol-specific data.
        
        Args:
            data: Protocol-specific data to validate
            
        Raises:
            ValueError: If the data is invalid
        """
        pass

    @abstractmethod
    def parse_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse protocol-specific data into a standard format.
        
        Args:
            data: Protocol-specific data to parse
            
        Returns:
            Dict containing parsed data
            
        Raises:
            ValueError: If parsing fails
        """
        pass

    @abstractmethod
    def format_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format standard data into protocol-specific format.
        
        Args:
            data: Standard data to format
            
        Returns:
            Dict containing formatted data
            
        Raises:
            ValueError: If formatting fails
        """
        pass

    @abstractmethod
    def get_protocol_name(self) -> str:
        """
        Get the name of the protocol.
        
        Returns:
            Protocol name
        """
        pass 
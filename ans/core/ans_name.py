"""
ANSName module for handling structured agent names in the Agent Name Service.
"""
from dataclasses import dataclass
from typing import Optional
import re
import semver
from urllib.parse import urlparse

@dataclass
class ANSName:
    """
    Represents a structured agent name in the format:
    Protocol://AgentID.agentCapability.Provider.vVersion,Extension
    """
    protocol: str
    agent_id: str
    capability: str
    provider: str
    version: str
    extension: Optional[str] = None

    # Regular expression for parsing ANS names
    ANS_NAME_PATTERN = re.compile(
        r'^([^:]+)://([^.]+)\.([^.]+)\.([^.]+)\.v([^,]+)(?:,(.+))?$'
    )

    @classmethod
    def parse(cls, name_str: str) -> 'ANSName':
        """
        Parse an ANS name string into an ANSName object.
        
        Args:
            name_str: The ANS name string to parse
            
        Returns:
            ANSName object
            
        Raises:
            ValueError: If the name string is invalid
        """
        match = cls.ANS_NAME_PATTERN.match(name_str)
        if not match:
            raise ValueError(f"Invalid ANS name format: {name_str}")

        protocol, agent_id, capability, provider, version, extension = match.groups()
        
        # Validate version format
        try:
            semver.VersionInfo.parse(version)
        except ValueError as e:
            raise ValueError(f"Invalid version format: {e}")

        return cls(
            protocol=protocol,
            agent_id=agent_id,
            capability=capability,
            provider=provider,
            version=version,
            extension=extension
        )

    def __str__(self) -> str:
        """Convert the ANSName object to its string representation."""
        base = f"{self.protocol}://{self.agent_id}.{self.capability}.{self.provider}.v{self.version}"
        if self.extension:
            base += f",{self.extension}"
        return base

    def is_compatible_with(self, other: 'ANSName') -> bool:
        """
        Check if this ANS name is compatible with another ANS name.
        
        Args:
            other: Another ANSName object to compare with
            
        Returns:
            bool: True if the names are compatible
        """
        if (self.protocol != other.protocol or
            self.agent_id != other.agent_id or
            self.capability != other.capability or
            self.provider != other.provider):
            return False

        try:
            return semver.VersionInfo.parse(self.version).match(other.version)
        except ValueError:
            return False

    def validate(self) -> bool:
        """
        Validate the ANS name components.
        
        Returns:
            bool: True if the name is valid
            
        Raises:
            ValueError: If any component is invalid
        """
        # Validate protocol
        try:
            parsed = urlparse(f"{self.protocol}://example.com")
            if not parsed.scheme:
                raise ValueError("Invalid protocol format")
        except Exception as e:
            raise ValueError(f"Invalid protocol: {e}")

        # Validate agent_id (alphanumeric with hyphens and underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.agent_id):
            raise ValueError("Invalid agent_id format")

        # Validate capability (alphanumeric with hyphens and underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.capability):
            raise ValueError("Invalid capability format")

        # Validate provider (alphanumeric with hyphens and underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.provider):
            raise ValueError("Invalid provider format")

        # Validate version
        try:
            semver.VersionInfo.parse(self.version)
        except ValueError as e:
            raise ValueError(f"Invalid version format: {e}")

        # Validate extension if present
        if self.extension and not re.match(r'^[a-zA-Z0-9_-]+$', self.extension):
            raise ValueError("Invalid extension format")

        return True 
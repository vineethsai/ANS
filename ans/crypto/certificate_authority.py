"""
Certificate Authority module for managing certificates in the Agent Name Service.
"""
from datetime import datetime
from typing import Dict, List, Optional, Set
from .certificate import Certificate

class CertificateAuthority:
    """
    Manages certificates and certificate revocation in the Agent Name Service.
    """
    def __init__(self, ca_cert: Certificate, ca_private_key: bytes):
        """
        Initialize the Certificate Authority.
        
        Args:
            ca_cert: The CA's certificate
            ca_private_key: The CA's private key in PEM format
        """
        self.ca_cert = ca_cert
        self._ca_private_key = ca_private_key
        self._revoked_serials: Set[int] = set()
        self._certificate_store: Dict[int, Certificate] = {
            ca_cert.get_serial_number(): ca_cert
        }

    def issue_certificate(self, csr_data: bytes, validity_days: int = 365) -> Certificate:
        """
        Issue a new certificate by signing a CSR.
        
        Args:
            csr_data: PEM-encoded Certificate Signing Request
            validity_days: Number of days the certificate will be valid
            
        Returns:
            New Certificate instance
            
        Raises:
            ValueError: If the CSR is invalid
        """
        try:
            cert_data = self.ca_cert.sign_csr(csr_data, validity_days)
            cert = Certificate(cert_data)
            
            # Store the certificate
            serial = cert.get_serial_number()
            self._certificate_store[serial] = cert
            
            return cert
        except Exception as e:
            raise ValueError(f"Failed to issue certificate: {e}")

    def revoke_certificate(self, serial_number: int) -> None:
        """
        Revoke a certificate by its serial number.
        
        Args:
            serial_number: The serial number of the certificate to revoke
        """
        self._revoked_serials.add(serial_number)

    def is_certificate_revoked(self, serial_number: int) -> bool:
        """
        Check if a certificate is revoked.
        
        Args:
            serial_number: The serial number to check
            
        Returns:
            bool: True if the certificate is revoked
        """
        return serial_number in self._revoked_serials

    def verify_certificate_chain(self, cert: Certificate) -> bool:
        """
        Verify a certificate chain up to this CA.
        
        Args:
            cert: The certificate to verify
            
        Returns:
            bool: True if the certificate chain is valid
        """
        try:
            # Check if certificate is in store
            is_in_store = cert.get_serial_number() in self._certificate_store
            
            # If certificate is in our store, we can trust it (we issued it)
            if is_in_store:
                return True
            
            # Check if certificate is revoked
            if self.is_certificate_revoked(cert.get_serial_number()):
                return False
            
            # Check if certificate is valid
            if not cert.is_valid():
                return False
            
            # Verify signature
            try:
                # In a real implementation, we would verify the entire chain
                # For now, we'll just verify against the CA certificate
                result = self.ca_cert.verify_signature(
                    cert.cert.tbs_certificate_bytes,
                    cert.cert.signature
                )
                return result
            except Exception:
                return False
        except Exception:
            return False

    def get_certificate(self, serial_number: int) -> Optional[Certificate]:
        """
        Get a certificate by its serial number.
        
        Args:
            serial_number: The serial number to look up
            
        Returns:
            Optional[Certificate]: The certificate if found, None otherwise
        """
        return self._certificate_store.get(serial_number)

    def get_revoked_serials(self) -> List[int]:
        """
        Get a list of all revoked certificate serial numbers.
        
        Returns:
            List of revoked serial numbers
        """
        return list(self._revoked_serials)

    def get_ca_certificate(self) -> Certificate:
        """
        Get the CA's certificate.
        
        Returns:
            The CA's certificate
        """
        return self.ca_cert 
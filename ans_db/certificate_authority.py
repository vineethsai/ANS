"""
Certificate Authority module for managing certificates in the Agent Name Service.
"""
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
import json
from .certificate import Certificate
from .ocsp import OCSPResponder, OCSPClient, OCSPStatus

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
        self._revoked_serials: Dict[int, Tuple[datetime, Optional[str]]] = {}
        self._certificate_store: Dict[int, Certificate] = {
            ca_cert.get_serial_number(): ca_cert
        }
        self._ocsp_responder: Optional[OCSPResponder] = None
        self._ocsp_client: Optional[OCSPClient] = None

    def set_ocsp_responder(self, registry_cert: Certificate) -> None:
        """
        Set up the OCSP responder.

        Args:
            registry_cert: The registry's certificate for signing OCSP responses
        """
        self._ocsp_responder = OCSPResponder(self.ca_cert, registry_cert)
        self._ocsp_client = OCSPClient(self.ca_cert)

    def issue_certificate(self, csr_data: bytes, validity_days: int = 365) -> bytes:
        """
        Issue a new certificate by signing a CSR.

        Args:
            csr_data: PEM-encoded Certificate Signing Request
            validity_days: Number of days the certificate will be valid

        Returns:
            PEM-encoded certificate data

        Raises:
            ValueError: If the CSR is invalid
        """
        try:
            cert_data = self.ca_cert.sign_csr(csr_data, validity_days)
            cert = Certificate(cert_data)

            # Store the certificate
            serial = cert.get_serial_number()
            self._certificate_store[serial] = cert

            return cert_data
        except Exception as e:
            raise ValueError(f"Failed to issue certificate: {e}")

    def revoke_certificate(self, serial_number: int, reason: Optional[str] = None) -> None:
        """
        Revoke a certificate by its serial number.

        Args:
            serial_number: The serial number of the certificate to revoke
            reason: Optional reason for revocation
        """
        # Record revocation time and reason
        self._revoked_serials[serial_number] = (datetime.utcnow(), reason)

    def is_certificate_revoked(self, serial_number: int) -> bool:
        """
        Check if a certificate is revoked.

        Args:
            serial_number: The serial number to check

        Returns:
            bool: True if the certificate is revoked
        """
        return serial_number in self._revoked_serials

    def get_ocsp_response(self, serial_number: int) -> Dict[str, Any]:
        """
        Get an OCSP response for a certificate.

        Args:
            serial_number: The serial number of the certificate

        Returns:
            Dict containing the OCSP response

        Raises:
            ValueError: If OCSP responder is not set up or serial number is invalid
        """
        if not self._ocsp_responder:
            raise ValueError("OCSP responder not initialized")

        # Convert revoked serials to the format expected by OCSP responder
        revoked_serials = [
            (serial, revocation_time, reason)
            for serial, (revocation_time, reason) in self._revoked_serials.items()
        ]

        # Get OCSP response from responder
        return self._ocsp_responder.get_certificate_status(serial_number, revoked_serials)

    def check_ocsp_status(self, cert: Certificate, ocsp_response: Dict[str, Any]) -> str:
        """
        Check certificate status using OCSP.

        Args:
            cert: The certificate to check
            ocsp_response: OCSP response data

        Returns:
            str: Status (good, revoked, unknown)

        Raises:
            ValueError: If OCSP client is not set up or response is invalid
        """
        if not self._ocsp_client:
            raise ValueError("OCSP client not initialized")

        return self._ocsp_client.check_certificate_status(cert, ocsp_response)

    def verify_certificate_chain(self, cert: Certificate, use_ocsp: bool = False,
                              ocsp_response: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verify a certificate chain up to this CA.

        Args:
            cert: The certificate to verify
            use_ocsp: Whether to use OCSP for verification
            ocsp_response: Optional pre-fetched OCSP response

        Returns:
            bool: True if the certificate chain is valid
        """
        try:
            serial_number = cert.get_serial_number()

            # For OCSP verification
            if use_ocsp and self._ocsp_client:
                # Use provided response or fetch new one
                response = ocsp_response
                if not response:
                    if not self._ocsp_responder:
                        # Fall back to non-OCSP method if no responder
                        return self._verify_certificate_without_ocsp(cert)

                    # Get fresh OCSP response
                    revoked_serials = [
                        (serial, revocation_time, reason)
                        for serial, (revocation_time, reason) in self._revoked_serials.items()
                    ]
                    response = self._ocsp_responder.get_certificate_status(serial_number, revoked_serials)

                # Check certificate status
                status = self._ocsp_client.check_certificate_status(cert, response)
                if status == OCSPStatus.REVOKED:
                    return False
                elif status == OCSPStatus.UNKNOWN:
                    # Fall back to non-OCSP method for unknown status
                    return self._verify_certificate_without_ocsp(cert)

                # For GOOD status, continue with normal verification

            # Check if certificate is revoked using traditional method
            if self.is_certificate_revoked(serial_number):
                return False

            # Continue with basic validation
            return self._verify_certificate_without_ocsp(cert)
        except Exception:
            return False

    def _verify_certificate_without_ocsp(self, cert: Certificate) -> bool:
        """
        Verify a certificate without using OCSP.

        Args:
            cert: The certificate to verify

        Returns:
            bool: True if the certificate is valid
        """
        serial_number = cert.get_serial_number()

        # Check if certificate is in store
        is_in_store = serial_number in self._certificate_store

        # If certificate is in our store, we can trust it (we issued it)
        if is_in_store:
            return True

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

    def get_certificate(self, serial_number: int) -> Optional[Certificate]:
        """
        Get a certificate by its serial number.

        Args:
            serial_number: The serial number to look up

        Returns:
            Optional[Certificate]: The certificate if found, None otherwise
        """
        return self._certificate_store.get(serial_number)

    def get_revoked_serials(self) -> List[Tuple[int, datetime, Optional[str]]]:
        """
        Get a list of all revoked certificate serial numbers with revocation time and reason.

        Returns:
            List of (serial_number, revocation_time, reason) tuples
        """
        return [(serial, time, reason) for serial, (time, reason) in self._revoked_serials.items()]

    def get_ca_certificate(self) -> Certificate:
        """
        Get the CA's certificate.

        Returns:
            The CA's certificate
        """
        return self.ca_cert 
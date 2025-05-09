"""
OCSP (Online Certificate Status Protocol) module for the Agent Name Service.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List
import hashlib
import json
import base64
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from .certificate import Certificate

class OCSPStatus:
    """OCSP status codes."""
    GOOD = "good"
    REVOKED = "revoked"
    UNKNOWN = "unknown"

class OCSPResponder:
    """
    OCSP Responder for checking certificate status in real-time.
    """
    def __init__(self, ca_cert: Certificate, registry_cert: Certificate):
        """
        Initialize the OCSP Responder.
        
        Args:
            ca_cert: The Certificate Authority certificate
            registry_cert: The Registry certificate
        """
        self.ca_cert = ca_cert
        self.registry_cert = registry_cert
        # Cache of responses to avoid regenerating them frequently
        self._response_cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        # Default cache time of 1 hour
        self.cache_time = timedelta(hours=1)

    def generate_response(self, 
                        serial_number: int, 
                        status: str, 
                        revocation_time: Optional[datetime] = None,
                        revocation_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an OCSP response for a certificate.
        
        Args:
            serial_number: The serial number of the certificate
            status: The status of the certificate (good, revoked, unknown)
            revocation_time: When the certificate was revoked (if applicable)
            revocation_reason: Why the certificate was revoked (if applicable)
            
        Returns:
            Dict containing the OCSP response
        """
        # Creation time and validity period
        this_update = datetime.utcnow()
        next_update = this_update + timedelta(hours=1)
        
        # Create the basic response structure
        response = {
            "version": 1,
            "responder_id": self.registry_cert.get_subject_name(),
            "produced_at": this_update.isoformat(),
            "responses": [
                {
                    "cert_id": {
                        "hash_algorithm": "sha256",
                        "issuer_name_hash": self._hash_issuer_name(self.ca_cert),
                        "issuer_key_hash": self._hash_issuer_key(self.ca_cert),
                        "serial_number": str(serial_number)
                    },
                    "cert_status": status,
                    "this_update": this_update.isoformat(),
                    "next_update": next_update.isoformat()
                }
            ]
        }
        
        # Add revocation info if applicable
        if status == OCSPStatus.REVOKED and revocation_time:
            response["responses"][0]["revocation_time"] = revocation_time.isoformat()
            if revocation_reason:
                response["responses"][0]["revocation_reason"] = revocation_reason
        
        # Sign the response
        response_bytes = json.dumps(response, sort_keys=True).encode()
        signature = self.registry_cert.sign_data(response_bytes)
        
        # Complete response with signature
        complete_response = {
            "response": response,
            "signature": signature.hex(),
            "signing_cert": self.registry_cert.get_pem().decode()
        }
        
        # Cache the response
        cache_key = self._get_cache_key(serial_number)
        self._response_cache[cache_key] = (complete_response, datetime.utcnow())
        
        return complete_response
    
    def get_response(self, 
                   serial_number: int, 
                   status: str, 
                   revocation_time: Optional[datetime] = None,
                   revocation_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Get an OCSP response, using cache if available.
        
        Args:
            serial_number: The serial number of the certificate
            status: The status of the certificate (good, revoked, unknown)
            revocation_time: When the certificate was revoked (if applicable)
            revocation_reason: Why the certificate was revoked (if applicable)
            
        Returns:
            Dict containing the OCSP response
        """
        cache_key = self._get_cache_key(serial_number)
        
        # Check cache first
        if cache_key in self._response_cache:
            cached_response, cache_time = self._response_cache[cache_key]
            # If not expired and status hasn't changed from good to revoked
            if (datetime.utcnow() - cache_time < self.cache_time and
                (status == cached_response["response"]["responses"][0]["cert_status"] or 
                 status != OCSPStatus.REVOKED)):
                return cached_response
        
        # Generate new response if not in cache or cache expired
        return self.generate_response(serial_number, status, revocation_time, revocation_reason)
    
    def verify_response(self, response: Dict[str, Any]) -> bool:
        """
        Verify an OCSP response signature.
        
        Args:
            response: The OCSP response to verify
            
        Returns:
            bool: True if the signature is valid
        """
        try:
            # Extract components
            response_data = response["response"]
            signature = bytes.fromhex(response["signature"])
            signing_cert = Certificate(response["signing_cert"].encode())
            
            # Verify signing certificate
            # In a production environment, should verify it's a valid responder cert
            if signing_cert.get_subject_name() != self.registry_cert.get_subject_name():
                return False
            
            # Verify signature
            response_bytes = json.dumps(response_data, sort_keys=True).encode()
            return signing_cert.verify_signature(response_bytes, signature)
        except Exception:
            return False
    
    def get_certificate_status(self, serial_number: int, 
                             revoked_serials: List[Tuple[int, Optional[datetime], Optional[str]]]) -> Dict[str, Any]:
        """
        Get the status of a certificate.
        
        Args:
            serial_number: The serial number of the certificate
            revoked_serials: List of (serial, revocation_time, reason) tuples
            
        Returns:
            OCSP response
        """
        # Check if the certificate is revoked
        for revoked_serial, revocation_time, reason in revoked_serials:
            if revoked_serial == serial_number:
                return self.get_response(
                    serial_number, 
                    OCSPStatus.REVOKED,
                    revocation_time,
                    reason
                )
        
        # If not revoked, return good status
        return self.get_response(serial_number, OCSPStatus.GOOD)
    
    def _hash_issuer_name(self, issuer_cert: Certificate) -> str:
        """Hash the issuer's name for the certificate ID."""
        name_bytes = issuer_cert.cert.subject.public_bytes()
        digest = hashlib.sha256(name_bytes).digest()
        return base64.b64encode(digest).decode()
    
    def _hash_issuer_key(self, issuer_cert: Certificate) -> str:
        """Hash the issuer's public key for the certificate ID."""
        key_bytes = issuer_cert.cert.public_key().public_bytes(
            encoding=x509.encoding.DER,
            format=x509.PublicFormat.PKCS1
        )
        digest = hashlib.sha256(key_bytes).digest()
        return base64.b64encode(digest).decode()
    
    def _get_cache_key(self, serial_number: int) -> str:
        """Generate a cache key for a serial number."""
        return f"ocsp_{serial_number}"

class OCSPClient:
    """
    OCSP Client for checking certificate status.
    """
    def __init__(self, ca_cert: Certificate):
        """
        Initialize the OCSP Client.
        
        Args:
            ca_cert: The Certificate Authority certificate
        """
        self.ca_cert = ca_cert
        # Cache of responses to avoid frequent checks
        self._response_cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        # Default cache time of 10 minutes
        self.cache_time = timedelta(minutes=10)
    
    def check_certificate_status(self, cert: Certificate, ocsp_response: Dict[str, Any]) -> str:
        """
        Check the status of a certificate using an OCSP response.
        
        Args:
            cert: The certificate to check
            ocsp_response: The OCSP response
            
        Returns:
            str: The status of the certificate (good, revoked, unknown)
            
        Raises:
            ValueError: If the response is invalid
        """
        # Check cache first
        serial = cert.get_serial_number()
        cache_key = f"ocsp_{serial}"
        
        if cache_key in self._response_cache:
            cached_response, cache_time = self._response_cache[cache_key]
            if datetime.utcnow() - cache_time < self.cache_time:
                return cached_response["response"]["responses"][0]["cert_status"]
        
        # Verify the response
        responder = OCSPResponder(self.ca_cert, Certificate(ocsp_response["signing_cert"].encode()))
        if not responder.verify_response(ocsp_response):
            raise ValueError("Invalid OCSP response signature")
        
        # Extract the certificate status
        response_data = ocsp_response["response"]
        cert_responses = response_data["responses"]
        
        # Find matching certificate response
        for cert_response in cert_responses:
            if cert_response["cert_id"]["serial_number"] == str(serial):
                status = cert_response["cert_status"]
                
                # Cache the response
                self._response_cache[cache_key] = (ocsp_response, datetime.utcnow())
                
                return status
        
        return OCSPStatus.UNKNOWN
"""
Certificate module for handling X.509 certificates in the Agent Name Service.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

class Certificate:
    """
    Handles X.509 certificate operations for the Agent Name Service.
    """
    def __init__(self, cert_data: bytes):
        """
        Initialize with certificate data.
        
        Args:
            cert_data: PEM-encoded certificate data
        """
        self.cert = x509.load_pem_x509_certificate(cert_data)
        self._private_key = None  # Only set for self-signed certificates

    @classmethod
    def generate_self_signed_cert(cls, 
                                subject_name: str,
                                validity_days: int = 365,
                                key_size: int = 2048) -> Tuple['Certificate', bytes]:
        """
        Generate a self-signed certificate.
        
        Args:
            subject_name: The subject name for the certificate
            validity_days: Number of days the certificate is valid
            key_size: Size of the RSA key in bits
            
        Returns:
            Tuple of (Certificate instance, private key in PEM format)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        
        # Generate public key
        public_key = private_key.public_key()
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name)
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=validity_days)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        ).sign(private_key, hashes.SHA256())
        
        # Create Certificate instance
        cert_instance = cls(cert.public_bytes(serialization.Encoding.PEM))
        cert_instance._private_key = private_key
        
        # Return certificate and private key
        return cert_instance, private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    @classmethod
    def create_csr(cls,
                  subject_name: str,
                  private_key: bytes) -> bytes:
        """
        Create a Certificate Signing Request (CSR).
        
        Args:
            subject_name: The subject name for the certificate
            private_key: PEM-encoded private key
            
        Returns:
            PEM-encoded CSR
        """
        # Load private key
        key = load_pem_private_key(private_key, password=None)
        
        # Create CSR
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, subject_name)
            ])
        ).sign(key, hashes.SHA256())
        
        return csr.public_bytes(serialization.Encoding.PEM)

    def sign_csr(self, csr_data: bytes, validity_days: int = 365) -> bytes:
        """
        Sign a Certificate Signing Request (CSR).
        
        Args:
            csr_data: PEM-encoded CSR
            validity_days: Number of days the certificate will be valid
            
        Returns:
            PEM-encoded signed certificate
            
        Raises:
            ValueError: If this certificate doesn't have a private key
        """
        if not self._private_key:
            raise ValueError("This certificate doesn't have a private key for signing")
        
        # Load CSR
        csr = x509.load_pem_x509_csr(csr_data)
        
        # Create certificate
        cert = x509.CertificateBuilder().subject_name(
            csr.subject
        ).issuer_name(
            self.cert.subject
        ).public_key(
            csr.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=validity_days)
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        ).sign(self._private_key, hashes.SHA256())
        
        return cert.public_bytes(serialization.Encoding.PEM)

    def sign_data(self, data: bytes) -> bytes:
        """
        Sign data using this certificate's private key.
        
        Args:
            data: The data to sign
            
        Returns:
            bytes: The signature
            
        Raises:
            ValueError: If this certificate doesn't have a private key
        """
        if not self._private_key:
            raise ValueError("This certificate doesn't have a private key for signing")
        
        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature

    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """
        Verify a signature using this certificate's public key.
        
        Args:
            data: The data that was signed
            signature: The signature to verify
            
        Returns:
            bool: True if the signature is valid
        """
        try:
            self.cert.public_key().verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def is_valid(self) -> bool:
        """
        Check if the certificate is currently valid.
        
        Returns:
            bool: True if the certificate is valid
        """
        now = datetime.utcnow()
        return (self.cert.not_valid_before <= now <= self.cert.not_valid_after)

    def get_pem(self) -> bytes:
        """
        Get the certificate in PEM format.
        
        Returns:
            bytes: PEM-encoded certificate
        """
        return self.cert.public_bytes(serialization.Encoding.PEM)

    def get_serial_number(self) -> int:
        """
        Get the certificate's serial number.
        
        Returns:
            int: Serial number
        """
        return self.cert.serial_number

    def get_subject_name(self) -> str:
        """
        Get the certificate's subject name.
        
        Returns:
            str: Subject name
        """
        return self.cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value 
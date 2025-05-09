"""
Tests for the OCSP implementation in ANS.
"""
import unittest
import json
from datetime import datetime, timedelta
from ..crypto.certificate import Certificate
from ..crypto.certificate_authority import CertificateAuthority
from ..crypto.ocsp import OCSPResponder, OCSPClient, OCSPStatus

class TestOCSP(unittest.TestCase):
    """Test cases for the OCSP implementation."""
    
    def setUp(self):
        # Set up certificates for testing
        ca_cert, ca_private_key = Certificate.generate_self_signed_cert(
            "Test CA",
            validity_days=30
        )
        self.ca = CertificateAuthority(ca_cert, ca_private_key)
        
        # Set up registry certificate
        registry_cert, registry_private_key = Certificate.generate_self_signed_cert(
            "Test Registry",
            validity_days=30
        )
        self.registry_cert = registry_cert
        
        # Generate agent key pair and certificate
        private_key, public_key = self._generate_key_pair()
        csr = Certificate.create_csr("test-agent", private_key)
        cert_data = self.ca.issue_certificate(csr, validity_days=30)
        self.agent_cert = Certificate(cert_data)
        
        # Set up OCSP responder and client
        self.responder = OCSPResponder(ca_cert, registry_cert)
        self.client = OCSPClient(ca_cert)
    
    def _generate_key_pair(self):
        """Generate a test key pair."""
        ca_cert, ca_private_key = Certificate.generate_self_signed_cert(
            "Temp",
            validity_days=1
        )
        return ca_private_key, ca_cert.cert.public_key()
    
    def test_ocsp_good_status(self):
        """Test OCSP status for a good certificate."""
        # Get a response for a good certificate
        response = self.responder.get_response(
            self.agent_cert.get_serial_number(),
            OCSPStatus.GOOD
        )
        
        # Verify the response
        self.assertTrue(self.responder.verify_response(response))
        
        # Check the status
        status = self.client.check_certificate_status(self.agent_cert, response)
        self.assertEqual(status, OCSPStatus.GOOD)

    def test_ocsp_revoked_status(self):
        """Test OCSP status for a revoked certificate."""
        # Revoke the certificate
        serial = self.agent_cert.get_serial_number()
        revocation_time = datetime.utcnow()
        reason = "Key compromise"
        
        # Get a response for a revoked certificate
        response = self.responder.get_response(
            serial,
            OCSPStatus.REVOKED,
            revocation_time,
            reason
        )
        
        # Verify the response
        self.assertTrue(self.responder.verify_response(response))
        
        # Check the status
        status = self.client.check_certificate_status(self.agent_cert, response)
        self.assertEqual(status, OCSPStatus.REVOKED)
        
        # Verify revocation time and reason are included
        self.assertIn("revocation_time", response["response"]["responses"][0])
        if "revocation_reason" in response["response"]["responses"][0]:
            self.assertEqual(response["response"]["responses"][0]["revocation_reason"], reason)

    def test_ocsp_response_caching(self):
        """Test OCSP response caching."""
        serial = self.agent_cert.get_serial_number()
        
        # Get first response
        response1 = self.responder.get_response(serial, OCSPStatus.GOOD)
        
        # Get second response right away (should use cache)
        response2 = self.responder.get_response(serial, OCSPStatus.GOOD)
        
        # The responses should have the same produced_at time
        self.assertEqual(
            response1["response"]["produced_at"],
            response2["response"]["produced_at"]
        )

    def test_ocsp_response_signing(self):
        """Test OCSP response signing."""
        serial = self.agent_cert.get_serial_number()
        response = self.responder.get_response(serial, OCSPStatus.GOOD)
        
        # Check that the response contains the required fields
        self.assertIn("response", response)
        self.assertIn("signature", response)
        self.assertIn("signing_cert", response)
        
        # Verify that the signature is valid
        response_data = response["response"]
        signature = bytes.fromhex(response["signature"])
        signing_cert = Certificate(response["signing_cert"].encode())
        
        # Convert response data to bytes for verification
        response_bytes = json.dumps(response_data, sort_keys=True).encode()
        
        # Verify signature using the signing certificate
        self.assertTrue(signing_cert.verify_signature(response_bytes, signature))

if __name__ == "__main__":
    unittest.main()
"""
Example OCSP client for validating certificates using the ANS OCSP service.
"""
import requests
import json
import argparse
from datetime import datetime

def check_certificate_status(server_url: str, serial_number: int) -> None:
    """
    Check a certificate's status using OCSP.
    
    Args:
        server_url: URL of the ANS server
        serial_number: Serial number of the certificate to check
    """
    # Build the OCSP request
    ocsp_request = {
        "serial_number": serial_number
    }
    
    # Send the request to the OCSP endpoint
    try:
        response = requests.post(
            f"{server_url}/ocsp",
            json=ocsp_request,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if request was successful
        if response.status_code != 200:
            print(f"Error: OCSP request failed with status {response.status_code}")
            print(response.text)
            return
        
        # Parse the response
        ocsp_response = response.json()
        
        # Extract the certificate status
        if "response" in ocsp_response:
            response_data = ocsp_response["response"]
            cert_responses = response_data["responses"]
            
            if cert_responses:
                cert_status = cert_responses[0]["cert_status"]
                this_update = datetime.fromisoformat(cert_responses[0]["this_update"])
                next_update = datetime.fromisoformat(cert_responses[0]["next_update"])
                
                # Print the status information
                print(f"Certificate Status: {cert_status}")
                print(f"Status as of: {this_update}")
                print(f"Status valid until: {next_update}")
                
                # If revoked, show revocation information
                if cert_status == "revoked" and "revocation_time" in cert_responses[0]:
                    revocation_time = datetime.fromisoformat(cert_responses[0]["revocation_time"])
                    reason = cert_responses[0].get("revocation_reason", "Not specified")
                    print(f"Revocation Time: {revocation_time}")
                    print(f"Revocation Reason: {reason}")
                
                # Verify response signature
                print("\nResponse Signature: ", end="")
                if "signature" in ocsp_response and "signing_cert" in ocsp_response:
                    print("Present (Use cryptography library to verify signature)")
                else:
                    print("Missing")
            else:
                print("Error: No certificate status in response")
        else:
            print("Error: Invalid OCSP response format")
            print(json.dumps(ocsp_response, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check certificate status using OCSP")
    parser.add_argument("--server", default="http://localhost:8000", help="ANS server URL")
    parser.add_argument("--serial", type=int, required=True, help="Certificate serial number")
    args = parser.parse_args()
    
    check_certificate_status(args.server, args.serial)
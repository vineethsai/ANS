"""
Simple example script to resolve an agent's ANS name to its endpoint.
"""
import sys
import os
import json
import requests

# Add the parent directory to the Python path so we can import ANS modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ANS server URL
ANS_URL = "http://localhost:8000"

def resolve_agent(ans_name, version_range=None):
    """
    Resolve an agent's ANS name to its endpoint record.
    
    Args:
        ans_name: ANS name to resolve
        version_range: Optional version range constraint
        
    Returns:
        dict: Endpoint record with signature if successful, None otherwise
    """
    request_data = {
        "ans_name": ans_name,
        "version_range": version_range
    }
    
    try:
        response = requests.post(
            f"{ANS_URL}/resolve",
            json=request_data
        )
        
        if response.status_code != 200:
            print(f"Resolution failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        return response.json()
    except Exception as e:
        print(f"Error during resolution: {e}")
        return None

def verify_endpoint_record(endpoint_record):
    """
    Verify the signature on an endpoint record.
    
    In a production implementation, this would verify using the registry's
    public key. For this example, we just print the signature information.
    
    Args:
        endpoint_record: The endpoint record to verify
        
    Returns:
        bool: True if verification passes (simplified for example)
    """
    if not endpoint_record:
        return False
    
    # Show verification details
    print(f"Signature: {endpoint_record.get('signature', 'None')[:30]}...")
    print(f"Registry certificate available: {'Yes' if endpoint_record.get('registry_certificate') else 'No'}")
    
    # In a real implementation, we would verify the signature
    return True

def display_endpoint_record(endpoint_record):
    """
    Display the endpoint record in a readable format.
    
    Args:
        endpoint_record: The endpoint record to display
    """
    if not endpoint_record:
        print("No endpoint record available")
        return
    
    data = endpoint_record.get("data", {})
    
    print("\nEndpoint Record:")
    print(f"ANS Name: {data.get('ans_name')}")
    print(f"Agent ID: {data.get('agent_id')}")
    print(f"Endpoint: {data.get('endpoint')}")
    print(f"Capabilities: {', '.join(data.get('capabilities', []))}")
    
    # Display protocol extensions if available
    protocol_extensions = data.get("protocol_extensions", {})
    if protocol_extensions:
        print("\nProtocol Extensions:")
        for key, value in protocol_extensions.items():
            if isinstance(value, dict) or isinstance(value, list):
                print(f"  {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"  {key}: {value}")
    
    print(f"\nActive: {'Yes' if data.get('is_active') else 'No'}")

def main():
    """Example script to resolve an agent's ANS name."""
    # Get ANS name from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python resolve_agent.py <ans_name> [version_range]")
        print("Example: python resolve_agent.py a2a://example-agent.chat.example.v1.0.0")
        print("Example with version: python resolve_agent.py a2a://example-agent.chat.example.v1.0.0 \">=1.0.0 <2.0.0\"")
        return
    
    ans_name = sys.argv[1]
    version_range = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Resolving ANS name: {ans_name}" + (f" with version range: {version_range}" if version_range else ""))
    
    # Resolve the ANS name
    endpoint_record = resolve_agent(ans_name, version_range)
    
    if endpoint_record:
        # Verify the endpoint record
        verified = verify_endpoint_record(endpoint_record)
        if verified:
            print("Endpoint record verified successfully")
        else:
            print("Endpoint record verification failed")
        
        # Display the endpoint record
        display_endpoint_record(endpoint_record)
    else:
        print(f"Failed to resolve ANS name: {ans_name}")

if __name__ == "__main__":
    main() 
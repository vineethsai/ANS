"""
Simple example script to list agents with a given protocol.
"""
import sys
import os
import json
import requests

# Add the parent directory to the Python path so we can import ANS modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ANS server URL
ANS_URL = "http://localhost:8000"

def find_agents(protocol=None, capability=None, provider=None):
    """Find agents matching criteria."""
    params = {}
    if protocol:
        params["protocol"] = protocol
    if capability:
        params["capability"] = capability
    if provider:
        params["provider"] = provider
    
    response = requests.get(
        f"{ANS_URL}/agents",
        params=params
    )
    
    if response.status_code != 200:
        print(f"Query failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

def display_agents(agents_response):
    """Display agents in a readable format."""
    if not agents_response:
        print("No response received")
        return
    
    if agents_response.get("status") != "success":
        print(f"Error: {agents_response.get('error')}")
        return
    
    # Get the list of matching agents
    matching_agents = agents_response.get("matchingAgents", [])
    query_params = agents_response.get("queryParameters", {})
    
    # Display query information
    protocol = query_params.get("protocol", "*")
    capability = query_params.get("capability", "*")
    provider = query_params.get("provider", "*")
    
    print(f"Query: protocol={protocol}, capability={capability}, provider={provider}")
    print(f"Found {len(matching_agents)} matching agents")
    print("---------------------------------------------")
    
    # Display each agent
    for i, agent in enumerate(matching_agents, 1):
        print(f"{i}. {agent.get('ansName')}")
        print(f"   ID: {agent.get('agentID')}")
        print(f"   Protocol: {agent.get('protocol')}")
        print(f"   Capabilities: {', '.join(agent.get('capabilities', []))}")
        print(f"   Endpoint: {agent.get('endpoint')}")
        print(f"   Active: {'Yes' if agent.get('isActive') else 'No'}")
        print(f"   Last updated: {agent.get('lastUpdated')}")
        print("---------------------------------------------")

def main():
    """Main function to list agents."""
    # Get protocol from command line arguments if provided
    protocol = None
    capability = None
    provider = None
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("protocol="):
                protocol = arg.split("=")[1]
            elif arg.startswith("capability="):
                capability = arg.split("=")[1]
            elif arg.startswith("provider="):
                provider = arg.split("=")[1]
    
    agents = find_agents(protocol, capability, provider)
    display_agents(agents)

if __name__ == "__main__":
    main() 
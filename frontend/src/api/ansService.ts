import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Type definitions for API responses
export interface Agent {
  agentID: string;
  ansName: string;
  protocol: string;
  capabilities: string[];
  protocolExtensions: Record<string, any>;
  endpoint: string;
  certificate: string;
  registrationTime: string;
  lastRenewalTime: string | null;
  isActive: boolean;
}

// Backend API agent format (snake_case)
interface BackendAgent {
  agent_id: string;
  ans_name: string;
  capabilities: string[];
  protocol_extensions: Record<string, any>;
  endpoint: string;
  certificate: string;
  registration_time: string;
  last_renewal_time: string | null;
  is_active: boolean;
}

export interface AgentListResponse {
  responseType: string;
  status: string;
  matchingAgents?: Agent[];
  agents?: BackendAgent[];
  queryParameters?: {
    protocol: string;
    capability: string;
    provider: string;
  };
  resultCount?: number;
  totalCount?: number;
}

export interface AgentRegistrationResponse {
  responseType: string;
  status: string;
  registeredAgent?: Agent;
  certificate?: string;
  error?: string;
}

export interface EndpointRecord {
  data: {
    ans_name: string;
    agent_id: string;
    endpoint: string;
    capabilities: string[];
    protocol_extensions: Record<string, any>;
    is_active: boolean;
  };
  signature: string;
  registry_certificate: string;
}

// API service functions
const ansService = {
  // Get list of agents
  async getAgents(protocol?: string, capability?: string, provider?: string) {
    try {
      const params: Record<string, string> = {};
      if (protocol) params.protocol = protocol;
      if (capability) params.capability = capability;
      if (provider) params.provider = provider;
      
      const response = await axios.get<AgentListResponse>(`${API_URL}/agents`, { params });
      
      // Make sure we have a valid response
      if (!response.data || typeof response.data !== 'object') {
        return { 
          status: 'error', 
          message: 'Invalid response from server',
          matchingAgents: []
        };
      }
      
      // Map the 'agents' field from API to 'matchingAgents' expected by the frontend
      if (response.data.agents && !response.data.matchingAgents) {
        // Transform the API response agents (snake_case) to the frontend format (camelCase)
        const transformedAgents = response.data.agents.map(agent => ({
          agentID: agent.agent_id,
          ansName: agent.ans_name,
          // Extract protocol from ans_name (format: protocol://agent_id.capability.provider.vVersion)
          protocol: agent.ans_name.split('://')[0],
          capabilities: agent.capabilities,
          protocolExtensions: agent.protocol_extensions,
          endpoint: agent.endpoint,
          certificate: agent.certificate,
          registrationTime: agent.registration_time,
          lastRenewalTime: agent.last_renewal_time,
          isActive: agent.is_active
        }));
        
        return {
          ...response.data,
          matchingAgents: transformedAgents
        };
      }
      
      // Ensure we have matchingAgents array
      if (!response.data.matchingAgents) {
        return {
          ...response.data,
          matchingAgents: []
        };
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching agents:', error);
      return {
        status: 'error',
        message: 'Failed to fetch agents',
        matchingAgents: []
      };
    }
  },

  // Resolve an agent by ANS name
  async resolveAgent(ansName: string, versionRange?: string) {
    try {
      const response = await axios.post<EndpointRecord>(`${API_URL}/resolve`, {
        ans_name: ansName,
        version_range: versionRange || null
      });
      return response.data;
    } catch (error) {
      console.error('Error resolving agent:', error);
      throw error;
    }
  },

  // Register a new agent
  async registerAgent(registrationData: any) {
    try {
      const response = await axios.post<AgentRegistrationResponse>(
        `${API_URL}/register`, 
        registrationData
      );
      return response.data;
    } catch (error) {
      console.error('Error registering agent:', error);
      throw error;
    }
  },

  // Health check
  async checkHealth() {
    try {
      const response = await axios.get(`${API_URL}/health`);
      return response.data;
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }
};

export default ansService; 
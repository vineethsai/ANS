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

export interface AgentListResponse {
  responseType: string;
  status: string;
  matchingAgents: Agent[];
  queryParameters: {
    protocol: string;
    capability: string;
    provider: string;
  };
  resultCount: number;
  totalCount: number;
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
      return response.data;
    } catch (error) {
      console.error('Error fetching agents:', error);
      throw error;
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
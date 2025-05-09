import React, { useState, useEffect } from 'react';
import ansService, { Agent } from '../api/ansService';

interface AgentListProps {
  protocol?: string;
  capability?: string;
  provider?: string;
}

// Helper function to safely format dates
const formatDate = (dateString: string | null) => {
  if (!dateString) return 'N/A';
  
  try {
    const date = new Date(dateString);
    // Check if date is valid
    return isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString();
  } catch (error) {
    return 'Invalid Date';
  }
};

const AgentList: React.FC<AgentListProps> = ({ protocol, capability, provider }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        setLoading(true);
        const response = await ansService.getAgents(protocol, capability, provider);
        if (response.status === 'success') {
          setAgents(response.matchingAgents || []);
          setError(null);
        } else {
          setError(response.status);
        }
      } catch (err) {
        setError('Failed to fetch agents');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
  }, [protocol, capability, provider]);

  if (loading) {
    return <div>Loading agents...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (agents.length === 0) {
    return <div>No agents found</div>;
  }

  return (
    <div className="agent-list">
      <h2>Agents</h2>
      <div className="filter-info">
        <p>
          Showing agents
          {protocol && <span> with protocol: <strong>{protocol}</strong></span>}
          {capability && <span> with capability: <strong>{capability}</strong></span>}
          {provider && <span> from provider: <strong>{provider}</strong></span>}
        </p>
      </div>
      <div className="agent-grid">
        {agents.map((agent) => (
          <div key={agent.agentID} className="agent-card">
            <h3>{agent.agentID}</h3>
            <p><strong>ANS Name:</strong> {agent.ansName || 'N/A'}</p>
            <p><strong>Protocol:</strong> {agent.protocol || 'N/A'}</p>
            <p><strong>Capabilities:</strong> {agent.capabilities?.join(', ') || 'N/A'}</p>
            <p><strong>Endpoint:</strong> {agent.endpoint || 'N/A'}</p>
            <p><strong>Status:</strong> {agent.isActive ? 'Active' : 'Inactive'}</p>
            <p><strong>Registered:</strong> {formatDate(agent.registrationTime)}</p>
            {agent.lastRenewalTime && (
              <p><strong>Last Renewed:</strong> {formatDate(agent.lastRenewalTime)}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentList; 
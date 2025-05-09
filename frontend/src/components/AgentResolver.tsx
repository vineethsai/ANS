import React, { useState } from 'react';
import ansService, { EndpointRecord } from '../api/ansService';

const AgentResolver: React.FC = () => {
  const [ansName, setAnsName] = useState('');
  const [versionRange, setVersionRange] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EndpointRecord | null>(null);

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ansName) {
      setError('ANS name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const endpointRecord = await ansService.resolveAgent(ansName, versionRange || undefined);
      setResult(endpointRecord);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to resolve agent');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-resolver">
      <h2>Resolve Agent</h2>
      <form onSubmit={handleResolve}>
        <div className="form-group">
          <label htmlFor="ansName">ANS Name</label>
          <input
            id="ansName"
            type="text"
            value={ansName}
            onChange={(e) => setAnsName(e.target.value)}
            placeholder="e.g., a2a://agent-name.capability.provider.v1.0.0"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="versionRange">Version Range (optional)</label>
          <input
            id="versionRange"
            type="text"
            value={versionRange}
            onChange={(e) => setVersionRange(e.target.value)}
            placeholder="e.g., >=1.0.0 <2.0.0"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Resolving...' : 'Resolve Agent'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <div className="resolution-result">
          <h3>Resolution Result</h3>
          <div className="result-card">
            <p><strong>ANS Name:</strong> {result.data.ans_name}</p>
            <p><strong>Agent ID:</strong> {result.data.agent_id}</p>
            <p><strong>Endpoint:</strong> {result.data.endpoint}</p>
            <p><strong>Capabilities:</strong> {result.data.capabilities.join(', ')}</p>
            <p><strong>Status:</strong> {result.data.is_active ? 'Active' : 'Inactive'}</p>
            
            <div className="protocol-extensions">
              <h4>Protocol Extensions</h4>
              <pre>{JSON.stringify(result.data.protocol_extensions, null, 2)}</pre>
            </div>
            
            <details>
              <summary>Signature Information</summary>
              <p><strong>Signature:</strong> {result.signature.substring(0, 20)}...</p>
              <p><strong>Registry Certificate:</strong> Available</p>
            </details>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentResolver; 
import React, { useState } from 'react';
import ansService from '../api/ansService';

interface FormValues {
  protocol: string;
  agentName: string;
  agentCategory: string;
  providerName: string;
  version: string;
  extension: string;
  agentUseJustification: string;
  agentCapability: string;
  agentEndpoint: string;
  agentDID: string;
  agentDNSName: string;
  csrPEM: string;
}

const initialFormValues: FormValues = {
  protocol: 'a2a',
  agentName: '',
  agentCategory: '',
  providerName: '',
  version: '1.0.0',
  extension: 'agent',
  agentUseJustification: '',
  agentCapability: '',
  agentEndpoint: '',
  agentDID: '',
  agentDNSName: '',
  csrPEM: '',
};

const AgentRegistration: React.FC = () => {
  const [formValues, setFormValues] = useState<FormValues>(initialFormValues);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [registrationResult, setRegistrationResult] = useState<any>(null);

  // Certificate information state (for demonstration purposes)
  const [certificateInfo, setCertificateInfo] = useState({
    certificateSubject: '',
    certificateIssuer: '',
    certificateSerialNumber: '',
    certificateValidFrom: '',
    certificateValidTo: '',
    certificatePEM: '',
    certificatePublicKeyAlgorithm: 'RSA',
    certificateSignatureAlgorithm: 'SHA256withRSA',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormValues((prev) => ({ ...prev, [name]: value }));
  };

  const updateDNSName = () => {
    if (formValues.agentName && formValues.agentCategory && formValues.providerName) {
      const dnsName = `${formValues.agentName}.${formValues.agentCategory}.${formValues.providerName}.ans`;
      setFormValues((prev) => ({ ...prev, agentDNSName: dnsName }));
    }
  };

  const updateDID = () => {
    if (formValues.agentName) {
      const did = `did:example:${formValues.agentName}`;
      setFormValues((prev) => ({ ...prev, agentDID: did }));
    }
  };

  // Helper functions to handle certificate generation would normally go here
  // For this demo, we'll just use placeholders

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // In a real app, you would generate a CSR and certificate here
      // For this demo, we'll use a placeholder certificate
      
      // Example current date/time for certificate validity
      const now = new Date();
      const validTo = new Date();
      validTo.setDate(now.getDate() + 30); // Valid for 30 days
      
      // Update certificate info
      const certInfo = {
        certificateSubject: `CN=${formValues.agentName}, O=Example Organization, C=US`,
        certificateIssuer: `CN=${formValues.agentName}, O=Example Organization, C=US`,
        certificateSerialNumber: Math.floor(Math.random() * 1000000000).toString(),
        certificateValidFrom: now.toISOString(),
        certificateValidTo: validTo.toISOString(),
        certificatePEM: '-----BEGIN CERTIFICATE-----\nSample certificate would go here\n-----END CERTIFICATE-----',
        certificatePublicKeyAlgorithm: 'RSA',
        certificateSignatureAlgorithm: 'SHA256withRSA',
      };
      
      // Prepare registration data
      const registrationData = {
        requestType: 'registration',
        requestingAgent: {
          ...formValues,
          certificate: certInfo,
          csrPEM: '-----BEGIN CERTIFICATE REQUEST-----\nSample CSR would go here\n-----END CERTIFICATE REQUEST-----',
        }
      };
      
      // Register the agent
      const result = await ansService.registerAgent(registrationData);
      
      setRegistrationResult(result);
      setSuccess(result.status === 'success');
      if (result.status !== 'success') {
        setError(result.error || 'Registration failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-registration">
      <h2>Register a New Agent</h2>
      
      {success && (
        <div className="success-message">
          <p>Agent registered successfully!</p>
          {registrationResult && (
            <div>
              <p>Agent ID: {registrationResult.registeredAgent?.agentID}</p>
              <p>ANS Name: {registrationResult.registeredAgent?.ansName}</p>
            </div>
          )}
        </div>
      )}
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="protocol">Protocol</label>
            <select
              id="protocol"
              name="protocol"
              value={formValues.protocol}
              onChange={handleChange}
              required
            >
              <option value="a2a">a2a</option>
              <option value="mcp">mcp</option>
              <option value="acp">acp</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="agentName">Agent Name</label>
            <input
              id="agentName"
              name="agentName"
              type="text"
              value={formValues.agentName}
              onChange={(e) => {
                handleChange(e);
                // Update DNS name and DID when agent name changes
                setTimeout(() => {
                  updateDNSName();
                  updateDID();
                }, 100);
              }}
              placeholder="unique-agent-name"
              required
            />
          </div>
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="agentCategory">Agent Category</label>
            <input
              id="agentCategory"
              name="agentCategory"
              type="text"
              value={formValues.agentCategory}
              onChange={(e) => {
                handleChange(e);
                // Update DNS name when category changes
                setTimeout(updateDNSName, 100);
              }}
              placeholder="chat"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="providerName">Provider Name</label>
            <input
              id="providerName"
              name="providerName"
              type="text"
              value={formValues.providerName}
              onChange={(e) => {
                handleChange(e);
                // Update DNS name when provider changes
                setTimeout(updateDNSName, 100);
              }}
              placeholder="example"
              required
            />
          </div>
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="version">Version</label>
            <input
              id="version"
              name="version"
              type="text"
              value={formValues.version}
              onChange={handleChange}
              placeholder="1.0.0"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="agentCapability">Agent Capability</label>
            <input
              id="agentCapability"
              name="agentCapability"
              type="text"
              value={formValues.agentCapability}
              onChange={handleChange}
              placeholder="conversation"
              required
            />
          </div>
        </div>
        
        <div className="form-group">
          <label htmlFor="agentEndpoint">Agent Endpoint URL</label>
          <input
            id="agentEndpoint"
            name="agentEndpoint"
            type="url"
            value={formValues.agentEndpoint}
            onChange={handleChange}
            placeholder="https://example.com/agent"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="agentUseJustification">Use Justification</label>
          <textarea
            id="agentUseJustification"
            name="agentUseJustification"
            value={formValues.agentUseJustification}
            onChange={handleChange}
            placeholder="Explain the purpose of this agent"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="agentDID">Agent DID</label>
          <input
            id="agentDID"
            name="agentDID"
            type="text"
            value={formValues.agentDID}
            onChange={handleChange}
            placeholder="did:example:agent-name"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="agentDNSName">Agent DNS Name</label>
          <input
            id="agentDNSName"
            name="agentDNSName"
            type="text"
            value={formValues.agentDNSName}
            onChange={handleChange}
            placeholder="agent-name.category.provider.ans"
            required
            readOnly
          />
        </div>
        
        <div className="form-actions">
          <button type="submit" disabled={loading}>
            {loading ? 'Registering...' : 'Register Agent'}
          </button>
        </div>
      </form>
      
      <div className="note">
        <p><strong>Note:</strong> In a production environment, you would generate real certificates and CSRs. This demo uses placeholders.</p>
      </div>
    </div>
  );
};

export default AgentRegistration; 
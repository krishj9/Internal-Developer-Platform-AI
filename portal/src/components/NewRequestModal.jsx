import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { X, Send, Sparkles, AlertTriangle } from 'lucide-react';

export default function NewRequestModal({ template, onClose, onRequestCreated }) {
  const { activeWorkspace, user, isAdmin } = useAuth();
  const [environment, setEnvironment] = useState('dev');
  const [inputs, setInputs] = useState(() => {
    if (template.template_id === 't1-agent-engine') {
      return {
        agent_name: 'support-agent',
        model_name: template.allowed_models[0] || 'gemini-2.5-flash',
        region: template.allowed_regions[0] || 'us-central1'
      };
    } else if (template.template_id === 't2-managed-rag') {
      return {
        corpus_name: 'support-docs-corpus',
        embedding_model: template.allowed_models[0] || 'text-embedding-004',
        chunk_size: 512,
        region: template.allowed_regions[0] || 'us-central1',
        source_gcs_prefix: 'gs://idp-poc-dev-docs/support'
      };
    } else if (template.template_id === 't3-cloud-run-agent') {
      return {
        service_name: 'agent-service-poc',
        model_name: template.allowed_models[0] || 'gemini-2.5-flash',
        cpu: '1',
        memory: '512Mi',
        max_instances: 3,
        region: template.allowed_regions[0] || 'us-central1'
      };
    } else {
      return {
        policy_name: 'standard-armor-policy',
        guardrail_mode: 'block',
        alert_email: 'alerts@example.com'
      };
    }
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (key, value) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        workspace: activeWorkspace,
        template_id: template.template_id,
        template_version: template.template_version,
        environment,
        inputs
      };

      const res = await api.submitRequest(payload);
      onRequestCreated(res);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit deployment request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '580px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Deploy {template.display_name}</h3>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Workspace: <strong style={{ color: '#60a5fa' }}>{activeWorkspace}</strong> · Version: {template.template_version}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ margin: '16px 24px 0', padding: '12px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ padding: '20px 24px' }}>
          {/* Environment Selector */}
          <div className="form-group">
            <label className="form-label" htmlFor="req-env">Target Environment</label>
            <select
              id="req-env"
              className="form-select"
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
            >
              {(template.supported_environments || ['dev']).map((env) => (
                <option key={env} value={env} disabled={env === 'prod' && !isAdmin}>
                  {env.toUpperCase()} {env === 'prod' && !isAdmin ? '(Platform Admin Only)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Dynamic Template Inputs */}
          {template.template_id === 't1-agent-engine' && (
            <>
              <div className="form-group">
                <label className="form-label" htmlFor="inp-agent-name">Agent Name</label>
                <input
                  id="inp-agent-name"
                  className="form-input"
                  type="text"
                  value={inputs.agent_name || ''}
                  onChange={(e) => handleInputChange('agent_name', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="inp-model-name">Governed Model</label>
                <select
                  id="inp-model-name"
                  className="form-select"
                  value={inputs.model_name}
                  onChange={(e) => handleInputChange('model_name', e.target.value)}
                >
                  {template.allowed_models.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            </>
          )}

          {template.template_id === 't2-managed-rag' && (
            <>
              <div className="form-group">
                <label className="form-label" htmlFor="inp-corpus-name">Corpus Name</label>
                <input
                  id="inp-corpus-name"
                  className="form-input"
                  type="text"
                  value={inputs.corpus_name || ''}
                  onChange={(e) => handleInputChange('corpus_name', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="inp-embed-model">Embedding Model</label>
                <select
                  id="inp-embed-model"
                  className="form-select"
                  value={inputs.embedding_model}
                  onChange={(e) => handleInputChange('embedding_model', e.target.value)}
                >
                  {template.allowed_models.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="inp-gcs-prefix">GCS Source Prefix</label>
                <input
                  id="inp-gcs-prefix"
                  className="form-input"
                  type="text"
                  value={inputs.source_gcs_prefix || ''}
                  onChange={(e) => handleInputChange('source_gcs_prefix', e.target.value)}
                  required
                />
              </div>
            </>
          )}

          {template.template_id === 't3-cloud-run-agent' && (
            <>
              <div className="form-group">
                <label className="form-label" htmlFor="inp-service-name">Service Name</label>
                <input
                  id="inp-service-name"
                  className="form-input"
                  type="text"
                  value={inputs.service_name || ''}
                  onChange={(e) => handleInputChange('service_name', e.target.value)}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="inp-cpu">CPU</label>
                  <input
                    id="inp-cpu"
                    className="form-input"
                    type="text"
                    value={inputs.cpu || '1'}
                    onChange={(e) => handleInputChange('cpu', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="inp-memory">Memory</label>
                  <input
                    id="inp-memory"
                    className="form-input"
                    type="text"
                    value={inputs.memory || '512Mi'}
                    onChange={(e) => handleInputChange('memory', e.target.value)}
                  />
                </div>
              </div>
            </>
          )}

          {/* Region */}
          <div className="form-group">
            <label className="form-label" htmlFor="inp-region">GCP Region</label>
            <select
              id="inp-region"
              className="form-select"
              value={inputs.region || 'us-central1'}
              onChange={(e) => handleInputChange('region', e.target.value)}
            >
              {(template.allowed_regions || ['us-central1']).map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {/* Action Footer */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button id="btn-submit-request" type="submit" className="btn btn-primary" disabled={loading}>
              <Send size={16} />
              <span>{loading ? 'Dispatching via GitHub...' : 'Submit Provisioning Request'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

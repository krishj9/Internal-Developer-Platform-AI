import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import DestroyModal from './DestroyModal';
import { Server, Trash2, Clock, CheckCircle2, AlertCircle, RefreshCw, ExternalLink, Code, Download } from 'lucide-react';

export default function DeploymentsList({ onTrackRequest }) {
  const { activeWorkspace } = useAuth();
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDestroyDep, setSelectedDestroyDep] = useState(null);
  const [viewConfigDep, setViewConfigDep] = useState(null);

  const loadDeployments = async () => {
    try {
      setLoading(true);
      const data = await api.getDeployments(activeWorkspace);
      setDeployments(data);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to load deployments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDeployments();
  }, [activeWorkspace]);

  const handleDestroySuccess = (res) => {
    onTrackRequest(res.request_id);
    loadDeployments();
  };

  const handleDownloadConfig = (dep) => {
    const outputs = dep.safe_outputs || {};
    const config = {
      deployment_id: dep.deployment_id,
      workspace: dep.workspace,
      environment: dep.environment,
      template_id: dep.template_id,
      template_version: dep.template_version,
      status: dep.status,
      model_name: outputs.model_name || 'gemini-2.5-flash',
      region: outputs.region || 'us-central1',
      runtime_service_account: outputs.runtime_sa_email || '',
      staging_bucket: `idp-state-${dep.workspace}`,
      raw_outputs: outputs,
    };
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `idp-config-${dep.deployment_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: '0 24px 32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '6px' }}>
            Workload Deployments
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Active and historical governed cloud workloads in workspace: <strong style={{ color: '#60a5fa' }}>{activeWorkspace}</strong>
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadDeployments} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '14px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {deployments.length === 0 && !loading ? (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center' }}>
          <Server size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3 style={{ fontSize: '1.1rem', marginBottom: '6px' }}>No Deployments Found</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Use the Template Catalog to provision your first governed agentic AI workload.
          </p>
        </div>
      ) : (
        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'rgba(0, 0, 0, 0.3)', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <th style={{ padding: '14px 20px' }}>Deployment ID</th>
                <th style={{ padding: '14px 20px' }}>Template</th>
                <th style={{ padding: '14px 20px' }}>Environment</th>
                <th style={{ padding: '14px 20px' }}>Status</th>
                <th style={{ padding: '14px 20px' }}>Expiry / TTL</th>
                <th style={{ padding: '14px 20px' }}>Created</th>
                <th style={{ padding: '14px 20px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {deployments.map((dep) => {
                const isExpired = dep.expires_at && new Date(dep.expires_at) <= new Date();
                return (
                  <tr
                    key={dep.deployment_id}
                    style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.15s ease' }}
                    className="table-row"
                  >
                    <td style={{ padding: '16px 20px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#93c5fd' }}>
                      {dep.deployment_id}
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ fontWeight: 600 }}>{dep.template_id}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>v{dep.template_version}</div>
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#60a5fa' }}>
                        {dep.environment}
                      </span>
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <span className={`badge badge-${dep.status.toLowerCase()}`}>
                        {dep.status}
                      </span>
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      {dep.expires_at ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={14} color={isExpired ? '#f87171' : '#fbbf24'} />
                          <span style={{ fontSize: '0.8rem', color: isExpired ? '#f87171' : 'var(--text-secondary)' }}>
                            {isExpired ? 'EXPIRED' : new Date(dep.expires_at).toLocaleDateString()}
                          </span>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No Expiry</span>
                      )}
                    </td>
                    <td style={{ padding: '16px 20px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {new Date(dep.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                          onClick={() => setViewConfigDep(dep)}
                          title="View Outputs / Config"
                        >
                          <Code size={14} />
                          <span>Outputs</span>
                        </button>
                        {dep.status === 'ACTIVE' && (
                          <button
                            id={`btn-destroy-${dep.deployment_id}`}
                            className="btn btn-danger"
                            style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                            onClick={() => setSelectedDestroyDep(dep)}
                          >
                            <Trash2 size={14} />
                            <span>Destroy</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Destroy Confirmation Modal */}
      {selectedDestroyDep && (
        <DestroyModal
          deployment={selectedDestroyDep}
          onClose={() => setSelectedDestroyDep(null)}
          onDestroyTriggered={handleDestroySuccess}
        />
      )}

      {/* Outputs / Config Modal */}
      {viewConfigDep && (
        <div className="modal-overlay" onClick={() => setViewConfigDep(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '640px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Safe Outputs: {viewConfigDep.deployment_id}</h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Workload configuration for application deployment</div>
              </div>
              <button onClick={() => setViewConfigDep(null)} className="btn btn-secondary" style={{ padding: '4px 8px' }}>✕</button>
            </div>
            <div style={{ padding: '20px 24px' }}>
              <pre style={{ background: '#090d16', padding: '16px', borderRadius: '8px', overflowX: 'auto', fontSize: '0.8rem', color: '#93c5fd', border: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
                {JSON.stringify(viewConfigDep.safe_outputs || {}, null, 2)}
              </pre>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  id="btn-download-config"
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '8px 14px' }}
                  onClick={() => handleDownloadConfig(viewConfigDep)}
                >
                  <Download size={14} />
                  <span>Download idp-config.json</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { api } from '../services/api';
import { AlertTriangle, Trash2, X } from 'lucide-react';

export default function DestroyModal({ deployment, onClose, onDestroyTriggered }) {
  const [confirmInput, setConfirmInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const targetId = deployment.deployment_id;
  const isConfirmed = confirmInput.trim() === targetId;

  const handleDestroy = async () => {
    if (!isConfirmed) return;
    setLoading(true);
    setError('');

    try {
      const res = await api.destroyDeployment(targetId);
      onDestroyTriggered(res);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to dispatch destroy request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#f87171' }}>
            <AlertTriangle size={22} />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Confirm Workload Teardown</h3>
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

        <div style={{ padding: '20px 24px' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
            This action dispatches a WIF-authenticated GitHub Actions workflow to run <code>terraform destroy</code>. All provisioned cloud resources, endpoints, and storage for this workload will be permanently deleted.
          </p>

          <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px', borderRadius: '8px', marginBottom: '18px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <div>Deployment: <strong style={{ color: '#fff', fontFamily: 'var(--font-mono)' }}>{targetId}</strong></div>
            <div>Template: {deployment.template_id} ({deployment.environment})</div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="confirm-dep-id">
              Type <strong style={{ color: '#f87171', fontFamily: 'var(--font-mono)' }}>{targetId}</strong> to confirm:
            </label>
            <input
              id="confirm-dep-id"
              className="form-input"
              type="text"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              placeholder="Enter deployment ID"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button
              id="btn-confirm-destroy"
              type="button"
              className="btn btn-danger"
              disabled={!isConfirmed || loading}
              onClick={handleDestroy}
            >
              <Trash2 size={16} />
              <span>{loading ? 'Dispatching Destroy...' : 'Permanently Destroy'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

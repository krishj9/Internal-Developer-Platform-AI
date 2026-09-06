import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Activity, CheckCircle2, Clock, XCircle, ArrowRight, ExternalLink, RefreshCw } from 'lucide-react';

export default function RequestTracker({ initialRequestId }) {
  const [requestId, setRequestId] = useState(initialRequestId || '');
  const [requestData, setRequestData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [autoPoll, setAutoPoll] = useState(true);

  const fetchStatus = async (idToFetch) => {
    if (!idToFetch) return;
    try {
      setLoading(true);
      const data = await api.getRequest(idToFetch);
      setRequestData(data);
      setError('');
      // If terminal status reached, stop polling
      if (['SUCCEEDED', 'FAILED', 'CANCELLED'].includes(data.status)) {
        setAutoPoll(false);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch request status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialRequestId) {
      setRequestId(initialRequestId);
      fetchStatus(initialRequestId);
    }
  }, [initialRequestId]);

  useEffect(() => {
    let interval = null;
    if (autoPoll && requestId && requestData && !['SUCCEEDED', 'FAILED', 'CANCELLED'].includes(requestData.status)) {
      interval = setInterval(() => {
        fetchStatus(requestId);
      }, 2500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoPoll, requestId, requestData]);

  const stages = ['PENDING', 'DISPATCHED', 'PLANNING', 'APPLYING', 'SUCCEEDED'];
  const currentStageIndex = stages.indexOf(requestData?.status) >= 0 ? stages.indexOf(requestData?.status) : 1;

  return (
    <div style={{ padding: '0 24px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '6px' }}>Request Lifecycle Tracker</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Real-time tracking of asynchronous WIF pipeline execution and lifecycle state machine transitions.
        </p>
      </div>

      {/* Search Input Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', gap: '12px' }}>
        <input
          id="req-tracker-input"
          className="form-input"
          style={{ maxWidth: '400px' }}
          type="text"
          placeholder="Enter Request ID (e.g. req-abc12345)"
          value={requestId}
          onChange={(e) => setRequestId(e.target.value)}
        />
        <button
          id="btn-track-request"
          className="btn btn-primary"
          onClick={() => {
            setAutoPoll(true);
            fetchStatus(requestId);
          }}
          disabled={loading || !requestId}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          <span>Track Status</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '14px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {requestData && (
        <div className="glass-panel" style={{ padding: '28px' }}>
          {/* Header Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '18px' }}>
            <div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Request: <span style={{ fontFamily: 'var(--font-mono)', color: '#60a5fa' }}>{requestData.request_id}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Deployment ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{requestData.deployment_id}</span> · Template: {requestData.template_id} ({requestData.environment})
              </div>
            </div>
            <div>
              <span className={`badge badge-${requestData.status.toLowerCase()}`} style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
                {requestData.status}
              </span>
            </div>
          </div>

          {/* Stepper Timeline */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '36px', position: 'relative' }}>
            {stages.map((stage, idx) => {
              const isPast = currentStageIndex > idx;
              const isCurrent = currentStageIndex === idx;
              const isFailed = requestData.status === 'FAILED' && stage === 'SUCCEEDED';

              return (
                <div key={stage} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2, position: 'relative' }}>
                  <div
                    style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: '50%',
                      background: isFailed ? '#ef4444' : isPast || isCurrent ? '#3b82f6' : 'rgba(255, 255, 255, 0.08)',
                      border: isCurrent ? '3px solid #93c5fd' : '1px solid rgba(255, 255, 255, 0.2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      boxShadow: isCurrent ? '0 0 16px rgba(59, 130, 246, 0.6)' : 'none',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    {isFailed ? <XCircle size={20} /> : isPast ? <CheckCircle2 size={20} /> : isCurrent ? <Clock size={20} /> : <span style={{ fontSize: '0.8rem', fontWeight: 700 }}>{idx + 1}</span>}
                  </div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, marginTop: '8px', color: isCurrent ? '#60a5fa' : isPast ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {stage}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Details & Safe Summary Card */}
          <div style={{ background: 'rgba(0, 0, 0, 0.3)', borderRadius: '10px', padding: '20px', border: '1px solid var(--border-subtle)' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px', color: '#93c5fd' }}>
              Execution Summary & Telemetry
            </h4>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              {requestData.safe_summary || 'Workflow execution in progress...'}
            </p>
            {requestData.failure_class && (
              <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '6px', fontSize: '0.8rem' }}>
                <strong>Failure Class:</strong> {requestData.failure_class}
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginTop: '16px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <div>Created: {new Date(requestData.created_at).toLocaleTimeString()}</div>
              <div>Updated: {new Date(requestData.updated_at).toLocaleTimeString()}</div>
              {requestData.completed_at && <div>Completed: {new Date(requestData.completed_at).toLocaleTimeString()}</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

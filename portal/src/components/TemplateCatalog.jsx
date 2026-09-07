import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Layers, Cpu, Database, Cloud, ShieldAlert, ArrowRight, CheckCircle, Tag, DollarSign } from 'lucide-react';

export default function TemplateCatalog({ onSelectTemplate }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadTemplates() {
      try {
        setLoading(true);
        const data = await api.getTemplates();
        setTemplates(data);
      } catch (err) {
        setError(err.message || 'Failed to load templates');
      } finally {
        setLoading(false);
      }
    }
    loadTemplates();
  }, []);

  const getTemplateIcon = (id) => {
    if (id.includes('t1')) return Cpu;
    if (id.includes('t2')) return Database;
    if (id.includes('t3')) return Cloud;
    return ShieldAlert;
  };

  const getTierBadge = (tier) => {
    if (tier === 'low') {
      return (
        <span className="badge badge-active" style={{ whiteSpace: 'nowrap', flexShrink: 0 }}>
          Low Cost
        </span>
      );
    }
    if (tier === 'high') {
      return (
        <span className="badge badge-failed" style={{ whiteSpace: 'nowrap', flexShrink: 0 }}>
          High Cost
        </span>
      );
    }
    return (
      <span className="badge badge-pending" style={{ whiteSpace: 'nowrap', flexShrink: 0 }}>
        Medium Cost
      </span>
    );
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px' }}>
        <div className="pulse-dot" style={{ width: '16px', height: '16px' }} />
        <span style={{ marginLeft: '12px', color: 'var(--text-secondary)' }}>Loading Governed Templates...</span>
      </div>
    );
  }

  return (
    <div style={{ padding: '0 24px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '6px' }}>Governed AI Templates</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Version-pinned, immutable infrastructure stacks provisioned via GitHub Actions & WIF.
        </p>
      </div>

      {error && (
        <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '20px' }}>
        {templates.map((tpl) => {
          const Icon = getTemplateIcon(tpl.template_id);
          return (
            <div key={tpl.template_id} className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0, flex: 1 }}>
                    <div style={{ width: '42px', height: '42px', minWidth: '42px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa', flexShrink: 0 }}>
                      <Icon size={22} />
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3, wordBreak: 'break-word' }}>
                        {tpl.display_name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {tpl.template_id} · v{tpl.template_version}
                      </div>
                    </div>
                  </div>
                  {getTierBadge(tpl.cost_tier)}
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '18px', minHeight: '40px', lineHeight: 1.5 }}>
                  {tpl.description}
                </p>

                {/* Constraints & Spec */}
                <div style={{ background: 'rgba(0, 0, 0, 0.25)', borderRadius: '8px', padding: '12px', marginBottom: '20px', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Supported Envs:</span>
                    <span style={{ fontWeight: 600, color: '#93c5fd' }}>{tpl.supported_environments?.join(', ')}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Allowed Models:</span>
                    <span style={{ fontWeight: 600, color: '#34d399', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {tpl.allowed_models?.join(', ')}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Commit SHA:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {tpl.template_commit_sha?.substring(0, 7)}
                    </span>
                  </div>
                </div>
              </div>

              <button
                id={`btn-deploy-${tpl.template_id}`}
                className="btn btn-primary"
                style={{ width: '100%' }}
                onClick={() => onSelectTemplate(tpl)}
              >
                <span>Configure & Deploy</span>
                <ArrowRight size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

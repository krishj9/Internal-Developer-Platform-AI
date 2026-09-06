import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Layers, Server, Activity, ShieldCheck, LogOut, Terminal, BookOpen, ExternalLink } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, activeWorkspace, switchWorkspace, logout, isAdmin } = useAuth();

  const tabs = [
    { id: 'catalog', label: 'Template Catalog', icon: Layers },
    { id: 'deployments', label: 'Deployments', icon: Server },
    { id: 'requests', label: 'Requests', icon: Activity },
    { id: 'governance', label: 'Governance & Model Armor', icon: ShieldCheck },
    { id: 'guide', label: 'User Guide', icon: BookOpen },
  ];

  return (
    <header className="glass-panel" style={{ margin: '16px 24px', padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => setActiveTab('catalog')}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', boxShadow: '0 0 16px rgba(59, 130, 246, 0.4)' }}>
            <Terminal size={20} />
          </div>
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #ffffff, #93c5fd)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              IDP Control Plane
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              Agentic AI on GCP
            </div>
          </div>
        </div>

        {/* Nav Tabs */}
        <nav style={{ display: 'flex', gap: '8px' }}>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`nav-tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  background: isActive ? 'rgba(59, 130, 246, 0.18)' : 'transparent',
                  color: isActive ? '#60a5fa' : 'var(--text-secondary)',
                  borderBottom: isActive ? '2px solid #3b82f6' : '2px solid transparent',
                  transition: 'all 0.2s ease',
                }}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Right Controls: Architecture Link, Workspace & Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Architecture Document Link */}
        <a
          id="nav-link-architecture"
          href="/architecture.html"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{
            padding: '6px 12px',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            border: '1px solid rgba(59, 130, 246, 0.35)',
            background: 'rgba(59, 130, 246, 0.1)',
            color: '#93c5fd',
            textDecoration: 'none',
          }}
          title="Open Technical Architecture Document"
        >
          <BookOpen size={14} color="#60a5fa" />
          <span>Architecture.html</span>
          <ExternalLink size={12} style={{ opacity: 0.6 }} />
        </a>

        {/* Workspace Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(15, 23, 42, 0.6)', padding: '4px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>WORKSPACE:</span>
          <select
            id="workspace-selector"
            value={activeWorkspace}
            onChange={(e) => switchWorkspace(e.target.value)}
            style={{ background: 'transparent', color: '#60a5fa', border: 'none', fontSize: '0.8125rem', fontWeight: 700, outline: 'none', cursor: 'pointer' }}
          >
            {(user?.workspaces || ['ws-dev']).map((ws) => (
              <option key={ws} value={ws} style={{ background: '#0f172a', color: '#fff' }}>
                {ws}
              </option>
            ))}
          </select>
        </div>

        {/* User Role Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {user?.username}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
              <span className={`badge ${isAdmin ? 'badge-purple' : 'badge-active'}`} style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
                {user?.role}
              </span>
            </div>
          </div>

          <button
            id="btn-logout"
            onClick={logout}
            className="btn btn-secondary"
            style={{ padding: '8px 12px' }}
            title="Sign Out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}

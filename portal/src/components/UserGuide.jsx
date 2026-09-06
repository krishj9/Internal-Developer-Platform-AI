import React, { useState } from 'react';
import {
  BookOpen,
  Terminal,
  ExternalLink,
  ShieldCheck,
  Layers,
  Activity,
  Server,
  Trash2,
  Lock,
  CheckCircle2,
  Sparkles,
  Cpu,
  Database,
  Cloud,
  Copy,
  Check,
  AlertCircle,
  Clock,
  ArrowRight
} from 'lucide-react';

export default function UserGuide() {
  const [activeSection, setActiveSection] = useState('quickstart');
  const [copiedIndex, setCopiedIndex] = useState(null);

  const handleCopy = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const navItems = [
    { id: 'quickstart', label: '1. Quick Start & Roles', icon: Sparkles },
    { id: 'templates', label: '2. Governed Templates', icon: Layers },
    { id: 'lifecycle', label: '3. Request Lifecycle', icon: Activity },
    { id: 'deployments', label: '4. Deployments & Safe Outputs', icon: Server },
    { id: 'destroy', label: '5. Safe Teardown', icon: Trash2 },
    { id: 'governance', label: '6. Model Armor Guardrails', icon: ShieldCheck },
    { id: 'cli', label: '7. IDP CLI Reference', icon: Terminal },
  ];

  return (
    <div style={{ padding: '0 24px 48px' }}>
      {/* Top Banner with Architecture & Documentation Links */}
      <div
        className="glass-panel"
        style={{
          padding: '24px 28px',
          marginBottom: '28px',
          background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.35) 0%, rgba(17, 24, 39, 0.8) 100%)',
          border: '1px solid rgba(59, 130, 246, 0.4)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="badge badge-purple" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                DOCUMENTATION & ARCHITECTURE
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Platform Specification v2.1
              </span>
            </div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '6px' }}>
              IDP Control Plane User Guide
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '680px' }}>
              Comprehensive reference for provisioning, managing, governing, and tearing down agentic AI workloads on Google Cloud.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <a
              href="/architecture.html"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
              style={{ padding: '10px 18px', fontSize: '0.85rem' }}
            >
              <BookOpen size={16} />
              <span>Interactive Architecture</span>
              <ExternalLink size={13} style={{ opacity: 0.7 }} />
            </a>

            <a
              href="/presentation.html"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
              style={{ padding: '10px 18px', fontSize: '0.85rem' }}
            >
              <Sparkles size={16} color="#fbbf24" />
              <span>Slide Deck (14 Slides)</span>
              <ExternalLink size={13} style={{ opacity: 0.7 }} />
            </a>

            <a
              href="https://idp-api-754915077075.us-central1.run.app/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
              style={{ padding: '10px 18px', fontSize: '0.85rem' }}
            >
              <Terminal size={16} color="#60a5fa" />
              <span>Swagger REST API</span>
              <ExternalLink size={13} style={{ opacity: 0.7 }} />
            </a>
          </div>
        </div>
      </div>

      {/* Main Content Layout: Sidebar Nav + Detail View */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Sidebar Nav */}
        <div className="glass-panel" style={{ padding: '12px', position: 'sticky', top: '24px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '8px 12px 12px' }}>
            Navigation Sections
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    border: 'none',
                    cursor: 'pointer',
                    textAlign: 'left',
                    background: isActive ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                    color: isActive ? '#60a5fa' : 'var(--text-secondary)',
                    borderLeft: isActive ? '3px solid #3b82f6' : '3px solid transparent',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Section Content Area */}
        <div className="glass-panel" style={{ padding: '32px' }}>
          {/* SECTION 1: QUICK START & ROLES */}
          {activeSection === 'quickstart' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
                  <Sparkles size={20} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>1. Quick Start & Role Permissions</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px', lineHeight: 1.6 }}>
                The IDP Control Plane uses <strong>Argon2id password verification</strong> and issues <strong>60-minute signed JWT bearer tokens</strong>. Tokens are stored securely in browser <code>localStorage</code> and automatically included in all authenticated API requests.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '28px' }}>
                <div className="glass-card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                    <span className="badge badge-purple">ROLE: platform_admin</span>
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '6px' }}>Platform Administrator</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                    Demo user: <code style={{ color: '#93c5fd' }}>admin_gov</code> / <code style={{ color: '#93c5fd' }}>AdminPass123!</code>
                  </div>
                  <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <li>Deploy to any environment (<code>dev</code> and <code>prod</code>)</li>
                    <li>Approve production GitHub Environment gates</li>
                    <li>Reconcile unhandled dead-letter callbacks</li>
                    <li>Override TTL expirations for workloads</li>
                  </ul>
                </div>

                <div className="glass-card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                    <span className="badge badge-active">ROLE: developer</span>
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '6px' }}>Developer</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                    Demo user: <code style={{ color: '#93c5fd' }}>dev_gov</code> / <code style={{ color: '#93c5fd' }}>DevPass123!</code>
                  </div>
                  <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <li>Provision workloads in authorized workspaces</li>
                    <li>Inspect safe operational outputs (zero secrets)</li>
                    <li>Trigger safe two-step teardown</li>
                    <li>Inspect Model Armor guardrail rules</li>
                  </ul>
                </div>
              </div>

              <div style={{ background: 'rgba(0, 0, 0, 0.3)', borderRadius: '10px', padding: '16px 20px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#93c5fd', marginBottom: '6px' }}>
                  💡 Fast-Fill Login Tip:
                </div>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                  When on the Login screen, click either <strong>"👑 Platform Admin"</strong> or <strong>"💻 Developer"</strong> to instantly populate credentials and sign in.
                </p>
              </div>
            </div>
          )}

          {/* SECTION 2: GOVERNED TEMPLATES */}
          {activeSection === 'templates' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
                  <Layers size={20} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>2. Governed AI Workload Templates</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
                Every workload provisioned by the platform corresponds to an immutable, schema-validated infrastructure template pinned to an exact repository commit SHA.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div className="glass-card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Cpu size={20} color="#60a5fa" />
                      <span style={{ fontWeight: 700, fontSize: '1rem' }}>T1: Agent on Vertex AI Agent Engine</span>
                    </div>
                    <span className="badge badge-active">Cost: Low Tier</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                    Provisions a dedicated runtime service account (<code>sa-t1-...</code>) and deploys an ADK-compliant reasoning agent to Google Cloud Agent Engine.
                  </p>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    <span>Allowed Models: <strong style={{ color: '#34d399' }}>gemini-2.5-flash, gemini-2.5-pro</strong></span>
                    <span>Region: <strong style={{ color: '#93c5fd' }}>us-central1</strong></span>
                  </div>
                </div>

                <div className="glass-card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Database size={20} color="#34d399" />
                      <span style={{ fontWeight: 700, fontSize: '1rem' }}>T2: Vertex AI Managed RAG Engine</span>
                    </div>
                    <span className="badge badge-pending">Cost: Medium Tier</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                    Deploys a serverless Vertex AI RAG corpus with <code>RagManagedDb</code> vector indexing. Enforces bounded ingestion limits (&le; 100 documents, &le; 500 MB).
                  </p>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    <span>Embedding Models: <strong style={{ color: '#34d399' }}>text-embedding-004, text-embedding-005</strong></span>
                    <span>Chunk Size: <strong style={{ color: '#93c5fd' }}>512 tokens</strong></span>
                  </div>
                </div>

                <div className="glass-card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Cloud size={20} color="#a78bfa" />
                      <span style={{ fontWeight: 700, fontSize: '1rem' }}>T3: Agent on Cloud Run Service</span>
                    </div>
                    <span className="badge badge-pending">Cost: Medium Tier</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                    Containerized ADK agent service on Cloud Run v2 with dedicated service account (<code>sa-t3-...</code>) and strict IAM invocation (zero public access).
                  </p>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    <span>Scaling: <strong style={{ color: '#a78bfa' }}>0 to 3 instances</strong></span>
                    <span>Resources: <strong style={{ color: '#93c5fd' }}>1 CPU / 512 MiB</strong></span>
                  </div>
                </div>

                <div className="glass-card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <ShieldCheck size={20} color="#f59e0b" />
                      <span style={{ fontWeight: 700, fontSize: '1rem' }}>T4: Governance & Operational Controls</span>
                    </div>
                    <span className="badge badge-active">Cost: Low Tier</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                    Configures Model Armor guardrails, Cloud Monitoring alerts, and automated TTL cleanup policies across workspaces.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 3: REQUEST LIFECYCLE */}
          {activeSection === 'lifecycle' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
                  <Activity size={20} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>3. Asynchronous Request Lifecycle</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
                Infrastructure provisioning is asynchronous. When you submit a request, the control plane holds an atomic deployment lock and tracks execution via trusted pipeline callbacks.
              </p>

              {/* Visual Stepper */}
              <div style={{ background: 'rgba(0, 0, 0, 0.3)', borderRadius: '12px', padding: '24px', border: '1px solid var(--border-subtle)', marginBottom: '28px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
                  {[
                    { step: '1', title: 'PENDING', desc: 'Lock acquired' },
                    { step: '2', title: 'DISPATCHED', desc: 'GitHub triggered' },
                    { step: '3', title: 'PLANNING', desc: 'TF plan verified' },
                    { step: '4', title: 'APPLYING', desc: 'Resources created' },
                    { step: '5', title: 'SUCCEEDED', desc: 'Readiness passed' },
                  ].map((s, idx) => (
                    <div key={s.step} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', zIndex: 2 }}>
                      <div
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '50%',
                          background: '#3b82f6',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#fff',
                          fontWeight: 700,
                          fontSize: '0.85rem',
                          marginBottom: '8px',
                          boxShadow: '0 0 12px rgba(59, 130, 246, 0.5)',
                        }}
                      >
                        {s.step}
                      </div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#93c5fd' }}>{s.title}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{s.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '10px' }}>Key Architecture Guarantees</h3>
              <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li>
                  <strong>Idempotency with 24h TTL:</strong> Every request carries an <code>Idempotency-Key</code> header. Replaying the identical payload returns the cached result without creating duplicate resources. Replaying with altered inputs triggers <code>HTTP 409 Conflict</code>.
                </li>
                <li>
                  <strong>Atomic Deployment Locking:</strong> A deployment can only execute one non-terminal lifecycle request at a time. Attempting concurrent operations returns <code>HTTP 409 Conflict</code>.
                </li>
                <li>
                  <strong>Pre-Activation Smoke Test Gate:</strong> A workload is never marked <code>ACTIVE</code> or <code>SUCCEEDED</code> until an automated readiness test confirms health against the model runtime.
                </li>
                <li>
                  <strong>Sanitized Failure Recovery:</strong> If a stage fails, the request transitions safely to <code>FAILED</code>, the failure class (e.g. <code>terraform_plan_failed</code>, <code>readiness_failed</code>) is captured, and the deployment lock is safely released.
                </li>
              </ul>
            </div>
          )}

          {/* SECTION 4: DEPLOYMENTS & OUTPUTS */}
          {activeSection === 'deployments' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
                  <Server size={20} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>4. Workload Deployments & Safe Outputs</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
                The <strong>Deployments</strong> tab lists all provisioned and historical workloads within your active workspace.
              </p>

              <div className="glass-card" style={{ padding: '24px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px', color: '#93c5fd' }}>
                  Zero-Secret Output Inspection
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  Clicking the <strong>"Outputs"</strong> button on any active deployment opens the Safe Configuration Inspector. The control plane filters out all internal provider configurations, Terraform state, and secrets:
                </p>
                <div style={{ background: '#0a0e1a', borderRadius: '8px', padding: '16px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ color: '#94a3b8' }}>&#123;</span><br />
                  &nbsp;&nbsp;<span style={{ color: '#93c5fd' }}>"deployment_id"</span>: <span style={{ color: '#34d399' }}>"dep-bdba18c9"</span>,<br />
                  &nbsp;&nbsp;<span style={{ color: '#93c5fd' }}>"agent_name"</span>: <span style={{ color: '#34d399' }}>"support-agent"</span>,<br />
                  &nbsp;&nbsp;<span style={{ color: '#93c5fd' }}>"model_name"</span>: <span style={{ color: '#34d399' }}>"gemini-2.5-flash"</span>,<br />
                  &nbsp;&nbsp;<span style={{ color: '#93c5fd' }}>"region"</span>: <span style={{ color: '#34d399' }}>"us-central1"</span>,<br />
                  &nbsp;&nbsp;<span style={{ color: '#93c5fd' }}>"runtime_sa_email"</span>: <span style={{ color: '#34d399' }}>"sa-t1-depbdba18c9@mybrightday-dev.iam.gserviceaccount.com"</span>,<br />
                  &nbsp;&nbsp;<span style={{ color: '#93c5fd' }}>"status"</span>: <span style={{ color: '#34d399' }}>"PROVISIONED"</span><br />
                  <span style={{ color: '#94a3b8' }}>&#125;</span>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 5: SAFE TEARDOWN */}
          {activeSection === 'destroy' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f87171' }}>
                  <Trash2 size={20} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>5. Safe Two-Step Workload Destruction</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
                The platform enforces controlled, complete teardown to avoid orphaned cloud resources or residual IAM permissions.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', background: 'rgba(0, 0, 0, 0.25)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ background: '#3b82f6', color: '#fff', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, flexShrink: 0 }}>
                    1
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>Two-Step Confirmation</div>
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                      Click the red <strong>Destroy</strong> icon on the target deployment row. You must explicitly type the exact Deployment ID (e.g. <code>dep-bdba18c9</code>) into the prompt to enable the confirmation button.
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', background: 'rgba(0, 0, 0, 0.25)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ background: '#3b82f6', color: '#fff', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, flexShrink: 0 }}>
                    2
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>Lock & Teardown Execution</div>
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                      The deployment status transitions to <code>DESTROYING</code> and the lock is held. GitHub Actions runs <code>terraform destroy</code> against the isolated state key.
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', background: 'rgba(0, 0, 0, 0.25)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ background: '#3b82f6', color: '#fff', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, flexShrink: 0 }}>
                    3
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>Terminal State Enforcement</div>
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                      Once the destroy callback arrives, the deployment status permanently becomes <code>DESTROYED</code> and the lock is cleared. Re-destroying an already-destroyed deployment is rejected with <code>HTTP 422</code>.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 6: MODEL ARMOR */}
          {activeSection === 'governance' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fbbf24' }}>
                  <ShieldCheck size={20} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>6. Model Armor & AI Governance</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
                The <strong>Governance & Model Armor</strong> tab allows you to inspect and test enterprise AI safety guardrails in real time.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                <div className="glass-card" style={{ padding: '16px' }}>
                  <span className="badge badge-failed" style={{ marginBottom: '8px' }}>MODE: BLOCK</span>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>Hard Rejection</div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Immediate error returned when prompt injections, jailbreaks, or toxic patterns are detected.
                  </p>
                </div>

                <div className="glass-card" style={{ padding: '16px' }}>
                  <span className="badge badge-pending" style={{ marginBottom: '8px' }}>MODE: REDACT</span>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>Automated Redaction</div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Sensitive identifiers (SSN, credit card, API keys) are masked with <code>[REDACTED]</code> before processing.
                  </p>
                </div>

                <div className="glass-card" style={{ padding: '16px' }}>
                  <span className="badge badge-active" style={{ marginBottom: '8px' }}>MODE: ALLOW_WITH_AUDIT</span>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>Audited Execution</div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Permits execution while writing security telemetry to the immutable Firestore audit ledger.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 7: CLI REFERENCE */}
          {activeSection === 'cli' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
                  <Terminal size={20} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>7. IDP CLI Command Reference</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
                Developers and automated build scripts can perform all platform operations using the Python command-line interface under <code>cli/main.py</code>.
              </p>

              {[
                {
                  title: 'Authenticate & Obtain Token',
                  cmd: 'uv run python cli/main.py login --username admin_gov --password "AdminPass123!"',
                },
                {
                  title: 'List Governed Templates',
                  cmd: 'uv run python cli/main.py templates list',
                },
                {
                  title: 'Submit Provisioning Request',
                  cmd: 'uv run python cli/main.py requests create --template t1-agent-engine --workspace default --env dev --input agent_name="cli-agent" --input model_name="gemini-2.5-flash" --input region="us-central1"',
                },
                {
                  title: 'Check Request Execution Telemetry',
                  cmd: 'uv run python cli/main.py requests status --request-id req-<id>',
                },
                {
                  title: 'List Deployments in Workspace',
                  cmd: 'uv run python cli/main.py deployments list --workspace default',
                },
                {
                  title: 'Tear Down & Destroy Workload',
                  cmd: 'uv run python cli/main.py deployments destroy --deployment-id dep-<id>',
                },
              ].map((item, idx) => (
                <div key={idx} style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#93c5fd', marginBottom: '6px' }}>
                    {item.title}
                  </div>
                  <div
                    style={{
                      background: '#0a0e1a',
                      borderRadius: '8px',
                      padding: '12px 16px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      border: '1px solid var(--border-subtle)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8rem',
                    }}
                  >
                    <code style={{ color: '#f1f5f9', wordBreak: 'break-all' }}>{item.cmd}</code>
                    <button
                      onClick={() => handleCopy(item.cmd, idx)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: copiedIndex === idx ? '#34d399' : 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        marginLeft: '12px',
                        flexShrink: 0,
                      }}
                      title="Copy command"
                    >
                      {copiedIndex === idx ? <Check size={16} /> : <Copy size={16} />}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

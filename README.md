# Internal Developer Platform (IDP) for Governed Agentic AI on GCP

[![CI Validation](https://github.com/idp-platform-org/idp-platform/actions/workflows/validate-repository.yml/badge.svg)](https://github.com/idp-platform-org/idp-platform/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.9+-7b42bc.svg)](https://www.terraform.io/)
[![GCP WIF](https://img.shields.io/badge/Auth-Workload%20Identity%20Federation-4285F4.svg)](https://cloud.google.com/iam/docs/workload-identity-federation)

A secure, repeatable, self-service Internal Developer Platform (IDP) control plane designed to provision, govern, monitor, and destroy agentic-AI workloads on Google Cloud Platform.

---

## 🚀 Key Platform Features

- **Control Plane Architecture**: Asynchronous FastAPI control plane running on Cloud Run backed by Firestore Native mode.
- **Zero Static Service Account Keys**: 100% keyless machine authentication via GitHub Actions OIDC + GCP Workload Identity Federation (WIF).
- **Argon2id + 60-Minute JWTs**: Secure user authentication with `token_version` revocation.
- **24-Hour TTL Idempotency**: SHA-256 payload digest verification preventing duplicate or conflicting provisioning requests.
- **Atomic Deployment Locking**: Concurrency safety preventing simultaneous mutations or premature teardowns.
- **Parameter-Bound Pipeline Callbacks**: Strict OIDC ID token validation, monotonic sequence counters, and parameter context binding.
- **Governed AI Templates**:
  - **T1: Vertex AI Agent Engine**: Immutable ADK agent packaging with pre-activation smoke test verification.
  - **T2: Managed Vertex AI RAG Engine**: Managed corpus creation with bounded document ingestion and retrieval validation.
  - **T3: Cloud Run Agent Service**: Containerized FastAPI + ADK agent runtime with private IAM invocation and horizontal auto-scaling.
  - **T4: Model Armor & Governance Controls**: Prompt injection defense, PII redactions (SSN/CC/Email), Cloud Monitoring alert policies, and automated TTL cleanup.
- **Production Approval Gate**: GitHub Environment review enforcement before production Terraform execution.
- **React Developer Portal**: Modern, cybernetic dark-themed UI for template discovery, request tracking, deployment management, and Model Armor inspection.
- **IDP CLI**: Lightweight terminal client mirroring portal capabilities.

---

## 🏗️ Repository Architecture

```text
├── docs/                 Architecture diagrams, security model, API contract, runbooks, ADRs
├── infra/                Bootstrap Terraform stacks (State bucket, Firestore, WIF, Secret Manager, Cloud Run)
├── api/                  FastAPI control plane backend (auth, lifecycle, callbacks, governance, repositories)
├── portal/               React developer portal frontend (Vite + Vanilla CSS design tokens)
├── cli/                  Python CLI client (`idp login`, `idp request`, `idp deployments`, etc.)
├── templates/
│   ├── t1-agent-engine/      Vertex AI Agent Engine ADK template
│   ├── t2-managed-rag/       Vertex AI Managed RAG Engine with RagManagedDb
│   ├── t3-cloud-run-agent/   Cloud Run containerized agent template
│   └── t4-governance/        Model Armor guardrails and Cloud Monitoring alert policies
├── .github/
│   ├── actions/          Reusable composite actions (WIF auth, Terraform lifecycle, callbacks, smoke tests)
│   └── workflows/        CI validation and lifecycle workflows (deploy-t1..t4, cleanup)
└── scripts/              Bootstrap and operational utility scripts
```

---

## ⚡ Quick Start: Local Development

### 1. Backend Control Plane
```bash
# Set up virtual environment using uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run test suite with full coverage
pytest -v --cov=api/app --cov=templates

# Start FastAPI control plane locally
uvicorn api.app.main:app --reload --port 8000
```

### 2. Frontend React Portal
```bash
cd portal
npm install
npm run dev
# Portal accessible at http://localhost:3000 (proxies API requests to :8000)
```

### 3. IDP CLI
```bash
# Login using demo platform admin credentials
idp login -u admin_gov -p AdminPass123! --url http://localhost:8000

# Discover templates
idp templates list

# Submit provisioning request
idp requests create --template t1-agent-engine --workspace ws-dev --environment dev

# Test Model Armor guardrails
idp governance inspect "Check customer SSN: 111-22-3333" --mode redact
```

---

## 🧪 Testing & Quality Gates

Run all linting and test suites:
```bash
# Code formatting and linting
ruff check .
ruff format --check .

# Full test suite (74 unit and integration tests)
pytest -v
```

---

## 📖 Documentation & Runbooks

- [Architecture Overview](docs/architecture.md)
- [Security Model & Trust Boundaries](docs/security-model.md)
- [REST API Contract](docs/api-contract.md)
- [Platform Bootstrap Runbook](docs/runbooks/bootstrap.md)
- [Incident & Break-Glass Runbook](docs/runbooks/incident-and-break-glass.md)
- [Destroy-All Teardown Runbook](docs/runbooks/destroy-all.md)
- [Key Rotation Runbook](docs/runbooks/key-rotation.md)
- [Architecture Decision Records (ADR 001-006)](docs/adr/)

# Agent Instructions: Internal Developer Platform for Agentic AI on GCP

## Mission

Build a secure, repeatable internal developer platform (IDP) that provisions and destroys governed agentic-AI workloads on Google Cloud Platform.

The platform is a control plane—not a direct infrastructure execution environment. The control plane accepts authenticated and authorized requests, records lifecycle state, dispatches version-pinned GitHub Actions workflows, receives trusted pipeline callbacks, and exposes only safe operational metadata.

```text
Authenticated API request
  → authorization and validation
  → GitHub Actions workflow dispatch (fine-grained PAT from Secret Manager)
  → WIF-authenticated Terraform plan/apply
  → readiness validation
  → authenticated callback
  → ACTIVE deployment record
  → authorized destroy request
  → WIF-authenticated Terraform destroy
  → DESTROYED deployment record
```

Do not optimize for UI breadth, framework breadth, or production-scale tenancy before this flow is demonstrably correct, secure, tested, and repeatable.

---

## Primary Delivery Order

Implement features in this exact order unless explicitly changed:

1. Foundation and identity.
2. T1 Agent Engine manual deployment and destruction through GitHub Actions using WIF.
3. FastAPI authentication and secret retrieval.
4. Request, deployment, audit, callback, and idempotency domain model.
5. Full API-driven T1 lifecycle.
6. Callback reliability, dead-lettering, and reconciliation.
7. T3 Cloud Run agent path.
8. T2 managed Vertex AI RAG path.
9. T4 governance controls.
10. Production GitHub Environment approval gate.
11. Portal and optional CLI.
12. Retrospective, runbooks, and final teardown verification.

---

## Scope Boundaries

### Phase 0 and Phase 1: Permitted Scope

Until Phase 1 T1 lifecycle exit criteria are satisfied, work only on:
- Monorepo baseline, CI validation, and GCP bootstrap Terraform.
- State bucket, Firestore Native database, Secret Manager, service accounts, WIF, and Cloud Run API.
- FastAPI control plane with Argon2id auth, 60-minute JWTs, and fine-grained PAT workflow dispatch.
- Firestore domain models, append-only callback ledgers, deployment locking, and idempotency.
- Immutable T1 Agent on Agent Engine template (ADK only).
- Request/deployment state machine, pipeline callbacks, backoff retries, dead-letter storage, and reconciliation.
- Direct automated tests supporting the T1 golden path.

### Explicitly Deferred Scope

Do not introduce these unless explicitly requested:
- React portal before API lifecycle is fully automated and tested.
- LangGraph support or arbitrary agent frameworks.
- Vertex AI Search, Cloud SQL, AlloyDB, pgvector, Chroma, LanceDB, or Firestore vector search.
- API Gateway or GKE.
- Enterprise SSO, OAuth, SAML, registration UI, refresh tokens, or user-management UI.
- Service-account JSON keys.
- Developer direct access to workload data planes.
- Arbitrary model, region, or Terraform selection.

---

## Non-Negotiable Security Rules

- **Zero JSON Keys**: Never create, download, commit, or use service-account JSON keys.
- **Workload Identity Federation**: All GCP provisioning and pipeline callbacks must use GitHub Actions OIDC + GCP WIF.
- **Secrets Management**: Store JWT signing secrets and GitHub workflow dispatch PAT in Google Secret Manager; retrieve at runtime using the API runtime service account.
- **Least Privilege**: Do not grant Owner or Editor roles. Separate API runtime, pipeline, and workload service accounts.
- **Token Handling**: 60-minute JWT access tokens signed with Secret Manager key. Store portal tokens in browser `localStorage`.
- **Sensitive Data & State**: Never expose Terraform state, secret values, bearer tokens, or raw credentials in responses, logs, or build artifacts.

---

## Repository Structure & Boundaries

```text
docs/                 Architecture, spec, ADRs, API contract, runbooks
infra/                Bootstrap stacks, reusable Terraform modules, environment composition
api/                  FastAPI control plane only
portal/               React portal only (deferred until API readiness)
cli/                  Optional API client (never direct infrastructure access)
templates/            Versioned, immutable infrastructure templates
.github/actions/      Reusable CI/CD composite actions
.github/workflows/    Versioned lifecycle workflows
scripts/              Controlled operational/bootstrap scripts
.agents/skills/       Lazy-loaded specialized agent skills
```

---

## Technology Stack Summary

| Component | Required Technology |
|---|---|
| Control Plane API | FastAPI / Python |
| Database & Metadata | Firestore Native mode |
| Infrastructure Provisioning | Terraform executed via GitHub Actions |
| CI/CD Authentication | GitHub OIDC + GCP Workload Identity Federation (WIF) |
| Workflow Dispatch | GitHub API dispatched via fine-grained PAT in Secret Manager |
| API Auth | Argon2id password hashes, 60-minute JWT bearer tokens |
| Secret Management | Google Secret Manager |
| Terraform State | Protected GCS backend with versioning and isolated state keys |
| First Agent Framework | ADK only (Agent Engine) |
| Portal Token Persistence | Browser `localStorage` (when portal phase begins) |

---

## Deep-Dive Skills Reference

For specific implementation rules, schema layouts, state machines, and testing guidelines, consult the corresponding lazy-loaded skills under `.agents/skills/`:

- **Firestore & Domain Models**: Read [`firestore-domain-model`](file:///.agents/skills/firestore-domain-model/SKILL.md)
- **FastAPI Control Plane**: Read [`secure-fastapi-control-plane`](file:///.agents/skills/secure-fastapi-control-plane/SKILL.md)
- **GitHub Actions & Callbacks**: Read [`github-actions-pipeline-callbacks`](file:///.agents/skills/github-actions-pipeline-callbacks/SKILL.md)
- **Template Authoring**: Read [`template-authoring`](file:///.agents/skills/template-authoring/SKILL.md)
- **Terraform, IAM & WIF**: Read [`terraform-gcp-wif`](file:///.agents/skills/terraform-gcp-wif/SKILL.md)
- **Testing & Quality Gates**: Read [`testing-and-quality-gates`](file:///.agents/skills/testing-and-quality-gates/SKILL.md)
- **Security Audit**: Read [`security-review`](file:///.agents/skills/security-review/SKILL.md)

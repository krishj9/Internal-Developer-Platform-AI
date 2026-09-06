# POC Specification: Internal Developer Platform for Agentic AI Infrastructure on GCP

**Status:** Draft v2.1 — revised architecture, authentication storage, and execution model  
**Owner:** Platform Engineering  
**Primary build target:** Google Cloud Platform  
**Supersedes:** `idp-poc-spec-agentic-ai-gcp-v2-0.md`  
**Last updated:** 2026-09-05

## Changelog

- **v2.1** — Incorporates architectural review decisions: establishes 60-minute JWT token lifetime with `localStorage` client persistence to preserve session across refreshes; defines narrowly scoped GitHub credential (fine-grained PAT with Actions write in Secret Manager) for workflow dispatch; adds callback failure recovery (exponential backoff retry, dead-letter storage, admin reconciliation); details Firestore compound query patterns and index requirements; formalizes template publishing workflow; enforces per-user request submission rate limiting and active-deployment concurrency locking; locks public Cloud Run API ingress with application-level JWT verification and Firebase Hosting CORS; removes all calendar timelines in favor of milestone-based criteria.
- **v2.0** — Replaces IAP-based portal authentication with preconfigured application credentials verified using adaptive password hashes and short-lived JWT bearer tokens. Retains GitHub Actions Workload Identity Federation (WIF) for CI/CD and extends it to authenticated pipeline callbacks. Adds role-based authorization, immutable template references, idempotency, output classification, explicit request/deployment state machines, readiness contracts, token/key handling, and TTL/orphan cleanup.
- **v1.2** — React SPA replaces Streamlit; local profile is mock-only; UI authentication via IAP.

---

## 1. Purpose and Scope

### 1.1 Problem statement

Teams building agentic AI solutions on GCP repeatedly assemble similar infrastructure: agent runtimes, retrieval systems, Cloud Run services, service identities, observability, safety controls, and release workflows. A lightweight Internal Developer Platform (IDP) provides self-service, opinionated golden paths so developers can provision compliant AI infrastructure in minutes rather than days without needing deep Terraform, IAM, or GCP-service knowledge.

### 1.2 POC goals

- Provide self-service provisioning of three production-shaped agentic-AI templates, with a fourth governance profile/template.
- Deliver an end-to-end, auditable workflow: authenticated request → validation → plan → approval where required → apply → readiness verification → registration → teardown.
- Bake in low-cost governance: required labels, least-privilege service accounts, keyless CI/CD, cost controls, audit records, and Model Armor integration.
- Provide a React portal with preconfigured user login and an API that supports bearer-token authorization.
- Preserve a CLI and YAML contract for technical users and automation.
- Create reusable ADRs and an AWS↔GCP comparison as educational outputs.

### 1.3 Non-goals

- A general-purpose IDP for non-AI workloads.
- A full portal framework or Backstage adoption.
- Production-grade HA/DR, multi-project tenancy, folder design, or organization-wide landing-zone architecture.
- GKE-based workload hosting.
- Direct developer IAM data-plane access to provisioned resources from laptops.
- Enterprise identity federation, SSO, or custom IdP integration. This POC uses preconfigured application users.
- A full user-administration interface, password reset process, or self-service onboarding.

### 1.4 Personas

| Persona | Primary need |
|---|---|
| AI/application developer | Provision approved agent infrastructure without deep GCP, IAM, or Terraform expertise |
| Platform engineer | Publish, version, and govern templates; operate the provisioning workflow |
| Approver | Gate production requests after Terraform plan review |
| Platform administrator | Bootstrap users, manage templates, handle break-glass operations, and perform POC cleanup |

### 1.5 Locked decisions

| Decision | Choice |
|---|---|
| User base | One internal team |
| Cloud scope | One GCP project for the POC |
| IaC engine | Terraform |
| Provisioning executor | GitHub Actions workflows |
| CI/CD cloud authentication | GitHub OIDC + GCP Workload Identity Federation; no service-account keys |
| Workflow dispatch credential | Narrowly scoped GitHub credential (fine-grained PAT with repo Actions write) stored in Secret Manager |
| Portal/API authentication | Preconfigured username/password verified by API against adaptive password hashes; 60-minute JWT bearer access tokens stored in browser `localStorage` |
| API authorization | Role- and workspace-based authorization enforced by FastAPI |
| Portal UI | React SPA built with Vite and hosted on Firebase Hosting |
| API networking & CORS | Cloud Run API with public ingress, JWT-protected endpoints, and CORS configured for Firebase Hosting origin |
| Primary interface | React portal plus CLI/YAML contract |
| Runtime targets | Vertex AI Agent Engine and Cloud Run only |
| Local access | Mock-only local profile; no platform-managed cloud endpoints, credentials, or data-plane IAM roles on developer laptops |
| Approval policy | Auto-continue for `dev`; GitHub Environment required reviewers for `prod` |
| Vector default | Vertex AI RAG Engine with RagManagedDb |
| POC intent | Throwaway/educational, while retaining inexpensive security and platform practices |

---

## 2. Architecture Principles and Invariants

### 2.1 Core architecture principles

1. **Terraform is the infrastructure source of truth.** The API coordinates requests; it does not directly provision infrastructure through cloud SDKs.
2. **GitHub Actions is the provisioning executor.** It runs plan, apply, destroy, package, and narrowly scoped gcloud/REST fallback steps.
3. **All machine access is short-lived and keyless.** GitHub Actions uses WIF; Cloud Run uses its attached service account; no service-account JSON keys are created or stored.
4. **Authentication and authorization are separate.** Login establishes a human identity; API authorization determines which templates, workspaces, environments, and operations that identity may use.
5. **Every request is idempotent and auditable.** A retry cannot create duplicate infrastructure for the same intended operation.
6. **Every deployment has an isolated Terraform state prefix, immutable template reference, owner, labels, and teardown path.**
7. **A deployment becomes `ACTIVE` only after its template-specific readiness check succeeds.** A successful Terraform apply alone is insufficient.
8. **Sensitive runtime configuration never reaches the developer laptop or browser.** The `gcp` configuration profile is delivered only to deployed workloads through runtime environment variables and/or Secret Manager.
9. **The portal cannot claim authority that the API has not verified.** The server derives requester identity, roles, ownership, and permitted workspace scope from validated credentials and server-side records.
10. **Budget alerts are notifications, not hard spend limits.** Enforced template limits, expiration, orphan detection, and teardown provide the actual cost-control mechanism.

### 2.2 Control-plane boundaries

| Plane | Responsibility | Not responsible for |
|---|---|---|
| React portal | Login, template discovery, request submission, request/deployment status display | Credential verification, authorization decisions, provisioning, direct GCP data access |
| FastAPI control plane | Login, JWT issuance/verification, authorization, input validation, request records, GitHub dispatch, status registration | Direct Terraform execution or broad cloud provisioning |
| GitHub Actions execution plane | Terraform plan/apply/destroy, packaging, approved gcloud/REST fallbacks, readiness tests, status callbacks | Human authentication and final portal authorization |
| Terraform state plane | Desired-state tracking and lifecycle of managed infrastructure | Application-level request status or user authorization |
| Workload data plane | Runs deployed agents and accesses approved runtime resources | Platform administration, template changes, or user login |

---

## 3. Build vs. Adopt

### ADR-001 — Build a thin platform layer; do not adopt Backstage

**Decision:** Use a thin custom control plane consisting of FastAPI, React, GitHub Actions, Terraform, Firestore, and GCS. Do not adopt Backstage or another portal framework for this POC.

**Rationale:** At one team and fewer than ten templates, the platform problem is governed provisioning, not catalog UI sophistication. Backstage adds operational and integration overhead without materially improving the proof-of-concept hypothesis. The portal is intentionally thin; the API, template contract, pipeline, state, and governance controls are the platform core.

### 3.1 Out-of-box building blocks

| Building block | POC use |
|---|---|
| `google-agents-cli` / agents-cli | Scaffold/reference source for Agent Engine and Cloud Run golden paths; pin version before adoption |
| Vertex AI Agent Engine | Managed runtime for T1 agent deployments |
| Vertex AI RAG Engine + RagManagedDb | Default managed retrieval backend for T2 |
| Cloud Run | Runtime target for T3 and FastAPI control plane |
| Model Armor | Guardrail policy used by agent/service reference implementations and governance profile |
| Terraform Google provider and Google-maintained Vertex AI modules | Primary resource provisioning mechanism where coverage exists |
| Cloud Foundation Fabric | Reference source for WIF, IAM, project, and foundation patterns |
| GitHub Actions + WIF | Keyless provisioning execution and authenticated pipeline callbacks |
| Firestore Native mode | Platform metadata: users, workspaces, templates, requests, deployments, callback events |
| GCS | Terraform state, agent artifacts, and controlled RAG source objects |
| Secret Manager | JWT signing secret and runtime secrets; no secrets in source, Terraform state, or browser assets |
| Firebase Hosting | React SPA hosting |

### 3.2 Verified implementation assumptions

Before implementation depends on them, validate these assumptions in Phase 0:

- The pinned `agents-cli` version supports the chosen GitHub Actions or exportable Terraform workflow. Fallback: a thin in-repository reference implementation or Cloud Build trigger invoked through the same API contract.
- The current Terraform provider supports the intended `google_vertex_ai_reasoning_engine` packaging/deployment path. Fallback: package through a pinned composite GitHub Action based on the validated deployment flow.
- RAG corpus and document lifecycle operations have sufficient Terraform coverage. Fallback: a versioned, idempotent gcloud/REST pipeline step, with its inputs and outputs recorded in the deployment state.
- The selected region supports every POC service and model used by the templates. Default assumption: `us-central1`; confirm before template implementation.

---

## 4. Architecture Overview

```text
                                 ┌─────────────────────────────┐
                                 │ React SPA                    │
                                 │ Firebase Hosting             │
                                 │ Login + bearer-token client  │
                                 └──────────────┬──────────────┘
                                                │ HTTPS /api/**
                                                │ Authorization: Bearer <JWT>
                                                ▼
Developer / Portal User ───────────────► ┌─────────────────────────────┐
                                          │ FastAPI Request API          │
CLI (future token login or IAM mode) ───► │ Cloud Run                   │
                                          │ - authn/authz                │
                                          │ - request validation         │
                                          │ - Firestore metadata         │
                                          │ - workflow dispatch          │
                                          └──────┬───────────┬──────────┘
                                                 │           │
                                                 │           └────► Secret Manager
                                                 │                   JWT signing secret
                                                 ▼
                                        ┌─────────────────────────────┐
                                        │ GitHub Actions               │
                                        │ GitHub OIDC → GCP WIF        │
                                        │ template-specific SA         │
                                        │ plan → approval → apply      │
                                        └──────┬───────────┬──────────┘
                                               │           │
                                               │           └────► Authenticated callback
                                               │                  Google ID token to API
                                               ▼
          ┌────────────────────────────────────────────────────────────────────────────┐n          │ GCP project                                                                │
          │ Agent Engine | Cloud Run | RAG Engine | Firestore | GCS | Model Armor       │
          │ Cloud Monitoring | Pub/Sub | Secret Manager                                  │
          └────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
                                  ┌─────────────────────────────┐
                                  │ Platform state               │
                                  │ GCS: Terraform state         │
                                  │ Firestore: catalog/workflow  │
                                  └─────────────────────────────┘
```

### 4.1 Components

| Component | Choice | Responsibility |
|---|---|---|
| React portal | React + Vite SPA on Firebase Hosting | Login, template catalog, parameter form, request submission, request/deployment status. Holds access token in browser `localStorage`. |
| Request API | FastAPI on Cloud Run | User authentication, JWT issuance, authorization, schema validation, idempotency, Firestore records, workflow dispatch, callback validation, API responses. Enforces CORS for Firebase Hosting origin. |
| API runtime identity | `idp-api-runtime@PROJECT_ID.iam.gserviceaccount.com` | Firestore read/write, Secret Manager access to JWT signing key and GitHub dispatch token (`idp-github-dispatch-token`), Pub/Sub publish. No broad provisioning roles. |
| Template registry | Git monorepo | Immutable, versioned Terraform modules, `template.yaml`, schemas, defaults, cost tier, readiness tests, and workflow definitions. |
| Provisioning pipeline | GitHub Actions workflows | Terraform plan/apply/destroy, packaging, gcloud/REST fallback steps, readiness tests, callback posting. |
| WIF trust boundary | GCP Workload Identity Pool/provider | Exchanges GitHub OIDC tokens only for approved org/repository/workflow/ref claims; permits limited service-account impersonation. |
| Terraform state | GCS backend | Independent state prefix per deployment: `<template-id>/<deployment-id>`. |
| Metadata store | Firestore Native mode | Users, workspaces, templates, requests, deployments, callback event ledger, audit metadata. |
| Secret store | Secret Manager | JWT signing secret, narrowly scoped GitHub dispatch token (`idp-github-dispatch-token`), and explicitly required runtime secrets. |
| Notifications | Pub/Sub to Slack webhook function | Provisioning success/failure and cleanup notifications. |

### 4.2 Developer configuration contract: `idp-config.yaml`

Agent/application code must obtain all environment-specific configuration through the platform-generated configuration contract. Endpoints, buckets, resource names, and credentials must not be hard-coded in agent code.

```yaml
version: "1.0"
metadata:
  workspace: policy-qa
  deployment_id: rag-a1b2c3
  template: rag-stack
  template_version: "2.0.0"

profiles:
  local:
    llm: local-stub
    retrieval:
      type: mock_local_directory
      path: ./dev_context/
    session: memory://

  gcp:
    # Injected only at deploy/runtime. Never returned by API, committed,
    # or distributed to developer machines.
    llm: vertexai/gemini-flash-class
    retrieval:
      type: rag_engine
      endpoint: <runtime-injected>
    session: firestore://<runtime-injected>
```

Rules:

- `IDP_PROFILE=local` is the default outside deployed workloads.
- The local profile contains mocks/emulators only. A developer may use a personally managed local test key only when allowed by team policy; it is never platform-managed.
- The pipeline sets `IDP_PROFILE=gcp` and injects the GCP profile into workloads at deploy time.
- The API endpoint `GET /deployments/{id}/config` returns only metadata and the `local` profile.
- The `gcp` profile is classified as sensitive runtime configuration and is never exposed through the portal or API response.

### 4.3 Workspaces and naming

A workspace groups related deployments under an owner, labels, access scope, and optional shared runtime identity.

- Firestore record: `workspaces/{workspace-name}`.
- Optional workspace service account: `idp-ws-<workspace>@<project>.iam.gserviceaccount.com`.
- Deployment resources use `idp-<workspace>-<resource-type>-<short-hash>`.
- The short hash is deterministically derived from the deployment ID.
- Every resource carries the labels: `platform=idp-poc`, `template`, `template_version`, `deployment_id`, `workspace`, `owner`, `team`, `env`, `cost_center`, and `expires_at` where applicable.

---

## 5. Authentication and Authorization

### 5.1 User authentication

The portal uses preconfigured application users. The browser posts credentials over HTTPS to FastAPI. The API validates the password against a stored adaptive password hash and returns a signed, short-lived access token.

**Required controls:**

- Use **Argon2id** for password hashing. bcrypt is acceptable only if Argon2id is not practical in the selected application stack.
- Do not use SHA-256, SHA-1, MD5, or any general-purpose hash for passwords.
- Do not store plaintext passwords, reversible password encryption, or password values in source code, Firebase configuration, Terraform variables, GitHub Actions logs, or browser assets.
- Store password hashes in Firestore user records. Each hash includes a unique salt and algorithm work parameters.
- Use HTTPS for all portal and API traffic.
- Return a generic login failure response; do not reveal whether a username exists.
- Apply basic login rate limiting and audit failed login attempts. For this internal POC, a simple per-user and per-source-IP limit is sufficient.

### 5.2 Token contract

On successful login, the API issues a JWT access token with a 60-minute lifetime (3600 seconds).

Required token claims:

```json
{
  "sub": "user-123",
  "username": "prasad",
  "role": "platform_admin",
  "workspaces": ["policy-qa"],
  "token_version": 1,
  "iss": "idp-poc-api",
  "aud": "idp-poc-portal",
  "iat": 1788630000,
  "exp": 1788633600,
  "jti": "unique-token-id"
}
```

Rules:

- The React client stores the access token in browser `localStorage` so that user sessions persist across page refreshes and tab navigations during provisioning workflows.
- The client sends `Authorization: Bearer <access-token>` for protected API calls.
- On HTTP `401 Unauthorized` or explicit logout, the client removes the access token from `localStorage` and redirects to the login screen.
- Refresh tokens remain out of scope for the POC; the 60-minute token lifetime paired with `localStorage` persistence eliminates re-login friction while retaining token expiration bounds.
- The API validates signature, issuer, audience, expiry, token version, and user active status on every protected operation.
- Disable/revoke a user by setting `active=false` or incrementing `token_version` in the Firestore user record.
- Store the JWT signing secret in Secret Manager only. The Cloud Run API runtime service account receives secret access only for that secret.
- Use a `kid` JWT header so signing-key rotation can be introduced without changing the token contract.

### 5.3 User records

```yaml
users/{user_id}:
  username: prasad
  display_name: Prasad Jammula
  password_hash: "$argon2id$v=19$..."
  role: platform_admin
  workspaces:
    - policy-qa
  active: true
  token_version: 1
  created_at: <timestamp>
  updated_at: <timestamp>
```

User bootstrap is an administrative script or controlled operational procedure. A user-management UI is not part of this POC.

### 5.4 Authorization model

| Role | Allowed operations |
|---|---|
| `developer` | List templates; submit permitted `dev` requests to authorized workspaces; view own and workspace-authorized records; destroy own eligible dev deployments |
| `approver` | View eligible production plans and approve/reject through GitHub Environment protection; no authority to modify request inputs after plan generation |
| `platform_admin` | View and operate all workspaces; publish/deprecate templates; bootstrap/disable users; rerun eligible workflows; perform documented break-glass actions |
| `pipeline` | Call only pipeline callback endpoint for runs it owns; execute only the permissions granted to its template-specific service account |

Authorization rules:

- FastAPI derives requester identity from the verified token. Client-provided `owner`, `requester`, `role`, or permitted-workspace fields are ignored.
- Workspace access is checked server-side for all request, read, and destroy operations.
- A developer may not submit `prod` requests unless explicitly granted that role/capability; the GitHub Environment approval is a second control, not a substitute for API authorization.
- The server creates audit fields and resource labels; the client cannot override them.

### 5.5 API and pipeline identities

The following identities are deliberately distinct:

| Identity | Purpose | Scope |
|---|---|---|
| Portal user JWT subject | Human portal/API access | User authorization only; never GCP workload access |
| `idp-api-runtime` service account | Cloud Run FastAPI runtime | Firestore, JWT signing secret, notifications, controlled dispatch support; no broad provisioning role |
| Template pipeline service accounts | GitHub Actions WIF execution | Per-template, least-privilege infrastructure provisioning and state access |
| Workspace/per-deployment workload identities | Agent/workload runtime | Only data-plane access required by the deployed service |
| Platform admin group | Existing break-glass access | Emergency operations; auditable and outside normal developer flow |

---

## 6. GitHub Actions and Workload Identity Federation

### 6.1 WIF is the CI/CD authentication mechanism

GitHub Actions uses GitHub-issued OIDC tokens and GCP Workload Identity Federation to obtain short-lived credentials and impersonate template-specific pipeline service accounts. No service-account JSON keys are created, downloaded, or stored.

```text
GitHub Actions workflow
  → GitHub OIDC token
  → GCP Workload Identity Pool/provider
  → approved template pipeline service account
  → Terraform / gcloud / REST / readiness steps
```

### 6.2 Trust constraints

The WIF provider and service-account bindings must constrain trust to the intended GitHub claims:

- Approved GitHub organization/owner.
- Approved repository, such as the IDP template monorepo.
- Approved workflow file or workflow identity where supported.
- Approved protected branch/ref and/or GitHub Environment.
- Separate service accounts for distinct templates and environments where the extra setup is reasonable.

Illustrative identity pattern:

| GitHub workflow context | May impersonate |
|---|---|
| `idp-platform`, T1 deploy workflow, `dev` environment | `idp-pipeline-t1-dev@PROJECT_ID.iam.gserviceaccount.com` |
| `idp-platform`, T1 deploy workflow, `prod` environment | `idp-pipeline-t1-prod@PROJECT_ID.iam.gserviceaccount.com` |
| `idp-platform`, T2 deploy workflow, `dev` environment | `idp-pipeline-t2-dev@PROJECT_ID.iam.gserviceaccount.com` |

### 6.3 Pipeline callback authentication

Pipeline status callbacks do not use human JWTs or a shared webhook secret.

1. The workflow authenticates to GCP through WIF.
2. It impersonates its template-specific pipeline service account.
3. It obtains a short-lived Google OIDC ID token with the Cloud Run API URL as the audience.
4. It invokes `POST /callbacks/pipeline` with `Authorization: Bearer <Google-ID-token>`.
5. Cloud Run IAM allows invocation only from approved pipeline service accounts.
6. FastAPI validates callback identity, request/run binding, event sequence, and legal state transition before updating Firestore.

The API must reject callbacks that do not match the original request’s repository, workflow, run ID, template ID/version, deployment ID, and expected pipeline identity.

### 6.4 Workflow dispatch mechanism

The FastAPI control plane dispatches GitHub Actions workflows asynchronously via the GitHub REST API (`POST /repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches`):

- **Dispatch credential:** A narrowly scoped GitHub credential—specifically a fine-grained Personal Access Token (PAT) restricted strictly to the platform repository with `Actions: Read and write` permission only.
- **Credential storage:** The credential is stored securely in GCP Secret Manager under `idp-github-dispatch-token`. It is loaded into memory at startup by the `idp-api-runtime` service account. Static keys or broad personal tokens are prohibited.
- **Dispatch payload:** The API passes explicit execution context in the dispatch inputs: `request_id`, `deployment_id`, `template_id`, `template_version`, `template_commit_sha`, `operation` (`create` | `update` | `destroy`), `environment`, and parameter references.
- **Failure handling:** If the GitHub API returns an error or is unreachable during dispatch, the request transition to `DISPATCHED` fails, the request record is marked `FAILED` with failure code `DISPATCH_ERROR`, and an error response is returned to the caller.

---

## 7. Template Catalog and Golden Paths

Each template is an immutable release containing:

- Terraform module(s).
- `template.yaml` with JSON Schema inputs, defaults, allowed values, cost tier, and policy limits.
- Versioned workflow definition.
- Readiness test contract.
- Destroy workflow path.
- Documentation and examples.

Every request resolves a specific template version and immutable Git commit SHA at submission. Pipelines check out that exact commit. A mutable branch such as `main` must not be used as the deployment source for an accepted request.

### 7.1 POC templates

| ID | Template | Initial scope | Key inputs | Readiness contract |
|---|---|---|---|---|
| T1 | Agent on Agent Engine | ADK-only initial implementation; packaged and deployed to Vertex AI Agent Engine with dedicated runtime SA and baseline logging | model allow-list, region, workspace, env | Agent resource resolves and a non-sensitive smoke invocation succeeds |
| T2 | Managed RAG stack | Vertex AI RAG Engine + RagManagedDb + managed GCS source bucket/prefix + asynchronous import job | embedding model allow-list, ingestion preset, source prefix | Corpus exists, import succeeds, and a known test document is retrievable |
| T3 | Agent service on Cloud Run | ADK-based Cloud Run agent service; Firestore session state; IAM-protected invocation; controlled scaling | model allow-list, CPU/memory preset, concurrency/max instances, workspace, env | Revision is ready, authenticated health check succeeds, and smoke request succeeds |
| T4 | Governance profile/pack | Model Armor policy reference, Monitoring dashboard, alerts, labels, budget notifications, expiration/orphan controls | governance level, budget alert threshold, alert channel | Governance resources exist and the reference path demonstrates policy/telemetry wiring |

### 7.2 Deliberate template constraints

To preserve POC scope:

- T1 supports **ADK only** at first. LangGraph and other frameworks are follow-on variants after Agent Engine packaging is stable.
- T2 supports **RAG Engine + RagManagedDb only** at first.
- Vertex AI Search, Cloud SQL/AlloyDB pgvector, Chroma, LanceDB, and Firestore vector alternatives are documented but not built in the first POC.
- T3 chooses one initial access mode: Cloud Run IAM with CI/service-identity smoke testing. API Gateway and additional external access modes are deferred.
- T4 baseline labels, logs, and cost attribution are mandatory for T1–T3. T4 adds stricter policy/alerts and governance controls; it is not a reason to omit baseline governance.

### 7.3 Model and cost guardrails

Templates must use validated allow-lists and bounded presets rather than arbitrary resource inputs.

Examples:

- Approved Gemini Flash-class model IDs for POC agent workloads.
- Approved text-embedding model IDs for RAG.
- Maximum Cloud Run instance count, CPU, memory, and concurrency presets.
- Maximum RAG source document count and total source size.
- Fixed, versioned chunking/ingestion presets rather than unrestricted tuning values.
- Default `dev` expiry/TTL.

### 7.4 T2 ingestion contract

RAG infrastructure readiness and document ingestion readiness are distinct. Terraform success does not imply that documents are indexed and retrievable.

```yaml
source:
  type: gcs_prefix
  prefix: workspace/deployment/documents/

ingestion:
  preset: standard_small
  accepted_mime_types:
    - application/pdf
    - text/markdown
    - text/plain
  max_document_count: 100
  max_total_size_mb: 250

readiness:
  smoke_document_uri: gs://<managed-bucket>/<prefix>/smoke.md
  expected_retrieval_phrase: "IDP retrieval readiness marker"
```

---

## 8. Request, State, and Lifecycle Design

### 8.1 Request submission contract

```http
POST /requests
Authorization: Bearer <access-token>
Idempotency-Key: <client-generated-unique-key>
Content-Type: application/json
```

```json
{
  "template_id": "rag-stack",
  "template_version": "2.0.0",
  "workspace": "policy-qa",
  "environment": "dev",
  "parameters": {
    "ingestion_preset": "standard_small"
  }
}
```

The API:

1. Validates the bearer token and user authorization.
2. Applies per-user request submission rate limits (e.g. 5 requests/min, 20 requests/hour); returns `429 Too Many Requests` if exceeded.
3. Resolves workspace access, template version, and immutable template commit.
4. Validates input against the template JSON Schema and policy limits.
5. Calculates and stores a parameter digest.
6. Evaluates idempotency scoped to `(requester_user_id, idempotency_key)` with a 24-hour TTL:
   - If the exact key was previously submitted by the same user with identical payload, returns the prior accepted response (`202 Accepted` or current request status).
   - If the key was previously submitted with a different payload within the TTL, returns `409 Conflict`.
7. Evaluates deployment concurrency:
   - For update or destroy requests targeting an existing deployment, verifies that no active (non-terminal) request is currently executing for that deployment. Returns `409 Conflict` if a concurrent operation is in progress.
8. Creates a request record and dispatches the matching GitHub Actions workflow via the narrowly scoped dispatch credential.
9. Returns `202 Accepted` with `request_id` and status URL.

### 8.2 Request states

| State | Meaning |
|---|---|
| `SUBMITTED` | Request persisted and awaiting validation/dispatch |
| `VALIDATED` | Schema, policy, user, workspace, and idempotency checks passed |
| `DISPATCHED` | Workflow dispatch recorded |
| `PLANNING` | Pipeline is producing Terraform plan |
| `AWAITING_APPROVAL` | Production plan is awaiting required GitHub Environment approval |
| `APPLYING` | Pipeline is applying infrastructure changes |
| `VALIDATING` | Template readiness test is running |
| `SUCCEEDED` | Provision or destroy operation completed successfully |
| `FAILED` | Terminal operation failure with classified reason |
| `CANCELLED` | Request cancelled before irreversible execution where permitted |
| `EXPIRED` | Request not completed within defined workflow expiration window |

### 8.3 Deployment states

| State | Meaning |
|---|---|
| `PROVISIONING` | Create/update request is in progress |
| `ACTIVE` | Infrastructure and readiness verification succeeded |
| `UPDATE_PENDING` | Change request accepted but not yet executing |
| `UPDATING` | Update workflow is in progress |
| `DESTROY_PENDING` | Destroy request accepted |
| `DESTROYING` | Terraform destroy is in progress |
| `DESTROYED` | Teardown completed and resources are no longer active |
| `FAILED` | Deployment operation failed; inspect linked request/run |
| `DRIFTED` | Optional future state when drift detection identifies material difference |
| `EXPIRED` | Dev deployment exceeded TTL and is queued for or undergoing cleanup |

### 8.4 State-transition rules

- The API validates all transitions; callbacks cannot set arbitrary status values.
- Callbacks include a monotonically increasing `event_sequence`; duplicate callbacks are accepted idempotently but do not repeat side effects.
- Terminal states (`SUCCEEDED`, `FAILED`, `CANCELLED`, `EXPIRED`) cannot be changed except through a newly submitted, authorized lifecycle request.
- A deployment is locked against concurrent lifecycle operations: only one non-terminal request may target a deployment at any time. Concurrent requests are rejected with `409 Conflict`.
- A destroy request does not reuse the create request; it creates a distinct request linked to the deployment and requires its own `Idempotency-Key`.
- A request cannot change template version, parameters, workspace, or environment after plan generation. Submit a new request instead.

### 8.5 Pipeline callback payload

```json
{
  "request_id": "req-123",
  "deployment_id": "dep-a1b2c3",
  "template_id": "agent-engine",
  "template_version": "2.0.0",
  "template_commit_sha": "<immutable-git-sha>",
  "repository": "org/idp-platform",
  "workflow": "deploy-t1.yml",
  "github_run_id": "1234567890",
  "event_sequence": 4,
  "operation": "create",
  "status": "VALIDATING",
  "plan_artifact_url": "<authorized-artifact-reference>",
  "summary": "Terraform apply completed; smoke test started",
  "timestamp": "2026-09-05T17:00:00Z"
}
```

The callback event ledger is stored separately from the current request/deployment projection so audit history is append-only.

### 8.6 Callback failure recovery and reconciliation

To prevent orphaned deployment states when temporary network errors or Cloud Run restarts interrupt callback delivery:

1. **Pipeline retry:** The GitHub Actions `post-pipeline-callback` composite action implements 3 retry attempts with exponential backoff (delays of 5s, 15s, and 45s) upon receiving HTTP 5xx responses or connection timeouts.
2. **Dead-letter ledger:** If all retries are exhausted without a 200 response, the composite action writes the callback payload to the deployment's GCS state bucket under `callbacks/dead-letter/{request_id}/{event_sequence}.json` and logs a structured alert in the workflow run.
3. **Reconciliation endpoint:** Platform administrators can trigger `POST /admin/reconcile-callbacks` to scan the dead-letter prefix, replay missing callback payloads through the state machine, and advance or fail stuck requests deterministically.

---

## 9. API Contract

### 9.1 Authentication endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/login` | Verify username/password against stored adaptive password hash; issue 60-minute bearer access token |
| `GET` | `/auth/me` | Return authenticated identity, role, active status, and permitted workspaces |
| `POST` | `/auth/logout` | Optional POC endpoint; client removes token from `localStorage` |

### 9.2 User endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/templates` | List templates available to authenticated user, including schemas and safe defaults |
| `POST` | `/requests` | Submit create/update request; requires `Idempotency-Key` header; returns `202 Accepted` |
| `GET` | `/requests/{id}` | Read an authorized request, status, plan summary, and safe workflow metadata |
| `GET` | `/deployments` | List deployments within authorized owner/workspace/template scope |
| `GET` | `/deployments/{id}` | Read deployment detail and non-sensitive outputs |
| `GET` | `/deployments/{id}/config` | Return metadata and `local` config profile only |
| `POST` | `/deployments/{id}/destroy` | Submit authorized destroy request; requires `Idempotency-Key` header; returns `202 Accepted` |

### 9.3 Pipeline and admin endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/callbacks/pipeline` | WIF-authenticated, idempotent pipeline status callback. Caller uses a Google OIDC ID token; Cloud Run IAM and FastAPI validate identity and request/run binding. |
| `POST` | `/admin/reconcile-callbacks` | Platform admin endpoint to scan GCS dead-letter callbacks and replay state transitions for stuck runs. |

### 9.4 Error behavior

| Status | Meaning |
|---|---|
| `200` | Successful read or synchronous action |
| `202` | Request accepted for asynchronous processing |
| `400` | Invalid schema or invalid request format |
| `401` | Missing, invalid, expired, or revoked bearer token |
| `403` | Authenticated identity lacks required authorization |
| `404` | Resource does not exist or is outside authorized visibility scope |
| `409` | Conflicting lifecycle operation, active deployment concurrency lock, or idempotency key reused with different payload |
| `422` | Valid request format but failed policy/input constraints |
| `429` | Rate limit exceeded for request submissions |

---

## 10. Firestore Data Model

### 10.1 Collections

```text
users/{user_id}
workspaces/{workspace_name}
templates/{template_id#version}
requests/{request_id}
deployments/{deployment_id}
callback_events/{event_id}
audit_events/{event_id}
```

### 10.2 Core records

```yaml
workspaces/{workspace_name}:
  owner_user_id: user-123
  members: [user-123]
  labels: {}
  shared_service_account: idp-ws-policy-qa@PROJECT_ID.iam.gserviceaccount.com
  created_at: <timestamp>

requests/{request_id}:
  idempotency_key: <opaque-value>
  requester_user_id: user-123
  requester_username: prasad
  workspace: policy-qa
  template_id: rag-stack
  template_version: "2.0.0"
  template_commit_sha: <git-sha>
  operation: create
  environment: dev
  parameters: {}
  parameters_digest: <sha-256-digest>
  status: DISPATCHED
  github_repository: org/idp-platform
  github_workflow: deploy-t2.yml
  github_run_id: <run-id>
  status_sequence: 2
  pipeline_run_url: <url>
  failure_code: null
  failure_summary: null
  created_at: <timestamp>
  updated_at: <timestamp>

deployments/{deployment_id}:
  workspace: policy-qa
  template_id: rag-stack
  template_version: "2.0.0"
  template_commit_sha: <git-sha>
  state_prefix: rag-stack/dep-a1b2c3
  status: ACTIVE
  owner_user_id: user-123
  labels: {}
  cost_tier: low
  expires_at: <timestamp>
  non_sensitive_outputs: {}
  resource_inventory: []
  last_successful_run_id: <run-id>
  created_at: <timestamp>
  updated_at: <timestamp>
  destroyed_at: null
```

### 10.3 Output classification

| Classification | Examples | Allowed location and visibility |
|---|---|---|
| Public platform metadata | Deployment ID, template/version, workspace, status, labels | Firestore and authorized API responses |
| Internal operational metadata | Resource names, Cloud Run URL, dashboard link, workflow run link | Firestore; authorized workspace/platform users as appropriate |
| Sensitive runtime configuration | Internal retrieval endpoint, secret reference, runtime policy identifier | Workload environment/Secret Manager; not returned through portal API |
| Secret | Passwords, JWT signing key, API tokens, private certificates | Secret Manager only; never Firestore output fields, Terraform outputs, browser payloads, or logs |
| Prohibited | Terraform state, service-account keys, raw sensitive prompt/response data | Never exposed by platform API |

### 10.4 Required Query Patterns and Composite Indexes

Firestore requires defined composite indexes for compound queries used by the control plane and operational jobs. The repository must define and maintain `firestore.indexes.json` covering:

| Collection | Query Pattern | Filter Fields | Sort Fields | Purpose |
|---|---|---|---|---|
| `deployments` | List deployments by workspace and status | `workspace == X AND status == Y` | `created_at DESC` | Workspace deployment filtering in portal |
| `requests` | List requests by user | `requester_user_id == X` | `created_at DESC` | User request history view |
| `deployments` | Expired TTL scan | `status == ACTIVE AND expires_at <= NOW` | `expires_at ASC` | Scheduled cleanup and orphan detection |
| `callback_events` | Callback ledger validation | `request_id == X` | `event_sequence ASC` | Sequence verification and audit history |
| `requests` | Idempotency lookup | `idempotency_key == X AND requester_user_id == Y` | `created_at DESC` | Scoped idempotency checks |

### 10.5 Template Publishing Workflow

Templates are managed in Git and published to the Firestore metadata catalog through a governed release workflow:

1. **Tag release:** Platform engineers tag immutable releases in Git adhering to the pattern `templates/<template-id>/v<semver>` (e.g., `templates/t1-agent-engine/v2.0.0`).
2. **CI validation and publish:** A GitHub Actions workflow validates `template.yaml` against the platform meta-schema, resolves the immutable commit SHA, and registers the template document in Firestore at `templates/{template_id#version}`.
3. **Catalog record:** Stored records include `template_id`, `version`, `commit_sha`, `schema`, `cost_tier`, `defaults`, and `status: active`.
4. **Deprecation:** When a template version is retired, an administrative script or PR workflow updates its status to `deprecated`. The API rejects new requests targeting deprecated versions with `422 Unprocessable Entity`, while existing deployments remain visible and destroyable.
5. **Runtime isolation:** The FastAPI control plane reads template definitions strictly from Firestore; it never queries Git repositories during request validation or dispatch.

---

## 11. Security and Governance Baseline

### 11.1 Human and API access

- Portal users authenticate through the password-hash/JWT flow described in Section 5.
- FastAPI enforces role- and workspace-based authorization.
- Developers receive no direct IAM data roles for provisioned GCP data-plane resources.
- Testing against real GCP services occurs through deployed dev environments, approved service endpoints, and CI smoke/integration tests—not direct laptop access to underlying buckets, RAG stores, Firestore collections, or service accounts.
- Existing platform-admin access is the documented break-glass path and must be auditable.

### 11.2 Machine access

- GitHub Actions uses WIF and dedicated, least-privilege pipeline service accounts.
- The API Cloud Run runtime service account is distinct from pipeline and workload identities.
- Deployed workloads use workspace or per-deployment runtime service accounts with only required data-plane access.
- Service-account keys are prohibited. Apply `iam.disableServiceAccountKeyCreation` when organization-policy scope is available.

### 11.3 Model Armor and observability

For T1 and T3 reference workloads:

- Model Armor policy integration is explicit application middleware/wrapper behavior, not assumed transparent endpoint enforcement.
- The reference path identifies which content is screened: user prompts, tool inputs, retrieved context where applicable, and model responses where applicable.
- Policy failure behavior is configured as block, redact, or allow-with-audit according to the governance profile.
- Logs and metrics avoid recording sensitive prompt content unless an explicitly approved test policy permits it.
- Baseline logging, dashboards, labels, and cost attribution are mandatory; enhanced alerts and strict policy are applied through T4.

### 11.4 Cost controls and cleanup

- Every deployment has required labels, owner, cost center, and environment.
- `dev` deployments receive a default TTL/expiry unless a platform admin grants an exception.
- A scheduled orphan/expiry workflow reports and destroys expired eligible dev deployments after notification.
- Billing budgets and alerts notify owners/platform operators but do not claim to stop spending automatically.
- Templates enforce resource, scaling, model, ingestion, and size limits.
- The POC includes a scripted `destroy-all` runbook and verifies all stacks are removed at completion.

### 11.5 Kept versus deferred

| Kept in POC | Deliberately deferred |
|---|---|
| WIF and no service-account keys | Multi-project/folder landing zone |
| Password-hash login, short-lived JWTs, role/workspace authorization | Enterprise SSO/custom IdP |
| Least-privilege pipeline and runtime identities | HA/DR for the platform API |
| Terraform state isolation and locking | OPA/Config Validator policy-as-code |
| Immutable template references and audit records | VPC Service Controls |
| Mandatory labels, TTL, budget alerts, orphan cleanup | CMEK; Google-managed encryption keys are acceptable for POC |
| Plan review and GitHub Environment prod approval | Full self-service user management |
| Teardown and readiness checks | Full drift reconciliation engine |

---

## 12. Provisioning Workflow

### 12.1 Create/update workflow

1. **Authenticate** — User logs in to portal and receives a short-lived access token.
2. **Submit** — Portal or CLI submits a request with an idempotency key.
3. **Authorize and validate** — API verifies identity, role, workspace access, template availability, immutable template version, JSON Schema, model allow-list, and cost limits.
4. **Record and dispatch** — API creates a Firestore request record, returns `202 Accepted`, and dispatches the version-pinned GitHub Actions workflow.
5. **Plan** — Workflow authenticates using WIF, runs Terraform plan, posts safe plan summary/status callback.
6. **Approve** — For `prod`, GitHub Environment required reviewers approve the protected deployment step. `dev` continues automatically.
7. **Apply** — Workflow runs Terraform apply and controlled fallback steps where explicitly allowed.
8. **Validate readiness** — Workflow runs the template-specific smoke/readiness contract.
9. **Register** — API records safe outputs and marks deployment `ACTIVE` only after successful readiness verification.
10. **Notify** — Pub/Sub notification sends success/failure to Slack.

### 12.2 Destroy workflow

1. An authorized user submits `POST /deployments/{id}/destroy`.
2. API creates a distinct destroy request, confirms state and lifecycle eligibility, and dispatches the pinned destroy workflow.
3. Workflow uses WIF and the relevant pipeline service account to run Terraform destroy.
4. Workflow verifies expected resource removal where feasible.
5. API marks deployment `DESTROYED`, preserves audit metadata, and does not delete history.

### 12.3 Readiness rules

| Template | `ACTIVE` condition |
|---|---|
| T1 | Agent Engine resource is available and non-sensitive smoke invocation returns expected result |
| T2 | Corpus/import succeeds and known smoke document is retrievable |
| T3 | Cloud Run revision is ready, IAM-authenticated health check succeeds, and smoke request succeeds |
| T4 | Required policy/monitoring/budget/alert resources exist and reference integration telemetry is confirmed |

---

## 13. Delivery Plan

### Phase 0 — Foundation and validation

Scope:

- Create monorepo and base Terraform layout.
- Create GCS Terraform state bucket and state-prefix convention.
- Configure WIF provider, tight GitHub claim constraints, and one dev pipeline service account.
- Create `idp-api-runtime` Cloud Run service account with minimal Firestore/Secret Manager permissions.
- Bootstrap one platform-admin user with Argon2id password hash and JWT signing secret in Secret Manager.
- Build a static ADK-only T1 reference path and validate Agent Engine packaging/deploy behavior.
- Pin/validate `agents-cli`; decide scaffold-only versus pipeline dependency.

Exit criteria:

- GitHub Actions provisions and destroys one T1 dev deployment using WIF with no service-account key.
- A manual API login returns a valid JWT; a protected endpoint rejects missing/invalid JWTs.
- Agent Engine smoke test succeeds; no console-based developer provisioning is required.

### Phase 1 — Control plane and T1 lifecycle

Scope:

- Implement FastAPI login, JWT verification, role/workspace authorization, idempotency, Firestore records, state-machine validation, and request/deployment endpoints.
- Implement WIF-authenticated pipeline callbacks with Cloud Run IAM and request/run binding checks.
- Implement T1 entirely through the API request → workflow → callback → readiness → registration lifecycle.
- Implement destroy request lifecycle and audit records.

Exit criteria:

- A developer user can submit authorized T1 dev request and receive `ACTIVE` only after smoke verification.
- Retried request with same idempotency key does not create duplicate deployment.
- Unauthorized user, invalid token, invalid workspace, and invalid callback are rejected.
- Destroy succeeds through the same governed workflow.

### Phase 2 — T3, T2, and governance

Scope:

- Implement T3 Cloud Run agent service with IAM-protected health/smoke path.
- Implement narrowed T2 managed RAG path with ingestion contract and retrieval readiness test.
- Add T4 baseline/enhanced governance profile: Model Armor reference integration, Monitoring dashboards, alert policy, budget alert, TTL/orphan report, and cleanup job.
- Add GitHub Environment production approval flow.
- Add Pub/Sub-to-Slack notifications.

Exit criteria:

- T1, T2, and T3 complete full request → provision → validate → register → destroy lifecycle.
- Prod-tagged request cannot apply without GitHub Environment approval.
- Expired dev deployment is identified by cleanup workflow.
- T2 is not marked active until retrieval smoke test passes.

### Phase 3 — React portal and learning outputs

Scope:

- Build React login page, `localStorage` bearer-token client, template/request/deployment views, and destroy action with confirmation.
- Host portal on Firebase Hosting and route API calls directly to Cloud Run API with configured CORS.
- Complete ADRs, AWS↔GCP comparison, implementation notes, and POC teardown.

Exit criteria:

- Portal user logs in, submits an authorized request, polls status, and views deployment without direct GCP data-plane access.
- All POC stacks are destroyed or documented as intentionally retained.
- Educational artifacts are published.

---

## 14. Success Metrics

- T1 median request-to-`ACTIVE` time is under 15 minutes.
- At least five deployments are completed by at least three authorized users or representative user accounts.
- 100% of deployments include required labels, owner, state prefix, immutable template version, and teardown history.
- 100% of successful deployment records passed their template readiness test.
- Zero service-account keys are created or used.
- Zero developers receive direct IAM data-plane roles for provisioned resources.
- No duplicate deployment is created from an idempotent retry.
- Monthly POC cost remains below $50 under planned usage, excluding any explicitly approved experimental exception.
- At least four ADRs and one AWS↔GCP comparison are completed.

---

## 15. Cost Notes

- Managed/serverless services are selected to minimize standing cost: Cloud Run, Firestore, GCS, Pub/Sub, Firebase Hosting, and managed RAG services at POC scale.
- Model token usage and ingestion volume are expected to be the dominant variable costs; templates enforce allow-lists and bounded inputs.
- Agent Engine and associated resource pricing must be verified against current GCP pricing before implementation; pricing assumptions are not hard-coded into governance logic.
- Billing budgets are alerts, not automatic shutoffs. TTL cleanup, scaling limits, ingestion limits, and the destroy-all runbook are required cost controls.

---

## 16. Open Items

1. Confirm final region and first-party model allow-list for T1/T2/T3.
2. Validate exact `agents-cli` compatibility and choose the pinned version/fallback route.
3. Validate current Terraform coverage for Agent Engine packaging and RAG corpus/file lifecycle.
4. Confirm the least-privilege GCP roles required for each template-specific pipeline service account.
5. CLI authentication strategy: CLI uses the same username/password login endpoint (`POST /auth/login`) and holds the bearer token in local session memory, mirroring portal semantics without requiring separate GCP IAM credentials.
6. Portal API routing & CORS: Locked to direct HTTPS client calls from the Firebase Hosting domain to the Cloud Run API URL, with CORS explicitly restricted to the portal origin. Cloud Run service allows unauthenticated invocation at the ingress edge; FastAPI enforces JWT validation on all protected endpoints.

---

## 17. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `agents-cli` tooling changes | Pin version; validate in Phase 0; keep templates thin and maintain a fallback reference implementation |
| Agent Engine packaging is brittle | Encapsulate packaging/deploy mechanics in a versioned composite action and validate with T1 before other templates |
| RAG Terraform coverage is incomplete | Use a versioned, idempotent gcloud/REST fallback only within pipeline; record result in callback/audit metadata |
| Password/JWT implementation is too weak | Use vetted Argon2id/JWT libraries, Secret Manager signing key, short expiry, generic errors, rate limiting, and tests for authorization boundaries |
| Callback spoofing or stale updates | Use WIF identity, Cloud Run IAM, request/run identity binding, event sequence, idempotency, and server-side transition validation |
| Single-project isolation is limited | Document limitation; use per-template/per-deployment identities, required labels, state isolation, and bounded POC scope |
| No local real-resource access slows iteration | Invest in high-quality mocks and smoke tests; retain a fast dev deployment loop |
| Forgotten resources increase spend | TTL, orphan report, alerts, cleanup workflow, required owner labels, and destroy-all runbook |
| Portal UI expands scope | Deliver API/CLI lifecycle first; implement portal only after core API contracts are proven |

---

## Appendix A: Additional ADRs

### ADR-002 — Terraform over SDK-direct provisioning

**Decision:** Terraform remains the primary provisioning engine. Direct Google Cloud SDK calls are not used by the FastAPI control plane.

**Rationale:** Terraform preserves plan/apply diffs, infrastructure lifecycle state, reproducibility, and destroy capability. It avoids turning the control plane into a custom reconciler. gcloud/REST calls are permitted only as explicit, versioned pipeline fallback steps where Terraform coverage is absent.

### ADR-003 — Firestore over SQLite for platform metadata

**Decision:** Use Firestore Native mode for platform metadata.

**Rationale:** Cloud Run has an ephemeral filesystem and can scale concurrently. Firestore is serverless, concurrent, and sufficient at POC scale. SQLite remains acceptable for local API development only.

### ADR-004 — Application password-hash login and JWTs over IAP for the POC portal

**Decision:** Replace IAP-based portal login with preconfigured application users verified through Argon2id password hashes and short-lived JWT bearer tokens.

**Rationale:** This POC needs a controlled application login page and an explicit bearer-token API contract. The design avoids coupling Firebase Hosting routing behavior to an IAP browser session model and keeps portal authentication testable through FastAPI. It is deliberately not an enterprise SSO design and must not be carried unchanged into a production multi-team platform without identity-provider integration.

### ADR-005 — WIF for GitHub Actions and pipeline callbacks

**Decision:** GitHub Actions uses GitHub OIDC plus GCP Workload Identity Federation for provisioning and for authenticated callbacks to the private Cloud Run API.

**Rationale:** WIF eliminates service-account keys and provides short-lived, claim-constrained machine identity. Pipeline callbacks use Google OIDC ID tokens and Cloud Run IAM rather than shared webhook secrets or human JWTs.

### ADR-006 — Immutable template releases and readiness-gated activation

**Decision:** Requests resolve an immutable template version and Git commit at submission; deployments are marked active only after template-specific readiness verification.

**Rationale:** Mutable template branches undermine reproducibility and auditability. Terraform success does not prove that an agent is invokable, a Cloud Run service is reachable, or RAG documents are retrievable. Readiness contracts make the platform status meaningful.

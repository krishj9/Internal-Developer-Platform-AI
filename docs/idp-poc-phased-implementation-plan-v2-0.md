# Internal Developer Platform for Agentic AI on GCP
# Phased Implementation Plan

**Aligned specification:** Draft v2.1 — revised architecture, authentication storage, and execution model  
**Plan status:** Implementation-ready POC plan v2.1  
**Delivery model:** Milestone- and criteria-driven phases (calendar-independent)  
**Primary owner:** Platform Engineering  
**Primary delivery objective:** Prove a secure, repeatable, self-service control plane that provisions and destroys governed agentic-AI infrastructure on GCP through Terraform executed by GitHub Actions using Workload Identity Federation (WIF).

---

## 1. Delivery Strategy

### 1.1 Implementation order

Build the platform from the security and execution core outward. Do not begin with the portal UI, RAG variants, or broad framework support.

```text
Foundation and identity
        ↓
One complete golden path (T1)
        ↓
Control-plane lifecycle and callback reliability
        ↓
Additional runtime and RAG paths
        ↓
Governance automation and production gate
        ↓
React portal and learning artifacts
```

The first usable vertical slice is not a UI. It is an authenticated API request that dispatches a WIF-authenticated GitHub Actions workflow, applies one Terraform template, validates readiness, records state, and destroys the deployment successfully.

### 1.2 Scope guardrails

The following constraints apply throughout the implementation:

- Build only **T1 Agent on Agent Engine** in the first vertical slice.
- Support **ADK only** for T1 until the Agent Engine packaging and deployment process is stable.
- Support only managed **Vertex AI RAG Engine with RagManagedDb** for T2.
- Defer Vertex AI Search, pgvector, Cloud SQL, AlloyDB, Chroma, LanceDB, Firestore vector search, LangGraph, API Gateway, and GKE.
- Use preconfigured users with Argon2id hashes and 60-minute JWTs stored in browser `localStorage`; do not build self-service registration, password reset, refresh tokens, SSO, or enterprise IdP integration.
- Use a narrowly scoped GitHub credential (fine-grained PAT with repo Actions write stored in Secret Manager) for API-initiated workflow dispatch.
- Use GitHub Actions WIF for all cloud provisioning and pipeline callbacks; do not create service-account JSON keys.
- Do not expose real data-plane credentials, raw Terraform state, or GCP runtime configuration to a laptop or browser.
- Do not build the React portal until the API request lifecycle has passed automated tests.

### 1.3 Delivery definitions

| Term | Definition |
|---|---|
| Vertical slice | A deployable, testable end-to-end capability across API, pipeline, infrastructure, state, and audit layers |
| Ready | Accepted into the next phase because the listed exit criteria and automated tests pass |
| Done | Code merged, Terraform planned/applied in dev, tests pass, docs updated, and lifecycle/teardown behavior verified where relevant |
| Deployment | A provisioned instance of a versioned template, with isolated Terraform state and an auditable lifecycle |
| Request | An asynchronous create, update, or destroy action submitted through the control plane |

---

## 2. Target Repository Structure

Create a single monorepo with explicit boundaries between the portal, control plane, templates, pipelines, and documentation.

```text
idp-platform/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── security-model.md
│   ├── api-contract.md
│   ├── runbooks/
│   │   ├── bootstrap.md
│   │   ├── incident-and-break-glass.md
│   │   ├── destroy-all.md
│   │   └── key-rotation.md
│   └── adr/
│       ├── ADR-001-no-backstage.md
│       ├── ADR-002-terraform-over-sdk.md
│       ├── ADR-003-firestore-over-sqlite.md
│       ├── ADR-004-password-hash-jwt-auth.md
│       ├── ADR-005-wif-and-pipeline-callbacks.md
│       └── ADR-006-immutable-templates-readiness.md
├── infra/
│   ├── bootstrap/
│   │   ├── state-bucket/
│   │   ├── service-accounts/
│   │   ├── workload-identity/
│   │   ├── secret-manager/
│   │   ├── firestore/
│   │   │   └── firestore.indexes.json
│   │   └── cloud-run-api/
│   ├── modules/
│   │   ├── labels/
│   │   ├── workload-identity/
│   │   ├── service-account/
│   │   ├── monitoring-baseline/
│   │   ├── budget-alert/
│   │   └── expiration-policy/
│   └── environments/
│       └── poc/
├── api/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── auth/
│   │   ├── authorization/
│   │   ├── domain/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── settings.py
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── portal/
│   ├── src/
│   ├── tests/
│   ├── firebase.json
│   └── package.json
├── cli/
│   ├── idp/
│   └── tests/
├── templates/
│   ├── t1-agent-engine/
│   │   ├── template.yaml
│   │   ├── terraform/
│   │   ├── agent/
│   │   ├── tests/
│   │   └── README.md
│   ├── t2-managed-rag/
│   │   ├── template.yaml
│   │   ├── terraform/
│   │   ├── scripts/
│   │   ├── tests/
│   │   └── README.md
│   ├── t3-cloud-run-agent/
│   │   ├── template.yaml
│   │   ├── terraform/
│   │   ├── service/
│   │   ├── tests/
│   │   └── README.md
│   └── t4-governance/
│       ├── template.yaml
│       ├── terraform/
│       ├── tests/
│       └── README.md
├── .github/
│   ├── actions/
│   │   ├── authenticate-gcp-wif/
│   │   ├── terraform-lifecycle/
│   │   ├── package-agent-engine/
│   │   ├── post-pipeline-callback/
│   │   └── run-readiness-test/
│   └── workflows/
│       ├── deploy-t1.yml
│       ├── deploy-t2.yml
│       ├── deploy-t3.yml
│       ├── apply-governance.yml
│       ├── cleanup-expired.yml
│       ├── publish-template.yml
│       └── validate-repository.yml
└── scripts/
    ├── bootstrap_admin_user.py
    ├── generate_password_hash.py
    ├── create_jwt_signing_secret.sh
    ├── publish_template.py
    ├── validate_template.py
    └── destroy_all.sh
```

### 2.1 Repository conventions

- Protect the default branch; require pull request review and successful validation workflow.
- Tag immutable template releases, for example `templates/t1-agent-engine/v2.0.0`.
- Record the resolved Git commit SHA in every request and deployment record.
- Pin Terraform, provider versions, Python, Node.js, GitHub Actions, and `agents-cli` versions where used.
- Run formatting, unit tests, Terraform validation, security checks, and schema validation on every pull request.
- Do not include passwords, JWT signing secrets, service-account keys, Terraform state, or real runtime configuration in the repository.

---

## 3. Phase 0 — Foundation and Identity

**Objective:** Establish keyless machine identity, state management, initial application identity, password/JWT security primitives, narrowly scoped dispatch secrets, composite Firestore indexes, and a manually triggered T1 deployment.

### 3.1 Work packages

| Work package | Implementation tasks | Deliverables |
|---|---|---|
| Repository baseline | Create monorepo, branch protection, PR workflow, lint/test framework, documentation skeleton, ADR directory | Repository structure; CI validation workflow; contribution guide |
| GCP bootstrap | Enable required services; create Terraform state GCS bucket; create Firestore Native database; deploy composite indexes (`firestore.indexes.json`); configure lifecycle/versioning/logging for state bucket | Bootstrap Terraform stack; Firestore indexes; documented project prerequisites |
| Identity layout | Create API runtime service account and initial T1 dev pipeline service account; assign only necessary roles; prohibit static SA key use | IAM Terraform definitions; least-privilege role matrix |
| WIF configuration | Create workload identity pool/provider; bind GitHub organization, repository, workflow/ref/environment claims to T1 dev pipeline SA | WIF Terraform; GitHub Actions authentication proof |
| Secrets | Create Secret Manager secrets for JWT signing secret (`idp-jwt-signing-key`) and narrowly scoped GitHub dispatch token (`idp-github-dispatch-token`); grant API runtime SA access to both | Secret bootstrap procedure; access policy |
| User bootstrap | Implement secure script to generate Argon2id password hash and create one `platform_admin` Firestore user | `generate_password_hash` and `bootstrap_admin_user` scripts; bootstrap runbook |
| API skeleton | Create FastAPI service with `/healthz`, settings management, Cloud Run packaging, structured logging, Firestore connectivity, and CORS configuration | Deployable FastAPI skeleton; Cloud Run service |
| Authentication primitives | Implement password verification, JWT issuance/validation with 60-minute lifetime, `POST /auth/login`, `GET /auth/me`, token expiry, issuer/audience checks | Unit-tested authentication module and endpoints |
| T1 discovery spike | Validate pinned `agents-cli` and Agent Engine deployment packaging path; choose agents-cli use or fallback reference packaging implementation | ADR/update documenting selected path; working T1 manual pipeline |

### 3.2 GCP bootstrap checklist

Provision through bootstrap Terraform where possible:

- GCS bucket for Terraform state:
  - Uniform bucket-level access.
  - Versioning enabled.
  - Public access prevention enabled.
  - Separate prefixes for bootstrap, API, deployment templates, and callback dead-lettering (`callbacks/dead-letter/`).
- Firestore Native mode database and `firestore.indexes.json` composite indexes.
- Secret Manager secrets:
  - `idp-jwt-signing-key` (HMAC signing secret).
  - `idp-github-dispatch-token` (fine-grained GitHub PAT with repository `Actions: Read and write` permission).
- API runtime service account: `idp-api-runtime@PROJECT_ID.iam.gserviceaccount.com`.
- T1 development pipeline service account: `idp-pipeline-t1-dev@PROJECT_ID.iam.gserviceaccount.com`.
- Workload Identity Pool and GitHub OIDC provider.
- Required Cloud APIs for Cloud Run, Firestore, Secret Manager, IAM Credentials, Resource Manager, Cloud Build/Artifact Registry if selected, Vertex AI, Cloud Storage, Cloud Logging, Cloud Monitoring, Pub/Sub, and Service Usage.
- Cloud Run service for API: public ingress enabled (allowing unauthenticated invocation at the cloud edge), application-level JWT bearer token authentication enforced by FastAPI on all protected routes, and CORS headers explicitly permitting the Firebase Hosting portal origin.

### 3.3 Minimum IAM design

| Identity | Required baseline permissions | Explicit exclusions |
|---|---|---|
| API runtime service account | Firestore read/write for platform collections; Secret Manager accessor for `idp-jwt-signing-key` and `idp-github-dispatch-token`; Pub/Sub publisher | No Owner/Editor; no broad Vertex AI Admin; no general Terraform provisioning permissions; no service-account key admin |
| T1 dev pipeline service account | State-bucket access restricted to T1 prefixes; required Agent Engine/Vertex AI, GCS artifact, runtime-SA binding, and logging permissions for T1 only | No access to JWT secret; no Firestore user administration; no ability to impersonate unrelated pipeline accounts |
| Bootstrap operator | Temporary/admin setup permissions needed to apply bootstrap; not used by runtime systems | Do not embed personal credentials in code, CI, or deployed systems |

Use predefined roles only where they are demonstrably narrow enough for the POC. Otherwise, define project-level or resource-level custom roles after observing required permissions in a controlled dev run.

### 3.4 Authentication acceptance tests

Automate at least the following:

- Valid configured username/password returns a JWT with correct required claims and 60-minute expiry (3600 seconds).
- Invalid password returns generic `401 Unauthorized` response and does not reveal account existence.
- Expired token is rejected.
- Wrong issuer, audience, signature, and malformed bearer token are rejected.
- Disabled user is rejected even if token signature is valid.
- Incremented `token_version` invalidates previously issued token.
- Protected API endpoint rejects no bearer token.
- JWT signing secret and GitHub dispatch token are loaded from Secret Manager in deployed API, not from source configuration.

### 3.5 Phase 0 exit criteria

- GitHub Actions authenticates to GCP using WIF; no downloaded or stored GCP service-account key is used.
- WIF trust allows only the intended GitHub repository/workflow/ref/environment to impersonate the T1 dev pipeline service account.
- Terraform state is stored in the managed GCS backend and a state-lock/concurrency test succeeds.
- Composite indexes are deployed in Firestore.
- FastAPI runs on Cloud Run and connects to Firestore and Secret Manager through `idp-api-runtime` service identity.
- A preconfigured admin can log in through `POST /auth/login` and call `GET /auth/me` using a bearer JWT.
- A manually triggered GitHub Actions workflow provisions, smoke-tests, and destroys a single T1 Agent Engine development deployment.
- The selected Agent Engine/agents-cli packaging method is pinned, documented, and reproducible.

### 3.6 Phase 0 decision gate

Proceed only if all of the following are true:

1. WIF is confirmed to work with intended GitHub trust restrictions.
2. T1 can be provisioned and destroyed without manual console steps.
3. T1 packaging is stable enough to encapsulate in a composite action.
4. API login and deployed-secret retrieval are working.

If T1 packaging remains unstable, stop adding templates and replace `agents-cli` usage with a minimal, documented reference deployment path before proceeding.

---

## 4. Phase 1 — Control Plane and Governed T1 Lifecycle

**Objective:** Convert the manual T1 proof into the first complete self-service vertical slice: authorized request → Terraform plan/apply → authenticated callback with retry/dead-letter recovery → readiness validation → deployment catalog → governed destroy.

### 4.1 Work packages

| Work package | Implementation tasks | Deliverables |
|---|---|---|
| Domain model | Implement request, deployment, workspace, template, audit-event, callback-event records and deploy composite indexes | Firestore repository layer; document schemas; index definitions |
| Authorization & Rate Limiting | Implement `developer`, `approver`, `platform_admin`, and `pipeline` roles; workspace checks; server-derived requester/ownership labels; per-user request rate limiting (429 response) | Authorization middleware/dependencies, rate limiter, and test matrix |
| Concurrency control | Implement deployment locking ensuring only one active (non-terminal) request can target a deployment at a time; reject concurrent attempts with 409 Conflict | Concurrency validation logic and unit tests |
| Template registry & publishing | Define `template.yaml`, JSON Schema, defaults, cost/policy constraints; implement tag-triggered publishing script/workflow to register immutable templates in Firestore | T1 immutable template release; `publish_template.py`; validation utility |
| Request API | Implement `GET /templates`, `POST /requests`, `GET /requests/{id}`, `GET /deployments`, `GET /deployments/{id}`, `GET /deployments/{id}/config`, and `POST /deployments/{id}/destroy` | Versioned OpenAPI contract; API integration tests |
| Idempotency | Require `Idempotency-Key` header on create and destroy requests; scope to `(user_id, idempotency_key)` with 24-hour TTL; persist caller/key/payload digest/result mapping | Idempotency service and integration tests |
| Workflow dispatch | Implement API-to-GitHub dispatch via GitHub REST API using the narrowly scoped credential (`idp-github-dispatch-token`) stored in Secret Manager; pass explicit execution context | Dispatch service; operational failure handling |
| T1 workflow | Standardize WIF auth, Terraform plan/apply/destroy, artifact packaging, output filtering, readiness test, and callback events | `deploy-t1.yml` and reusable composite actions |
| Callback API & reliability | Implement `POST /callbacks/pipeline`; validate Cloud Run caller identity, request/run/template binding, payload schema, event sequence, and legal state transition. Add 3x exponential backoff retries to callback action and dead-letter recording in GCS | Callback endpoint; append-only callback event ledger; composite action retries; negative tests |
| Reconciliation | Implement administrative endpoint `POST /admin/reconcile-callbacks` to scan GCS dead-letter callbacks and replay stuck state transitions | Admin reconciliation service and integration test |
| Lifecycle state machine | Enforce request and deployment states; separate create/destroy requests; ensure terminal-state protection | State-machine module and tests |
| Config contract | Generate safe `idp-config.yaml` metadata/local profile; prevent GCP profile from API output | Config generator and contract tests |
| Audit | Persist actor, action, correlation/request ID, template version, run ID, timestamps, outcome, and failure class | Audit-event model and query views |

### 4.2 T1 template definition of done

The initial T1 template must include:

- ADK-only sample agent and smoke-test prompt/expected response.
- Terraform module with isolated state key based on template and deployment ID.
- Dedicated runtime service account, where required by the Agent Engine integration.
- Mandatory labels from the platform label module.
- Bounded approved model input; no arbitrary model ID.
- Region input constrained to supported POC region(s).
- Cloud Logging and baseline monitoring hooks.
- Non-sensitive Terraform outputs only.
- `template.yaml` with JSON Schema and examples.
- Destroy path that removes all template-managed resources and artifacts that are safe to remove.
- Readiness test that invokes or verifies the Agent Engine deployment using a non-sensitive smoke test.

### 4.3 Request flow implementation

```text
1. User sends POST /requests with valid JWT + Idempotency-Key.
2. API verifies token, active user, role, workspace access, template release, input schema, and policy constraints.
3. API checks rate limits and verifies no concurrent operation is active on the target deployment.
4. API resolves immutable template Git SHA and creates request/deployment records.
5. API dispatches the matching GitHub workflow via narrowly scoped Secret Manager credential and records dispatch metadata.
6. Workflow uses WIF to impersonate T1 pipeline service account.
7. Workflow posts PLANNING / APPLYING / VALIDATING / SUCCEEDED or FAILED callbacks (with retry + dead-letter on failure).
8. API validates callback caller and event sequence, then updates projections and appends audit events.
9. Workflow runs T1 readiness test.
10. API marks deployment ACTIVE only after validated successful readiness callback.
```

### 4.4 Pipeline callback requirements

Each callback must contain:

```yaml
request_id: req-...
deployment_id: dep-...
template_id: t1-agent-engine
template_version: 2.0.0
template_commit_sha: <immutable-sha>
repository: org/idp-platform
workflow: deploy-t1.yml
github_run_id: <run-id>
event_sequence: 1
operation: create
status: PLANNING
summary: Terraform plan started
artifact_references: []
timestamp: <RFC3339>
```

The FastAPI callback handler must:

- Require a Google OIDC ID token from the WIF-authorized pipeline identity.
- Verify the Cloud Run/IAM caller matches the expected service account for the template/environment.
- Verify request ID, deployment ID, repository, workflow, run ID, template version, commit SHA, and operation match the original request.
- Reject sequence regressions and invalid state transitions.
- Treat exact duplicate events as idempotent.
- Store the raw safe callback payload in append-only callback-event collection.
- Never accept a human portal JWT for this endpoint.

### 4.5 Phase 1 test matrix

| Test category | Required scenarios |
|---|---|
| Authentication | Valid/invalid/expired/revoked JWT; 60-minute lifetime expiration; logout clearance |
| Authorization | Developer allowed own workspace dev request; denied foreign workspace; developer denied template/admin action; approver/admin permissions verified |
| Rate limiting | Submitting above configured per-user request threshold returns `429 Too Many Requests` |
| Concurrency control | Submitting a lifecycle request on a deployment with an active non-terminal request returns `409 Conflict` |
| Idempotency | Same user + same key/same payload returns same request result; same key/different payload returns `409`; 24-hour TTL expiration verified; destroy idempotency verified |
| Request validation | Invalid schema, disallowed model, disallowed environment, unapproved template version, absent workspace access |
| Callback trust & reliability | Wrong pipeline identity, mismatched run ID, mismatched template, stale event sequence, duplicate event, malformed payload, callback retry backoff, dead-letter writing, admin reconciliation replay |
| Lifecycle | Valid create states; invalid jumps; terminal state protection; separate destroy request behavior |
| T1 integration | Request through API reaches `ACTIVE`; safe outputs visible; gcp profile absent; destroy reaches `DESTROYED` |
| Security regression | No secret output exposed; no JWT written to logs; no plaintext password stored; no service-account key created |

### 4.6 Phase 1 exit criteria

- A developer user can submit a T1 development request through the API and receive `202 Accepted`.
- A version-pinned GitHub workflow runs Terraform plan/apply using WIF and reports authenticated callbacks.
- Pipeline callbacks recover from transient failures via exponential retries, dead-letter unrecoverable failures, and support admin reconciliation.
- T1 becomes `ACTIVE` only after its smoke/readiness test passes.
- The API returns only non-sensitive deployment data and local configuration profile.
- Duplicate requests cannot create duplicate infrastructure; concurrent requests on active deployments are blocked.
- Unauthorized workspace/template/environment actions fail with `403` or `422` as applicable.
- Destroy is an authorized, separate idempotent request that completes through the same pipeline and marks deployment `DESTROYED`.
- Every request, callback, plan/apply outcome, and destroy action has auditable records linked by request/deployment/run identifiers.

---

## 5. Phase 2 — Additional Golden Paths and Governance

**Objective:** Add Cloud Run agents, managed RAG, guardrails, cost controls, production approval, and cleanup automation without relaxing the Phase 1 control-plane guarantees.

### 5.1 Implementation sequence

Implement in this order:

1. **T3 Cloud Run agent service** — lower integration risk than RAG and validates a second runtime target.
2. **T2 Managed RAG** — narrow managed backend with asynchronous ingestion and retrieval readiness.
3. **T4 Governance profile** — Model Armor reference integration, dashboards, alerts, budgets, TTL/orphan reporting.
4. **Production approval gate** — GitHub Environments applied to approved template workflows.
5. **Notifications and cleanup jobs** — Pub/Sub/Slack status updates and scheduled TTL cleanup.

### 5.2 T3 — Cloud Run agent service

#### Scope

- ADK-based Cloud Run service generated or adapted from the validated reference path.
- Dedicated runtime service account.
- Firestore session state where required.
- IAM-protected invocation; no public unauthenticated endpoint in baseline.
- Bounded CPU, memory, concurrency, timeout, and maximum instance presets.
- Structured logs, baseline dashboard/metrics, labels, and cost attribution.
- Non-sensitive health endpoint and authenticated smoke request.

#### Required implementation tasks

- Add `templates/t3-cloud-run-agent/template.yaml` with JSON Schema and policy limits.
- Build `deploy-t3.yml` from reusable WIF, Terraform, callback, and readiness composite actions.
- Define Cloud Run service naming, runtime service account, and secret/environment injection convention.
- Implement safe output filtering; do not expose internal secret references or service credentials.
- Implement readiness probe using an authorized CI identity or controlled service-to-service invocation.
- Verify destroy removes service revisions, IAM bindings created by template, associated session configuration, and managed artifacts according to retention policy.

#### T3 exit criteria

- An authorized developer submits a T3 dev request through the same API contract.
- Cloud Run revision reaches ready state and authenticated health/smoke request passes.
- No public unauthenticated invocation is configured unless explicitly approved and documented as an exception.
- Destroy completes and leaves no unowned template resources.

### 5.3 T2 — Managed RAG stack

#### Scope

Build only:

- Vertex AI RAG Engine.
- RagManagedDb.
- GCS source bucket or managed prefix convention.
- Restricted document ingestion contract.
- One versioned ingestion preset.
- Asynchronous import status and retrieval smoke test.

Do not build in the POC baseline:

- Vertex AI Search backend.
- Self-managed pgvector, Cloud SQL, AlloyDB.
- Chroma, LanceDB, or Firestore vector alternatives.
- Arbitrary connectors or unbounded document uploads.

#### Required implementation tasks

- Confirm Terraform provider support; implement a narrowly scoped, idempotent gcloud/REST action only if needed.
- Put REST/gcloud logic in versioned scripts or composite action, never in ad hoc workflow shell commands.
- Add document MIME type, count, total-size, and source-prefix validation before workflow dispatch.
- Implement an import-job state model inside the request/deployment projection or a linked ingestion record.
- Add a smoke document and expected retrieval assertion.
- Record ingestion job identifiers, corpus/resource names, and safe operational metadata in Firestore.
- Ensure that sensitive runtime endpoint/config values remain workload-only.
- Add a cleanup procedure for imported documents/corpus resources on destroy.

#### T2 readiness semantics

A T2 deployment is not `ACTIVE` until all are true:

1. Infrastructure/corpus creation succeeds.
2. Source document import job completes successfully.
3. The known smoke document is retrievable through the configured retrieval contract.

#### T2 exit criteria

- A bounded GCS document source is accepted through T2 schema validation.
- The pipeline creates corpus and completes ingestion using WIF-authenticated execution.
- Readiness test retrieves expected content from the smoke document.
- Failure states distinguish Terraform failure, ingestion failure, and retrieval validation failure.
- Destroy removes or safely retains resources according to documented retention behavior.

### 5.4 T4 — Governance profile and operational controls

#### Baseline governance applied to T1–T3

All templates must already include:

- Required platform labels.
- Owner, workspace, environment, cost center, template version, and expiration metadata.
- Basic logs and audit linkage.
- Bounded resource and model configuration.
- Destroy path.

#### T4 additions

| Capability | Implementation requirement |
|---|---|
| Model Armor | Define policy/template and reference integration middleware/wrapper for T1/T3. Make screen points explicit: prompt, tool input, retrieved content where applicable, and model output where applicable. |
| Policy behavior | Configure and test `block`, `redact`, or `allow-with-audit` behavior by governance preset. |
| Monitoring | Per-template dashboard with deployment identifiers, errors, latency, invocation volume, and readiness-related signals. |
| Alerts | Budget/usage threshold notification; error-rate or failed readiness alert; failed cleanup alert. |
| Budget controls | Template limits plus billing budget alert. Do not describe alert as automatic hard spending cap. |
| TTL | Default expiry for dev deployments; platform-admin exception mechanism recorded in audit log. |
| Orphan detection | Scheduled workflow finds active deployments with expired TTL, missing owner, or stale metadata; notifies and queues eligible destroy requests. |
| Cleanup | Scheduled cleanup workflow uses WIF and same destroy mechanics; preserves audit trail. |

#### T4 exit criteria

- Model Armor reference integration can demonstrate expected behavior with a safe test case.
- Monitoring dashboard and alert policies exist for a test deployment.
- A test budget/usage notification route is confirmed.
- An expired dev deployment is detected and follows documented notification/destroy process.
- Cleanup failure is visible and auditable.

### 5.5 Production approval gate

Implement production workflow controls after development flows are stable.

- API only accepts `prod` request from authorized role/capability.
- Pipeline selects GitHub Environment `prod` based on server-validated request data, not user-controlled workflow input alone.
- GitHub Environment requires designated reviewers before Terraform apply.
- Plan summary/artifact reference is available to approvers.
- Approval/rejection events are linked to request and pipeline run metadata.
- Apply cannot proceed if request parameters/template commit differ from the planned request.

#### Production-gate exit criteria

- A production request reaches `AWAITING_APPROVAL` after plan.
- Terraform apply does not execute until the required GitHub Environment approval occurs.
- Rejected or expired approval prevents apply and produces an auditable terminal request state.

### 5.6 Notifications

Use Pub/Sub as the event boundary between control plane and Slack delivery.

- API publishes a normalized event after terminal state change.
- Cloud Run notification function posts success/failure/cleanup messages to Slack webhook.
- Notification messages include request ID, deployment ID, template, workspace, status, and pipeline link; exclude secrets and sensitive runtime details.
- Slack webhook URL is stored in Secret Manager.

### 5.7 Phase 2 exit criteria

- T1, T2, and T3 support the same governed request → plan → apply → readiness → register → destroy lifecycle.
- T2 is not active until document ingestion and retrieval smoke test pass.
- T1/T3 baseline governance is present, and T4 enhanced governance controls are testable.
- Production requests require GitHub Environment review before apply.
- TTL/orphan detection and cleanup workflow function in a controlled test.
- Notifications communicate terminal provisioning and cleanup outcomes without exposing sensitive configuration.

---

## 6. Phase 3 — React Portal, Operational Hardening, and Retrospective

**Objective:** Deliver the thin developer portal over the proven API, finish operational documentation, execute final security verification, and leave the project clean.

### 6.1 React portal implementation

#### Required screens

| Screen | Required behavior |
|---|---|
| Login | Submit username/password to `POST /auth/login`; show generic failure; store token in browser `localStorage` |
| Template catalog | Display templates the authenticated user may request, their version, safe defaults, cost tier, inputs, and constraints |
| New request | Render schema-guided form; submit bearer-authenticated request with generated idempotency key; do not allow user to set owner/requester fields |
| Request detail | Poll authorized request endpoint; display lifecycle status, safe plan/apply/readiness summaries, and pipeline link |
| Deployment list/detail | List authorized deployments; show non-sensitive outputs, labels, expiry, and lifecycle state |
| Destroy confirmation | Require explicit browser confirmation, then submit destroy request; do not directly delete resources from UI |
| Session handling | Token persists across page refreshes; on `401`, clear `localStorage` token and return to login; on `403`, show authorization error without treating it as logout |

#### Portal security requirements

- Store bearer token in `localStorage` for session continuity across page refreshes during long-running provisioning workflows.
- Do not store bearer token in URL parameters, logs, or analytics events.
- On explicit logout or HTTP 401 response, immediately clear token from `localStorage`.
- Do not render or cache sensitive runtime configuration.
- Do not trust UI role/workspace state; API remains authoritative.
- Add CSP and dependency scanning where straightforward in Firebase Hosting configuration/build pipeline.
- Ensure CORS model explicitly restricts allowed origin to the Firebase Hosting portal domain.
- Use generic login errors and avoid user-enumeration hints.

### 6.2 CLI decision and minimal implementation

The CLI is secondary to the portal in this phase. Select one supported POC model:

| Option | Description | Recommendation |
|---|---|---|
| JWT login | CLI calls login endpoint and holds token in process/keychain-supported local session | Preferred if CLI must mirror portal behavior |
| Cloud Run IAM caller | CLI uses developer GCP identity to invoke a separate/internal API path | Defer unless strong reason exists; creates two human auth models |
| No CLI in POC | Portal is primary; API remains automation-ready | Acceptable if time is constrained |

If implemented, CLI must use the same request API, idempotency behavior, and authorization enforcement. It must not gain direct data-plane access.

### 6.3 Operational documentation

Complete and test the following runbooks:

- Platform bootstrap and teardown.
- Preconfigured user creation, password hash generation, disable/revoke procedure.
- JWT signing-key rotation procedure.
- WIF configuration and GitHub claim troubleshooting.
- Template release/versioning procedure.
- Failed deployment triage.
- Callback failure/replay procedure.
- Break-glass procedure and audit expectation.
- Expired/orphan cleanup procedure.
- Destroy-all end-of-POC procedure.
- Cost anomaly response.

### 6.4 Final security review checklist

| Area | Verification |
|---|---|
| Passwords | Argon2id hashes only; no plaintext/reversible values; bootstrap path documented |
| JWTs | Secret Manager signing key; 60-minute expiry; issuer/audience/expiry/token-version checks; token absent from logs; cleared from `localStorage` on logout/401 |
| API authorization | Role/workspace tests; server-derived ownership; unauthorized reads return `404` or `403` per chosen policy |
| WIF | Provider restricted to intended GitHub owner/repository/workflow/ref/environment; no broad impersonation bindings |
| Service accounts | Separate API, pipeline, workspace/workload identities; least-privilege review; no keys |
| Callbacks | Google ID token, Cloud Run IAM, request/run binding, sequence enforcement, exponential retry backoff, dead-letter logging, append-only ledger |
| Terraform | State bucket protected; state prefixes isolated; secrets absent from outputs; apply/destroy via pipeline only |
| Portal | `localStorage` token cleared on 401/logout; no sensitive display; CORS/CSP controlled; dependency scan passes |
| Data plane | No developer IAM roles on provisioned data resources; workload identities constrained |
| Cleanup | TTL/orphan flow tested; destroy-all runbook validated |

### 6.5 Retrospective and educational outputs

Produce:

- Final architecture diagram and component interaction sequence.
- AWS↔GCP IDP comparison focused on equivalent capabilities, operational trade-offs, and governance primitives.
- Completed ADRs, including findings from agents-cli and RAG Terraform validation.
- Template authoring guide.
- POC results against success metrics.
- Backlog separating productionization work from POC learnings.

### 6.6 Phase 3 exit criteria

- A user logs in to the React portal, submits an authorized request, observes status through `ACTIVE`, and submits a governed destroy request.
- Portal session persists across page refreshes via `localStorage` token storage and does not expose sensitive configuration.
- Security checklist passes or every exception is documented, time-bounded, and accepted.
- Runbooks are complete and have been exercised where feasible.
- All POC deployments are destroyed or explicitly documented as retained with owner, cost, expiry, and justification.
- Retrospective, ADRs, and comparison documents are published.

---

## 7. Cross-Cutting Engineering Standards

### 7.1 Definition of done for every feature

A feature is complete only when:

- Implementation is merged through protected-branch review.
- Unit and relevant integration tests pass.
- Error behavior and security boundaries are tested.
- Logs use correlation IDs and exclude secrets, passwords, raw tokens, and sensitive runtime configuration.
- Documentation/API contract/template docs are updated.
- Terraform formatting, validation, and plan checks pass.
- The relevant destroy/rollback behavior is considered and documented.

### 7.2 Testing layers

| Layer | Focus | Examples |
|---|---|---|
| Unit | Pure logic | Password verification wrapper, JWT parsing, policy validation, state transitions, idempotency digest |
| Component | Service boundary | Firestore repositories, Secret Manager loading, GitHub dispatch adapter, callback verifier |
| API integration | HTTP/security contract | Login, bearer auth, workspace authorization, 202 semantics, error codes |
| Infrastructure | Terraform/modules | `terraform validate`, plan tests, resource labels, IAM bindings, output safety |
| Workflow | CI/CD behavior | WIF auth, plan/apply/destroy, callback sequence, protected prod gate |
| End-to-end | Full vertical slice | Login → request → pipeline → readiness → active → destroy |
| Security regression | Negative controls | Token tampering, callback spoofing, cross-workspace access, secret leakage checks |

### 7.3 Observability and correlation

Use and propagate these identifiers:

- `request_id`
- `deployment_id`
- `workspace`
- `template_id`
- `template_version`
- `template_commit_sha`
- `github_run_id`
- `operation`
- `actor_user_id` or pipeline identity

FastAPI structured logs, Firestore audit events, GitHub workflow logs, and notifications should all include the applicable identifiers.

### 7.4 Data and secret handling

- Treat Terraform state as sensitive administrative data even if template outputs are filtered.
- Do not place secrets in Terraform outputs.
- Store only secret references—not secret values—in Firestore metadata, where needed.
- Redact authorization headers, passwords, JWTs, and secret values from application/workflow logs.
- Keep pipeline artifacts private and time-limited; do not attach raw state or secrets to workflow artifacts.

---

## 8. Milestones and Demonstrations

| Milestone | Target Gate | Demonstration |
|---|---|---|
| M0: Trusted foundation | Phase 0 Exit | WIF-authenticated GitHub workflow deploys/destroys T1; API validates password hash and issues JWT |
| M1: First governed golden path | Phase 1 Exit | Developer submits T1 through authenticated API; callbacks with retry recovery, readiness, catalog record, and destroy all work |
| M2: Platform breadth with governance | Phase 2 Exit | T1/T2/T3 lifecycle works; prod approval gate, Model Armor reference integration, budgets/TTL cleanup, and notifications work |
| M3: Usable POC and retro | Phase 3 Exit | React portal login/request/status/destroy works with `localStorage` token persistence; security/runbooks/ADRs complete; resources cleaned up |

---

## 9. Initial Backlog by Priority

### P0 — Must complete for credible POC

- Bootstrap Terraform state bucket, Firestore, Secret Manager, API runtime SA, WIF, and T1 pipeline SA.
- Implement Argon2id login, JWT validation with 60-minute lifetime, active-user and token-version checks.
- Implement T1 manual pipeline with WIF, Terraform, readiness, and destroy.
- Implement request/deployment state machine, idempotency with 24h TTL, authorization, audit records, callback retry/recovery, and callback trust contract.
- Deliver full API-driven T1 vertical slice.
- Prevent sensitive `gcp` config, secrets, and Terraform state from API/portal outputs.

### P1 — Required for full target POC

- T3 Cloud Run agent golden path.
- T2 managed RAG with bounded ingestion and retrieval readiness.
- T4 governance profile, monitoring, Model Armor reference integration, budget notifications, TTL/orphan cleanup.
- GitHub Environment production approval gate.
- Pub/Sub-to-Slack notifications.
- React portal login/catalog/request/status/destroy with `localStorage` persistence.

### P2 — Documented or optional follow-on

- CLI JWT login.
- Template upgrade workflow.
- Drift detection/reconciliation.
- LangGraph support.
- Vertex AI Search alternative RAG backend.
- Self-managed vector backends.
- Refresh tokens.
- User-management UI/password reset.
- Enterprise SSO/IdP integration.
- Multi-project/folder tenancy and VPC Service Controls.

---

## 10. Key Risks and Stop Conditions

| Risk | Early warning | Mitigation | Stop/escalate condition |
|---|---|---|---|
| WIF trust too broad or fails | Workflow requires broad IAM or unbounded repository trust | Narrow GitHub claim mapping and use per-template service accounts | Do not proceed with real provisioning until WIF restrictions are verified |
| Agent Engine packaging instability | Repeated manual fixes or non-reproducible artifact behavior | Pin tools; encapsulate packaging; adopt minimal fallback reference path | Do not add T2/T3 until T1 deploy/destroy is reproducible |
| RAG API/Terraform coverage gaps | Corpus/import requires uncontrolled shell steps | Isolate versioned gcloud/REST action with idempotency and audit | Keep T2 document-only if retrieval smoke test cannot be automated |
| Auth implementation over-expands | Refresh tokens, account management, password reset creep | Keep preconfigured users and access tokens only | Defer portal polish if login/JWT boundary is not securely testable |
| API/pipeline state mismatch | Stale or duplicate callbacks change statuses incorrectly | Sequence numbers, callback ledger, request/run binding, idempotent handlers, exponential retry and reconciliation | Stop prod enablement until negative callback tests pass |
| Cost drift | Forgotten dev stacks or high model/ingestion usage | TTL, resource limits, alerts, cleanup workflows | Execute destroy-all and pause new deployments if budget threshold is breached |
| Portal delays core platform | UI builds before API lifecycle stabilizes | API-first milestones and mocked portal contract | Move portal to post-POC if M2 core controls are incomplete |

---

## 11. Final Acceptance Criteria

The POC is accepted when all of the following are demonstrated:

1. A preconfigured developer authenticates through password verification using Argon2id and receives a 60-minute JWT.
2. FastAPI authorizes the developer by role and workspace and rejects unauthorized operations.
3. The API accepts an idempotent T1 request and returns `202 Accepted` with a request ID.
4. GitHub Actions uses WIF—not static service-account keys—to execute Terraform plan/apply/destroy.
5. Pipeline callbacks authenticate using WIF-derived Google ID tokens and cannot be spoofed by a user bearer token or mismatched workflow run.
6. T1, T2, and T3 each support request → provision → readiness validation → active registration → destroy lifecycle.
7. RAG is not marked active until an ingestion and retrieval smoke test passes.
8. Production apply is gated by GitHub Environment approval.
9. Portal UI supports login, request, status, and destroy using bearer tokens stored in browser `localStorage`.
10. No developer has direct data-plane IAM access to provisioned resources; sensitive runtime configuration, secrets, and Terraform state are never exposed through the portal/API.
11. Required labels, cost controls, TTL/orphan detection, teardown, audit records, and safe notifications are operating.
12. Final teardown/runbook verification leaves the POC project clean or explicitly records approved retained resources.

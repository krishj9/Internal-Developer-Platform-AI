# Internal Developer Platform (IDP) — User & Operator Guide

Welcome to the **Internal Developer Platform for Governed Agentic AI on Google Cloud Platform**.

This platform provides an automated, self-service developer control plane to provision, monitor, govern, and tear down enterprise AI workloads securely on Google Cloud without requiring direct infrastructure execution privileges or static service account JSON keys.

---

## 1. Quick Access & Platform Links

| Resource | Description | Access URL |
|---|---|---|
| **Developer Portal UI** | Self-service web interface | [http://localhost:3000](http://localhost:3000) |
| **Interactive Architecture Document** | Technical architecture specification | [/architecture.html](http://localhost:3000/architecture.html) |
| **Executive Presentation Deck** | 14-slide interactive deck | [/presentation.html](http://localhost:3000/presentation.html) |
| **Control Plane REST API** | Live Cloud Run OpenAPI docs | [https://idp-api-754915077075.us-central1.run.app/docs](https://idp-api-754915077075.us-central1.run.app/docs) |
| **GitHub Actions Repository** | Source code & pipeline execution plane | [krishj9/Internal-Developer-Platform-AI](https://github.com/krishj9/Internal-Developer-Platform-AI) |

---

## 2. Platform Roles & Authentication

The platform authenticates callers via **Argon2id** password verification and issues **60-minute signed JWT bearer tokens** with claims backed by Google Secret Manager signing keys.

### 2.1 Demo Test Accounts

| Username | Password | Role | Assigned Workspaces | Capabilities |
|---|---|---|---|---|
| `admin_gov` | `AdminPass123!` | `platform_admin` | `default`, `admin`, `ws-dev` | Full access: provision dev/prod, approve prod deployments, reconcile callbacks, TTL override |
| `dev_gov` | `DevPass123!` | `developer` | `default`, `ws-dev` | Workspace access: provision dev workloads, track status, inspect safe outputs, trigger teardown |
| `admin` | `AdminPass2026#` | `platform_admin` | `default`, `admin` | Platform administrative credentials |

> [!TIP]
> On the Portal Login screen, you can click the **"👑 Platform Admin"** or **"💻 Developer"** fast-fill buttons to auto-populate credentials.

---

## 3. Web Portal User Guide

### 3.1 Template Catalog

Navigate to **Template Catalog** in the top navigation bar. You will find four pre-approved, version-pinned, immutable templates:

1. **T1: Agent on Vertex AI Agent Engine (`t1-agent-engine`)**
   - *Description*: Governed ADK-compliant reasoning agent deployed to Google Cloud Agent Engine.
   - *Supported Models*: `gemini-2.5-flash`, `gemini-2.5-pro`
   - *Cost Tier*: Low
2. **T2: Vertex AI Managed RAG Engine (`t2-managed-rag`)**
   - *Description*: Managed RAG Engine corpus with vector index and bounded document ingestion ($\le 100$ files, $\le 500$ MB).
   - *Supported Models*: `text-embedding-004`, `text-embedding-005`
   - *Cost Tier*: Medium
3. **T3: Agent on Cloud Run Service (`t3-cloud-run-agent`)**
   - *Description*: Containerized FastAPI + ADK agent service with private IAM invocation (zero public `allUsers`).
   - *Supported Models*: `gemini-2.5-flash`, `gemini-2.5-pro`
   - *Cost Tier*: Medium
4. **T4: Governance & Operational Controls (`t4-governance`)**
   - *Description*: Model Armor guardrails, Cloud Monitoring alerts, and automated TTL cleanup policies.
   - *Cost Tier*: Low

---

### 3.2 Provisioning a Workload

1. Click **"Configure & Deploy"** on any template card (e.g., **Agent on Vertex AI Agent Engine**).
2. Complete the modal form:
   - **Target Environment**: Select `dev` (or `prod` if authorized).
   - **Agent Name**: Enter a logical identifier (e.g., `support-agent-v1`).
   - **Governed Model**: Choose from the approved model dropdown (e.g., `gemini-2.5-flash`).
   - **GCP Region**: Target region (e.g., `us-central1`).
3. Click **"Submit Provisioning Request"**.
4. The control plane validates policies, checks for deployment locks, verifies idempotency, writes the audit log, and redirects you to the **Request Tracker**.

---

### 3.3 Request Lifecycle Tracker

The tracker displays live execution telemetry through an interactive stage timeline:

```text
[1] PENDING ──▶ [2] DISPATCHED ──▶ [3] PLANNING ──▶ [4] APPLYING ──▶ [5] SUCCEEDED
```

- **PENDING**: Request record created, atomic deployment lock acquired.
- **DISPATCHED**: GitHub Actions workflow triggered via fine-grained credentials.
- **PLANNING**: Terraform plan generated and validated against remote state in Cloud Storage.
- **APPLYING**: Terraform apply executed; workload runtime service accounts and cloud resources provisioned.
- **SUCCEEDED**: Pre-activation readiness smoke test verified; deployment transitioned to `ACTIVE`; deployment lock released.
- **FAILED**: If any stage fails, the request transitions to `FAILED` with a sanitized failure class (e.g. `readiness_failed`, `terraform_apply_failed`) and lock is safely released.

---

### 3.4 Managing Deployments & Inspecting Safe Outputs

Navigate to the **Deployments** tab to view workloads in your active workspace.

#### Inspecting Safe Workload Configuration:
1. Click the **Outputs** (`Code` icon) button on any active deployment.
2. The modal displays only safe, non-sensitive operational metadata:
   - `deployment_id`: Unique identifier (e.g., `dep-bdba18c9`)
   - `runtime_sa_email`: Workload service account (e.g., `sa-t1-depbdba18c9@mybrightday-dev.iam.gserviceaccount.com`)
   - `model_name`: Configured foundation model (e.g., `gemini-2.5-flash`)
   - `region`: Cloud deployment region (e.g., `us-central1`)
   - `status`: `PROVISIONED`

> [!IMPORTANT]
> The platform adheres to strict data-masking rules: **Zero credentials, secrets, bearer tokens, or raw Terraform state files are ever returned to the client.**

#### Safe Two-Step Workload Destruction:
1. Click the red **Destroy** (`Trash2` icon) button on the target deployment row.
2. In the confirmation dialog, type the exact **Deployment ID** to confirm.
3. Click **"Permanently Destroy"**.
4. The system acquires the teardown lock, sets status to `DESTROYING`, and executes `terraform destroy` via GitHub Actions.
5. Once complete, the deployment status permanently transitions to `DESTROYED`.
6. Any subsequent attempt to destroy an already-destroyed deployment is rejected with `HTTP 422 Unprocessable Content`.

---

### 3.5 Governance & Model Armor Guardrails

Navigate to **Governance & Model Armor** to test live AI guardrails across four screening points:

1. **Prompt Inspection (`PROMPT`)**: Detects prompt injections, jailbreaks, and sensitive data before sending prompts to Gemini.
2. **Tool Input Inspection (`TOOL_INPUT`)**: Inspects arguments before agents invoke tools or APIs.
3. **Retrieved Content (`RETRIEVED_CONTENT`)**: Screens documents retrieved by RAG before passing them into the model context.
4. **Model Output (`MODEL_OUTPUT`)**: Screens generated model responses for PII, toxic content, or policy violations.

#### Enforcement Modes:
- **BLOCK**: Rejects the request with an error message.
- **REDACT**: Replaces sensitive data (e.g. credit cards, SSNs, API keys) with `[REDACTED]`.
- **ALLOW_WITH_AUDIT**: Permits execution while logging a security audit event for compliance review.

---

## 4. Command Line Interface (CLI) Guide

Developers can also operate the platform via the command-line interface `idp`.

### 4.1 Login & Profile
```bash
# Login to obtain 60-minute JWT bearer token
uv run python cli/main.py login --username admin_gov --password "AdminPass123!"

# Verify current profile & permissions
uv run python cli/main.py me
```

### 4.2 Browse Templates
```bash
# List all published governed templates
uv run python cli/main.py templates list
```

### 4.3 Submit Provisioning Request
```bash
# Provision T1 Vertex AI Agent Engine
uv run python cli/main.py requests create \
  --template t1-agent-engine \
  --workspace default \
  --env dev \
  --input agent_name="cli-agent-demo" \
  --input model_name="gemini-2.5-flash" \
  --input region="us-central1"
```

### 4.4 Track Request Status
```bash
# Check asynchronous execution telemetry
uv run python cli/main.py requests status --request-id req-<request-id>
```

### 4.5 List & Destroy Deployments
```bash
# List all deployments in active workspace
uv run python cli/main.py deployments list --workspace default

# Inspect safe configuration
uv run python cli/main.py deployments config --deployment-id dep-<id>

# Teardown & destroy workload
uv run python cli/main.py deployments destroy --deployment-id dep-<id>
```

### 4.6 Inspect Guardrails via CLI
```bash
# Test Model Armor inspection
uv run python cli/main.py governance inspect \
  --text "My credit card is 4111-2222-3333-4444" \
  --mode redact \
  --point prompt
```

---

## 5. Security & Governance Policies

1. **Zero Service Account Keys**:
   - No `.json` service account keys exist in the repository or GCP.
   - All CI/CD execution uses GitHub OIDC tokens exchanged with Google Cloud Workload Identity Federation (WIF).
2. **Workload Identity Trust Boundary**:
   - Only workflows running on branch `refs/heads/main` of repository `krishj9/Internal-Developer-Platform-AI` are permitted to mint credentials.
3. **Idempotency Guarantee**:
   - Every mutating request requires an `Idempotency-Key` header with 24-hour TTL caching to prevent duplicate infrastructure creations.
4. **Isolated Remote State**:
   - Each deployment uses a dedicated, isolated Terraform state path (`templates/{template_id}/{deployment_id}/default.tfstate`) in `gs://idp-tfstate-mybrightday-dev`.
5. **Immutable Audit Trail**:
   - Every API invocation and pipeline callback is permanently recorded in Firestore collection `audit_events`.

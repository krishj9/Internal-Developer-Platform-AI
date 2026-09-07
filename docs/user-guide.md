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

The platform authenticates callers via **Argon2id** password verification and issues **cryptographically signed JWT bearer tokens** with claims backed by Google Secret Manager signing keys.

### 2.1 Role-Based Access Control (RBAC) Matrix

| Role | Typical Assignment | Capabilities |
|---|---|---|
| `platform_admin` | Platform Engineering & Operations | Full access: provision across environments (`dev` and `prod`), approve production gates, reconcile dead-letter callbacks, manage workload TTLs |
| `developer` | Application Engineering Teams | Project-scoped access: provision development workloads within assigned workspaces, inspect safe operational outputs, initiate safe workload teardowns |

Authentication credentials are provisioned out-of-band by Platform Operations and mapped to approved developer workspaces.

---

## 3. Web Portal User Guide

### 3.1 Template Catalog

Navigate to **Template Catalog** in the top navigation bar. You will find four pre-approved, version-pinned, immutable templates:

1. **T1: Agent on Vertex AI Agent Engine (`t1-agent-engine`) — Enterprise Elevated**
   - *Description*: Governed enterprise-grade ADK reasoning agent platform deployed to Google Cloud Vertex AI Agent Engine.
   - *Infrastructure Provisioned*:
     - **Dedicated Runtime Identity**: Least-privilege service account (`sa-t1-{deployment_id}`) with Vertex AI user permissions.
     - **Dedicated Staging & Artifact Bucket**: Versioned Cloud Storage bucket (`idp-agent-staging-{deployment_id}`) with an automated 30-day lifecycle expiration rule.
     - **Tool Secret Store**: Dedicated Google Secret Manager secret (`sa-t1-{deployment_id}-tool-secret`) with IAM secret accessor granted to the agent runtime.
     - **Cloud Monitoring Alert Policy**: Automated metric threshold alert (`idp-t1-{deployment_id}-error-rate`) logging reasoning engine errors.
   - *Supported Models*: `gemini-2.5-flash`, `gemini-2.5-pro`
   - *Cost Tier*: Low
   - *Interactive Testing*: Native **Agent Playground** support in the portal.
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

### 3.2 Workspaces and Context Switching

In the top right navigation bar, the **`WORKSPACE`** selector defines your active security, tenancy, and state boundary:
- **Tenant Scope**: Pre-populates all deployment requests with your active workspace (e.g., `ws-dev`, `default`, `admin`).
- **RBAC Enforcement**: The FastAPI control plane verifies your user identity against the target workspace; non-admin users attempting cross-tenant provisioning are rejected with `403 Forbidden`.
- **Terraform State Isolation**: Scopes the GCS remote state storage key (`idp-tfstate-{project}/workspaces/{workspace}/deployments/...`), preventing state collisions between teams.
- **View Filter**: The **Deployments** tab automatically filters workloads to display only those belonging to your selected workspace.

---

### 3.3 Provisioning a Workload & GitHub Dispatch

1. Click **"Configure & Deploy"** on any template card (e.g., **Agent on Vertex AI Agent Engine**).
2. Complete the modal form:
   - **Target Environment**: Select `dev` (or `prod` if authorized).
   - **Agent Name**: Enter a logical identifier (e.g., `support-agent-v1`).
   - **Governed Model**: Choose from the approved model dropdown (e.g., `gemini-2.5-flash`).
   - **GCP Region**: Target region (e.g., `us-central1`).
3. Click **"Submit Provisioning Request"**.
4. The control plane validates policies, checks for deployment locks, verifies idempotency, writes the audit log, and dispatches the workflow.

> [!NOTE]
> **Why a GitHub PAT is Used for Workflow Dispatch**:
> The FastAPI control plane running on Cloud Run is strictly isolated from infrastructure execution—it holds no direct broad Terraform permissions. Instead, it dispatches versioned GitHub Actions workflows via the GitHub REST API using a fine-grained Personal Access Token (PAT) stored in Google Secret Manager (`idp-github-dispatch-token`). Once triggered, GitHub Actions executes 100% keyless provisioning on GCP using Workload Identity Federation (WIF).

---

### 3.4 Request Lifecycle Tracker

The tracker displays live execution telemetry through an interactive stage timeline:

```text
[1] PENDING ──▶ [2] DISPATCHED ──▶ [3] PLANNING ──▶ [4] APPLYING ──▶ [5] SUCCEEDED
```

- **PENDING**: Request record created, atomic deployment lock acquired.
- **DISPATCHED**: GitHub Actions workflow triggered via fine-grained credentials.
- **PLANNING**: Terraform plan generated and validated against remote state in Cloud Storage.
- **APPLYING**: Terraform apply executed; workload runtime service accounts, staging buckets, secrets, and alert policies provisioned.
- **SUCCEEDED**: Pre-activation readiness smoke test verified; deployment transitioned to `ACTIVE`; deployment lock released.
- **FAILED**: If any stage fails, the request transitions to `FAILED` with a sanitized failure class (e.g. `readiness_failed`, `terraform_apply_failed`) and lock is safely released.

---

### 3.5 Managing Deployments, Safe Outputs & Agent Playground

Navigate to the **Deployments** tab to view active workloads in your selected workspace.

#### 1. Interactive Agent Playground:
Click the **Playground** (`Play` / `Terminal` icon) button on any active T1 deployment:
- Send interactive reasoning queries directly to the provisioned agent.
- Inspect the live reasoning response, model metadata, execution latency, and Model Armor safety evaluation.

#### 2. Inspecting Safe Operational Configuration:
Click the **Outputs** (`Code` icon) button on any active deployment to view sanitized operational metadata:
- `deployment_id`: Unique identifier (e.g., `dep-bdba18c9`)
- `runtime_sa_email`: Dedicated service account (e.g., `sa-t1-depbdba18c9@mybrightday-dev.iam.gserviceaccount.com`)
- `staging_bucket`: GCS bucket for agent artifacts (`idp-agent-staging-depbdba18c9`)
- `tool_secret_id`: Secret Manager secret for tool credentials
- `alert_policy_id`: Cloud Monitoring alert policy for error rate tracking
- `model_name`: Configured foundation model (e.g., `gemini-2.5-flash`)
- `region`: Cloud deployment region (e.g., `us-central1`)
- `status`: `PROVISIONED`

> [!IMPORTANT]
> The platform adheres to strict data-masking rules: **Zero credentials, secret values, bearer tokens, or raw Terraform state files are ever returned to the client.**

#### 3. Safe Two-Step Workload Destruction:
1. Click the red **Destroy** (`Trash2` icon) button on the target deployment row.
2. In the confirmation dialog, type the exact **Deployment ID** to confirm.
3. Click **"Permanently Destroy"**.
4. The system acquires the teardown lock, sets status to `DESTROYING`, and executes `terraform destroy` via GitHub Actions to cleanly tear down the Reasoning Engine, staging bucket, secrets, and alert policies.
5. Once complete, the deployment status permanently transitions to `DESTROYED`.

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
# Login to obtain access token
uv run python cli/main.py login --username <username> --password "<password>"

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

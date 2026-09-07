# IDP Control Plane Architecture
**Internal Developer Platform for Governed Agentic AI on Google Cloud Platform**

---

## 1. System Overview

The Internal Developer Platform (IDP) is an asynchronous, secure, self-service control plane designed to provision, govern, monitor, and tear down enterprise agentic AI workloads on Google Cloud Platform. 

The platform separates the **control plane** (FastAPI running on Cloud Run with Firestore Native persistence) from the **infrastructure execution plane** (version-pinned GitHub Actions workflows executing Terraform via GCP Workload Identity Federation) and the **workload data plane** (Vertex AI Agent Engine, Managed Vertex AI RAG, Cloud Run containers, and Model Armor guardrails).

```text
+-----------------------------------------------------------------------------------+
|                                CLIENT LAYER                                       |
|                                                                                   |
|    +-----------------------------+             +-----------------------------+    |
|    |      React Developer        |             |         IDP Python          |    |
|    |           Portal            |             |            CLI              |    |
|    +--------------+--------------+             +--------------+--------------+    |
+-------------------|-------------------------------------------|-------------------+
                    | 60-min JWT Bearer Token                   |
                    v                                           v
+-----------------------------------------------------------------------------------+
|                          CONTROL PLANE (Cloud Run)                                |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                             FastAPI App                                     |  |
|  |                                                                             |  |
|  |   [ /auth ]        [ /templates ]     [ /requests ]      [ /deployments ]   |  |
|  |   Argon2id auth    Versioned catalog  Idempotent dispatch Locking & status  |  |
|  |                                                                             |  |
|  |   [ /governance ]  [ /callbacks ]     [ /admin ]         [ Pub/Sub Svc ]    |  |
|  |   Model Armor      WIF ID Token auth  Reconciliation     Event boundary     |  |
|  +-----------------------------------------------------------------------------+  |
|           |                           |                          |                |
|           v                           v                          v                |
|    +--------------+            +--------------+           +--------------+        |
|    |  Firestore   |            |    Secret    |           |   Pub/Sub    |        |
|    |    Native    |            |   Manager    |           |  Topic /     |        |
|    |   Database   |            |  JWT Key/PAT |           |    Slack     |        |
|    +--------------+            +--------------+           +--------------+        |
+---------------------------------------|-------------------------------------------+
                                        | GitHub Actions Workflow Dispatch
                                        | (Fine-grained PAT from Secret Manager)
                                        v
+-----------------------------------------------------------------------------------+
|                     EXECUTION PLANE (GitHub Actions + WIF)                        |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Job: plan                                                                   |  |
|  |   1. Authenticate to GCP via Workload Identity Federation (OIDC)            |  |
|  |   2. Post PLANNING callback with pipeline ID token to Control Plane         |  |
|  |   3. Run `terraform plan` on immutable template checkout                    |  |
|  +-----------------------------------------------------------------------------+  |
|                                       |                                           |
|                                       v (Environment Approval Gate: prod / dev)   |
|  +-----------------------------------------------------------------------------+  |
|  | Job: apply                                                                  |  |
|  |   1. Hold for required reviewer approvals if environment == 'prod'          |  |
|  |   2. Post APPLYING callback with sequence verification                      |  |
|  |   3. Run `terraform apply` using isolated GCS state backend                 |  |
|  |   4. Run template readiness smoke tests (ADK query, RAG retrieval, HTTP)    |  |
|  |   5. Post SUCCEEDED callback with safe output attributes                    |  |
|  +-----------------------------------------------------------------------------+  |
|                                       |                                           |
|                                       v                                           |
|                         GCP Workload Resources                                    |
|       (Staging Bucket · Runtime SA · Tool Secrets · Alert Policy · Agent Engine)  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

1. **Control Plane $\neq$ Execution Environment**: The API never executes Terraform directly. It creates auditable lifecycle records, validates schema inputs against immutable templates, and dispatches GitHub Actions pipelines.
2. **Zero Service-Account JSON Keys**: All pipeline operations authenticate via GitHub Actions OIDC + GCP Workload Identity Federation (WIF).
3. **Parameter & Context Binding**: Pipeline callbacks validate monotonic sequence counters and strict request-to-deployment context matching before updating state machines.
4. **Idempotency with 24-hour TTL**: All mutation endpoints require an `Idempotency-Key` header with SHA-256 payload digest verification.
5. **Deployment Concurrency Locking**: Atomic locks prevent concurrent mutations or premature teardowns on active requests.
6. **Immutable Templates**: Infrastructure templates in `templates/` are version-pinned and referenced by exact Git commit SHAs.
7. **Perimeter Governance via Model Armor**: All agent interactions are governed by bidirectional screening against prompt injection, jailbreaks, and PII leakage.

---

## 3. Plane Separation & Boundaries

The architecture enforces strict separation between three distinct runtime planes:

| Plane | Technologies | Responsibilities | Security Constraints |
|---|---|---|---|
| **Control Plane** | FastAPI, Python 3.11+, Cloud Run, Firestore Native | User auth, template catalog, request queueing, concurrency locks, state records, safe telemetry. | Zero direct Terraform execution; cannot access data planes; reads secrets via IAM. |
| **Execution Plane** | GitHub Actions, WIF, Terraform 1.9+, GCS State | Checkout immutable templates, plan/apply infrastructure, run smoke tests, post monotonic callbacks. | Keyless OIDC identity; scoped service accounts; isolated remote state keys. |
| **Workload Data Plane** | Vertex AI Agent Engine, Cloud Run v2, RagManagedDb | Host reasoning loops, embed documents, execute agent tools, serve user queries. | Private IAM authentication; zero public data ingress without Model Armor mediation. |

---

## 4. Platform Plane vs. Workload Plane Separation

The platform strictly decouples **Platform Infrastructure Provisioning** from **Workload Application Deployment**:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Platform Plane (Terraform via GitHub Actions)            │
│    • Dedicated GCS Staging Bucket (gs://idp-t1-...)         │
│    • Dedicated Runtime Service Account (sa-t1-...)          │
│    • Dedicated Tool Secrets Container (idp-tools-...)       │
│    • Cloud Monitoring Watchdog Alert Policy                 │
└──────────────────────────────┬──────────────────────────────┘
                               │  "The house has been built;
                               │   ready for application code"
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Workload Plane (Developer Application Code)              │
│    • Ingests platform contract via idp-config.json          │
│    • Packages custom tools, system instructions, & wheels   │
│    • Uploads serialized agent bundle to GCS Staging Bucket  │
│    • Registers physical ReasoningEngine on Vertex AI        │
└─────────────────────────────────────────────────────────────┘
```

### Why the Staging Bucket is Initially Empty
When a `t1-agent-engine` deployment reaches `ACTIVE` status:
* Terraform has fully provisioned the staging bucket, runtime service account, tool secret, and alert policy on Google Cloud.
* The bucket is initially empty because application code has not yet been packaged and deployed into it.
* The developer runs `python deploy.py` (or CI/CD packaging) which serializes the agent and uploads the artifact bundle to the provisioned staging bucket.

### Contract Bridging (`idp-config.json`)
The IDP exports a clean, sanitized configuration file linking platform outputs to the workload:
```json
{
  "deployment_id": "dep-2899d395",
  "project_id": "mybrightday-dev",
  "region": "us-central1",
  "runtime_service_account": "sa-t1-dep2899d395@mybrightday-dev.iam.gserviceaccount.com",
  "staging_bucket": "idp-t1-mybrightday-dev-dep-2899d395",
  "tool_secret_id": "idp-tools-dep2899d395",
  "model_name": "gemini-2.5-flash"
}
```

---

## 5. Zero-Static-Key WIF & Workflow Dispatch Model

No service account JSON keys are ever generated, committed, or stored. All machine-to-cloud interactions use OIDC tokens exchanged via Google Cloud Workload Identity Federation.

### Workflow Dispatch Architecture
1. **GitHub Personal Access Token (PAT)**:
   * The GitHub REST API requires authentication to trigger `workflow_dispatch` events.
   * A fine-grained PAT scoped strictly to `Actions: Read and write` on this repository is stored in Google Secret Manager (`idp-github-dispatch-token`).
   * The API runtime service account (`idp-api-runtime`) retrieves this token into memory on startup via IAM.
2. **Keyless Cloud Provisioning**:
   * Once triggered, GitHub Actions exchanges its GitHub OIDC token for temporary Google Cloud federated credentials via WIF.
   * Dedicated pipeline service accounts (e.g. `idp-pipeline-t1-dev`) execute Terraform with strictly scoped permissions.
3. **Cryptographic Callbacks**:
   * On completion, the pipeline mints a Google OIDC ID token to authenticate callbacks back to the control plane API.

---

## 6. Control Plane Authentication & Tenancy

* **Password Hashing**: Argon2id with OWASP-compliant parameters (64 MiB memory, 3 iterations, 4 threads).
* **JWT Access Tokens**: Stateless HMAC-SHA256 tokens bounded to a strict 60-minute lifetime, signed with a secret retrieved from Secret Manager.
* **Revocation & Invalidation**: Global token versioning counter in Firestore invalidates existing sessions on password change.
* **Workspace Isolation**: Role-based access control enforces tenancy across `developer` and `platform_admin` roles.

---

## 7. Agent Runtime & Model Armor Gateway Architecture

The control plane provides a secure, governed proxy gateway via `POST /deployments/{deployment_id}/query` (powering the Developer Portal **Query Agent** playground).

```text
Client / Developer Portal
       │
       ▼
[IDP Control Plane API: POST /deployments/{deployment_id}/query]
       │
       ├─► 1. AUTH & TENANCY: Verify 60-min JWT & workspace membership
       │
       ├─► 2. MODEL ARMOR INGRESS: Screen for Prompt Injections, Jailbreaks & PII (SSN, Cards)
       │      └─ [VIOLATION] ──► Block query immediately (HTTP 400 Policy Violation)
       │
       ├─► 3. INTELLIGENT ROUTING DECISION:
       │      ├─► A. Physical Vertex AI Engine (resource_id is active & non-simulated):
       │      │      Dispatches to remote reasoning engine container on Vertex AI
       │      │
       │      └─► B. Simulated / Staging Workload (resource_id contains 'simulated-'):
       │             Evaluates reasoning loop and autonomous tool calls (e.g. add, subtract)
       │             locally via embedded agent proxy without incurring cloud GPU/VM cost
       │
       ├─► 4. MODEL ARMOR EGRESS: Screen final response for sensitive data leakage
       │
       └─► 5. AUDIT EVENT LEDGER: Append immutable record to Firestore `audit_events`
              (actor_user_id, deployment_id, tool_calls, guardrail_status: PASSED)
```

### Model Armor Dual-Mode Integration
1. **Automated Perimeter Gateway (Zero-Code)**: When querying through the IDP API or Developer Portal, Model Armor is active and enforced automatically. Injections and PII are blocked at the perimeter before touching foundation models.
2. **Embedded Python SDK Guardrail**: Standalone Python workloads can import the engine directly:
   ```python
   from api.app.governance.model_armor import ModelArmorEngine, PolicyAction, InspectionPoint

   armor = ModelArmorEngine(mode=PolicyAction.BLOCK, pii_detection=True, prompt_injection_filter=True)
   result = armor.inspect(prompt, point=InspectionPoint.PROMPT)
   if not result["passed"]:
       raise ValueError(f"Blocked: {result['reason']}")
   ```

---

## 8. Multi-Layer Operational Verification

Operators and developers can verify that workloads are strictly bound to their provisioned infrastructure across four verifiable proof points:

| Validation Layer | Cloud Resource | Verification Method / Evidence |
|---|---|---|
| **Identity Attribution** | Runtime Service Account | Cloud Logging filter: `protoPayload.authenticationInfo.principalEmail == "sa-t1-{dep_id}@..."` proves execution identity. |
| **Storage Isolation** | GCS Staging Bucket | `gcloud storage ls gs://idp-t1-{project}-{dep_id}/` verifies serialized model bundles and dependencies are isolated with 7-day TTL. |
| **Secret Governance** | Secret Manager Container | Audit log query on `secrets/idp-tools-{dep_id}` verifies tool credentials are read only by the authorized runtime SA. |
| **Observability** | Cloud Monitoring Alert | `gcloud monitoring policies describe {alert_id}` confirms active watchdog policy targeting `ReasoningEngine` error rate > 5%. |
| **Control Plane Audit** | Firestore `audit_events` | Querying `/audit?deployment_id={dep_id}` provides an immutable record of queries, actors, and guardrail verdicts. |

---

## 9. Quality Gates & Test Verification

All architectural contracts, security constraints, and lifecycle transitions are validated by automated test suites:

* **Unit Tests (23 Passed)**: Argon2id hashing, JWT generation, SHA-256 idempotency, state machines.
* **API Integration (33 Passed)**: Auth routes, template catalog, lifecycle requests, locking, reconciliation.
* **Template Contracts (18 Passed)**: T1, T2, T3, and T4 manifests, smoke tests, Model Armor filters.
* **CLI Client (5 Passed)**: Login, template listing, request creation, governance inspection.
* **Total Quality Gate**: **74 / 74 PASSED (100%)**

# IDP Control Plane Architecture

## 1. System Overview

The Internal Developer Platform (IDP) for Agentic AI on Google Cloud Platform is an asynchronous, secure, and governed control plane. The platform enables development teams to provision, manage, and destroy governed agentic AI workloads (Vertex AI Agent Engine, Managed Vertex AI RAG Engine, Cloud Run Agent containers, and Model Armor governance profiles) via self-service APIs and a modern React developer portal.

The platform separates the **control plane** (FastAPI running on Cloud Run with Firestore Native state) from the **infrastructure execution plane** (version-pinned GitHub Actions workflows executing Terraform via GCP Workload Identity Federation).

```
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
|             (Vertex AI Agent Engine / RAG Engine / Cloud Run)                     |
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

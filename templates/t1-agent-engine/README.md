# T1 Template: Agent on Vertex AI Agent Engine

## Overview

The `t1-agent-engine` template provisions a governed, enterprise-grade AI reasoning platform on Google Cloud Vertex AI Agent Engine using the Agent Development Kit (ADK) framework.

Rather than provisioning a lone identity, T1 deploys a complete, secure operational ecosystem with dedicated staging buckets, tool secrets, Cloud Monitoring alert policies, and live reasoning management.

---

## 1. Specifications

- **Template ID**: `t1-agent-engine`
- **Supported Environments**: `dev`
- **Supported Models**: `gemini-2.5-flash`, `gemini-2.5-pro`
- **Supported Regions**: `us-central1`
- **Cost Tier**: Low
- **Framework**: Agent Development Kit (ADK)

---

## 2. Enterprise Infrastructure Stack

Every T1 deployment provisions the following isolated Google Cloud resources:

1. **Dedicated Runtime Service Account**:
   - Resource: `google_service_account.agent_runtime` (`sa-t1-{deployment_id}`)
   - Roles: `roles/aiplatform.user`, `roles/storage.objectViewer` on its staging bucket, `roles/secretmanager.secretAccessor` on its tool secret.
2. **Dedicated Artifact & Staging Storage**:
   - Resource: `google_storage_bucket.agent_staging` (`idp-agent-staging-{deployment_id}`)
   - Configuration: Object versioning enabled, force destroy enabled, automated 30-day lifecycle expiration rule.
3. **Dedicated Tool Secret**:
   - Resource: `google_secret_manager_secret.agent_tool_secret` (`sa-t1-{deployment_id}-tool-secret`)
   - Purpose: Securely stores external API keys and tool credentials for the agent without hardcoding.
4. **Cloud Monitoring Alert Policy**:
   - Resource: `google_monitoring_alert_policy.agent_error_alert` (`idp-t1-{deployment_id}-error-rate`)
   - Metric Filter: Tracks reasoning engine errors and abnormal failure spikes via Cloud Logging.
5. **Vertex AI Reasoning Engine**:
   - Managed Reasoning Engine resource deployed via `manage_reasoning_engine.py`.

---

## 3. Directory Layout

```text
templates/t1-agent-engine/
├── template.yaml            # Governed manifest with JSON Schema
├── README.md                # Template documentation
├── terraform/               # Isolated Terraform definition
│   ├── main.tf              # SA, GCS bucket, Secret, Alert Policy
│   ├── variables.tf         # Parameter schemas
│   └── outputs.tf           # Safe operational outputs
├── agent/                   # ADK agent logic & smoke test
│   ├── agent.py             # Governed agent implementation
│   ├── smoke_test.py        # Readiness verification probe
│   └── requirements.txt
└── scripts/
    └── manage_reasoning_engine.py  # Live CLI manager (deploy, query, destroy)
```

---

## 4. Lifecycle Behavior

- **Create**:
  1. Terraform initializes with isolated remote state key: `templates/t1-agent-engine/{deployment_id}/terraform.tfstate`.
  2. Provisions runtime SA, staging bucket, Secret Manager secret, and Cloud Monitoring alert policy.
  3. Deploys Agent Engine reasoning engine via `manage_reasoning_engine.py deploy`.
  4. Runs `agent/smoke_test.py` readiness check verifying `agent.query("ping") == "pong"`.
  5. Emits `SUCCEEDED` callback with safe outputs to transition deployment to `ACTIVE`.

- **Destroy**:
  1. Tears down the Reasoning Engine resource via `manage_reasoning_engine.py destroy`.
  2. Executes `terraform destroy` to cleanly delete the service account, staging bucket, tool secret, and alert policy.
  3. Emits `SUCCEEDED` callback to mark deployment permanently `DESTROYED`.

---

## 5. Safe Operational Outputs Contract

The template exposes only non-sensitive operational metadata back to the control plane and portal:
- `deployment_id`: Unique workload identifier
- `runtime_sa_email`: Attached service account
- `staging_bucket`: GCS bucket URI
- `tool_secret_id`: Secret Manager secret identifier
- `alert_policy_id`: Cloud Monitoring alert policy identifier
- `agent_engine_resource_id`: Deployed Vertex AI Reasoning Engine resource ID
- `model_name`: Configured Gemini model
- `region`: Cloud deployment region

---

## 6. Interactive Testing via Agent Playground

Once `ACTIVE`, developers can query the live agent directly from the **Deployments** tab in the developer portal using the **Playground** button. Queries are routed through the control plane's Model Armor guardrails and returned with reasoning traces, latency, and safety evaluation.

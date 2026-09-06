# T1 Template: Agent on Vertex AI Agent Engine

## Overview

The `t1-agent-engine` template provisions a governed, enterprise-grade AI agent on Google Cloud Vertex AI Agent Engine using the Agent Development Kit (ADK) framework.

---

## 1. Specifications

- **Template ID**: `t1-agent-engine`
- **Supported Environments**: `dev`
- **Supported Models**: `gemini-2.5-flash`, `gemini-2.5-pro`
- **Supported Regions**: `us-central1`
- **Cost Tier**: Low

---

## 2. Directory Layout

```text
templates/t1-agent-engine/
├── template.yaml        # Governed manifest with JSON Schema
├── README.md            # Template documentation
├── terraform/           # Isolated Terraform definition
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── agent/               # ADK agent logic & smoke test
    ├── agent.py
    ├── smoke_test.py
    └── requirements.txt
```

---

## 3. Lifecycle Behavior

- **Create**:
  1. Terraform initializes with isolated remote state key: `templates/t1-agent-engine/{deployment_id}/terraform.tfstate`.
  2. Provisions a dedicated runtime service account (`sa-t1-{deployment_id}`).
  3. Deploys Agent Engine reasoning engine.
  4. Runs `agent/smoke_test.py` readiness check.
  5. Emits `SUCCEEDED` callback to mark deployment `ACTIVE`.

- **Destroy**:
  1. Terraform destroys the dedicated runtime service account and Agent Engine resources.
  2. Emits `SUCCEEDED` callback to mark deployment `DESTROYED`.

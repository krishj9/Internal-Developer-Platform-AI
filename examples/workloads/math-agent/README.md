# Sample Workload: Governed Math Reasoning Agent

This directory contains a complete, working sample of a domain-specific agentic AI application built on top of the **IDP T1 (Vertex AI Agent Engine)** platform template.

---

## 🏛️ Architecture: Platform vs. Workload Separation

In the Internal Developer Platform (IDP), infrastructure blueprints and application workloads are strictly decoupled:

| Layer | Responsibility | Directory / Component |
|---|---|---|
| **Platform Plane** | Provisions runtime service accounts, Vertex AI IAM permissions, Cloud Logging, and GCS staging | `templates/t1-agent-engine` (100% generic for all 10 teams) |
| **Workload Plane** | Defines domain-specific tools, ReAct reasoning loops, and business logic | `examples/workloads/math-agent` (Specific to this team's application) |

---

## 🚀 End-to-End Developer Walkthrough

### Step 1: Provision Infrastructure via IDP

Using the IDP CLI or Web Portal:

```bash
# Authenticate to IDP
idp login -u <username> -p <password>

# Submit T1 Agent Engine provisioning request
idp requests create \
  --template t1-agent-engine \
  --workspace ws-dev \
  --environment dev \
  --inputs-json '{"agent_name": "math-agent", "model_name": "gemini-2.5-flash", "region": "us-central1"}'
```

---

### Step 2: Export Workload Configuration (`idp-config.json`)

Once provisioning reaches `ACTIVE`, export your deployment's configuration:

#### Option A: Via IDP CLI
```bash
idp deployments config <deployment_id> --out idp-config.json
```

#### Option B: Via Developer Portal
In the **Deployments** tab, open your deployment's **Outputs** modal and click **"Download idp-config.json"**. Place this file in `examples/workloads/math-agent/`.

The resulting `idp-config.json` looks like:
```json
{
  "deployment_id": "dep-a1b2c3d4",
  "workspace": "ws-dev",
  "environment": "dev",
  "project_id": "mybrightday-dev",
  "region": "us-central1",
  "model_name": "gemini-2.5-flash",
  "runtime_service_account": "sa-t1-a1b2c3d4@mybrightday-dev.iam.gserviceaccount.com",
  "staging_bucket": "idp-state-mybrightday-dev"
}
```

---

### Step 3: Test Locally (Fast & Free)

Run the autonomous tool-calling loop locally:

```bash
# Run arithmetic multi-step reasoning
uv run python query.py "Add 200 to 423 and subtract 98 from it"
```

**Output:**
```text
============================================================
🤖 MATH REASONING AGENT EXECUTION
============================================================
Prompt:       "Add 200 to 423 and subtract 98 from it"
Status:       SUCCESS
Model:        gemini-2.5-flash
------------------------------------------------------------
🛠️  AUTONOMOUS TOOL INVOCATION SEQUENCE:
   [1] add({'a': 200.0, 'b': 423.0}) => 623.0
   [2] subtract({'a': 623.0, 'b': 98.0}) => 525.0
------------------------------------------------------------
🎯 Numerical Result: 525.0
📝 Reasoning Answer: Adding 200.0 to 423.0 gives 623.0. Subtracting 98.0 from 623.0 gives 525.0.
============================================================
```

Run the test suite:
```bash
uv run pytest tests/ -v
```

---

### Step 4: Deploy to Vertex AI Agent Engine

Package and deploy your agent to Google Cloud using the provisioned runtime identity:

```bash
# Dry run verification
uv run python deploy.py --dry-run

# Live deployment to Vertex AI Agent Engine
uv run python deploy.py
```

`deploy.py` automatically reads `idp-config.json`, uploads the agent bundle to Cloud Storage, and registers the Reasoning Engine resource on Google Cloud Vertex AI.

---

### Step 5: Query Live Vertex AI Engine

```bash
uv run python query.py --cloud "Multiply 15 by 8 and add 40"
```

---

### Step 6: Teardown Infrastructure

When the workload is no longer needed:
```bash
idp deployments destroy <deployment_id>
```
All GCP IAM bindings, runtime service accounts, and cloud artifacts are safely torn down by the IDP control plane.

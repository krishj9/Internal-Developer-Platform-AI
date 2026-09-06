---
name: template-authoring
description: Create, update, review, and validate governed, immutable, schema-driven IDP templates for GCP and GitHub Actions execution.
---

# Skill: Governed Template Authoring

## Purpose

Create and review immutable, schema-driven IDP templates that provision a narrow, safe infrastructure capability through Terraform and GitHub Actions.

## Use This Skill When

- Adding a new template under `templates/`.
- Changing `template.yaml`.
- Adding Terraform modules/resources to a template.
- Adding Agent Engine, Cloud Run, RAG, or governance template behavior.
- Publishing a template version.
- Defining readiness or destroy behavior.

## Template Layout

Each template follows:

```text
templates/<template-id>/
├── template.yaml
├── terraform/
├── agent/ or service/ or scripts/
├── tests/
└── README.md
```

Required initial templates:

```text
t1-agent-engine
t2-managed-rag
t3-cloud-run-agent
t4-governance
```

Do not start T2, T3, or T4 until the current delivery phase permits it.

## Immutable Release Rules

Every usable template must be released with:

```text
template_id
template_version
template_commit_sha
published manifest
input schema
safe output contract
readiness contract
destroy/retention contract
```

Rules:

- Template version is immutable after publishing.
- The request API resolves the commit SHA, not the caller.
- Workflow checks out the resolved SHA.
- Firestore template registry stores the release metadata.
- Changes require a new semantic version.
- Do not deploy from arbitrary branch input.

## `template.yaml` Requirements

Minimum manifest shape:

```yaml
id: t1-agent-engine
version: 2.0.0
display_name: Agent on Agent Engine
description: A short safe description.
supported_environments:
  - dev

inputs:
  type: object
  additionalProperties: false
  properties: {}
  required: []

defaults: {}

constraints:
  allowed_models: []
  allowed_regions: []
  resource_limits: {}
  allowed_workspaces: []

cost_tier: low

readiness:
  type: smoke_test
  description: Safe readiness condition.

output_contract:
  allowed_outputs: []

lifecycle:
  supports_create: true
  supports_destroy: true
  retention_notes: Safe description of retained or deleted assets.
```

Rules:

- Use JSON Schema-compatible validation.
- Set `additionalProperties: false` unless a strong documented reason exists.
- Define explicit enums for models, regions, environments, resource sizes, MIME types, and other bounded inputs.
- Do not accept arbitrary Terraform variable maps.
- Do not accept arbitrary resource names, shell commands, Git refs, model IDs, regions, service accounts, IAM roles, or secret references.
- Defaults must be secure and cost-bounded.
- The API validates inputs before workflow dispatch.

## Mandatory Governance Metadata

Every template must supply or derive:

```text
owner
workspace
environment
cost_center
template_id
template_version
deployment_id
expiration
managed_by=idp-platform
```

Client-provided ownership data must not override server-derived values.

## Safe Output Contract

Expose only explicitly approved, non-sensitive outputs.

Potentially safe:

```text
deployment_id
logical service name
lifecycle state
safe endpoint alias when approved
dashboard reference
readiness status
created time
expiration time
```

Never expose:

```text
secret values
service-account keys
bearer tokens
Terraform state
private configuration
raw provider values
runtime credentials
internal connection strings
unapproved endpoints
```

## Readiness Contract

A template is not active until it passes its declared readiness test.

### T1

- Deploy ADK agent to Agent Engine.
- Execute a safe smoke prompt or deterministic service verification.
- Confirm expected safe response/condition.
- Do not use sensitive data.
- Use approved identity for invocation.

### T2

- Create corpus.
- Complete document ingestion.
- Retrieve expected content from known smoke document.
- Distinguish infrastructure, ingestion, and retrieval failures.

### T3

- Confirm Cloud Run revision readiness.
- Perform authenticated health/smoke invocation.
- Do not enable unauthenticated public access by default.

## Destroy Contract

Every template must describe:

- Resources destroyed.
- Resources intentionally retained.
- Artifact retention behavior.
- State behavior.
- IAM bindings removed.
- Data retention requirements.
- Validation that no unowned template resources remain.

Destroy must use the same immutable template release and isolated Terraform state as create.

## T1-Specific Requirements

T1 is ADK only.

It must include:

- Pinned Agent Engine packaging/deployment method.
- Dedicated runtime service account where required.
- Approved model choices only.
- Approved POC region choices only.
- Structured logging and monitoring hooks.
- Non-sensitive Terraform outputs.
- Automated smoke test.
- Full destroy behavior.

Do not add LangGraph or arbitrary agent framework support before T1 is stable and reproducible.

## T2-Specific Guardrails

T2 supports only:

```text
Vertex AI RAG Engine
RagManagedDb
bounded GCS document source/prefix
versioned ingestion preset
```

Do not add:

```text
Vertex AI Search
Cloud SQL
AlloyDB
pgvector
Chroma
LanceDB
Firestore vector search
arbitrary connectors
unbounded upload paths
```

Validate document MIME type, count, total size, and source prefix before dispatch.

## Template Test Requirements

Each template must test:

- Manifest schema validation.
- Allowed/disallowed inputs.
- Required labels.
- Terraform formatting and validation.
- Output safety.
- Readiness success and failure behavior.
- Destroy behavior.
- IAM boundary expectations.
- Version/commit resolution contract.

# ADR-002: Declarative Terraform over Imperative SDK Execution

## Status
Accepted

## Context
Provisioning agentic infrastructure (Vertex AI Agent Engine, Cloud Run v2 services, Vertex AI RAG Managed Databases, IAM role bindings, and Cloud Monitoring alert policies) can be achieved either by invoking GCP Python SDKs directly from the control plane API or by dispatching declarative Terraform modules in CI/CD pipelines.

## Decision
We mandate declarative Terraform executed in GitHub Actions with isolated GCS remote state per deployment. The FastAPI control plane never runs direct infrastructure provisioning.

## Consequences
- Clean state locking, dry-run `terraform plan` reviews before apply, and guaranteed teardown fidelity via `terraform destroy`.
- Clear security separation: API service account has zero provisioning rights.

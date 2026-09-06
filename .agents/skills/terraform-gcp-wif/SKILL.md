---
name: terraform-gcp-wif
description: Guidelines and non-negotiable rules for Terraform, GCP IAM, Workload Identity Federation (WIF), and service account design in the IDP platform.
---

# Skill: Terraform, GCP IAM, and Workload Identity Federation

## Purpose

Safely build and review GCP bootstrap infrastructure, Terraform modules, state isolation, service accounts, and GitHub Actions Workload Identity Federation.

## Use This Skill When

- Creating or modifying Terraform.
- Configuring GCS Terraform state.
- Adding GCP service accounts or IAM bindings.
- Configuring WIF pools/providers.
- Adding Cloud Run, Firestore, Secret Manager, Vertex AI, Cloud Logging, Monitoring, Pub/Sub, or Artifact Registry permissions.
- Reviewing cloud security posture for a template or pipeline.

## Non-Negotiable Rules

- Never create, use, store, or download service-account JSON keys.
- GitHub Actions must authenticate with GitHub OIDC through GCP Workload Identity Federation.
- Do not grant Owner or Editor to API, pipeline, runtime, or workload identities.
- Prefer resource-scoped permissions.
- Separate API runtime, pipeline, and workload service accounts.
- Do not give the API runtime service account general infrastructure-provisioning permissions.
- Do not give the pipeline service account access to JWT signing secrets.
- Do not expose Terraform state or sensitive Terraform outputs.

## Bootstrap Requirements

Bootstrap infrastructure should provision:

- GCS state bucket.
- Firestore Native database.
- Firestore composite indexes.
- Secret Manager secret containers.
- API runtime service account.
- T1 development pipeline service account.
- WIF pool and GitHub OIDC provider.
- Necessary Cloud APIs.
- Cloud Run API deployment prerequisites.
- Required role bindings and custom roles only where predefined roles are too broad.

## Terraform State Bucket Requirements

The Terraform state bucket must have:

- Uniform bucket-level access.
- Versioning enabled.
- Public access prevention enabled.
- Logging/lifecycle controls as appropriate.
- Protected IAM access.
- Separate prefixes for:
  - bootstrap
  - API
  - template deployments
  - callback dead-letter payloads

Use state keys that isolate each deployment:

```text
templates/{template_id}/{deployment_id}/terraform.tfstate
```

Never place state files in:

- Repository source.
- Local shared paths.
- GitHub artifacts.
- API responses.
- Portal responses.
- General-purpose logs.

## WIF Trust Requirements

Restrict Workload Identity Federation trust to the intended:

- GitHub organization/owner.
- Repository.
- Workflow.
- Branch or immutable tag/ref.
- Environment, when applicable.

Do not use broad wildcard principal sets where more restrictive claims are available.

The binding should make clear:

```text
GitHub workflow identity
  → WIF provider
  → specific pipeline service account
  → only required project/resource permissions
```

Document:

- Attribute mappings.
- Attribute conditions.
- Service account impersonation binding.
- Approved repository/workflow/ref/environment combinations.
- Verification procedure.

## Service Account Design

Baseline identities:

```text
idp-api-runtime@PROJECT_ID.iam.gserviceaccount.com
idp-pipeline-t1-dev@PROJECT_ID.iam.gserviceaccount.com
```

Expected responsibilities:

| Identity | Allowed responsibilities | Explicit exclusions |
|---|---|---|
| API runtime | Firestore metadata, Secret Manager access to API secrets, Pub/Sub publishing | No general Terraform provisioning, no JWT secret exposure to pipeline, no broad Vertex admin |
| T1 pipeline | T1 state prefix, T1 runtime provisioning, scoped Vertex/GCS/logging actions | No user administration, no JWT signing secret, no unrelated pipeline impersonation |
| Bootstrap operator | Temporary setup access | Not used by deployed systems; no credentials in code |

Use dedicated runtime service accounts for Agent Engine/Cloud Run templates when required.

## IAM Change Procedure

For every IAM change:

1. State which identity receives the permission.
2. State which exact resource/scope it applies to.
3. State why it is needed.
4. State which operation fails without it.
5. Confirm it does not enable unrelated provisioning or impersonation.
6. Add or update least-privilege documentation.
7. Add infrastructure validation/tests where feasible.

Do not solve an access failure by adding broad roles without first identifying the missing permission.

## Terraform Module Standards

Use reusable modules for cross-cutting behavior:

```text
labels
workload-identity
service-account
monitoring-baseline
budget-alert
expiration-policy
```

Modules should:

- Have explicit typed variables.
- Validate bounded inputs.
- Set required labels.
- Avoid hidden provider defaults.
- Emit only safe outputs.
- Be versioned through repository commits/tags.
- Document resources created and destroyed.

## Required Labeling

Apply mandatory labels/tags/metadata consistently:

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

Derive values from validated server-side execution context. Do not allow arbitrary client-provided labels.

## Terraform Quality Gates

For Terraform changes, run:

```bash
terraform fmt -check -recursive
terraform validate
terraform plan
```

Also verify:

- Required provider versions are pinned.
- Terraform version is pinned.
- No sensitive output is exposed.
- State backend is remote and correctly scoped.
- IAM is least privilege.
- Resource labels exist.
- Destroy behavior is documented.
- No secret is present in variables, outputs, plan logs, or artifacts.

## Escalate Instead of Weakening Security

Stop and document alternatives if:

- WIF requires trust broader than the intended workflow/repository/ref/environment.
- A provider operation appears to require a service-account key.
- A required permission can only be satisfied with Owner/Editor.
- Terraform state isolation is not possible.
- A deployment cannot be safely destroyed.
- A resource name/region/model needs to be fully arbitrary.

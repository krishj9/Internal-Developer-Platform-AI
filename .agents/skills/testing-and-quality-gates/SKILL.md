---
name: testing-and-quality-gates
description: Platform definition of done, quality gates, test pyramid layers, and security regression checks for the IDP system.
---

# Skill: Testing and Quality Gates

## Purpose

Apply the platform definition of done through layered automated tests, infrastructure validation, workflow checks, and security regressions.

## Use This Skill When

- Adding or modifying any production code, Terraform, workflow, template, or API contract.
- Reviewing pull requests.
- Fixing defects.
- Adding lifecycle functionality.
- Preparing a phase exit demonstration.

## Test Pyramid

Use the appropriate level instead of relying only on end-to-end tests.

| Layer | Focus |
|---|---|
| Unit | Pure logic and domain rules |
| Component | Repositories and external-service adapters |
| API integration | HTTP contracts, auth, authorization, errors |
| Infrastructure | Terraform syntax, plans, IAM, labels, outputs |
| Workflow | WIF, lifecycle stages, callback behavior |
| End-to-end | Full golden path |
| Security regression | Abuse, spoofing, leakage, access-control failures |

## Mandatory Unit Tests

Cover:

- Argon2id verification wrapper.
- JWT issuance and parsing.
- JWT issuer/audience/signature/expiry validation.
- Token version invalidation.
- Disabled-user rejection.
- Role and workspace policy checks.
- Template input and policy validation.
- Lifecycle state transitions.
- Callback sequence handling.
- Idempotency payload hashing.
- Safe output filtering.
- Failure-class mapping.

## Mandatory API Integration Tests

Cover:

```text
POST /auth/login
GET  /auth/me
GET  /templates
POST /requests
GET  /requests/{id}
GET  /deployments
GET  /deployments/{id}
GET  /deployments/{id}/config
POST /deployments/{id}/destroy
POST /callbacks/pipeline
POST /admin/reconcile-callbacks
```

Minimum scenarios:

- Valid login.
- Generic invalid-login failure.
- Valid protected access.
- Missing bearer token.
- Expired and malformed tokens.
- Wrong issuer/audience/signature.
- Disabled user.
- Token version invalidation.
- Workspace authorization success and failure.
- Role authorization success and failure.
- Invalid template/environment/region/model/input.
- Rate limiting.
- Idempotency replay.
- Idempotency payload mismatch.
- Lifecycle concurrency conflict.
- Safe response filtering.
- Admin-only reconciliation.

## Callback Security Test Matrix

Test all of these negative cases:

- Wrong pipeline service account.
- Missing or invalid Google ID token.
- User JWT supplied to callback endpoint.
- Wrong request ID.
- Wrong deployment ID.
- Wrong template ID.
- Wrong template version.
- Wrong template commit SHA.
- Wrong repository.
- Wrong workflow.
- Wrong GitHub run ID.
- Wrong operation.
- Stale sequence number.
- Invalid state transition.
- Malformed payload.
- Exact duplicate event.
- Retry behavior.
- Dead-letter write after final retry.
- Reconciliation replay of dead-letter event.

## Terraform and Infrastructure Checks

At minimum run:

```bash
terraform fmt -check -recursive
terraform validate
terraform plan
```

Verify:

- Providers and Terraform version are pinned.
- State backend is remote and isolated.
- Required labels exist.
- No secrets appear in outputs.
- IAM is least privilege.
- WIF conditions are restricted.
- API identity cannot provision workloads directly.
- Pipeline identity cannot read API JWT signing secret.
- Destroy plan is viable.

## Workflow Checks

Validate:

- GitHub Actions versions are pinned.
- WIF authentication succeeds.
- No service-account key is used.
- Immutable template SHA is checked out.
- State key matches template/deployment isolation.
- Required callbacks are emitted in order.
- Callback retries use exponential backoff.
- Dead-letter records are written safely.
- Readiness test blocks success.
- Terraform state/secrets are not artifacts.
- Destroy is tested.

## End-to-End Golden Path

The T1 E2E test must demonstrate:

```text
login
→ obtain JWT
→ submit authorized request with Idempotency-Key
→ receive 202 Accepted
→ dispatch pipeline
→ WIF Terraform provisioning
→ callback progression
→ readiness passes
→ deployment ACTIVE
→ submit destroy request
→ WIF Terraform destroy
→ deployment DESTROYED
```

Test both successful and selected failure paths.

## Quality Gates Before Merge

A change is not complete until:

- Formatting passes.
- Unit tests pass.
- Relevant integration tests pass.
- Infrastructure validation passes when applicable.
- Security regression tests cover changed trust boundaries.
- Documentation and schemas are updated.
- No secrets or sensitive values enter logs, artifacts, or API output.
- Teardown/rollback behavior is considered.

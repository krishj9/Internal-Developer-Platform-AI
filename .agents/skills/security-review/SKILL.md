---
name: security-review
description: >-
  Use this skill when performing security reviews for identity, authentication,
  GCP IAM, WIF trust boundaries, Secret Manager access, pipeline callbacks,
  Terraform outputs, portal CORS/localStorage behavior, or readiness verification.
---

# Skill: Security Review for the GCP Agentic AI IDP

## Purpose

Perform a focused security review before merging any change that affects identity, secrets, cloud IAM, API authorization, callbacks, infrastructure lifecycle, portal behavior, or workload exposure.

## Use This Skill When

- Changing authentication, JWTs, password handling, or users.
- Changing service accounts, IAM, WIF, or Cloud Run IAM.
- Changing Secret Manager access.
- Adding a workflow or callback.
- Adding a template or Terraform module.
- Adding portal authentication/session behavior.
- Publishing deployment outputs/configuration.
- Adding RAG ingestion, model invocation, or notifications.
- Preparing a phase gate.

## Review Principles

- Default deny.
- Least privilege.
- Server-side enforcement.
- Immutable execution context.
- Explicit trust boundaries.
- Sensitive data minimization.
- Full lifecycle accountability.
- Destroyability and cost accountability.

## Authentication Review

Verify:

- Passwords use Argon2id only.
- Login failures are generic.
- JWTs have 60-minute expiry.
- Issuer, audience, signature, expiry, token version, and active user are checked.
- JWT signing material is in Secret Manager.
- Tokens, passwords, and secrets are never logged.
- Disabled accounts are denied.
- No refresh-token or registration scope is accidentally introduced.
- Browser token behavior is deferred until portal phase; when added, token is cleared on logout and `401`.

## Authorization Review

Verify:

- Workspace access is checked server-side.
- Role checks are performed at each protected operation.
- Owner/requester/cost metadata are server-derived.
- Templates, environment, model, region, and resource bounds are validated server-side.
- Cross-workspace reads and actions fail.
- Admin reconciliation requires platform admin.
- Human JWTs cannot use the callback endpoint.
- API does not trust portal roles, workflow inputs, or client-supplied identity fields.

## Secrets Review

Verify:

- Secret values are not in source control.
- Secret values are not Terraform outputs.
- Secret values are not Firestore fields.
- Secret values are not GitHub artifacts.
- Secret values are not callback payloads.
- Secret Manager IAM is narrowly scoped.
- API runtime can access only required API secrets.
- Pipeline identities cannot access JWT signing secret unless a documented exceptional need exists.
- Secret references, rather than values, are used in metadata.

## WIF and IAM Review

Verify:

- No service-account JSON key exists.
- GitHub WIF identity is restricted by repository, owner, workflow, ref, and environment.
- Pipeline service accounts are template/environment-specific where practical.
- API runtime lacks broad provisioning privileges.
- Pipeline service account has only required resource permissions.
- No Owner/Editor shortcuts are introduced.
- Service-account impersonation does not allow escalation to unrelated identities.
- Cloud Run callback caller is verified against expected pipeline identity.

## Callback Review

Verify:

- Google OIDC ID token is required.
- Callback audience is correct.
- Pipeline caller identity is verified.
- Request/deployment/template/version/commit/repository/workflow/run/operation are bound to original request.
- Event sequences are monotonic.
- Duplicate events are safe/idempotent.
- Invalid state transitions are rejected.
- Retries are bounded and use exponential backoff.
- Dead-letter payloads are safe and retained for reconciliation.
- Callback ledger is append-only.
- User bearer JWT cannot authenticate callbacks.

## Infrastructure Review

Verify:

- Terraform state is in protected GCS backend.
- State isolation uses template/deployment prefixes.
- Bucket versioning, uniform bucket-level access, and public access prevention are enabled.
- Required labels and expiration metadata are set.
- Sensitive outputs are excluded.
- Terraform execution occurs only in approved GitHub workflows.
- Destroy behavior is defined and tested.
- No direct developer data-plane IAM roles are added.

## Portal Review

When portal work begins, verify:

- `localStorage` use is limited to bearer-token persistence as specified.
- Token is cleared on logout and `401`.
- Token is absent from URLs, logs, telemetry, and analytics.
- UI does not expose sensitive deployment data.
- UI cannot set owner/requester fields.
- UI destroy action only submits an API destroy request.
- CORS allows only approved Firebase Hosting origin.
- CSP and dependency scanning are present where straightforward.
- UI authorization is treated as cosmetic; API is authoritative.

## AI/RAG Review

Verify:

- Models are allowlisted.
- Regions are allowlisted.
- Prompt/tool/retrieved-content/model-output screening behavior is explicit where Model Armor applies.
- RAG source types, paths, counts, MIME types, and total size are bounded.
- No arbitrary connector or data source is accepted.
- Readiness uses safe smoke content.
- Runtime credentials and private endpoints remain workload-only.
- Budget, TTL, and cleanup behavior are configured.

## Severity Guidance

Treat these as merge blockers:

- Service-account keys.
- Broad WIF trust.
- Owner/Editor assignment without explicit exceptional approval.
- Callback endpoint accepting portal JWTs.
- Secrets or Terraform state exposed by API, logs, artifacts, or outputs.
- Cross-workspace access.
- Mutable branch deployment after request approval.
- No destroy path for newly provisioned resources.
- User-controlled arbitrary infrastructure/model/region/workflow input.
- Missing readiness test before `ACTIVE`.

## Required Security Review Output

For any material security change, provide:

1. Trust boundary affected.
2. Identities involved.
3. Permissions added/removed.
4. Data classified as sensitive.
5. Validation and negative tests added.
6. Remaining risks or documented exceptions.
7. Rollback/destroy implications.

---
name: github-actions-pipeline-callbacks
description: >-
  Use this skill when authoring or modifying GitHub Actions workflows, composite actions,
  WIF authentication, Agent Engine packaging, Terraform execution, pipeline callbacks,
  exponential retries, dead-letter storage, or readiness tests.
---

# Skill: GitHub Actions Lifecycle Pipelines and Trusted Callbacks

## Purpose

Implement secure GitHub Actions workflows for Terraform lifecycle execution and authenticated callback delivery to the FastAPI control plane.

## Use This Skill When

- Adding workflows under `.github/workflows/`.
- Building composite actions under `.github/actions/`.
- Implementing WIF authentication.
- Packaging Agent Engine artifacts.
- Running Terraform plan/apply/destroy.
- Posting lifecycle callbacks.
- Adding callback retry, dead-letter, or reconciliation logic.

## Required Composite Actions

Maintain reusable composite actions for:

```text
authenticate-gcp-wif
terraform-lifecycle
package-agent-engine
post-pipeline-callback
run-readiness-test
```

Do not duplicate complex security logic across each workflow when a reusable action can enforce a consistent contract.

## Workflow Principles

- Pin GitHub Actions by version or immutable SHA per repository policy.
- Pin Terraform, provider, Python, Node.js, and `agents-cli` versions.
- Use WIF only; never use GCP service-account key JSON.
- Treat all workflow inputs as untrusted until verified against server-generated request context.
- Do not use arbitrary user input as a shell command, path, Terraform argument, state key, workflow selector, model, region, or service account.
- Do not print secrets, credentials, JWTs, authorization headers, Terraform state, or sensitive plan values.
- Do not upload Terraform state or sensitive configuration as artifacts.
- Use separate state prefixes by template and deployment ID.
- Fail closed if the execution context does not match the expected template/repository/workflow/ref/environment.

## Expected T1 Workflow Stages

```text
1. Receive validated dispatch input.
2. Check out immutable template commit SHA.
3. Authenticate with GCP using WIF.
4. Post PLANNING callback.
5. Initialize Terraform with isolated state key.
6. Run Terraform format/validate/plan.
7. Post APPLYING callback.
8. Run Terraform apply.
9. Package/deploy Agent Engine workload through pinned tooling.
10. Post VALIDATING callback.
11. Run readiness/smoke test.
12. Post SUCCEEDED callback.
13. On failure, post FAILED callback with safe failure class and summary.
```

Destroy stages:

```text
1. Receive validated destroy context.
2. Check out immutable template commit SHA.
3. Authenticate with WIF.
4. Post PLANNING callback.
5. Initialize Terraform using same isolated state key.
6. Post APPLYING callback.
7. Execute destroy.
8. Post SUCCEEDED callback.
9. On failure, post FAILED callback.
```

## Callback Payload

Callbacks must include:

```yaml
request_id: req-...
deployment_id: dep-...
template_id: t1-agent-engine
template_version: 2.0.0
template_commit_sha: immutable-sha
repository: organization/idp-platform
workflow: deploy-t1.yml
github_run_id: "123456789"
event_sequence: 1
operation: create
status: PLANNING
summary: Safe human-readable status
artifact_references: []
timestamp: RFC3339
```

Rules:

- Increment `event_sequence` monotonically for a request/run.
- Never include secrets, raw plans, state data, provider credentials, or sensitive runtime outputs.
- Use summaries that are operationally useful but safe.
- Include safe artifact references only.
- Use the exact resolved repository/workflow/template/commit metadata from dispatch context.

## Callback Authentication

The callback call must:

- Use a Google OIDC ID token minted for the Cloud Run callback audience.
- Be made by the WIF-authorized pipeline identity.
- Target the callback endpoint only.
- Never use a portal JWT, static API key, or GitHub token as callback authentication.
- Fail and retry when callback delivery fails transiently.

## Retry and Dead-Letter Requirements

For each callback:

1. Attempt delivery.
2. Retry up to three times.
3. Use exponential backoff.
4. Preserve the exact safe payload.
5. On final failure, write the safe callback envelope to the approved GCS dead-letter prefix.
6. Exit in a way that causes the overall workflow to be visible as failed when the callback is materially required.
7. Ensure reconciliation can replay dead-letter events without inventing new sequence data.

Dead-letter path pattern:

```text
callbacks/dead-letter/{request_id}/{github_run_id}/{event_sequence}.json
```

Do not store access tokens or secret-bearing headers in dead-letter payloads.

## Readiness Testing

Readiness is mandatory before a create request succeeds.

T1 readiness test requirements:

- Use a non-sensitive smoke prompt.
- Verify expected safe response or deterministic service condition.
- Authenticate through the approved CI/pipeline identity.
- Avoid public unauthenticated invocation.
- Return only safe result metadata in the callback.

A create request is not `SUCCEEDED` until readiness passes.

## Workflow Failure Handling

On failure:

- Capture a safe `failure_class`, such as:
  - `terraform_validation_failed`
  - `terraform_plan_failed`
  - `terraform_apply_failed`
  - `agent_packaging_failed`
  - `readiness_failed`
  - `callback_delivery_failed`
  - `destroy_failed`
- Post a `FAILED` callback when possible.
- Do not include stack traces that expose secrets, internals, or sensitive endpoints in the callback summary.
- Keep diagnostic detail in protected workflow logs, subject to redaction controls.
- Preserve request/deployment/run correlation identifiers.

## Review Checklist

- WIF is used and restricted.
- No SA key is used.
- Immutable template SHA is checked out.
- State key is isolated.
- Callbacks contain complete binding metadata.
- Callback retry/dead-letter behavior exists.
- Readiness precedes success.
- Outputs are filtered.
- Secrets/state are absent from logs/artifacts.
- Destroy uses the same validated execution context.

---
name: firestore-domain-model
description: >-
  Use this skill when designing or implementing Firestore persistence,
  schema models, idempotency with TTL, deployment locking, callback event
  ledgers, composite indexes, or reconciliation behavior for the IDP control plane.
---

# Skill: Firestore Domain Model, Idempotency, and Lifecycle State

## Purpose

Design and implement Firestore persistence for the IDP control plane, including lifecycle state, locking, idempotency, callbacks, templates, and audit records.

## Use This Skill When

- Adding Firestore collections or fields.
- Implementing repositories.
- Adding indexes.
- Creating request/deployment state transitions.
- Implementing lifecycle locking.
- Implementing idempotency.
- Recording audit or callback events.
- Building reconciliation behavior.

## Core Collections

```text
users
workspaces
templates
requests
deployments
audit_events
callback_events
idempotency_records
```

Keep document shapes explicit and versioned in Python domain models.

## Required Record Semantics

### Users

Store:

```text
user_id
username
password_hash
role
workspace_ids
active
token_version
created_at
updated_at
```

Rules:

- Store Argon2id hash only.
- Never store plaintext or reversible passwords.
- Increment `token_version` to revoke issued JWTs.
- Never return `password_hash` in API models.

### Templates

Store immutable published template metadata:

```text
template_id
template_version
template_commit_sha
manifest
schema_version
supported_environments
allowed_models
allowed_regions
status
published_at
published_by
```

Never overwrite a published immutable release. Create a new version.

### Requests

Store:

```text
request_id
deployment_id
operation
status
workspace
template_id
template_version
template_commit_sha
actor_user_id
actor_role
environment
safe_input_digest
github_repository
github_workflow
github_run_id
event_sequence
failure_class
safe_summary
created_at
updated_at
completed_at
```

Do not store unbounded raw request data if it might contain unsafe configuration. Persist validated, safe, necessary input metadata and a digest.

### Deployments

Store:

```text
deployment_id
workspace
template_id
template_version
template_commit_sha
environment
status
owner_user_id
labels
safe_outputs
expires_at
active_request_id
created_at
updated_at
destroyed_at
```

Rules:

- `active_request_id` is used to enforce one active lifecycle operation.
- Do not store runtime credentials, secret values, Terraform state, or sensitive provider configuration.
- `safe_outputs` must be filtered against template output contract.

### Callback events

Store append-only records:

```text
callback_event_id
request_id
deployment_id
github_run_id
event_sequence
operation
status
received_at
pipeline_identity
payload_digest
safe_payload
validation_result
```

Never mutate an accepted callback event. Record rejections safely for auditability.

### Audit events

Store:

```text
audit_event_id
actor_type
actor_id
action
resource_type
resource_id
request_id
deployment_id
outcome
correlation_id
safe_metadata
timestamp
```

Audit events must be append-only.

## Transactional Requirements

Use Firestore transactions or equivalent concurrency controls for operations that must be atomic:

- Checking and setting deployment `active_request_id`.
- Enforcing idempotency key behavior.
- Creating a request and reserving its lifecycle lock.
- Applying valid callback state transitions.
- Releasing the lock after terminal lifecycle state.
- Updating idempotency record result mapping.

Do not rely on in-memory locks in Cloud Run.

## Deployment Locking

For create, update, or destroy:

1. Read deployment state.
2. Check whether an active non-terminal request exists.
3. Reject with `409 Conflict` if another lifecycle request is active.
4. Create the new request.
5. Set `active_request_id`.
6. Release/clear it only after a valid terminal callback or terminal dispatch failure is recorded.

Ensure retries do not accidentally release or replace a lock owned by a different request.

## Idempotency Rules

Require:

```text
Idempotency-Key
```

Scope:

```text
(user_id, idempotency_key)
```

Persist:

```text
user_id
idempotency_key
payload_digest
request_id
response_status
safe_response
created_at
expires_at
```

Rules:

- Same key + same payload digest: return original result.
- Same key + different digest: `409 Conflict`.
- TTL: 24 hours.
- Do not duplicate dispatch for a valid idempotent retry.
- Destroy requests are also idempotent.
- Ensure TTL cleanup does not break active lifecycle correctness.

## Callback Processing

When processing a callback:

1. Verify pipeline identity before data processing.
2. Load original request and deployment.
3. Verify callback binding fields.
4. Verify event sequence.
5. Identify exact duplicate events.
6. Validate request/deployment state transition.
7. Append callback event.
8. Update request/deployment projections.
9. Write audit event.
10. Release lifecycle lock only for valid terminal state.

Reject stale sequence numbers and invalid transitions. Do not overwrite newer state with an older callback.

## Firestore Indexes

Keep composite indexes in:

```text
infra/bootstrap/firestore/firestore.indexes.json
```

Likely query patterns include:

- Deployments by workspace and updated time.
- Requests by deployment and creation time.
- Requests by actor and creation time.
- Requests by status and updated time.
- Deployments by status and expiry.
- Callback events by request and event sequence.
- Idempotency records by user and key.

Update the index file whenever a new compound query is introduced.

## Tests

Required tests include:

- Atomic deployment-lock behavior.
- Concurrent request rejection.
- Idempotency replay behavior.
- Idempotency key/payload mismatch.
- Idempotency TTL behavior.
- Valid and invalid lifecycle transitions.
- Duplicate callback idempotency.
- Stale callback rejection.
- Callback mismatch rejection.
- Terminal-state lock release.
- Audit/callback append-only behavior.
- Safe output filtering.
- Cross-workspace record access denial.

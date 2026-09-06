---
name: secure-fastapi-control-plane
description: >-
  Use this skill when building or reviewing FastAPI control plane endpoints,
  Argon2id authentication, 60-minute JWT token contracts, role/workspace authorization,
  request submission, rate limiting, workflow dispatch via Secret Manager credentials,
  or safe response contracts.
---

# Skill: Secure FastAPI Control Plane

## Purpose

Implement and review the FastAPI control plane for the IDP. The API is the authoritative policy, lifecycle, and orchestration boundary; it must never directly provision workload infrastructure.

## Use This Skill When

- Adding or changing FastAPI endpoints.
- Implementing authentication or authorization.
- Working with requests, deployments, workspaces, templates, or audit events.
- Adding workflow dispatch behavior.
- Handling lifecycle state transitions.
- Returning API responses that might expose deployment configuration.

## Core Rules

- Use FastAPI with clear module boundaries:
  - `api/` for route definitions and HTTP concerns.
  - `auth/` for password verification and JWT issuance/validation.
  - `authorization/` for role/workspace enforcement.
  - `domain/` for schemas, state machines, and policy decisions.
  - `repositories/` for Firestore persistence.
  - `services/` for orchestration, dispatch, callbacks, secrets, and audit.
- Keep routes thin. Put decision logic in services/domain modules.
- Use explicit Pydantic request and response models.
- Reject unknown or unsafe inputs unless the API contract intentionally permits them.
- Do not return raw Firestore records without response mapping and safe-field filtering.
- Do not permit client input to control actor identity, ownership, role, template commit SHA, workflow path, state key, service account, callback identity, or internal resource names.

## Required Endpoints

```text
GET  /healthz
POST /auth/login
GET  /auth/me

GET  /templates
POST /requests
GET  /requests/{request_id}
GET  /deployments
GET  /deployments/{deployment_id}
GET  /deployments/{deployment_id}/config
POST /deployments/{deployment_id}/destroy

POST /callbacks/pipeline
POST /admin/reconcile-callbacks
```

`/callbacks/pipeline` uses pipeline identity, not human bearer JWT authentication.

`/admin/reconcile-callbacks` requires a platform administrator and must be auditable.

## Authentication Requirements

- Users are preconfigured.
- Store and verify passwords with Argon2id.
- Return generic `401 Unauthorized` for failed login.
- Issue JWTs that expire in 3600 seconds.
- Validate issuer, audience, signature, expiry, token version, disabled-user status, and malformed tokens.
- Do not place access tokens in logs, exception traces, or response fields beyond the explicit login response.
- Ensure missing/invalid credentials fail closed.

Suggested JWT claims:

```json
{
  "sub": "user-id",
  "username": "platform_admin",
  "role": "platform_admin",
  "token_version": 1,
  "iss": "idp-platform",
  "aud": "idp-api",
  "iat": 0,
  "exp": 0
}
```

Treat role claims as convenience data only when consistent with the active user record. If current authorization depends on mutable server-side data, retrieve and validate the user record.

## Authorization Requirements

Roles:

```text
developer
approver
platform_admin
pipeline
```

Enforce:

- Workspace access.
- Template availability.
- Approved environment.
- Approved model and region constraints.
- Role/capability requirements.
- Server-derived request ownership and labels.
- Per-user rate limits.
- Protected administrative actions.
- Deployment read visibility.

Use dependencies such as:

```python
get_current_user
require_role
require_workspace_access
require_platform_admin
```

Never rely on portal-visible role state or client-submitted labels.

## Request Creation Workflow

For `POST /requests`:

1. Authenticate bearer token.
2. Verify active user, token version, role, and workspace access.
3. Require `Idempotency-Key`.
4. Validate rate limit.
5. Validate template release and schema.
6. Resolve immutable template commit SHA server-side.
7. Enforce allowed model, region, environment, cost, and policy constraints.
8. Verify no active non-terminal lifecycle request exists for the target deployment.
9. Perform idempotency lookup using `(user_id, idempotency_key)`.
10. Create request/deployment records and audit event transactionally where possible.
11. Dispatch the approved GitHub workflow using the server-held GitHub credential.
12. Persist dispatch metadata.
13. Return `202 Accepted` with safe request information.

If dispatch fails after a request record is created, transition the request safely to `FAILED`, record the failure class, and write an audit event. Never leave an ambiguous request without an observable outcome.

## Safe Response Contract

Allowed deployment response fields may include:

```text
deployment_id
request_id
workspace
template_id
template_version
status
environment
labels
created_at
updated_at
expires_at
safe_outputs
safe_summary
pipeline_run_url
```

Do not return:

```text
Terraform state
service account credentials
secret values
secret payloads
JWT signing material
GitHub dispatch token
private runtime endpoint details unless explicitly classified safe
raw provider configuration
internal state bucket locations when avoidable
```

`GET /deployments/{id}/config` must return only the safe local profile contract. It must never return a `gcp` profile or runtime credentials.

## Error Handling

Use stable, non-sensitive error responses.

| Condition | Expected response |
|---|---|
| Bad credentials | `401` generic error |
| Missing/invalid/expired JWT | `401` |
| Forbidden workspace/template/admin action | `403` |
| Absent resource under chosen concealment policy | `404` |
| Active lifecycle conflict | `409` |
| Idempotency key reused with different payload | `409` |
| Invalid schema/policy/model/region/environment | `422` |
| Rate limit exceeded | `429` |
| Unexpected error | `500` with correlation ID, no sensitive detail |

Log internal exception context securely and return a correlation identifier to the caller when appropriate.

## Completion Checklist

- Endpoint has request/response schema tests.
- Authorization is tested for every protected route.
- Negative cases are tested.
- Audit events exist for significant actions.
- Correlation IDs are included in logs.
- No secret or sensitive metadata is returned.
- State transitions use the domain state machine.
- Idempotency and concurrency checks are enforced.

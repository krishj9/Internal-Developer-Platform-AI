# IDP Security Model

## 1. Identity & Access Management (IAM)

The IDP control plane implements strict least-privilege principles and zero-static-key machine identity.

### Service Account Roles

| Identity | Purpose | Assigned Roles / Permissions | Prohibited Permissions |
|---|---|---|---|
| `idp-api-runtime` | Cloud Run FastAPI runtime | `roles/datastore.user` (Firestore), `roles/secretmanager.secretAccessor` (JWT key & PAT), `roles/pubsub.publisher` | No `Owner`/`Editor`, no SA key creation, no direct Terraform permissions |
| `idp-pipeline-t1-dev` | T1 Agent Engine Dev pipeline | `roles/aiplatform.user`, `roles/storage.objectAdmin` (T1 state prefix only) | No Firestore access, no Secret Manager access |
| `idp-pipeline-t2-dev` | T2 Managed RAG Dev pipeline | `roles/aiplatform.user`, `roles/storage.objectViewer` (docs bucket), `roles/storage.objectAdmin` (T2 state prefix) | No Secret Manager access |
| `idp-pipeline-t3-dev` | T3 Cloud Run Dev pipeline | `roles/run.admin`, `roles/iam.serviceAccountUser` (sa-t3 only), `roles/storage.objectAdmin` (T3 state prefix) | No global IAM admin, no Secret Manager access |
| `idp-pipeline-prod` | Production pipeline | Scoped to `prod` GCP resources and state prefix | Requires GitHub Environment manual approval gate |

---

## 2. Workload Identity Federation (WIF) Trust Policy

GitHub Actions workflows obtain GCP access tokens without static service account keys:

```
GitHub Actions Runner
  -> Requests OIDC ID token with audience = https://idp-api.internal/callbacks/pipeline
  -> Exchanges OIDC token with GCP Workload Identity Pool Provider
  -> Provider verifies claims:
       attribute.repository == "idp-platform-org/idp-platform"
       attribute.ref == "refs/heads/main" (or immutable release tags)
       attribute.environment == "dev" / "prod"
  -> Impersonates scoped pipeline service account
```

---

## 3. Control Plane Authentication & Sessions

- **Passwords**: Hashed with Argon2id using recommended OWASP parameters (memory cost 65536 KiB, time cost 3 iterations, parallelism 4 threads).
- **JWT Access Tokens**: 60-minute lifetime (3600 seconds), HMAC-SHA256 signed using secret key loaded from Google Secret Manager (`idp-jwt-signing-key`).
- **Token Invalidation**: User records contain a `token_version` integer. Incrementing `token_version` invalidates all previously issued JWTs across the platform.
- **Portal Storage**: Tokens stored in browser `localStorage`. Automatically cleared on logout or HTTP 401 response.

---

## 4. Pipeline Callback Authentication & Trust Boundary

Pipeline callbacks (`POST /callbacks/pipeline`) enforce:
1. **Google OIDC Token**: User JWT bearer tokens are strictly rejected. The request must present a valid Google ID token signed by `accounts.google.com`.
2. **Audience & Email Binding**: Auditing verifies the pipeline service account email against the expected workload role.
3. **Monotonic Sequence**: Rejects stale sequence numbers ($S \le S_{current}$) and recognizes exact duplicate replays safely.
4. **Parameter Context Match**: Request ID, deployment ID, template ID, and Git commit SHA must match the database record.

---

## 5. Model Armor Guardrails

Model Armor filters prompts, tool inputs, retrieved RAG content, and model outputs:
- **Jailbreak / Prompt Injection Filter**: Detects and neutralizes prompt override patterns.
- **PII Sanitizer**: Regex screening for SSNs, Credit Cards, and Email addresses.
- **Enforcement Modes**:
  - `BLOCK`: Rejects transaction immediately with auditable rejection record.
  - `REDACT`: Masks sensitive patterns with `[REDACTED_SSN]`, `[REDACTED_CC]`, `[REDACTED_EMAIL]`.
  - `ALLOW_WITH_AUDIT`: Permits transaction while appending security telemetry to audit logs.

# IDP Control Plane REST API Contract

Base URL: `/` (Cloud Run / Local: `http://localhost:8000`)

---

## 1. Authentication Endpoints

### `POST /auth/login`
- **Request Body**:
  ```json
  {
    "username": "admin_gov",
    "password": "<password>"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": "<seconds>"
  }
  ```

### `GET /auth/me`
- **Headers**: `Authorization: Bearer <jwt_token>`
- **Response (200 OK)**:
  ```json
  {
    "user_id": "usr-admin-001",
    "username": "admin_gov",
    "email": "admin@example.com",
    "role": "platform_admin",
    "workspaces": ["default", "admin", "ws-dev", "ws-prod"],
    "is_active": true
  }
  ```

---

## 2. Template Catalog

### `GET /templates`
- **Headers**: `Authorization: Bearer <jwt_token>`
- **Response (200 OK)**: List of `TemplateResponse` objects containing `template_id`, `template_version`, `display_name`, `description`, `supported_environments`, `allowed_models`, `cost_tier`.

---

## 3. Request Lifecycle

### `POST /requests`
- **Headers**:
  - `Authorization: Bearer <jwt_token>`
  - `Idempotency-Key: <unique_key>` (Required, 24h TTL)
- **Request Body**:
  ```json
  {
    "workspace": "ws-dev",
    "template_id": "t1-agent-engine",
    "template_version": "2.0.0",
    "environment": "dev",
    "inputs": {
      "agent_name": "support-agent",
      "model_name": "gemini-2.5-flash",
      "region": "us-central1"
    }
  }
  ```
- **Response (202 Accepted)**:
  ```json
  {
    "request_id": "req-a1b2c3d4",
    "deployment_id": "dep-e5f6g7h8",
    "operation": "create",
    "status": "DISPATCHED",
    "workspace": "ws-dev",
    "environment": "dev",
    "template_id": "t1-agent-engine",
    "template_version": "2.0.0",
    "created_at": "2026-09-05T21:00:00Z",
    "updated_at": "2026-09-05T21:00:00Z"
  }
  ```

### `GET /requests/{request_id}`
- **Headers**: `Authorization: Bearer <jwt_token>`
- **Response (200 OK)**: Execution status, safe summary, completion timestamps.

---

## 4. Deployment Management

### `GET /deployments`
- **Query Params**: `workspace` (optional)
- **Response (200 OK)**: List of deployments with status, expires_at, labels.

### `POST /deployments/{deployment_id}/destroy`
- **Headers**:
  - `Authorization: Bearer <jwt_token>`
  - `Idempotency-Key: <unique_key>`
- **Response (202 Accepted)**: Dispatches destroy pipeline and returns destroy request record.

---

## 5. Governance & Model Armor

### `POST /governance/inspect`
- **Request Body**:
  ```json
  {
    "text": "Check customer SSN: 111-22-3333",
    "point": "prompt",
    "mode": "redact"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "passed": true,
    "action_taken": "redacted",
    "point": "prompt",
    "processed_text": "Check customer SSN: [REDACTED_SSN]",
    "violations": ["ssn_detected"]
  }
  ```

### `POST /governance/ttl-override`
- **Platform Admin Only**
- **Request Body**: `{"deployment_id": "dep-xxx", "extension_days": 14, "reason": "Approved load test"}`

### `POST /governance/cleanup-expired`
- **Platform Admin Only**
- Automatically acquires locks and dispatches destroy requests for expired workloads.

---

## 6. Pipeline Callbacks & Reconciliation

### `POST /callbacks/pipeline`
- **Headers**: `Authorization: Bearer <google_oidc_token>`
- **Monotonic Sequence Enforcement**: Increments sequence from 1 (PLANNING) to 2 (APPLYING) to 3 (SUCCEEDED).

### `POST /admin/reconcile-callbacks`
- **Platform Admin Only**
- Replays dead-letter callbacks and synchronizes deployment status.

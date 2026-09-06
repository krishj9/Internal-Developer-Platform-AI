# Runbook: Incident Triage and Break-Glass Procedures

## 1. Dead-Letter Callback Recovery

When GitHub Actions runners cannot reach the Control Plane API due to transient network issues, callbacks are saved to the dead-letter prefix in Cloud Storage: `gs://<state-bucket>/callbacks/dead-letter/<request_id>/<sequence>.json`.

### Reconciling Dead Letters via API
```bash
# Obtain Admin JWT token
ADMIN_TOKEN=$(curl -s -X POST https://idp-api.internal/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_gov", "password": "..."}' | jq -r .access_token)

# Submit Dead-Letter Payload for Reconciliation
curl -X POST https://idp-api.internal/admin/reconcile-callbacks \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "dead_letter_events": [
      {
        "request_id": "req-123",
        "deployment_id": "dep-456",
        "template_id": "t1-agent-engine",
        "template_version": "2.0.0",
        "template_commit_sha": "010078c...",
        "repository": "idp-platform-org/idp-platform",
        "workflow": "deploy-t1.yml",
        "github_run_id": "11223344",
        "event_sequence": 3,
        "operation": "create",
        "status": "SUCCEEDED",
        "summary": "Recovered apply event",
        "outputs": {"endpoint": "https://..."}
      }
    ]
  }'
```

---

## 2. Lock Contention & Stuck Request Recovery

If a pipeline crashes before releasing the deployment lock:
1. Identify the holding request in Firestore `deployments/{deployment_id}` -> `active_request_id`.
2. Inspect GitHub Run logs corresponding to the request.
3. If confirmed dead, submit an administrative lock release:
   - Call `request_repo.update_status(req_id, RequestStatus.FAILED, safe_summary="Timed out by admin break-glass")`.
   - Call `deployment_repo.release_lock(deployment_id, req_id)`.

# T3 Cloud Run Agent Template

Governed containerized ADK-based agent service deployed to Google Cloud Run v2 with dedicated runtime identity and IAM invocation control.

## Capabilities

- Containerized Python 3.11 agent service running FastAPI.
- Dedicated runtime service account (`sa-t3-...`) scoped with `roles/aiplatform.user` and `roles/logging.logWriter`.
- Bounded autoscaling (0 to 10 instances), CPU (1-2), and memory (512Mi-2Gi).
- IAM-protected invocation; no public unauthenticated endpoint by default.
- Automated readiness validation via HTTP `/healthz` and deterministic `/query` ping.

## Lifecycle Operations

- **Create**: Provisions dedicated service account, IAM bindings, and Cloud Run v2 service.
- **Readiness**: Smoke test validates container readiness and query responses.
- **Destroy**: Completely removes Cloud Run service revisions, runtime service account, and IAM bindings.

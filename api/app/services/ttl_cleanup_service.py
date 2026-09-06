"""
Automated TTL and Orphan Deployment Cleanup Service for IDP Control Plane.
"""

import uuid
from datetime import UTC, datetime, timedelta

from api.app.domain.models import (
    AuditEventRecord,
    DeploymentRecord,
    DeploymentStatus,
    RequestOperation,
    RequestRecord,
    RequestStatus,
)
from api.app.repositories.platform_repositories import (
    AuditEventRepository,
    DeploymentRepository,
    RequestRepository,
    audit_repo,
    deployment_repo,
    request_repo,
)
from api.app.services.idempotency_service import compute_payload_digest


class TtlCleanupService:
    def __init__(
        self,
        deployments: DeploymentRepository = deployment_repo,
        requests: RequestRepository = request_repo,
        audits: AuditEventRepository = audit_repo,
    ):
        self.deployments = deployments
        self.requests = requests
        self.audits = audits

    async def find_expired_deployments(self, now: datetime | None = None) -> list[DeploymentRecord]:
        current_time = now or datetime.now(UTC)
        all_deps = await self.deployments.list_all()
        expired: list[DeploymentRecord] = []

        for dep in all_deps:
            if (
                dep.status == DeploymentStatus.ACTIVE
                and dep.expires_at is not None
                and dep.expires_at <= current_time
            ):
                expired.append(dep)

        return expired

    async def grant_ttl_extension(
        self,
        deployment_id: str,
        extension_days: int,
        admin_user_id: str,
        reason: str,
    ) -> DeploymentRecord:
        dep = await self.deployments.get(deployment_id)
        if not dep:
            raise ValueError(f"Deployment '{deployment_id}' not found.")

        base_time = dep.expires_at or datetime.now(UTC)
        new_expiry = base_time + timedelta(days=extension_days)
        dep.expires_at = new_expiry
        dep.updated_at = datetime.now(UTC)
        await self.deployments.save(dep)

        # Record auditable exception
        await self.audits.append(
            AuditEventRecord(
                audit_event_id=f"aud-ttl-{uuid.uuid4().hex[:8]}",
                actor_type="user",
                actor_id=admin_user_id,
                action="TTL_EXTENSION_GRANTED",
                resource_type="deployment",
                resource_id=deployment_id,
                deployment_id=deployment_id,
                outcome="SUCCESS",
                safe_metadata={
                    "workspace": dep.workspace,
                    "previous_expires_at": base_time.isoformat(),
                    "new_expires_at": new_expiry.isoformat(),
                    "extension_days": extension_days,
                    "reason": reason,
                },
            )
        )
        return dep

    async def process_expired_deployments(
        self,
        now: datetime | None = None,
    ) -> list[dict[str, str]]:
        expired = await self.find_expired_deployments(now)
        results: list[dict[str, str]] = []

        for dep in expired:
            req_id = f"req-cleanup-{uuid.uuid4().hex[:8]}"
            lock_acquired = await self.deployments.acquire_lock(dep.deployment_id, req_id)
            if not lock_acquired:
                results.append(
                    {
                        "deployment_id": dep.deployment_id,
                        "status": "SKIPPED_LOCKED",
                    }
                )
                continue

            destroy_req = RequestRecord(
                request_id=req_id,
                deployment_id=dep.deployment_id,
                actor_user_id="system-ttl-cleanup",
                actor_role="platform_admin",
                workspace=dep.workspace,
                environment=dep.environment,
                template_id=dep.template_id,
                template_version=dep.template_version,
                template_commit_sha=dep.template_commit_sha,
                operation=RequestOperation.DESTROY,
                status=RequestStatus.DISPATCHED,
                safe_input_digest=compute_payload_digest({"reason": "automated_ttl_expiration"}),
                inputs={"reason": "automated_ttl_expiration"},
            )
            await self.requests.save(destroy_req)

            await self.audits.append(
                AuditEventRecord(
                    audit_event_id=f"aud-cleanup-{uuid.uuid4().hex[:8]}",
                    actor_type="system",
                    actor_id="system-ttl-cleanup",
                    action="AUTOMATED_TTL_CLEANUP_QUEUED",
                    resource_type="deployment",
                    resource_id=dep.deployment_id,
                    request_id=req_id,
                    deployment_id=dep.deployment_id,
                    outcome="SUCCESS",
                    safe_metadata={
                        "workspace": dep.workspace,
                        "request_id": req_id,
                        "expired_at": dep.expires_at.isoformat() if dep.expires_at else "",
                    },
                )
            )

            results.append(
                {
                    "deployment_id": dep.deployment_id,
                    "request_id": req_id,
                    "status": "CLEANUP_DISPATCHED",
                }
            )

        return results


ttl_cleanup_service = TtlCleanupService()

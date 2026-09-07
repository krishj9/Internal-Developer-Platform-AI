"""
Administrative API endpoints: Dead-letter callback reconciliation.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.app.api.callback_schemas import PipelineCallbackInput, ReconcileResponse
from api.app.auth.callback_auth import PipelineIdentity
from api.app.auth.dependencies import get_current_user
from api.app.auth.hasher import hash_password
from api.app.domain.models import AuditEventRecord, TemplateRecord
from api.app.repositories.platform_repositories import (
    AuditEventRepository,
    CallbackEventRepository,
    DeploymentRepository,
    IdempotencyRepository,
    RequestRepository,
    TemplateRepository,
    get_audit_repo,
    get_callback_repo,
    get_deployment_repo,
    get_idempotency_repo,
    get_request_repo,
    get_template_repo,
)
from api.app.repositories.user_repository import UserRecord, UserRepository, get_user_repo
from api.app.services.notification_service import (
    NotificationService,
    notification_service,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


class DatabaseCleanupInput(BaseModel):
    include_users: bool = Field(default=False, description="Purge user accounts")
    include_templates: bool = Field(default=False, description="Purge template catalog")
    reseed: bool = Field(default=True, description="Reseed baseline users and templates")


class DatabaseCleanupResponse(BaseModel):
    status: str
    purged_collections: list[str]
    reseeded_users: int
    reseeded_templates: int
    message: str


class ReconcileRequestInput(BaseModel):
    dead_letter_events: list[PipelineCallbackInput] = Field(
        default_factory=list, description="List of unrecovered dead-letter events to replay"
    )


@router.post(
    "/reconcile-callbacks",
    response_model=ReconcileResponse,
    summary="Reconcile Dead-Letter Callbacks",
    description="Replay unrecovered dead-letter pipeline callback events (Platform Admin only).",
)
async def reconcile_callbacks(
    input_data: ReconcileRequestInput,
    current_user: UserRecord = Depends(get_current_user),
    requests: RequestRepository = Depends(get_request_repo),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
    callbacks: CallbackEventRepository = Depends(get_callback_repo),
    audits: AuditEventRepository = Depends(get_audit_repo),
    notifications: NotificationService = Depends(lambda: notification_service),
) -> ReconcileResponse:
    # 1. Admin Role Authorization
    if current_user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privilege required for reconciliation.",
        )

    reconciled_requests: list[str] = []
    details: list[dict[str, Any]] = []
    reconciled_count = 0
    failed_count = 0

    # 2. Replay each dead letter event safely through callback receiver logic
    from api.app.api.callback_router import receive_pipeline_callback

    for event_input in input_data.dead_letter_events:
        try:
            res = await receive_pipeline_callback(
                payload=event_input,
                pipeline_identity=PipelineIdentity(
                    email="admin-reconciled@idp.internal",
                    sub=f"reconciled-by-{current_user.user_id}",
                ),
                requests=requests,
                deployments=deployments,
                callbacks=callbacks,
                audits=audits,
                notifications=notifications,
            )
            reconciled_count += 1
            reconciled_requests.append(event_input.request_id)
            details.append(
                {
                    "request_id": event_input.request_id,
                    "status": "RECONCILED",
                    "result": res.model_dump(),
                }
            )
        except Exception as e:
            failed_count += 1
            details.append(
                {
                    "request_id": event_input.request_id,
                    "status": "FAILED",
                    "error": str(e),
                }
            )

    # 3. Record Audit Log for Reconciliation
    await audits.append(
        AuditEventRecord(
            audit_event_id=f"aud-rec-{uuid.uuid4().hex[:8]}",
            actor_type="admin",
            actor_id=current_user.user_id,
            action="reconcile_dead_letter_callbacks",
            resource_type="system",
            resource_id="reconciliation-batch",
            outcome="SUCCESS" if failed_count == 0 else "PARTIAL",
            safe_metadata={
                "reconciled_count": reconciled_count,
                "failed_count": failed_count,
            },
        )
    )

    return ReconcileResponse(
        reconciled_count=reconciled_count,
        failed_count=failed_count,
        reconciled_requests=reconciled_requests,
        details=details,
    )


@router.post(
    "/cleanup-database",
    response_model=DatabaseCleanupResponse,
    summary="Clean Up Database for a Fresh Start",
    description=(
        "Purge operational records and optionally reseed baseline accounts "
        "and templates (Platform Admin only)."
    ),
)
async def cleanup_database(
    input_data: DatabaseCleanupInput,
    current_user: UserRecord = Depends(get_current_user),
    requests: RequestRepository = Depends(get_request_repo),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
    callbacks: CallbackEventRepository = Depends(get_callback_repo),
    audits: AuditEventRepository = Depends(get_audit_repo),
    idempotency: IdempotencyRepository = Depends(get_idempotency_repo),
    templates: TemplateRepository = Depends(get_template_repo),
    users: UserRepository = Depends(get_user_repo),
) -> DatabaseCleanupResponse:
    if current_user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privilege required to clean up database.",
        )

    purged_collections = [
        "deployments",
        "requests",
        "callback_events",
        "audit_events",
        "idempotency_records",
    ]

    # 1. Purge Operational Repositories
    # In-memory support
    if hasattr(deployments, "_deployments"):
        deployments._deployments.clear()
    if hasattr(requests, "_requests"):
        requests._requests.clear()
    if hasattr(callbacks, "_events"):
        callbacks._events.clear()
    if hasattr(audits, "_events"):
        audits._events.clear()
    if hasattr(idempotency, "_records"):
        idempotency._records.clear()

    # Firestore support
    if hasattr(deployments, "_db"):
        db = deployments._db
        for coll_name in purged_collections:
            coll_ref = db.collection(coll_name)
            docs = [d async for d in coll_ref.limit(500).stream()]
            if docs:
                batch = db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                await batch.commit()

    # 2. Optionally Purge Users
    if input_data.include_users:
        purged_collections.append("users")
        if hasattr(users, "_users_by_id"):
            users._users_by_id.clear()
            users._users_by_username.clear()
        if hasattr(users, "_collection"):
            u_coll = users._collection
            docs = [d async for d in u_coll.limit(500).stream()]
            if docs:
                batch = users._db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                await batch.commit()

    # 3. Optionally Purge Templates
    if input_data.include_templates:
        purged_collections.append("templates")
        if hasattr(templates, "_templates"):
            templates._templates.clear()
        if hasattr(templates, "_collection"):
            t_coll = templates._collection
            docs = [d async for d in t_coll.limit(500).stream()]
            if docs:
                batch = templates._db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                await batch.commit()

    # 4. Reseed Baseline Users
    reseeded_users_count = 0
    if input_data.reseed:
        base_users = [
            UserRecord(
                user_id="usr-admin-gov",
                username="admin_gov",
                email="admin_gov@mybrightday-dev.internal",
                password_hash=hash_password("RY%%H4uIjQFAfQ15!=2l2z"),
                role="platform_admin",
                workspaces=["default", "admin", "ws-dev"],
                token_version=2,
                is_active=True,
            ),
            UserRecord(
                user_id="usr-dev-gov",
                username="dev_gov",
                email="dev_gov@mybrightday-dev.internal",
                password_hash=hash_password("oZ!f83h1vxp0v$rJAM#!H8"),
                role="developer",
                workspaces=["default", "ws-dev"],
                token_version=2,
                is_active=True,
            ),
            UserRecord(
                user_id="usr-admin-default",
                username="admin",
                email="admin@mybrightday-dev.internal",
                password_hash=hash_password("KotC-vurzwtBKgP7#x%5r+"),
                role="platform_admin",
                workspaces=["default", "admin"],
                token_version=2,
                is_active=True,
            ),
        ]
        for u in base_users:
            await users.save(u)
            reseeded_users_count += 1

    # 5. Reseed Baseline Templates
    reseeded_templates_count = 0
    if input_data.reseed:
        base_templates = [
            TemplateRecord(
                template_id="t1-agent-engine",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Agent on Vertex AI Agent Engine",
                description="Governed ADK-based agent deployed to Google Cloud Agent Engine.",
                supported_environments=["dev"],
                allowed_models=["gemini-2.5-flash", "gemini-2.5-pro"],
                allowed_regions=["us-central1"],
                cost_tier="low",
                manifest={"readiness": {"type": "smoke_test"}},
                status="published",
            ),
            TemplateRecord(
                template_id="t2-managed-rag",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Vertex AI Managed RAG Engine",
                description="Governed Vertex AI RAG Engine stack with RagManagedDb.",
                supported_environments=["dev"],
                allowed_models=["text-embedding-004", "text-embedding-005"],
                allowed_regions=["us-central1"],
                cost_tier="medium",
                manifest={"readiness": {"type": "rag_retrieval_smoke_test"}},
                status="published",
            ),
            TemplateRecord(
                template_id="t3-cloud-run-agent",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Agent on Cloud Run Service",
                description="Governed ADK-based agent deployed to Google Cloud Run v2.",
                supported_environments=["dev"],
                allowed_models=["gemini-2.5-flash", "gemini-2.5-pro"],
                allowed_regions=["us-central1"],
                cost_tier="medium",
                manifest={"readiness": {"type": "http_smoke_test"}},
                status="published",
            ),
            TemplateRecord(
                template_id="t4-governance",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Governance & Operational Controls",
                description=(
                    "Governed Model Armor guardrails, Cloud Monitoring alerts, "
                    "and automated TTL policies."
                ),
                supported_environments=["dev", "prod"],
                allowed_models=[],
                allowed_regions=["us-central1"],
                cost_tier="low",
                manifest={"readiness": {"type": "policy_verification_test"}},
                status="published",
            ),
        ]
        for t in base_templates:
            await templates.save(t)
            reseeded_templates_count += 1

    # 6. Audit Trail
    await audits.append(
        AuditEventRecord(
            audit_event_id=f"aud-clean-{uuid.uuid4().hex[:8]}",
            actor_type="admin",
            actor_id=current_user.user_id,
            action="cleanup_database",
            resource_type="system",
            resource_id="database-purge",
            outcome="SUCCESS",
            safe_metadata={
                "purged_collections": purged_collections,
                "reseeded_users": reseeded_users_count,
                "reseeded_templates": reseeded_templates_count,
            },
        )
    )

    return DatabaseCleanupResponse(
        status="success",
        purged_collections=purged_collections,
        reseeded_users=reseeded_users_count,
        reseeded_templates=reseeded_templates_count,
        message="Database cleaned up successfully for a fresh start.",
    )

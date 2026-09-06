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
from api.app.domain.models import AuditEventRecord
from api.app.repositories.platform_repositories import (
    AuditEventRepository,
    CallbackEventRepository,
    DeploymentRepository,
    RequestRepository,
    audit_repo,
    callback_repo,
    deployment_repo,
    request_repo,
)
from api.app.repositories.user_repository import UserRecord

router = APIRouter(prefix="/admin", tags=["Admin"])


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
    requests: RequestRepository = Depends(lambda: request_repo),
    deployments: DeploymentRepository = Depends(lambda: deployment_repo),
    callbacks: CallbackEventRepository = Depends(lambda: callback_repo),
    audits: AuditEventRepository = Depends(lambda: audit_repo),
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

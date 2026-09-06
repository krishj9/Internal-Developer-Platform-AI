"""
Pipeline callback receiver endpoint for trusted GitHub Actions execution events.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from api.app.api.callback_schemas import CallbackResponse, PipelineCallbackInput
from api.app.auth.callback_auth import PipelineIdentity, get_pipeline_identity
from api.app.domain.models import (
    AuditEventRecord,
    CallbackEventRecord,
    DeploymentStatus,
    RequestOperation,
    RequestStatus,
)
from api.app.domain.state_machine import InvalidStateTransitionError, validate_request_transition
from api.app.repositories.platform_repositories import (
    AuditEventRepository,
    CallbackEventRepository,
    DeploymentRepository,
    RequestRepository,
    get_audit_repo,
    get_callback_repo,
    get_deployment_repo,
    get_request_repo,
)
from api.app.services.idempotency_service import compute_payload_digest
from api.app.services.notification_service import (
    NotificationEvent,
    NotificationService,
    notification_service,
)

router = APIRouter(prefix="/callbacks", tags=["Callbacks"])


@router.post(
    "/pipeline",
    response_model=CallbackResponse,
    summary="Receive Pipeline Callback",
    description="Receive trusted execution status updates from WIF-authenticated pipelines.",
)
async def receive_pipeline_callback(
    payload: PipelineCallbackInput,
    pipeline_identity: PipelineIdentity = Depends(get_pipeline_identity),
    requests: RequestRepository = Depends(get_request_repo),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
    callbacks: CallbackEventRepository = Depends(get_callback_repo),
    audits: AuditEventRepository = Depends(get_audit_repo),
    notifications: NotificationService = Depends(lambda: notification_service),
) -> CallbackResponse:
    # 1. Fetch associated request record
    req = await requests.get(payload.request_id)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request '{payload.request_id}' not found.",
        )

    # 2. Strict context binding validation
    if req.deployment_id != payload.deployment_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Deployment ID does not match the original request context.",
        )
    if req.template_id != payload.template_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Template ID does not match the original request context.",
        )
    if req.template_commit_sha != payload.template_commit_sha:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Template commit SHA does not match the immutable request context.",
        )
    if req.operation.value != payload.operation:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Lifecycle operation does not match the original request.",
        )

    # 3. Monotonic sequence check
    if payload.event_sequence <= req.event_sequence:
        # Check if exact duplicate event (idempotent replay)
        if payload.status == req.status:
            return CallbackResponse(
                status="accepted",
                callback_event_id=f"cb-dup-{uuid.uuid4().hex[:8]}",
                request_status=req.status,
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Stale callback event sequence {payload.event_sequence}; "
                f"current sequence is {req.event_sequence}."
            ),
        )

    # 4. State transition validation
    try:
        validate_request_transition(req.status, payload.status)
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid pipeline state transition: {e!s}",
        ) from e

    # 5. Update request status & metadata
    req.github_run_id = payload.github_run_id
    req.event_sequence = payload.event_sequence
    req.github_repository = payload.repository
    req.github_workflow = payload.workflow
    await requests.update_status(
        request_id=req.request_id,
        new_status=payload.status,
        failure_class=payload.failure_class,
        safe_summary=payload.summary,
    )

    # 6. Apply deployment state updates on lifecycle progression
    dep = await deployments.get(req.deployment_id)
    if dep:
        if payload.status == RequestStatus.APPLYING:
            if req.operation == RequestOperation.CREATE:
                dep.status = DeploymentStatus.PROVISIONING
            elif req.operation == RequestOperation.DESTROY:
                dep.status = DeploymentStatus.DESTROYING
            await deployments.save(dep)

        elif payload.status == RequestStatus.SUCCEEDED:
            if req.operation == RequestOperation.CREATE:
                dep.status = DeploymentStatus.ACTIVE
                dep.safe_outputs = payload.outputs
                await deployments.save(dep)
                await deployments.release_lock(dep.deployment_id, req.request_id)
            elif req.operation == RequestOperation.DESTROY:
                dep.status = DeploymentStatus.DESTROYED
                dep.destroyed_at = datetime.now(UTC)
                await deployments.save(dep)
                await deployments.release_lock(dep.deployment_id, req.request_id)

        elif payload.status == RequestStatus.FAILED:
            dep.status = DeploymentStatus.FAILED
            await deployments.save(dep)
            await deployments.release_lock(dep.deployment_id, req.request_id)

    # 7. Record in append-only callback ledger
    event_id = f"cb-{uuid.uuid4().hex[:8]}"
    callback_record = CallbackEventRecord(
        callback_event_id=event_id,
        request_id=payload.request_id,
        deployment_id=payload.deployment_id,
        github_run_id=payload.github_run_id,
        event_sequence=payload.event_sequence,
        operation=payload.operation,
        status=payload.status,
        pipeline_identity=pipeline_identity.email,
        payload_digest=compute_payload_digest(payload.model_dump()),
        safe_payload=payload.model_dump(),
        validation_result="ACCEPTED",
    )
    await callbacks.append(callback_record)

    # 8. Record audit log
    await audits.append(
        AuditEventRecord(
            audit_event_id=f"aud-{uuid.uuid4().hex[:8]}",
            actor_type="pipeline",
            actor_id=pipeline_identity.email,
            action=f"pipeline_callback_{payload.status.lower()}",
            resource_type="request",
            resource_id=req.request_id,
            request_id=req.request_id,
            deployment_id=req.deployment_id,
            outcome="SUCCESS",
            safe_metadata={
                "sequence": payload.event_sequence,
                "status": payload.status,
                "run_id": payload.github_run_id,
            },
        )
    )

    # 8b. Publish notification event
    await notifications.publish(
        NotificationEvent(
            event_type=f"PIPELINE_{payload.status}",
            request_id=req.request_id,
            deployment_id=req.deployment_id,
            template_id=req.template_id,
            workspace=req.workspace,
            environment=req.environment,
            status=payload.status,
            actor_id=pipeline_identity.email,
            summary=payload.summary,
            safe_payload={"sequence": payload.event_sequence, "outputs": payload.outputs},
        )
    )

    return CallbackResponse(
        status="accepted",
        callback_event_id=event_id,
        request_status=payload.status,
    )

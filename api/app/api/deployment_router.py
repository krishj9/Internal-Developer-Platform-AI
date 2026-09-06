"""
Deployment catalog and destroy lifecycle API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status

from api.app.api.schemas import DeploymentConfigResponse, DeploymentResponse, RequestResponse
from api.app.auth.dependencies import get_current_user
from api.app.domain.models import (
    AuditEventRecord,
    DeploymentStatus,
    RequestOperation,
    RequestRecord,
    RequestStatus,
)
from api.app.domain.state_machine import DeploymentLockedError
from api.app.repositories.platform_repositories import (
    AuditEventRepository,
    DeploymentRepository,
    RequestRepository,
    get_audit_repo,
    get_deployment_repo,
    get_request_repo,
)
from api.app.repositories.user_repository import UserRecord
from api.app.services.github_dispatch_service import GitHubDispatchService, github_dispatcher
from api.app.services.idempotency_service import (
    IdempotencyMismatchError,
    IdempotencyService,
    compute_payload_digest,
    idempotency_service,
)

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.get(
    "",
    response_model=list[DeploymentResponse],
    summary="List Deployments",
    description="Retrieve all provisioned deployments in the caller's authorized workspaces.",
)
async def list_deployments(
    current_user: UserRecord = Depends(get_current_user),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
) -> list[DeploymentResponse]:
    all_deployments: list[DeploymentResponse] = []
    for ws in current_user.workspaces:
        records = await deployments.list_by_workspace(ws)
        for d in records:
            all_deployments.append(
                DeploymentResponse(
                    deployment_id=d.deployment_id,
                    workspace=d.workspace,
                    environment=d.environment,
                    template_id=d.template_id,
                    template_version=d.template_version,
                    status=d.status,
                    owner_user_id=d.owner_user_id,
                    safe_outputs=d.safe_outputs,
                    active_request_id=d.active_request_id,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
            )
    return all_deployments


@router.get(
    "/{deployment_id}",
    response_model=DeploymentResponse,
    summary="Get Deployment Details",
    description="Retrieve metadata, state, and safe outputs for a deployment.",
)
async def get_deployment(
    deployment_id: str,
    current_user: UserRecord = Depends(get_current_user),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
) -> DeploymentResponse:
    dep = await deployments.get(deployment_id)
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment '{deployment_id}' not found.",
        )

    if current_user.role != "platform_admin" and dep.workspace not in current_user.workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this deployment.",
        )

    return DeploymentResponse(
        deployment_id=dep.deployment_id,
        workspace=dep.workspace,
        environment=dep.environment,
        template_id=dep.template_id,
        template_version=dep.template_version,
        status=dep.status,
        owner_user_id=dep.owner_user_id,
        safe_outputs=dep.safe_outputs,
        active_request_id=dep.active_request_id,
        created_at=dep.created_at,
        updated_at=dep.updated_at,
    )


@router.get(
    "/{deployment_id}/config",
    response_model=DeploymentConfigResponse,
    summary="Get Safe Deployment Config",
    description="Retrieve non-sensitive configuration profile for the deployment.",
)
async def get_deployment_config(
    deployment_id: str,
    current_user: UserRecord = Depends(get_current_user),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
) -> DeploymentConfigResponse:
    dep = await deployments.get(deployment_id)
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment '{deployment_id}' not found.",
        )

    if current_user.role != "platform_admin" and dep.workspace not in current_user.workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this deployment config.",
        )

    safe_config = {
        "deployment_id": dep.deployment_id,
        "workspace": dep.workspace,
        "environment": dep.environment,
        "template_id": dep.template_id,
        "template_version": dep.template_version,
        "status": dep.status,
        "outputs": dep.safe_outputs,
    }

    return DeploymentConfigResponse(
        deployment_id=dep.deployment_id,
        workspace=dep.workspace,
        environment=dep.environment,
        template_id=dep.template_id,
        template_version=dep.template_version,
        safe_config=safe_config,
    )


@router.post(
    "/{deployment_id}/destroy",
    response_model=RequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Destroy Request",
    description="Submit an asynchronous request to destroy a provisioned deployment.",
)
async def destroy_deployment(
    deployment_id: str,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: UserRecord = Depends(get_current_user),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
    requests: RequestRepository = Depends(get_request_repo),
    audits: AuditEventRepository = Depends(get_audit_repo),
    dispatcher: GitHubDispatchService = Depends(lambda: github_dispatcher),
    idempotency: IdempotencyService = Depends(lambda: idempotency_service),
) -> RequestResponse:
    # 1. Fetch deployment
    dep = await deployments.get(deployment_id)
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment '{deployment_id}' not found.",
        )

    # 2. Authorization
    if current_user.role != "platform_admin" and dep.workspace not in current_user.workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to destroy this deployment.",
        )

    # 3. Idempotency replay check
    destroy_payload = {"operation": "destroy", "deployment_id": deployment_id}
    try:
        cached = await idempotency.check_idempotency(
            user_id=current_user.user_id,
            idempotency_key=idempotency_key,
            payload=destroy_payload,
        )
        if cached:
            _, response_body = cached
            return RequestResponse(**response_body)
    except IdempotencyMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    # 4. Check terminal state
    if dep.status == DeploymentStatus.DESTROYED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Deployment is already DESTROYED.",
        )

    # 5. Acquire deployment lock
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    try:
        await deployments.acquire_lock(deployment_id, request_id)
    except DeploymentLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    # 6. Update deployment status to DESTROYING
    dep.status = DeploymentStatus.DESTROYING
    await deployments.save(dep)

    # 7. Create destroy RequestRecord
    req = RequestRecord(
        request_id=request_id,
        deployment_id=deployment_id,
        operation=RequestOperation.DESTROY,
        status=RequestStatus.PENDING,
        workspace=dep.workspace,
        environment=dep.environment,
        template_id=dep.template_id,
        template_version=dep.template_version,
        template_commit_sha=dep.template_commit_sha,
        actor_user_id=current_user.user_id,
        actor_role=current_user.role,
        safe_input_digest=compute_payload_digest(destroy_payload),
    )
    await requests.save(req)

    # 8. Dispatch destroy workflow
    workflow_file = f"deploy-{dep.template_id.split('-')[0]}.yml"
    dispatch_inputs = {
        "request_id": request_id,
        "deployment_id": deployment_id,
        "template_id": dep.template_id,
        "template_version": dep.template_version,
        "template_commit_sha": dep.template_commit_sha,
        "operation": "destroy",
        "workspace": dep.workspace,
        "environment": dep.environment,
        "inputs_json": {},
        "callback_url": "https://idp-api.internal/callbacks/pipeline",
        "workload_identity_provider": (
            "projects/123/locations/global/workloadIdentityPools/idp-pool"
        ),
        "service_account": "idp-pipeline-t1-dev@project.iam.gserviceaccount.com",
        "state_bucket": "idp-tfstate-bucket",
    }
    await dispatcher.dispatch_workflow(
        workflow_id=workflow_file,
        ref=dep.template_commit_sha,
        inputs=dispatch_inputs,
    )

    # 9. Update request status to DISPATCHED
    dispatched_req = await requests.update_status(request_id, RequestStatus.DISPATCHED)

    # 10. Audit event
    await audits.append(
        AuditEventRecord(
            audit_event_id=f"aud-{uuid.uuid4().hex[:8]}",
            actor_type="user",
            actor_id=current_user.user_id,
            action="submit_destroy_request",
            resource_type="deployment",
            resource_id=deployment_id,
            request_id=request_id,
            deployment_id=deployment_id,
            outcome="SUCCESS",
            safe_metadata={"workspace": dep.workspace},
        )
    )

    response_payload = RequestResponse(
        request_id=dispatched_req.request_id,
        deployment_id=dispatched_req.deployment_id,
        operation=dispatched_req.operation,
        status=dispatched_req.status,
        workspace=dispatched_req.workspace,
        environment=dispatched_req.environment,
        template_id=dispatched_req.template_id,
        template_version=dispatched_req.template_version,
        created_at=dispatched_req.created_at,
        updated_at=dispatched_req.updated_at,
    )

    # 11. Record idempotency response
    await idempotency.record_response(
        user_id=current_user.user_id,
        idempotency_key=idempotency_key,
        payload=destroy_payload,
        status_code=status.HTTP_202_ACCEPTED,
        response_body=response_payload.model_dump(mode="json"),
    )

    return response_payload

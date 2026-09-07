"""
Deployment catalog and destroy lifecycle API endpoints.
"""

import json
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status

from api.app.api.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    DeploymentConfigResponse,
    DeploymentResponse,
    RequestResponse,
)
from api.app.auth.dependencies import get_current_user
from api.app.core.settings import settings
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
from api.app.services.agent_service import AgentPolicyViolationError, agent_proxy_service
from api.app.services.github_dispatch_service import (
    GitHubDispatchError,
    GitHubDispatchService,
    github_dispatcher,
)
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
        "project_id": settings.PROJECT_ID,
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
    "/{deployment_id}/query",
    response_model=AgentQueryResponse,
    summary="Query Deployed Agent",
    description="Send a governed prompt to an active deployment with Model Armor screening.",
)
async def query_deployment_agent(
    deployment_id: str,
    payload: AgentQueryRequest,
    current_user: UserRecord = Depends(get_current_user),
    deployments: DeploymentRepository = Depends(get_deployment_repo),
    audits: AuditEventRepository = Depends(get_audit_repo),
) -> AgentQueryResponse:
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

    if dep.status != DeploymentStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deployment is not in ACTIVE state (current status: {dep.status}).",
        )

    try:
        response_text, model_name, tools_executed, guardrail_status = (
            agent_proxy_service.execute_query(
                deployment_id=deployment_id,
                template_id=dep.template_id,
                safe_outputs=dep.safe_outputs,
                prompt=payload.prompt,
            )
        )
    except AgentPolicyViolationError as e:
        await audits.append(
            AuditEventRecord(
                audit_event_id=f"aud-{uuid.uuid4().hex[:8]}",
                actor_type="user",
                actor_id=current_user.user_id,
                action="agent_query_blocked",
                resource_type="deployment",
                resource_id=deployment_id,
                deployment_id=deployment_id,
                outcome="BLOCKED",
                safe_metadata={"violations": e.violations, "workspace": dep.workspace},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Model Armor violation",
                "message": str(e),
                "violations": e.violations,
            },
        ) from e

    # Audit successful query
    await audits.append(
        AuditEventRecord(
            audit_event_id=f"aud-{uuid.uuid4().hex[:8]}",
            actor_type="user",
            actor_id=current_user.user_id,
            action="agent_query",
            resource_type="deployment",
            resource_id=deployment_id,
            deployment_id=deployment_id,
            outcome="SUCCESS",
            safe_metadata={
                "workspace": dep.workspace,
                "tool_count": len(tools_executed),
                "model": model_name,
            },
        )
    )

    return AgentQueryResponse(
        deployment_id=deployment_id,
        status="success",
        response=response_text,
        model=model_name,
        tools_executed=tools_executed,
        guardrail_status=guardrail_status,
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
    tpl_prefix = dep.template_id.split("-")[0]
    pipeline_sa = (
        f"idp-pipeline-{tpl_prefix}-prod@{settings.PROJECT_ID}.iam.gserviceaccount.com"
        if dep.environment == "prod"
        else f"idp-pipeline-{tpl_prefix}-dev@{settings.PROJECT_ID}.iam.gserviceaccount.com"
    )
    destroy_tf_vars = {
        "project_id": settings.PROJECT_ID,
        "deployment_id": deployment_id,
        "agent_name": "destroy",
        "environment": dep.environment,
        "workspace": dep.workspace,
        "owner": current_user.username,
    }
    # Ensure commit SHA resolves to 'main' if it's a known stale SHA, dummy seed SHA, or empty
    resolved_commit_sha = dep.template_commit_sha
    if not resolved_commit_sha or resolved_commit_sha in {
        "010078cf6745f44da605f6fa0768b4f177c385a5",
        "55e69c7b9da54a49ef8b0f49c061fe7dbdb98998",
    }:
        resolved_commit_sha = "main"

    dispatch_inputs = {
        "request_id": request_id,
        "deployment_id": deployment_id,
        "template_id": dep.template_id,
        "template_version": dep.template_version,
        "template_commit_sha": resolved_commit_sha,
        "operation": "destroy",
        "workspace": dep.workspace,
        "environment": dep.environment,
        "inputs_json": json.dumps(destroy_tf_vars),
        "callback_url": f"{settings.API_BASE_URL}/callbacks/pipeline",
        "workload_identity_provider": settings.WIF_PROVIDER_NAME,
        "service_account": pipeline_sa,
        "state_bucket": settings.STATE_BUCKET_NAME,
    }
    try:
        await dispatcher.dispatch_workflow(
            workflow_id=workflow_file,
            ref=resolved_commit_sha,
            inputs=dispatch_inputs,
        )
    except GitHubDispatchError as e:
        await requests.update_status(
            request_id=request_id,
            new_status=RequestStatus.FAILED,
            failure_class="DISPATCH_FAILED",
            safe_summary=f"Destroy workflow dispatch failed: {e!s}",
        )
        await deployments.release_lock(deployment_id, request_id)
        dep.status = DeploymentStatus.ACTIVE
        await deployments.save(dep)
        await audits.append(
            AuditEventRecord(
                audit_event_id=f"aud-{uuid.uuid4().hex[:8]}",
                actor_type="user",
                actor_id=current_user.user_id,
                action="submit_destroy_request_failed",
                resource_type="deployment",
                resource_id=deployment_id,
                request_id=request_id,
                deployment_id=deployment_id,
                outcome="FAILURE",
                safe_metadata={"error": str(e)},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub destroy dispatch failed: {e!s}",
        ) from e

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

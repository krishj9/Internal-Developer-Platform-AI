"""
Request lifecycle API endpoints: Submit request, check status.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status

from api.app.api.schemas import CreateRequestInput, RequestResponse
from api.app.auth.dependencies import get_current_user
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
    TemplateRepository,
    audit_repo,
    deployment_repo,
    request_repo,
    template_repo,
)
from api.app.repositories.user_repository import UserRecord
from api.app.services.github_dispatch_service import GitHubDispatchService, github_dispatcher
from api.app.services.idempotency_service import (
    IdempotencyMismatchError,
    IdempotencyService,
    compute_payload_digest,
    idempotency_service,
)

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post(
    "",
    response_model=RequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Lifecycle Request",
    description="Submit an asynchronous create request to provision a governed template.",
)
async def create_request(
    input_data: CreateRequestInput,
    idempotency_key: str = Header(
        ..., alias="Idempotency-Key", description="Unique client key with 24h TTL"
    ),
    current_user: UserRecord = Depends(get_current_user),
    templates: TemplateRepository = Depends(lambda: template_repo),
    deployments: DeploymentRepository = Depends(lambda: deployment_repo),
    requests: RequestRepository = Depends(lambda: request_repo),
    audits: AuditEventRepository = Depends(lambda: audit_repo),
    dispatcher: GitHubDispatchService = Depends(lambda: github_dispatcher),
    idempotency: IdempotencyService = Depends(lambda: idempotency_service),
) -> RequestResponse:
    # 1. Authorization check: User must have access to workspace unless platform_admin
    user_workspaces = set(current_user.workspaces)
    if current_user.role != "platform_admin" and input_data.workspace not in user_workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to workspace '{input_data.workspace}'.",
        )

    # 2. Idempotency replay check
    try:
        cached = await idempotency.check_idempotency(
            user_id=current_user.user_id,
            idempotency_key=idempotency_key,
            payload=input_data.model_dump(),
        )
        if cached:
            _, response_body = cached
            return RequestResponse(**response_body)
    except IdempotencyMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    # 3. Resolve template release
    target_version = input_data.template_version or "2.0.0"
    template = await templates.get(input_data.template_id, target_version)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Template '{input_data.template_id}' version '{target_version}' not found.",
        )

    # 4. Validate template input constraints
    if input_data.environment not in template.supported_environments:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Environment '{input_data.environment}' is not supported for this template.",
        )

    model_input = input_data.inputs.get("model_name") or input_data.inputs.get("embedding_model")
    if model_input and model_input not in template.allowed_models:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Model '{model_input}' is not in allowed models: {template.allowed_models}",
        )

    region_input = input_data.inputs.get("region")
    if region_input and region_input not in template.allowed_regions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Region '{region_input}' is not in allowed regions: {template.allowed_regions}",
        )

    # 5. Create deployment and request entities
    deployment_id = f"dep-{uuid.uuid4().hex[:8]}"
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    input_digest = compute_payload_digest(input_data.inputs)

    deployment = DeploymentRecord(
        deployment_id=deployment_id,
        workspace=input_data.workspace,
        environment=input_data.environment,
        template_id=template.template_id,
        template_version=template.template_version,
        template_commit_sha=template.template_commit_sha,
        status=DeploymentStatus.PENDING,
        owner_user_id=current_user.user_id,
        active_request_id=request_id,
        labels={"workspace": input_data.workspace, "owner": current_user.username},
    )

    request_record = RequestRecord(
        request_id=request_id,
        deployment_id=deployment_id,
        operation=RequestOperation.CREATE,
        status=RequestStatus.PENDING,
        workspace=input_data.workspace,
        environment=input_data.environment,
        template_id=template.template_id,
        template_version=template.template_version,
        template_commit_sha=template.template_commit_sha,
        actor_user_id=current_user.user_id,
        actor_role=current_user.role,
        inputs=input_data.inputs,
        safe_input_digest=input_digest,
    )

    await deployments.save(deployment)
    await requests.save(request_record)

    # 6. Dispatch workflow via GitHub
    workflow_file = f"deploy-{template.template_id.split('-')[0]}.yml"
    dispatch_inputs = {
        "request_id": request_id,
        "deployment_id": deployment_id,
        "template_id": template.template_id,
        "template_version": template.template_version,
        "template_commit_sha": template.template_commit_sha,
        "operation": "create",
        "workspace": input_data.workspace,
        "environment": input_data.environment,
        "inputs_json": input_data.inputs,
        "callback_url": "https://idp-api.internal/callbacks/pipeline",
        "workload_identity_provider": (
            "projects/123/locations/global/workloadIdentityPools/idp-pool"
        ),
        "service_account": "idp-pipeline-t1-dev@project.iam.gserviceaccount.com",
        "state_bucket": "idp-tfstate-bucket",
    }
    await dispatcher.dispatch_workflow(
        workflow_id=workflow_file,
        ref=template.template_commit_sha,
        inputs=dispatch_inputs,
    )

    # 7. Update status to DISPATCHED
    dispatched_req = await requests.update_status(request_id, RequestStatus.DISPATCHED)

    # 8. Record audit event
    await audits.append(
        AuditEventRecord(
            audit_event_id=f"aud-{uuid.uuid4().hex[:8]}",
            actor_type="user",
            actor_id=current_user.user_id,
            action="submit_create_request",
            resource_type="request",
            resource_id=request_id,
            request_id=request_id,
            deployment_id=deployment_id,
            outcome="SUCCESS",
            safe_metadata={"workspace": input_data.workspace, "template_id": template.template_id},
        )
    )

    # 9. Format response and record idempotency cache
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

    await idempotency.record_response(
        user_id=current_user.user_id,
        idempotency_key=idempotency_key,
        payload=input_data.model_dump(),
        status_code=status.HTTP_202_ACCEPTED,
        response_body=response_payload.model_dump(mode="json"),
    )

    return response_payload


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    summary="Get Request Details",
    description="Retrieve execution state and lifecycle progression for a request.",
)
async def get_request(
    request_id: str,
    current_user: UserRecord = Depends(get_current_user),
    requests: RequestRepository = Depends(lambda: request_repo),
) -> RequestResponse:
    req = await requests.get(request_id)
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request '{request_id}' not found.",
        )

    if current_user.role != "platform_admin" and req.workspace not in current_user.workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this request.",
        )

    return RequestResponse(
        request_id=req.request_id,
        deployment_id=req.deployment_id,
        operation=req.operation,
        status=req.status,
        workspace=req.workspace,
        environment=req.environment,
        template_id=req.template_id,
        template_version=req.template_version,
        created_at=req.created_at,
        updated_at=req.updated_at,
        completed_at=req.completed_at,
        safe_summary=req.safe_summary,
        failure_class=req.failure_class,
    )

"""
Domain models and enums for the IDP Control Plane.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RequestStatus(StrEnum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    PLANNING = "PLANNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPLYING = "APPLYING"
    VALIDATING = "VALIDATING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DeploymentStatus(StrEnum):
    PENDING = "PENDING"
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    DESTROYING = "DESTROYING"
    DESTROYED = "DESTROYED"
    FAILED = "FAILED"


class RequestOperation(StrEnum):
    CREATE = "create"
    DESTROY = "destroy"


class TemplateRecord(BaseModel):
    template_id: str
    template_version: str
    template_commit_sha: str
    display_name: str
    description: str
    supported_environments: list[str]
    allowed_models: list[str]
    allowed_regions: list[str]
    cost_tier: str = "low"
    manifest: dict[str, Any]
    status: str = "published"
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    published_by: str = "system"


class RequestRecord(BaseModel):
    request_id: str
    deployment_id: str
    operation: RequestOperation
    status: RequestStatus = RequestStatus.PENDING
    workspace: str
    environment: str
    template_id: str
    template_version: str
    template_commit_sha: str
    actor_user_id: str
    actor_role: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    safe_input_digest: str
    github_repository: str | None = None
    github_workflow: str | None = None
    github_run_id: str | None = None
    event_sequence: int = 0
    failure_class: str | None = None
    safe_summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class DeploymentRecord(BaseModel):
    deployment_id: str
    workspace: str
    environment: str
    template_id: str
    template_version: str
    template_commit_sha: str
    status: DeploymentStatus = DeploymentStatus.PENDING
    owner_user_id: str
    labels: dict[str, str] = Field(default_factory=dict)
    safe_outputs: dict[str, Any] = Field(default_factory=dict)
    active_request_id: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    destroyed_at: datetime | None = None


class CallbackEventRecord(BaseModel):
    callback_event_id: str
    request_id: str
    deployment_id: str
    github_run_id: str
    event_sequence: int
    operation: str
    status: str
    pipeline_identity: str
    payload_digest: str
    safe_payload: dict[str, Any]
    validation_result: str = "ACCEPTED"
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditEventRecord(BaseModel):
    audit_event_id: str
    actor_type: str  # "user", "pipeline", "system"
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    request_id: str | None = None
    deployment_id: str | None = None
    outcome: str  # "SUCCESS", "DENIED", "FAILED", "REPLAYED"
    correlation_id: str | None = None
    safe_metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IdempotencyRecord(BaseModel):
    idempotency_key: str
    user_id: str
    payload_digest: str
    status_code: int
    response_body: dict[str, Any]
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

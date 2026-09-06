"""
Schemas for pipeline callbacks and dead-letter reconciliation.
"""

from typing import Any

from api.app.domain.models import RequestStatus
from pydantic import BaseModel, Field


class PipelineCallbackInput(BaseModel):
    request_id: str = Field(..., description="Correlation request identifier")
    deployment_id: str = Field(..., description="Target deployment identifier")
    template_id: str = Field(..., description="Template identifier")
    template_version: str = Field(..., description="Template semantic version")
    template_commit_sha: str = Field(..., description="Immutable template Git commit SHA")
    repository: str = Field(..., description="GitHub repository executing the workflow")
    workflow: str = Field(..., description="Workflow filename (e.g. deploy-t1.yml)")
    github_run_id: str = Field(..., description="GitHub Actions execution run ID")
    event_sequence: int = Field(..., ge=1, description="Monotonic callback sequence number")
    operation: str = Field(..., description="Operation type: 'create' or 'destroy'")
    status: RequestStatus = Field(..., description="Progress status of the pipeline")
    summary: str = Field(..., description="Safe human-readable progress summary")
    failure_class: str | None = Field(
        default=None, description="Standardized error category if failed"
    )
    artifact_references: list[str] = Field(
        default_factory=list, description="Safe GCS artifact paths"
    )
    outputs: dict[str, Any] = Field(default_factory=dict, description="Non-sensitive output values")


class CallbackResponse(BaseModel):
    status: str = "accepted"
    callback_event_id: str
    request_status: RequestStatus


class ReconcileResponse(BaseModel):
    reconciled_count: int
    failed_count: int
    reconciled_requests: list[str]
    details: list[dict[str, Any]]

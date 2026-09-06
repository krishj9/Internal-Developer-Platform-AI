"""
Pydantic API request and response schemas for templates, requests, and deployments.
"""

from datetime import datetime
from typing import Any

from api.app.domain.models import DeploymentStatus, RequestOperation, RequestStatus
from pydantic import BaseModel, Field


class CreateRequestInput(BaseModel):
    workspace: str = Field(..., description="Target workspace identifier")
    template_id: str = Field(..., description="Template ID to provision")
    template_version: str | None = Field(
        default=None, description="Optional specific semantic version"
    )
    environment: str = Field(default="dev", description="Target environment")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Template-specific inputs")


class RequestResponse(BaseModel):
    request_id: str
    deployment_id: str
    operation: RequestOperation
    status: RequestStatus
    workspace: str
    environment: str
    template_id: str
    template_version: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    safe_summary: str | None = None
    failure_class: str | None = None


class DeploymentResponse(BaseModel):
    deployment_id: str
    workspace: str
    environment: str
    template_id: str
    template_version: str
    status: DeploymentStatus
    owner_user_id: str
    safe_outputs: dict[str, Any] = Field(default_factory=dict)
    active_request_id: str | None = None
    created_at: datetime
    updated_at: datetime


class DeploymentConfigResponse(BaseModel):
    deployment_id: str
    workspace: str
    environment: str
    template_id: str
    template_version: str
    safe_config: dict[str, Any]


class TemplateResponse(BaseModel):
    template_id: str
    template_version: str
    display_name: str
    description: str
    supported_environments: list[str]
    allowed_models: list[str]
    allowed_regions: list[str]
    cost_tier: str

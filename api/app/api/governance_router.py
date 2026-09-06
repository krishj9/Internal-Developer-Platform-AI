"""
Governance API Router for Model Armor inspection and TTL lifecycle operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.app.auth.dependencies import get_current_user
from api.app.domain.models import DeploymentRecord
from api.app.governance.model_armor import (
    InspectionPoint,
    ModelArmorEngine,
    PolicyAction,
)
from api.app.repositories.user_repository import UserRecord
from api.app.services.ttl_cleanup_service import ttl_cleanup_service

router = APIRouter(prefix="/governance", tags=["Governance & Policy"])


class InspectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to inspect")
    point: InspectionPoint = Field(default=InspectionPoint.PROMPT, description="Screening point")
    mode: PolicyAction = Field(
        default=PolicyAction.BLOCK, description="Model Armor enforcement mode"
    )
    pii_detection: bool = Field(default=True, description="Enable PII detection")
    prompt_injection_filter: bool = Field(
        default=True, description="Enable prompt injection filter"
    )


class TtlOverrideRequest(BaseModel):
    deployment_id: str
    extension_days: int = Field(..., ge=1, le=30, description="Days to extend TTL")
    reason: str = Field(
        ..., min_length=5, max_length=200, description="Justification for extension"
    )


@router.post("/inspect")
async def inspect_content(
    req: InspectRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    """Run Model Armor inspection on text."""
    engine = ModelArmorEngine(
        mode=req.mode,
        pii_detection=req.pii_detection,
        prompt_injection_filter=req.prompt_injection_filter,
    )
    result = engine.inspect(req.text, point=req.point)
    return result


@router.get("/expired-deployments", response_model=list[DeploymentRecord])
async def list_expired_deployments(
    current_user: UserRecord = Depends(get_current_user),
):
    """List all active deployments past their TTL expiration date."""
    expired = await ttl_cleanup_service.find_expired_deployments()
    return expired


@router.post("/cleanup-expired")
async def cleanup_expired_deployments(
    current_user: UserRecord = Depends(get_current_user),
):
    """Trigger automated cleanup for expired deployments (platform_admin only)."""
    if current_user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform_admin users may trigger automated TTL cleanup.",
        )

    results = await ttl_cleanup_service.process_expired_deployments()
    return {
        "status": "success",
        "processed_count": len(results),
        "details": results,
    }


@router.post("/ttl-override")
async def override_ttl(
    req: TtlOverrideRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    """Grant an auditable TTL extension exception (platform_admin only)."""
    if current_user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform_admin users may grant TTL extensions.",
        )

    try:
        updated = await ttl_cleanup_service.grant_ttl_extension(
            deployment_id=req.deployment_id,
            extension_days=req.extension_days,
            admin_user_id=current_user.user_id,
            reason=req.reason,
        )
        return {
            "status": "success",
            "deployment_id": updated.deployment_id,
            "new_expires_at": updated.expires_at.isoformat() if updated.expires_at else None,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

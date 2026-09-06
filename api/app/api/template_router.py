"""
Template API endpoints.
"""

from fastapi import APIRouter, Depends

from api.app.api.schemas import TemplateResponse
from api.app.auth.dependencies import get_current_user
from api.app.repositories.platform_repositories import TemplateRepository, get_template_repo
from api.app.repositories.user_repository import UserRecord

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get(
    "",
    response_model=list[TemplateResponse],
    summary="List Published Templates",
    description="Retrieve catalog of available, governed infrastructure templates.",
)
async def list_templates(
    current_user: UserRecord = Depends(get_current_user),
    repository: TemplateRepository = Depends(get_template_repo),
) -> list[TemplateResponse]:
    templates = await repository.list_published()
    return [
        TemplateResponse(
            template_id=t.template_id,
            template_version=t.template_version,
            display_name=t.display_name,
            description=t.description,
            supported_environments=t.supported_environments,
            allowed_models=t.allowed_models,
            allowed_regions=t.allowed_regions,
            cost_tier=t.cost_tier,
        )
        for t in templates
    ]

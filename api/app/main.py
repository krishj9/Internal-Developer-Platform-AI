"""
Main FastAPI application entrypoint for the IDP Control Plane.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.api.admin_router import router as admin_router
from api.app.api.auth_router import router as auth_router
from api.app.api.callback_router import router as callback_router
from api.app.api.deployment_router import router as deployment_router
from api.app.api.governance_router import router as governance_router
from api.app.api.request_router import router as request_router
from api.app.api.template_router import router as template_router
from api.app.core.settings import settings
from api.app.domain.models import TemplateRecord
from api.app.repositories.platform_repositories import (
    get_template_repo,
    init_firestore_repositories,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.USE_FIRESTORE:
        init_firestore_repositories(settings.PROJECT_ID, settings.FIRESTORE_DATABASE)

    t_repo = get_template_repo()

    # Seed default T1 template if not already present
    t1 = await t_repo.get("t1-agent-engine", "2.0.0")
    if not t1:
        await t_repo.save(
            TemplateRecord(
                template_id="t1-agent-engine",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Agent on Vertex AI Agent Engine",
                description="Governed ADK-based agent deployed to Google Cloud Agent Engine.",
                supported_environments=["dev"],
                allowed_models=["gemini-2.5-flash", "gemini-2.5-pro"],
                allowed_regions=["us-central1"],
                cost_tier="low",
                manifest={"readiness": {"type": "smoke_test"}},
                status="published",
            )
        )

    # Seed default T3 Cloud Run template if not already present
    t3 = await t_repo.get("t3-cloud-run-agent", "2.0.0")
    if not t3:
        await t_repo.save(
            TemplateRecord(
                template_id="t3-cloud-run-agent",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Agent on Cloud Run Service",
                description="Governed ADK-based agent deployed to Google Cloud Run v2.",
                supported_environments=["dev"],
                allowed_models=["gemini-2.5-flash", "gemini-2.5-pro"],
                allowed_regions=["us-central1"],
                cost_tier="medium",
                manifest={"readiness": {"type": "http_smoke_test"}},
                status="published",
            )
        )

    # Seed default T2 Managed RAG template if not already present
    t2 = await t_repo.get("t2-managed-rag", "2.0.0")
    if not t2:
        await t_repo.save(
            TemplateRecord(
                template_id="t2-managed-rag",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Vertex AI Managed RAG Engine",
                description="Governed Vertex AI RAG Engine stack with RagManagedDb.",
                supported_environments=["dev"],
                allowed_models=["text-embedding-004", "text-embedding-005"],
                allowed_regions=["us-central1"],
                cost_tier="medium",
                manifest={"readiness": {"type": "rag_retrieval_smoke_test"}},
                status="published",
            )
        )

    # Seed default T4 Governance template if not already present
    t4 = await t_repo.get("t4-governance", "2.0.0")
    if not t4:
        await t_repo.save(
            TemplateRecord(
                template_id="t4-governance",
                template_version="2.0.0",
                template_commit_sha="010078cf6745f44da605f6fa0768b4f177c385a5",
                display_name="Governance & Operational Controls",
                description=(
                    "Governed Model Armor guardrails, Cloud Monitoring alerts, "
                    "and automated TTL policies."
                ),
                supported_environments=["dev", "prod"],
                allowed_models=[],
                allowed_regions=["us-central1"],
                cost_tier="low",
                manifest={"readiness": {"type": "policy_verification_test"}},
                status="published",
            )
        )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Control plane API for governed agentic-AI infrastructure on GCP.",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/healthz", tags=["Health"], summary="Health check")
    async def healthz():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # Mount API routers
    app.include_router(auth_router)
    app.include_router(template_router)
    app.include_router(request_router)
    app.include_router(deployment_router)
    app.include_router(callback_router)
    app.include_router(admin_router)
    app.include_router(governance_router)

    return app


app = create_app()

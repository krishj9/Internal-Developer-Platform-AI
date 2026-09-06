"""
Main FastAPI application entrypoint for the IDP Control Plane.
"""

from contextlib import asynccontextmanager

from api.app.api.auth_router import router as auth_router
from api.app.core.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions (e.g. initialize Secret Manager or Firestore clients if needed)
    yield
    # Shutdown actions


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

    return app


app = create_app()

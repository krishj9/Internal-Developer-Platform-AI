"""
Configuration and settings for the IDP Control Plane API.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project & Environment
    PROJECT_ID: str = Field(default="idp-poc-dev", description="GCP Project ID")
    ENVIRONMENT: str = Field(default="dev", description="Deployment environment")
    APP_NAME: str = "IDP Control Plane API"
    APP_VERSION: str = "2.1.0"
    DEBUG: bool = False

    # Authentication & JWT Configuration
    # In production, loaded via Google Secret Manager ('idp-jwt-signing-key')
    JWT_SECRET_KEY: str = Field(
        default="dev-insecure-secret-key-change-in-production-must-be-32bytes!",
        description="HMAC secret key for JWT signing",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60  # Exactly 60 minutes / 3600 seconds
    JWT_ISSUER: str = "idp-control-plane"
    JWT_AUDIENCE: str = "idp-portal"

    # CORS Configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Secret Manager Secret IDs
    SECRET_ID_JWT_SIGNING_KEY: str = "idp-jwt-signing-key"
    SECRET_ID_GITHUB_DISPATCH_TOKEN: str = "idp-github-dispatch-token"
    # GitHub Integration
    GITHUB_OWNER: str = "krishj9"
    GITHUB_REPO: str = "Internal-Developer-Platform-AI"
    GITHUB_DISPATCH_TOKEN: str = ""

    # Platform Infrastructure Context
    STATE_BUCKET_NAME: str = "idp-tfstate-mybrightday-dev"
    WIF_PROVIDER_NAME: str = (
        "projects/754915077075/locations/global/workloadIdentityPools/"
        "idp-github-pool/providers/idp-github-provider"
    )
    PIPELINE_SA_EMAIL: str = "idp-pipeline-t1-dev@mybrightday-dev.iam.gserviceaccount.com"
    API_BASE_URL: str = "https://idp-api-754915077075.us-central1.run.app"

    # Cloud Controls
    USE_SECRET_MANAGER: bool = False
    USE_FIRESTORE: bool = False
    FIRESTORE_DATABASE: str = "idp-db"


def load_secret_manager_secrets(cfg: Settings) -> None:
    """Optionally load runtime secrets directly from GCP Secret Manager."""
    if not cfg.USE_SECRET_MANAGER:
        return

    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()

        # 1. JWT Signing Key
        sec_name = (
            f"projects/{cfg.PROJECT_ID}/secrets/{cfg.SECRET_ID_JWT_SIGNING_KEY}/versions/latest"
        )
        response = client.access_secret_version(request={"name": sec_name})
        secret_val = response.payload.data.decode("utf-8").strip()
        if secret_val:
            cfg.JWT_SECRET_KEY = secret_val

        # 2. GitHub Dispatch Token
        dispatch_sec = (
            f"projects/{cfg.PROJECT_ID}/secrets/"
            f"{cfg.SECRET_ID_GITHUB_DISPATCH_TOKEN}/versions/latest"
        )
        disp_resp = client.access_secret_version(request={"name": dispatch_sec})
        disp_val = disp_resp.payload.data.decode("utf-8").strip()
        if disp_val:
            cfg.GITHUB_DISPATCH_TOKEN = disp_val
    except Exception as e:
        print(
            f"Warning: Could not load secrets from Secret Manager: {e}"
        )


settings = Settings()
if settings.USE_SECRET_MANAGER:
    load_secret_manager_secrets(settings)

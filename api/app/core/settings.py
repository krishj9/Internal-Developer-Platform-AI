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


settings = Settings()

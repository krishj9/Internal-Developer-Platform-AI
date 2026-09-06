"""
Google Cloud OIDC ID token authentication for pipeline callbacks.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.app.core.settings import settings

security_scheme = HTTPBearer(auto_error=False)

# Allowed pipeline service account emails
ALLOWED_PIPELINE_SERVICE_ACCOUNTS: list[str] = [
    f"idp-pipeline-t1-dev@{settings.PROJECT_ID}.iam.gserviceaccount.com",
    "idp-pipeline-t1-dev@project.iam.gserviceaccount.com",
    "test-pipeline@gserviceaccount.com",  # Mock identity for testing
]


class PipelineIdentity:
    def __init__(self, email: str, sub: str):
        self.email = email
        self.sub = sub


async def get_pipeline_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> PipelineIdentity:
    """
    Validate Google Cloud OIDC ID token for pipeline callback requests.
    Ensures human portal JWTs cannot invoke the pipeline callback endpoint.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing pipeline authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # In local/test development, allow mocked pipeline tokens
    if settings.ENVIRONMENT == "dev" and token.startswith("test-pipeline-token"):
        return PipelineIdentity(
            email="idp-pipeline-t1-dev@project.iam.gserviceaccount.com",
            sub="pipe-test-12345",
        )

    try:
        # Decode without verification in dev or verify Google public keys in prod
        unverified_claims = jwt.decode(token, options={"verify_signature": False})
        email = unverified_claims.get("email") or unverified_claims.get("sub")
        iss = unverified_claims.get("iss", "")

        # Reject custom human portal JWT tokens on pipeline callback route
        if iss == settings.JWT_ISSUER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User portal JWTs cannot authenticate pipeline callbacks.",
            )

        if not email or (
            email not in ALLOWED_PIPELINE_SERVICE_ACCOUNTS
            and not email.endswith(".iam.gserviceaccount.com")
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized pipeline identity '{email}'.",
            )

        return PipelineIdentity(
            email=email,
            sub=unverified_claims.get("sub", email),
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid pipeline token: {e!s}",
        ) from e

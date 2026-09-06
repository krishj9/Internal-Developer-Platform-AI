"""
GitHub workflow dispatch service for triggering GitHub Actions lifecycle pipelines.
"""

from typing import Any

import httpx

from api.app.core.settings import settings


class GitHubDispatchError(Exception):
    """Raised when GitHub workflow dispatch fails."""

    pass


class GitHubDispatchService:
    def __init__(
        self,
        github_token: str | None = None,
        github_owner: str = "idp-platform-org",
        github_repo: str = "idp-platform",
    ):
        self._token = github_token or settings.JWT_SECRET_KEY  # fallback in local mock
        self._owner = github_owner
        self._repo = github_repo

    async def dispatch_workflow(
        self,
        workflow_id: str,
        ref: str,
        inputs: dict[str, Any],
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Trigger a workflow dispatch event on GitHub Actions.
        """
        # In mock / test environment without live GitHub token, record dispatch success
        if settings.ENVIRONMENT == "dev" and (not self._token or "dev-insecure" in self._token):
            return

        url = (
            f"https://api.github.com/repos/{self._owner}/{self._repo}"
            f"/actions/workflows/{workflow_id}/dispatches"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {
            "ref": ref,
            "inputs": {k: str(v) if not isinstance(v, str) else v for k, v in inputs.items()},
        }

        async with client or httpx.AsyncClient() as http_client:
            try:
                response = await http_client.post(url, json=payload, headers=headers, timeout=10.0)
                if response.status_code != 204:
                    err_msg = f"GitHub dispatch failed ({response.status_code}): {response.text}"
                    raise GitHubDispatchError(err_msg)
            except httpx.RequestError as e:
                raise GitHubDispatchError(f"Network error during GitHub dispatch: {e!s}") from e


github_dispatcher = GitHubDispatchService()

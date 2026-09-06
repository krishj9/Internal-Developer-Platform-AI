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
        github_owner: str | None = None,
        github_repo: str | None = None,
    ):
        self._token = github_token
        self._owner = github_owner
        self._repo = github_repo

    @property
    def token(self) -> str:
        return self._token or settings.GITHUB_DISPATCH_TOKEN or settings.JWT_SECRET_KEY

    @property
    def owner(self) -> str:
        return self._owner or settings.GITHUB_OWNER

    @property
    def repo(self) -> str:
        return self._repo or settings.GITHUB_REPO

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
        tok = self.token
        # In dev environment without live GitHub token or with placeholder token, simulate dispatch
        if settings.ENVIRONMENT == "dev" and (
            not tok or "placeholder" in tok or "dev-insecure" in tok
        ):
            return

        if not tok or "placeholder" in tok:
            raise GitHubDispatchError("Valid GitHub dispatch token is not configured.")

        url = (
            f"https://api.github.com/repos/{self.owner}/{self.repo}"
            f"/actions/workflows/{workflow_id}/dispatches"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {tok}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        # GitHub Actions workflow dispatch requires a branch or tag name for `ref`.
        # When an immutable commit SHA is passed, dispatch on "main" while passing the
        # commit SHA in inputs for the checkout step.
        branch_ref = "main" if len(ref) == 40 and not ref.startswith("refs/") else ref
        payload = {
            "ref": branch_ref,
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

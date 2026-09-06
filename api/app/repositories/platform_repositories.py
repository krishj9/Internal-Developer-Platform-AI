"""
Platform repository interfaces and implementations for Requests, Deployments,
Callbacks, Audits, Templates, and Idempotency.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from api.app.domain.models import (
    AuditEventRecord,
    CallbackEventRecord,
    DeploymentRecord,
    DeploymentStatus,
    IdempotencyRecord,
    RequestRecord,
    RequestStatus,
    TemplateRecord,
)
from api.app.domain.state_machine import (
    DeploymentLockedError,
    validate_deployment_transition,
    validate_request_transition,
)


class TemplateRepository(ABC):
    @abstractmethod
    async def get(self, template_id: str, version: str) -> TemplateRecord | None:
        pass

    @abstractmethod
    async def list_published(self) -> list[TemplateRecord]:
        pass

    @abstractmethod
    async def save(self, template: TemplateRecord) -> None:
        pass


class DeploymentRepository(ABC):
    @abstractmethod
    async def get(self, deployment_id: str) -> DeploymentRecord | None:
        pass

    @abstractmethod
    async def list_by_workspace(
        self, workspace: str, status: DeploymentStatus | None = None
    ) -> list[DeploymentRecord]:
        pass

    @abstractmethod
    async def save(self, deployment: DeploymentRecord) -> None:
        pass

    @abstractmethod
    async def acquire_lock(self, deployment_id: str, request_id: str) -> DeploymentRecord:
        """
        Atomically acquire lifecycle lock on deployment.
        Raises DeploymentLockedError if another active request is holding the lock.
        """
        pass

    @abstractmethod
    async def release_lock(self, deployment_id: str, request_id: str) -> None:
        """
        Atomically release lifecycle lock if owned by request_id.
        """
        pass


class RequestRepository(ABC):
    @abstractmethod
    async def get(self, request_id: str) -> RequestRecord | None:
        pass

    @abstractmethod
    async def list_by_deployment(self, deployment_id: str) -> list[RequestRecord]:
        pass

    @abstractmethod
    async def save(self, request: RequestRecord) -> None:
        pass

    @abstractmethod
    async def update_status(
        self,
        request_id: str,
        new_status: RequestStatus,
        failure_class: str | None = None,
        safe_summary: str | None = None,
    ) -> RequestRecord:
        pass


class CallbackEventRepository(ABC):
    @abstractmethod
    async def append(self, event: CallbackEventRecord) -> None:
        pass

    @abstractmethod
    async def list_by_request(self, request_id: str) -> list[CallbackEventRecord]:
        pass


class AuditEventRepository(ABC):
    @abstractmethod
    async def append(self, event: AuditEventRecord) -> None:
        pass

    @abstractmethod
    async def list_by_workspace(self, workspace: str, limit: int = 50) -> list[AuditEventRecord]:
        pass


class IdempotencyRepository(ABC):
    @abstractmethod
    async def get(self, user_id: str, idempotency_key: str) -> IdempotencyRecord | None:
        pass

    @abstractmethod
    async def save(self, record: IdempotencyRecord) -> None:
        pass


# ---------------------------------------------------------------------------
# In-Memory Thread-Safe Implementations (for fast testing & local execution)
# ---------------------------------------------------------------------------

class InMemoryTemplateRepository(TemplateRepository):
    def __init__(self):
        self._templates: dict[str, TemplateRecord] = {}

    def _key(self, template_id: str, version: str) -> str:
        return f"{template_id}@{version}"

    async def get(self, template_id: str, version: str) -> TemplateRecord | None:
        return self._templates.get(self._key(template_id, version))

    async def list_published(self) -> list[TemplateRecord]:
        return list(self._templates.values())

    async def save(self, template: TemplateRecord) -> None:
        self._templates[self._key(template.template_id, template.template_version)] = template


class InMemoryDeploymentRepository(DeploymentRepository):
    def __init__(self):
        self._deployments: dict[str, DeploymentRecord] = {}
        self._lock = asyncio.Lock()

    async def get(self, deployment_id: str) -> DeploymentRecord | None:
        return self._deployments.get(deployment_id)

    async def list_by_workspace(
        self, workspace: str, status: DeploymentStatus | None = None
    ) -> list[DeploymentRecord]:
        results = [d for d in self._deployments.values() if d.workspace == workspace]
        if status:
            results = [d for d in results if d.status == status]
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    async def save(self, deployment: DeploymentRecord) -> None:
        async with self._lock:
            existing = self._deployments.get(deployment.deployment_id)
            if existing and existing.status != deployment.status:
                validate_deployment_transition(existing.status, deployment.status)
            deployment.updated_at = datetime.now(UTC)
            self._deployments[deployment.deployment_id] = deployment

    async def acquire_lock(self, deployment_id: str, request_id: str) -> DeploymentRecord:
        async with self._lock:
            dep = self._deployments.get(deployment_id)
            if not dep:
                raise ValueError(f"Deployment '{deployment_id}' does not exist.")

            if dep.active_request_id and dep.active_request_id != request_id:
                raise DeploymentLockedError(
                    f"Deployment '{deployment_id}' is locked by request '{dep.active_request_id}'."
                )

            dep.active_request_id = request_id
            dep.updated_at = datetime.now(UTC)
            self._deployments[deployment_id] = dep
            return dep

    async def release_lock(self, deployment_id: str, request_id: str) -> None:
        async with self._lock:
            dep = self._deployments.get(deployment_id)
            if dep and dep.active_request_id == request_id:
                dep.active_request_id = None
                dep.updated_at = datetime.now(UTC)
                self._deployments[deployment_id] = dep


class InMemoryRequestRepository(RequestRepository):
    def __init__(self):
        self._requests: dict[str, RequestRecord] = {}
        self._lock = asyncio.Lock()

    async def get(self, request_id: str) -> RequestRecord | None:
        return self._requests.get(request_id)

    async def list_by_deployment(self, deployment_id: str) -> list[RequestRecord]:
        results = [r for r in self._requests.values() if r.deployment_id == deployment_id]
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    async def save(self, request: RequestRecord) -> None:
        async with self._lock:
            existing = self._requests.get(request.request_id)
            if existing and existing.status != request.status:
                validate_request_transition(existing.status, request.status)
            request.updated_at = datetime.now(UTC)
            self._requests[request.request_id] = request

    async def update_status(
        self,
        request_id: str,
        new_status: RequestStatus,
        failure_class: str | None = None,
        safe_summary: str | None = None,
    ) -> RequestRecord:
        async with self._lock:
            req = self._requests.get(request_id)
            if not req:
                raise ValueError(f"Request '{request_id}' not found.")

            validate_request_transition(req.status, new_status)
            req.status = new_status
            if failure_class:
                req.failure_class = failure_class
            if safe_summary:
                req.safe_summary = safe_summary
            terminal_set = {
                RequestStatus.SUCCEEDED,
                RequestStatus.FAILED,
                RequestStatus.CANCELLED,
            }
            if new_status in terminal_set:
                req.completed_at = datetime.now(UTC)
            req.updated_at = datetime.now(UTC)
            self._requests[request_id] = req
            return req


class InMemoryCallbackEventRepository(CallbackEventRepository):
    def __init__(self):
        self._events: list[CallbackEventRecord] = []
        self._lock = asyncio.Lock()

    async def append(self, event: CallbackEventRecord) -> None:
        async with self._lock:
            self._events.append(event)

    async def list_by_request(self, request_id: str) -> list[CallbackEventRecord]:
        results = [e for e in self._events if e.request_id == request_id]
        return sorted(results, key=lambda x: x.event_sequence)


class InMemoryAuditEventRepository(AuditEventRepository):
    def __init__(self):
        self._audits: list[AuditEventRecord] = []
        self._lock = asyncio.Lock()

    async def append(self, event: AuditEventRecord) -> None:
        async with self._lock:
            self._audits.append(event)

    async def list_by_workspace(self, workspace: str, limit: int = 50) -> list[AuditEventRecord]:
        results = [
            a for a in self._audits if a.safe_metadata.get("workspace") == workspace
        ]
        return sorted(results, key=lambda x: x.timestamp, reverse=True)[:limit]


class InMemoryIdempotencyRepository(IdempotencyRepository):
    def __init__(self):
        self._records: dict[str, IdempotencyRecord] = {}

    def _key(self, user_id: str, key: str) -> str:
        return f"{user_id}:{key}"

    async def get(self, user_id: str, idempotency_key: str) -> IdempotencyRecord | None:
        record = self._records.get(self._key(user_id, idempotency_key))
        if record:
            # Check 24-hour TTL expiration
            if record.expires_at < datetime.now(UTC):
                del self._records[self._key(user_id, idempotency_key)]
                return None
        return record

    async def save(self, record: IdempotencyRecord) -> None:
        self._records[self._key(record.user_id, record.idempotency_key)] = record


# Global singletons
template_repo = InMemoryTemplateRepository()
deployment_repo = InMemoryDeploymentRepository()
request_repo = InMemoryRequestRepository()
callback_repo = InMemoryCallbackEventRepository()
audit_repo = InMemoryAuditEventRepository()
idempotency_repo = InMemoryIdempotencyRepository()

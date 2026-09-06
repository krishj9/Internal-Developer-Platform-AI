"""
Production Firestore repository implementations for the IDP Control Plane.
Strictly implements the domain repository interfaces using google.cloud.firestore.AsyncClient.
"""

from datetime import UTC, datetime
from typing import Any

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

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
from api.app.repositories.platform_repositories import (
    AuditEventRepository,
    CallbackEventRepository,
    DeploymentRepository,
    IdempotencyRepository,
    RequestRepository,
    TemplateRepository,
)
from api.app.repositories.user_repository import UserRecord, UserRepository


class FirestoreUserRepository(UserRepository):
    def __init__(self, db: firestore.AsyncClient):
        self._db = db
        self._collection = db.collection("users")

    async def get_by_username(self, username: str) -> UserRecord | None:
        query = self._collection.where(
            filter=FieldFilter("username", "==", username.lower())
        ).limit(1)
        docs = [d async for d in query.stream()]
        if not docs:
            return None
        return UserRecord(**docs[0].to_dict())

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        doc = await self._collection.document(user_id).get()
        if not doc.exists:
            return None
        return UserRecord(**doc.to_dict())

    async def save(self, user: UserRecord) -> None:
        user.updated_at = datetime.now(UTC)
        await self._collection.document(user.user_id).set(user.model_dump(mode="json"))


class FirestoreTemplateRepository(TemplateRepository):
    def __init__(self, db: firestore.AsyncClient):
        self._db = db
        self._collection = db.collection("templates")

    def _doc_id(self, template_id: str, version: str) -> str:
        return f"{template_id}@{version}"

    async def get(self, template_id: str, version: str) -> TemplateRecord | None:
        doc = await self._collection.document(self._doc_id(template_id, version)).get()
        if not doc.exists:
            return None
        return TemplateRecord(**doc.to_dict())

    async def list_published(self) -> list[TemplateRecord]:
        docs = [d async for d in self._collection.stream()]
        return [TemplateRecord(**d.to_dict()) for d in docs]

    async def save(self, template: TemplateRecord) -> None:
        doc_id = self._doc_id(template.template_id, template.template_version)
        await self._collection.document(doc_id).set(template.model_dump(mode="json"))


class FirestoreDeploymentRepository(DeploymentRepository):
    def __init__(self, db: firestore.AsyncClient):
        self._db = db
        self._collection = db.collection("deployments")

    async def get(self, deployment_id: str) -> DeploymentRecord | None:
        doc = await self._collection.document(deployment_id).get()
        if not doc.exists:
            return None
        return DeploymentRecord(**doc.to_dict())

    async def list_by_workspace(
        self, workspace: str, status: DeploymentStatus | None = None
    ) -> list[DeploymentRecord]:
        query = self._collection.where(filter=FieldFilter("workspace", "==", workspace))
        if status:
            query = query.where(filter=FieldFilter("status", "==", status.value))
        docs = [d async for d in query.stream()]
        records = [DeploymentRecord(**d.to_dict()) for d in docs]
        return sorted(records, key=lambda x: x.created_at, reverse=True)

    async def list_all(self) -> list[DeploymentRecord]:
        docs = [d async for d in self._collection.stream()]
        records = [DeploymentRecord(**d.to_dict()) for d in docs]
        return sorted(records, key=lambda x: x.created_at, reverse=True)

    async def save(self, deployment: DeploymentRecord) -> None:
        doc_ref = self._collection.document(deployment.deployment_id)
        doc = await doc_ref.get()
        if doc.exists:
            existing = DeploymentRecord(**doc.to_dict())
            if existing.status != deployment.status:
                validate_deployment_transition(existing.status, deployment.status)

        deployment.updated_at = datetime.now(UTC)
        await doc_ref.set(deployment.model_dump(mode="json"))

    async def acquire_lock(self, deployment_id: str, request_id: str) -> DeploymentRecord:
        doc_ref = self._collection.document(deployment_id)

        @firestore.async_transactional
        async def _acquire_in_tx(transaction: Any) -> DeploymentRecord:
            snapshot = await doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                raise ValueError(f"Deployment '{deployment_id}' does not exist.")

            data = snapshot.to_dict()
            dep = DeploymentRecord(**data)

            if dep.active_request_id and dep.active_request_id != request_id:
                raise DeploymentLockedError(
                    f"Deployment '{deployment_id}' is locked by request '{dep.active_request_id}'."
                )

            dep.active_request_id = request_id
            dep.updated_at = datetime.now(UTC)
            transaction.update(
                doc_ref,
                {
                    "active_request_id": request_id,
                    "updated_at": dep.updated_at.isoformat(),
                },
            )
            return dep

        transaction = self._db.transaction()
        return await _acquire_in_tx(transaction)

    async def release_lock(self, deployment_id: str, request_id: str) -> None:
        doc_ref = self._collection.document(deployment_id)

        @firestore.async_transactional
        async def _release_in_tx(transaction: Any) -> None:
            snapshot = await doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                return

            data = snapshot.to_dict()
            if data.get("active_request_id") == request_id:
                transaction.update(
                    doc_ref,
                    {
                        "active_request_id": None,
                        "updated_at": datetime.now(UTC).isoformat(),
                    },
                )

        transaction = self._db.transaction()
        await _release_in_tx(transaction)


class FirestoreRequestRepository(RequestRepository):
    def __init__(self, db: firestore.AsyncClient):
        self._db = db
        self._collection = db.collection("requests")

    async def get(self, request_id: str) -> RequestRecord | None:
        doc = await self._collection.document(request_id).get()
        if not doc.exists:
            return None
        return RequestRecord(**doc.to_dict())

    async def list_by_deployment(self, deployment_id: str) -> list[RequestRecord]:
        query = self._collection.where(
            filter=FieldFilter("deployment_id", "==", deployment_id)
        )
        docs = [d async for d in query.stream()]
        records = [RequestRecord(**d.to_dict()) for d in docs]
        return sorted(records, key=lambda x: x.created_at, reverse=True)

    async def save(self, request: RequestRecord) -> None:
        doc_ref = self._collection.document(request.request_id)
        doc = await doc_ref.get()
        if doc.exists:
            existing = RequestRecord(**doc.to_dict())
            if existing.status != request.status:
                validate_request_transition(existing.status, request.status)

        request.updated_at = datetime.now(UTC)
        await doc_ref.set(request.model_dump(mode="json"))

    async def update_status(
        self,
        request_id: str,
        new_status: RequestStatus,
        failure_class: str | None = None,
        safe_summary: str | None = None,
    ) -> RequestRecord:
        doc_ref = self._collection.document(request_id)

        @firestore.async_transactional
        async def _update_in_tx(transaction: Any) -> RequestRecord:
            snapshot = await doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                raise ValueError(f"Request '{request_id}' not found.")

            req = RequestRecord(**snapshot.to_dict())
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
            now = datetime.now(UTC)
            updates: dict[str, Any] = {
                "status": new_status.value,
                "updated_at": now.isoformat(),
            }
            if new_status in terminal_set:
                req.completed_at = now
                updates["completed_at"] = now.isoformat()
            if failure_class:
                updates["failure_class"] = failure_class
            if safe_summary:
                updates["safe_summary"] = safe_summary

            transaction.update(doc_ref, updates)
            return req

        transaction = self._db.transaction()
        return await _update_in_tx(transaction)


class FirestoreCallbackEventRepository(CallbackEventRepository):
    def __init__(self, db: firestore.AsyncClient):
        self._db = db
        self._collection = db.collection("callback_events")

    async def append(self, event: CallbackEventRecord) -> None:
        await self._collection.document(event.callback_event_id).set(
            event.model_dump(mode="json")
        )

    async def list_by_request(self, request_id: str) -> list[CallbackEventRecord]:
        query = self._collection.where(filter=FieldFilter("request_id", "==", request_id))
        docs = [d async for d in query.stream()]
        records = [CallbackEventRecord(**d.to_dict()) for d in docs]
        return sorted(records, key=lambda x: x.event_sequence)


class FirestoreAuditEventRepository(AuditEventRepository):
    def __init__(self, db: firestore.AsyncClient):
        self._db = db
        self._collection = db.collection("audit_events")

    async def append(self, event: AuditEventRecord) -> None:
        await self._collection.document(event.audit_event_id).set(
            event.model_dump(mode="json")
        )

    async def list_by_workspace(
        self, workspace: str, limit: int = 50
    ) -> list[AuditEventRecord]:
        query = self._collection.where(
            filter=FieldFilter("safe_metadata.workspace", "==", workspace)
        ).limit(limit)
        docs = [d async for d in query.stream()]
        records = [AuditEventRecord(**d.to_dict()) for d in docs]
        return sorted(records, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def list_by_actor(
        self, actor_id: str, limit: int = 50
    ) -> list[AuditEventRecord]:
        query = self._collection.where(
            filter=FieldFilter("actor_id", "==", actor_id)
        ).limit(limit)
        docs = [d async for d in query.stream()]
        records = [AuditEventRecord(**d.to_dict()) for d in docs]
        return sorted(records, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def list_all(self, limit: int = 100) -> list[AuditEventRecord]:
        docs = [d async for d in self._collection.limit(limit).stream()]
        records = [AuditEventRecord(**d.to_dict()) for d in docs]
        return sorted(records, key=lambda x: x.timestamp, reverse=True)[:limit]


class FirestoreIdempotencyRepository(IdempotencyRepository):
    def __init__(self, db: firestore.AsyncClient):
        self._db = db
        self._collection = db.collection("idempotency_records")

    def _doc_id(self, user_id: str, key: str) -> str:
        return f"{user_id}:{key}"

    async def get(self, user_id: str, idempotency_key: str) -> IdempotencyRecord | None:
        doc_id = self._doc_id(user_id, idempotency_key)
        doc = await self._collection.document(doc_id).get()
        if not doc.exists:
            return None

        record = IdempotencyRecord(**doc.to_dict())
        if record.expires_at < datetime.now(UTC):
            await self._collection.document(doc_id).delete()
            return None
        return record

    async def save(self, record: IdempotencyRecord) -> None:
        doc_id = self._doc_id(record.user_id, record.idempotency_key)
        await self._collection.document(doc_id).set(record.model_dump(mode="json"))

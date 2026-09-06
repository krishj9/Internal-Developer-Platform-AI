"""
User repository interface and implementations (In-memory mock for tests & Firestore for cloud).
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from pydantic import BaseModel, EmailStr


class UserRecord(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    password_hash: str
    role: str  # developer, approver, platform_admin, pipeline
    workspaces: list[str]
    token_version: int = 1
    is_active: bool = True
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> UserRecord | None:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> UserRecord | None:
        pass

    @abstractmethod
    async def save(self, user: UserRecord) -> None:
        pass


class InMemoryUserRepository(UserRepository):
    """In-memory user store for fast testing and local development."""

    def __init__(self):
        self._users_by_id: dict[str, UserRecord] = {}
        self._users_by_username: dict[str, UserRecord] = {}

    async def get_by_username(self, username: str) -> UserRecord | None:
        return self._users_by_username.get(username.lower())

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._users_by_id.get(user_id)

    async def save(self, user: UserRecord) -> None:
        self._users_by_id[user.user_id] = user
        self._users_by_username[user.username.lower()] = user


# Global singleton instance for local/test defaults (can be overridden via dependency injection)
user_repo: UserRepository = InMemoryUserRepository()


def get_user_repo() -> UserRepository:
    """Dependency getter returning current user repository instance."""
    return user_repo

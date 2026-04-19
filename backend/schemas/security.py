from __future__ import annotations

from enum import Enum
from typing import Any, Iterable

from pydantic import Field

from schemas.common import BaseSchema


class UserRole(str, Enum):
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    ANALYST = "analyst"
    VIEWER = "viewer"


ROLE_PRIORITY: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.ANALYST: 1,
    UserRole.COMPLIANCE_OFFICER: 2,
    UserRole.ADMIN: 3,
}


class AuthenticatedUser(BaseSchema):
    user_id: str
    email: str | None = None
    display_name: str | None = None
    roles: list[UserRole] = Field(default_factory=list)
    auth_mode: str
    token_claims: dict[str, Any] = Field(default_factory=dict, exclude=True)

    def has_any_role(self, allowed_roles: Iterable[UserRole]) -> bool:
        allowed = set(allowed_roles)
        return any(role in allowed for role in self.roles)

    @property
    def primary_role(self) -> UserRole:
        if not self.roles:
            return UserRole.VIEWER
        return max(self.roles, key=lambda role: ROLE_PRIORITY[role])

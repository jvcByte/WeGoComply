from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import Request

from repositories.audit_repository import AppendOnlyAuditRepository
from schemas.security import AuthenticatedUser


class AuditService:
    def __init__(self, repository: AppendOnlyAuditRepository) -> None:
        self.repository = repository

    def log_action(
        self,
        *,
        request: Request,
        actor: AuthenticatedUser,
        action: str,
        resource_type: str,
        status: str,
        details: dict[str, Any] | None = None,
        resource_id: str | None = None,
    ) -> None:
        request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
        event = {
            "event_id": str(uuid4()),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "actor": {
                "user_id": actor.user_id,
                "email": actor.email,
                "display_name": actor.display_name,
                "roles": [role.value for role in actor.roles],
                "auth_mode": actor.auth_mode,
            },
            "request": {
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent"),
            },
            "details": details or {},
        }
        self.repository.append(event)

from __future__ import annotations

from typing import Any

from fastapi import status


class AppError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ConfigurationError(AppError):
    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(
            message,
            code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExternalServiceError(AppError):
    def __init__(self, message: str, *, code: str = "EXTERNAL_SERVICE_ERROR", details: Any | None = None) -> None:
        super().__init__(
            message,
            code=code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


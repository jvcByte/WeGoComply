from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from core.errors import ConfigurationError

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class AppMode(str, Enum):
    MOCK = "mock"
    LIVE = "live"


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    mode: AppMode
    cors_origins: tuple[str, ...]
    dojah_app_id: str | None
    dojah_api_key: str | None
    dojah_base_url: str
    azure_openai_endpoint: str | None
    azure_openai_key: str | None
    azure_openai_deployment: str | None
    azure_face_endpoint: str | None
    azure_face_key: str | None
    azure_document_intelligence_endpoint: str | None
    azure_document_intelligence_key: str | None
    aml_model_path: Path

    @property
    def is_live(self) -> bool:
        return self.mode == AppMode.LIVE

    def validate_runtime(self) -> None:
        if not self.is_live:
            return

        required = {
            "DOJAH_APP_ID": self.dojah_app_id,
            "DOJAH_API_KEY": self.dojah_api_key,
            "AZURE_OPENAI_ENDPOINT": self.azure_openai_endpoint,
            "AZURE_OPENAI_KEY": self.azure_openai_key,
            "AZURE_OPENAI_DEPLOYMENT": self.azure_openai_deployment,
            "AZURE_FACE_ENDPOINT": self.azure_face_endpoint,
            "AZURE_FACE_KEY": self.azure_face_key,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigurationError(
                message="Live mode is enabled but required environment variables are missing.",
                details={"missing": missing},
            )


def _parse_mode(raw_mode: str | None) -> AppMode:
    mode = (raw_mode or AppMode.MOCK.value).strip().lower()
    try:
        return AppMode(mode)
    except ValueError as exc:
        raise ConfigurationError(
            message="WEGOCOMPLY_MODE must be either 'mock' or 'live'.",
            details={"received": raw_mode},
        ) from exc


def _parse_cors_origins(raw_origins: str | None) -> tuple[str, ...]:
    if not raw_origins:
        return ("http://localhost:5173",)
    origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
    return origins or ("http://localhost:5173",)


def _resolve_model_path(raw_model_path: str | None) -> Path:
    if not raw_model_path:
        return (BASE_DIR.parent / "ml" / "aml_model.pkl").resolve()

    model_path = Path(raw_model_path)
    if model_path.is_absolute():
        return model_path
    return (BASE_DIR / model_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name="WeGoComply API",
        app_version="1.1.0",
        mode=_parse_mode(os.getenv("WEGOCOMPLY_MODE")),
        cors_origins=_parse_cors_origins(os.getenv("BACKEND_CORS_ORIGINS")),
        dojah_app_id=os.getenv("DOJAH_APP_ID"),
        dojah_api_key=os.getenv("DOJAH_API_KEY"),
        dojah_base_url=os.getenv("DOJAH_BASE_URL", "https://api.dojah.io").rstrip("/"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_face_endpoint=os.getenv("AZURE_FACE_ENDPOINT"),
        azure_face_key=os.getenv("AZURE_FACE_KEY"),
        azure_document_intelligence_endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
        azure_document_intelligence_key=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY"),
        aml_model_path=_resolve_model_path(os.getenv("AML_MODEL_PATH")),
    )


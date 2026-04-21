from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from core.errors import ConfigurationError
from core.secrets import SecretResolver

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class AppMode(str, Enum):
    MOCK = "mock"
    LIVE = "live"


class AuthMode(str, Enum):
    MOCK = "mock"
    AZURE_AD_B2C = "azure_ad_b2c"


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    mode: AppMode
    auth_mode: AuthMode
    cors_origins: tuple[str, ...]
    cors_methods: tuple[str, ...]
    cors_headers: tuple[str, ...]
    cors_allow_credentials: bool
    mock_auth_user_id: str
    mock_auth_email: str
    mock_auth_name: str
    mock_auth_roles: tuple[str, ...]
    azure_ad_b2c_client_id: str | None
    azure_ad_b2c_metadata_url: str | None
    azure_ad_b2c_issuer: str | None
    azure_ad_b2c_jwks_url: str | None
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window_seconds: int
    redis_url: str | None
    audit_log_path: Path
    azure_key_vault_url: str | None
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
    fraud_model_path: Path | None
    verifyme_secret_key: str | None
    verifyme_base_url: str
    # Identity provider configuration
    identity_mode: str
    identity_provider: str
    # NIMC configuration
    nimc_username: str | None
    nimc_password: str | None
    nimc_orgid: str | None
    nimc_base_url: str
    nimc_vpn_required: bool
    # NIMC Mock configuration
    nimc_mock_username: str
    nimc_mock_password: str
    nimc_mock_orgid: str
    nimc_mock_token_expiry_minutes: int

    @property
    def is_live(self) -> bool:
        return self.mode == AppMode.LIVE

    def validate_runtime(self) -> None:
        if "*" in self.cors_origins:
            raise ConfigurationError(
                message="Wildcard CORS origins are not allowed.",
                details={"origins": self.cors_origins},
            )
        if "*" in self.cors_methods:
            raise ConfigurationError(
                message="Wildcard CORS methods are not allowed.",
                details={"methods": self.cors_methods},
            )
        if "*" in self.cors_headers:
            raise ConfigurationError(
                message="Wildcard CORS headers are not allowed.",
                details={"headers": self.cors_headers},
            )

        if self.auth_mode == AuthMode.AZURE_AD_B2C:
            auth_missing = []
            if not self.azure_ad_b2c_client_id:
                auth_missing.append("AZURE_AD_B2C_CLIENT_ID")
            if not self.azure_ad_b2c_metadata_url and (not self.azure_ad_b2c_issuer or not self.azure_ad_b2c_jwks_url):
                auth_missing.extend(["AZURE_AD_B2C_METADATA_URL or AZURE_AD_B2C_ISSUER", "AZURE_AD_B2C_METADATA_URL or AZURE_AD_B2C_JWKS_URL"])
            if auth_missing:
                raise ConfigurationError(
                    message="Azure AD B2C authentication is enabled but not fully configured.",
                    details={"missing": auth_missing},
                )

        if self.is_live and self.auth_mode != AuthMode.AZURE_AD_B2C:
            raise ConfigurationError(
                message="Live mode requires Azure AD B2C authentication.",
                details={"auth_mode": self.auth_mode.value},
            )

        if self.rate_limit_enabled and self.is_live and not self.redis_url:
            raise ConfigurationError(
                message="Live mode requires REDIS_URL for rate limiting.",
            )

        if self.is_live and not self.verifyme_secret_key:
            raise ConfigurationError(
                message="Live mode requires VERIFYME_SECRET_KEY for NIN verification.",
            )

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


def _parse_auth_mode(raw_mode: str | None) -> AuthMode:
    mode = (raw_mode or AuthMode.MOCK.value).strip().lower()
    try:
        return AuthMode(mode)
    except ValueError as exc:
        raise ConfigurationError(
            message="AUTH_MODE must be either 'mock' or 'azure_ad_b2c'.",
            details={"received": raw_mode},
        ) from exc


def _parse_csv(raw_value: str | None, *, default: tuple[str, ...]) -> tuple[str, ...]:
    if not raw_value:
        return default
    values = tuple(value.strip() for value in raw_value.split(",") if value.strip())
    return values or default


def _parse_bool(raw_value: str | None, *, default: bool) -> bool:
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(
        message="Expected a boolean configuration value.",
        details={"received": raw_value},
    )


def _parse_positive_int(raw_value: str | None, *, default: int, field_name: str) -> int:
    if raw_value is None:
        return default
    try:
        parsed_value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            message=f"{field_name} must be an integer.",
            details={"received": raw_value},
        ) from exc
    if parsed_value <= 0:
        raise ConfigurationError(
            message=f"{field_name} must be greater than zero.",
            details={"received": raw_value},
        )
    return parsed_value


def _resolve_model_path(raw_model_path: str | None) -> Path:
    if not raw_model_path:
        return (BASE_DIR.parent / "ml" / "aml_model.pkl").resolve()

    model_path = Path(raw_model_path)
    if model_path.is_absolute():
        return model_path
    return (BASE_DIR / model_path).resolve()


def _resolve_audit_log_path(raw_log_path: str | None) -> Path:
    if not raw_log_path:
        return (BASE_DIR / "audit" / "audit.log.jsonl").resolve()

    log_path = Path(raw_log_path)
    if log_path.is_absolute():
        return log_path
    return (BASE_DIR / log_path).resolve()


def _resolve_fraud_model_path(raw_model_path: str | None) -> Path | None:
    if not raw_model_path:
        candidates = [
            (BASE_DIR / "artifacts" / "fraud_dashboard_model.joblib").resolve(),
            (BASE_DIR.parent / "artifacts" / "fraud_dashboard_model.joblib").resolve(),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None
    model_path = Path(raw_model_path)
    if model_path.is_absolute():
        return model_path
    return (BASE_DIR / model_path).resolve()


@lru_cache
def get_settings() -> Settings:
    secret_resolver = SecretResolver(os.getenv("AZURE_KEY_VAULT_URL"))
    return Settings(
        app_name="WeGoComply API",
        app_version="1.1.0",
        mode=_parse_mode(os.getenv("WEGOCOMPLY_MODE")),
        auth_mode=_parse_auth_mode(os.getenv("AUTH_MODE")),
        cors_origins=_parse_csv(os.getenv("BACKEND_CORS_ORIGINS"), default=("http://localhost:5173",)),
        cors_methods=_parse_csv(os.getenv("BACKEND_CORS_ALLOWED_METHODS"), default=("GET", "POST", "OPTIONS")),
        cors_headers=_parse_csv(
            os.getenv("BACKEND_CORS_ALLOWED_HEADERS"),
            default=(
                "Authorization",
                "Content-Type",
                "X-Request-ID",
                "X-Mock-User",
                "X-Mock-Email",
                "X-Mock-Name",
                "X-Mock-Roles",
            ),
        ),
        cors_allow_credentials=_parse_bool(os.getenv("BACKEND_CORS_ALLOW_CREDENTIALS"), default=True),
        mock_auth_user_id=os.getenv("MOCK_AUTH_USER_ID", "demo-admin"),
        mock_auth_email=os.getenv("MOCK_AUTH_EMAIL", "admin@wegocomply.local"),
        mock_auth_name=os.getenv("MOCK_AUTH_NAME", "Demo Admin"),
        mock_auth_roles=_parse_csv(os.getenv("MOCK_AUTH_ROLES"), default=("admin",)),
        azure_ad_b2c_client_id=os.getenv("AZURE_AD_B2C_CLIENT_ID"),
        azure_ad_b2c_metadata_url=os.getenv("AZURE_AD_B2C_METADATA_URL"),
        azure_ad_b2c_issuer=os.getenv("AZURE_AD_B2C_ISSUER"),
        azure_ad_b2c_jwks_url=os.getenv("AZURE_AD_B2C_JWKS_URL"),
        rate_limit_enabled=_parse_bool(os.getenv("RATE_LIMIT_ENABLED"), default=True),
        rate_limit_requests=_parse_positive_int(os.getenv("RATE_LIMIT_REQUESTS"), default=60, field_name="RATE_LIMIT_REQUESTS"),
        rate_limit_window_seconds=_parse_positive_int(
            os.getenv("RATE_LIMIT_WINDOW_SECONDS"),
            default=60,
            field_name="RATE_LIMIT_WINDOW_SECONDS",
        ),
        redis_url=os.getenv("REDIS_URL"),
        audit_log_path=_resolve_audit_log_path(os.getenv("AUDIT_LOG_PATH")),
        azure_key_vault_url=os.getenv("AZURE_KEY_VAULT_URL"),
        dojah_app_id=secret_resolver.resolve("DOJAH_APP_ID"),
        dojah_api_key=secret_resolver.resolve("DOJAH_API_KEY"),
        dojah_base_url=os.getenv("DOJAH_BASE_URL", "https://api.dojah.io").rstrip("/"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_key=secret_resolver.resolve("AZURE_OPENAI_KEY"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_face_endpoint=os.getenv("AZURE_FACE_ENDPOINT"),
        azure_face_key=secret_resolver.resolve("AZURE_FACE_KEY"),
        azure_document_intelligence_endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
        azure_document_intelligence_key=secret_resolver.resolve("AZURE_DOCUMENT_INTELLIGENCE_KEY"),
        aml_model_path=_resolve_model_path(os.getenv("AML_MODEL_PATH")),
        fraud_model_path=_resolve_fraud_model_path(os.getenv("FRAUD_MODEL_PATH")),
        # Identity provider configuration
        identity_mode=os.getenv("IDENTITY_MODE", "mock"),
        identity_provider=os.getenv("IDENTITY_PROVIDER", "mock"),
        # VerifyMe configuration
        verifyme_secret_key=secret_resolver.resolve("VERIFYME_SECRET_KEY"),
        verifyme_base_url=os.getenv("VERIFYME_BASE_URL", "https://vapi.verifyme.ng/v1/verifications/identities"),
        # NIMC configuration
        nimc_username=os.getenv("NIMC_USERNAME"),
        nimc_password=secret_resolver.resolve("NIMC_PASSWORD"),
        nimc_orgid=os.getenv("NIMC_ORGID"),
        nimc_base_url=os.getenv("NIMC_BASE_URL", "https://api.nimc.gov.ng"),
        nimc_vpn_required=os.getenv("NIMC_VPN_REQUIRED", "true").lower() == "true",
        # NIMC Mock configuration
        nimc_mock_username=os.getenv("NIMC_MOCK_USERNAME", "demo_user"),
        nimc_mock_password=os.getenv("NIMC_MOCK_PASSWORD", "demo_pass"),
        nimc_mock_orgid=os.getenv("NIMC_MOCK_ORGID", "demo_org"),
        nimc_mock_token_expiry_minutes=_parse_positive_int(os.getenv("NIMC_MOCK_TOKEN_EXPIRY_MINUTES"), default=30, field_name="NIMC_MOCK_TOKEN_EXPIRY_MINUTES"),
    )

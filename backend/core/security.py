from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import httpx
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import AuthMode, Settings, get_settings
from core.errors import AuthenticationError, AuthorizationError, ConfigurationError
from schemas.security import AuthenticatedUser, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


class MockIdentityProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authenticate(
        self,
        request: Request,
        _: HTTPAuthorizationCredentials | None = None,
    ) -> AuthenticatedUser:
        roles_header = request.headers.get("X-Mock-Roles")
        raw_roles = roles_header.split(",") if roles_header else list(self.settings.mock_auth_roles)
        roles = _normalize_roles(raw_roles)
        if not roles:
            raise AuthenticationError("No mock roles were provided for the request.")

        user = AuthenticatedUser(
            user_id=request.headers.get("X-Mock-User", self.settings.mock_auth_user_id),
            email=request.headers.get("X-Mock-Email", self.settings.mock_auth_email),
            display_name=request.headers.get("X-Mock-Name", self.settings.mock_auth_name),
            roles=roles,
            auth_mode=self.settings.auth_mode.value,
        )
        request.state.current_user = user
        return user


class AzureADB2CIdentityProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._metadata: dict[str, str] | None = None
        self._jwks_client = None

    def authenticate(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> AuthenticatedUser:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise AuthenticationError("A bearer access token is required.")

        metadata = self._get_metadata()
        try:
            signing_key = self._get_jwks_client(metadata["jwks_uri"]).get_signing_key_from_jwt(credentials.credentials)
            payload = jwt.decode(
                credentials.credentials,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.settings.azure_ad_b2c_client_id,
                issuer=metadata["issuer"],
                options={"require": ["exp", "iat", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("The supplied access token is invalid or expired.") from exc

        roles = _normalize_roles(_extract_roles(payload))
        if not roles:
            raise AuthorizationError("The authenticated user has no assigned application roles.")

        user = AuthenticatedUser(
            user_id=str(payload.get("oid") or payload.get("sub") or ""),
            email=_extract_email(payload),
            display_name=payload.get("name"),
            roles=roles,
            auth_mode=self.settings.auth_mode.value,
            token_claims=payload,
        )
        if not user.user_id:
            raise AuthenticationError("The access token does not contain a usable subject identifier.")

        request.state.current_user = user
        return user

    def _get_metadata(self) -> dict[str, str]:
        if self._metadata is not None:
            return self._metadata

        if self.settings.azure_ad_b2c_metadata_url:
            try:
                response = httpx.get(self.settings.azure_ad_b2c_metadata_url, timeout=10)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                raise ConfigurationError(
                    message="Unable to fetch Azure AD B2C OpenID metadata.",
                    details={"metadata_url": self.settings.azure_ad_b2c_metadata_url},
                ) from exc

            issuer = data.get("issuer")
            jwks_uri = data.get("jwks_uri")
        else:
            issuer = self.settings.azure_ad_b2c_issuer
            jwks_uri = self.settings.azure_ad_b2c_jwks_url

        if not issuer or not jwks_uri:
            raise ConfigurationError(
                message="Azure AD B2C auth requires an issuer and JWKS URI.",
            )

        self._metadata = {"issuer": issuer, "jwks_uri": jwks_uri}
        return self._metadata

    def _get_jwks_client(self, jwks_uri: str) -> jwt.PyJWKClient:
        if self._jwks_client is None:
            self._jwks_client = jwt.PyJWKClient(jwks_uri)
        return self._jwks_client


@lru_cache
def get_identity_provider():
    settings = get_settings()
    if settings.auth_mode == AuthMode.MOCK:
        return MockIdentityProvider(settings)
    return AzureADB2CIdentityProvider(settings)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    provider = get_identity_provider()
    return provider.authenticate(request, credentials)


def require_roles(*allowed_roles: UserRole):
    def dependency(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not current_user.has_any_role(allowed_roles):
            raise AuthorizationError(
                f"Access denied. Required roles: {', '.join(role.value for role in allowed_roles)}."
            )
        return current_user

    return dependency


def _extract_roles(payload: dict) -> list[str]:
    candidates = (
        payload.get("roles"),
        payload.get("role"),
        payload.get("app_roles"),
        payload.get("extension_Roles"),
        payload.get("extension_roles"),
    )
    for candidate in candidates:
        if not candidate:
            continue
        if isinstance(candidate, str):
            return [candidate]
        if isinstance(candidate, Iterable):
            return [str(item) for item in candidate]
    return []


def _extract_email(payload: dict) -> str | None:
    emails = payload.get("emails")
    if isinstance(emails, list) and emails:
        return str(emails[0])
    return payload.get("preferred_username") or payload.get("email")


def _normalize_roles(raw_roles: Iterable[str]) -> list[UserRole]:
    roles: list[UserRole] = []
    for raw_role in raw_roles:
        normalized = raw_role.strip().lower().replace("-", "_").replace(" ", "_")
        if not normalized:
            continue
        try:
            role = UserRole(normalized)
        except ValueError:
            continue
        if role not in roles:
            roles.append(role)
    return roles

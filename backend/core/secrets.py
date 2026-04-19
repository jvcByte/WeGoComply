from __future__ import annotations

import os

from core.errors import ConfigurationError


class SecretResolver:
    def __init__(self, key_vault_url: str | None) -> None:
        self.key_vault_url = key_vault_url.rstrip("/") if key_vault_url else None
        self._client = None
        self._cache: dict[str, str] = {}

    def resolve(self, env_name: str, *, default: str | None = None) -> str | None:
        direct_value = os.getenv(env_name)
        if direct_value:
            return direct_value

        secret_name = os.getenv(f"{env_name}_SECRET_NAME")
        if not secret_name:
            return default

        return self._get_secret(secret_name)

    def _get_secret(self, secret_name: str) -> str:
        cached_value = self._cache.get(secret_name)
        if cached_value is not None:
            return cached_value

        client = self._get_client()
        try:
            value = client.get_secret(secret_name).value
        except Exception as exc:
            raise ConfigurationError(
                message="Unable to resolve a secret from Azure Key Vault.",
                details={"secret_name": secret_name},
            ) from exc

        if not value:
            raise ConfigurationError(
                message="Azure Key Vault returned an empty secret value.",
                details={"secret_name": secret_name},
            )

        self._cache[secret_name] = value
        return value

    def _get_client(self):
        if not self.key_vault_url:
            raise ConfigurationError(
                message="AZURE_KEY_VAULT_URL must be set when using Key Vault-backed secrets.",
            )

        if self._client is None:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
            except ImportError as exc:
                raise ConfigurationError(
                    message="Azure Key Vault dependencies are not installed.",
                ) from exc

            self._client = SecretClient(
                vault_url=self.key_vault_url,
                credential=DefaultAzureCredential(),
            )

        return self._client

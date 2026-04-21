"""
Identity verification services package.

This package provides a provider-agnostic architecture for identity verification,
supporting multiple providers through a unified interface.
"""

from .provider_factory import get_identity_factory, initialize_identity_providers
from .providers.base import IdentityProvider, ProviderError
from .providers.dojah_provider import DojahProvider
from .providers.verifyme_provider import VerifyMeProvider
from .providers.mock_provider import MockProvider
from .providers.nimc_provider import NIMCProvider

__all__ = [
    "get_identity_factory",
    "initialize_identity_providers",
    "IdentityProvider",
    "ProviderError",
    "DojahProvider",
    "VerifyMeProvider", 
    "MockProvider",
    "NIMCProvider",
]

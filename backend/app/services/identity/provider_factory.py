"""
Identity verification provider factory.

This module provides a centralized factory for creating and managing
identity verification providers based on configuration.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
from functools import lru_cache

from app.services.identity.providers.base import IdentityProvider, ProviderConfig, ProviderError
from app.services.identity.providers.dojah_provider import DojahProvider
from app.services.identity.providers.verifyme_provider import VerifyMeProvider
from app.services.identity.providers.mock_provider import MockProvider
from app.services.identity.providers.nimc_mock_provider import NIMCMockProvider
from app.schemas.identity import ProviderConfig as ProviderConfigSchema

logger = logging.getLogger(__name__)


class IdentityProviderFactory:
    """Factory for creating and managing identity verification providers"""
    
    def __init__(self) -> None:
        self._providers: Dict[str, IdentityProvider] = {}
        self._configs: Dict[str, ProviderConfig] = {}
        self._initialized = False
    
    def initialize(self, configs: List[ProviderConfigSchema]) -> None:
        """
        Initialize providers with configuration
        
        Args:
            configs: List of provider configurations
        """
        if self._initialized:
            logger.warning("IdentityProviderFactory already initialized")
            return
        
        logger.info(f"Initializing IdentityProviderFactory with {len(configs)} providers")
        
        for config in configs:
            try:
                provider_config = ProviderConfig(
                    name=config.name,
                    enabled=config.enabled,
                    config=config.config,
                )
                
                provider = self._create_provider(provider_config)
                if provider:
                    self._providers[config.name.lower()] = provider
                    self._configs[config.name.lower()] = provider_config
                    logger.info(f"Initialized provider: {config.name}")
                else:
                    logger.error(f"Failed to create provider: {config.name}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize provider {config.name}: {e}")
                continue
        
        self._initialized = True
        logger.info(f"IdentityProviderFactory initialized with {len(self._providers)} providers")
    
    def get_provider(self, provider_name: Optional[str] = None) -> IdentityProvider:
        """
        Get provider by name or return primary provider
        
        Args:
            provider_name: Name of provider to retrieve
            
        Returns:
            IdentityProvider instance
            
        Raises:
            ProviderError: If provider not found or not enabled
        """
        if not self._initialized:
            raise ProviderError(
                "ProviderFactory not initialized",
                "factory",
                "not_initialized"
            )
        
        # If no provider specified, return the first enabled provider
        if not provider_name:
            for name, config in self._configs.items():
                if config.enabled:
                    logger.info(f"Using default provider: {name}")
                    return self._providers[name]
            
            raise ProviderError(
                "No enabled identity providers available",
                "factory",
                "no_providers_available"
            )
        
        # Look up specific provider
        provider_key = provider_name.lower()
        if provider_key not in self._providers:
            available = list(self._providers.keys())
            raise ProviderError(
                f"Provider '{provider_name}' not found. Available: {available}",
                "factory",
                "provider_not_found"
            )
        
        provider = self._providers[provider_key]
        config = self._configs[provider_key]
        
        if not config.enabled:
            raise ProviderError(
                f"Provider '{provider_name}' is disabled",
                "factory",
                "provider_disabled"
            )
        
        logger.info(f"Using provider: {provider_name}")
        return provider
    
    def get_provider_for_operation(self, operation: str) -> IdentityProvider:
        """
        Get best provider for specific operation
        
        Args:
            operation: Operation to perform (verify_nin, verify_bvn, etc.)
            
        Returns:
            IdentityProvider instance that supports the operation
        """
        if not self._initialized:
            raise ProviderError(
                "ProviderFactory not initialized",
                "factory",
                "not_initialized"
            )
        
        # Find providers that support the operation
        suitable_providers = []
        for name, provider in self._providers.items():
            config = self._configs[name]
            if config.enabled and operation in provider.get_supported_operations():
                suitable_providers.append((name, provider, config.priority))
        
        if not suitable_providers:
            raise ProviderError(
                f"No providers support operation: {operation}",
                "factory",
                "operation_not_supported"
            )
        
        # Sort by priority (lower number = higher priority)
        suitable_providers.sort(key=lambda x: x[2])
        selected_name, selected_provider, _ = suitable_providers[0]
        
        logger.info(f"Selected provider '{selected_name}' for operation '{operation}'")
        return selected_provider
    
    def get_all_providers(self) -> List[Dict[str, any]]:
        """
        Get information about all configured providers
        
        Returns:
            List of provider information dictionaries
        """
        providers_info = []
        for name, provider in self._providers.items():
            config = self._configs[name]
            info = provider.get_provider_info()
            info.update({
                "enabled": config.enabled,
                "priority": config.priority
            })
            providers_info.append(info)
        
        return providers_info
    
    def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all enabled providers
        
        Returns:
            Dictionary mapping provider names to health status
        """
        health_status = {}
        
        for name, provider in self._providers.items():
            config = self._configs[name]
            if config.enabled:
                try:
                    health_status[name] = provider.is_healthy()
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    health_status[name] = False
            else:
                health_status[name] = False
        
        return health_status
    
    def _create_provider(self, config: ProviderConfig) -> Optional[IdentityProvider]:
        """
        Create provider instance based on configuration
        
        Args:
            config: Provider configuration
            
        Returns:
            IdentityProvider instance or None if creation fails
        """
        provider_name = config.name.lower()
        
        try:
            if provider_name == "dojah":
                return DojahProvider(config)
            elif provider_name == "verifyme":
                return VerifyMeProvider(config)
            elif provider_name == "mock":
                return MockProvider(config)
            elif provider_name == "nimc":
                # NIMC provider not implemented yet
                logger.warning("NIMC provider not implemented yet")
                return None
            elif provider_name == "nimc_mock":
                return NIMCMockProvider()
            else:
                logger.error(f"Unknown provider: {provider_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create provider {provider_name}: {e}")
            return None


# Global factory instance
_factory: Optional[IdentityProviderFactory] = None


@lru_cache()
def get_identity_factory() -> IdentityProviderFactory:
    """
    Get singleton instance of IdentityProviderFactory
    
    Returns:
        IdentityProviderFactory instance
    """
    global _factory
    if _factory is None:
        _factory = IdentityProviderFactory()
    return _factory


def initialize_identity_providers(configs: List[ProviderConfigSchema]) -> None:
    """
    Initialize the global identity provider factory
    
    Args:
        configs: List of provider configurations
    """
    factory = get_identity_factory()
    factory.initialize(configs)

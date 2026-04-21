"""
Identity verification service.

This module provides high-level identity verification operations
using the provider-agnostic architecture.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.services.identity import get_identity_factory
from app.schemas.identity import (
    IdentityRequest,
    IdentityResponse,
    ProviderConfig,
    ProviderHealth
)
from core.config import get_settings

logger = logging.getLogger(__name__)


class IdentityService:
    """High-level identity verification service"""
    
    def __init__(self) -> None:
        self.factory = get_identity_factory()
        self.settings = get_settings()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize identity providers from configuration"""
        if self._initialized:
            return
        
        # Create provider configurations
        configs = self._create_provider_configs()
        
        # Initialize factory
        self.factory.initialize(configs)
        self._initialized = True
        
        logger.info(f"IdentityService initialized with {len(configs)} providers")
    
    async def verify_identity(
        self, 
        request: IdentityRequest,
        provider_name: Optional[str] = None
    ) -> IdentityResponse:
        """
        Verify identity using specified or best provider
        
        Args:
            request: Identity verification request
            provider_name: Specific provider to use (optional)
            
        Returns:
            IdentityResponse: Verification result
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # Get provider
            if provider_name:
                provider = self.factory.get_provider(provider_name)
            else:
                provider = self.factory.get_provider_for_operation(
                    f"verify_{request.verification_type.value}"
                )
            
            # Perform verification
            if request.verification_type.value == "nin":
                return await provider.verify_nin(request)
            elif request.verification_type.value == "bvn":
                return await provider.verify_bvn(request)
            else:
                from app.services.identity.providers.base import ProviderError
                raise ProviderError(
                    f"Unsupported verification type: {request.verification_type.value}",
                    "service",
                    "unsupported_operation"
                )
                
        except Exception as e:
            logger.error(f"Identity verification failed: {e}")
            raise
    
    async def verify_face_match(
        self,
        selfie_image: bytes,
        reference_image: Optional[bytes] = None,
        provider_name: Optional[str] = None
    ) -> dict:
        """
        Perform face matching using specified or best provider
        
        Args:
            selfie_image: Selfie image bytes
            reference_image: Reference image bytes (optional)
            provider_name: Specific provider to use (optional)
            
        Returns:
            Dict containing face match results
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # Get provider
            if provider_name:
                provider = self.factory.get_provider(provider_name)
            else:
                provider = self.factory.get_provider_for_operation("verify_face_match")
            
            # Perform face matching
            return await provider.verify_face_match(selfie_image, reference_image)
            
        except Exception as e:
            logger.error(f"Face matching failed: {e}")
            raise
    
    def get_providers(self) -> List[dict]:
        """
        Get information about all configured providers
        
        Returns:
            List of provider information
        """
        if not self._initialized:
            self.initialize()
        
        return self.factory.get_all_providers()
    
    def check_provider_health(self) -> List[ProviderHealth]:
        """
        Check health of all providers
        
        Returns:
            List of provider health status
        """
        if not self._initialized:
            self.initialize()
        
        health_status = self.factory.health_check()
        
        # Convert to ProviderHealth format
        providers_health = []
        for name, healthy in health_status.items():
            provider_info = None
            for provider in self.get_providers():
                if provider["name"] == name:
                    provider_info = provider
                    break
            
            providers_health.append(ProviderHealth(
                provider=name,
                healthy=healthy,
                response_time_ms=None,  # Would be measured in real implementation
                last_check="2024-01-01T00:00:00Z",  # Would be actual timestamp
                supported_operations=provider_info["supported_operations"] if provider_info else [],
                error_message=None if healthy else "Health check failed"
            ))
        
        return providers_health
    
    def _create_provider_configs(self) -> List[ProviderConfig]:
        """
        Create provider configurations from environment settings
        
        Returns:
            List of ProviderConfig objects
        """
        configs = []
        
        # Mock provider (always enabled for development)
        mock_config = ProviderConfig(
            name="mock",
            enabled=True,
            priority=3,
            config={
                "always_succeed": True,
                "mock_data": {}
            }
        )
        configs.append(mock_config)
        
        # Dojah provider
        if self.settings.identity_mode == "live" and self.settings.dojah_api_key:
            dojah_config = ProviderConfig(
                name="dojah",
                enabled=True,
                priority=1,
                config={
                    "api_key": self.settings.dojah_api_key,
                    "app_id": self.settings.dojah_app_id,
                    "base_url": self.settings.dojah_base_url,
                    "timeout": 30
                }
            )
            configs.append(dojah_config)
        
        # VerifyMe provider
        if self.settings.identity_mode == "live" and self.settings.verifyme_secret_key:
            verifyme_config = ProviderConfig(
                name="verifyme",
                enabled=True,
                priority=2,
                config={
                    "secret_key": self.settings.verifyme_secret_key,
                    "base_url": self.settings.verifyme_base_url,
                    "timeout": 30
                }
            )
            configs.append(verifyme_config)
        
        # NIMC provider (placeholder for future implementation)
        if (self.settings.identity_mode == "live" and 
            all([self.settings.nimc_username, self.settings.nimc_password, self.settings.nimc_orgid])):
            nimc_config = ProviderConfig(
                name="nimc",
                enabled=False,  # Disabled until implemented
                priority=1,
                config={
                    "username": self.settings.nimc_username,
                    "password": self.settings.nimc_password,
                    "orgid": self.settings.nimc_orgid,
                    "base_url": self.settings.nimc_base_url,
                    "vpn_required": self.settings.nimc_vpn_required,
                    "timeout": 30
                }
            )
            configs.append(nimc_config)
        
        return configs

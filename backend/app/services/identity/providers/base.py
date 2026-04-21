"""
Base interface for identity verification providers.

This module defines the contract that all identity verification providers
must implement, ensuring consistency across different providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

from schemas.identity import IdentityRequest, IdentityResponse


@dataclass
class ProviderConfig:
    """Configuration for identity providers"""
    name: str
    enabled: bool
    config: Dict[str, Any]


class IdentityProvider(ABC):
    """
    Abstract base class for identity verification providers.
    
    All identity providers must implement this interface to ensure
    consistent behavior across different verification services.
    """
    
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = config.name
    
    @abstractmethod
    async def verify_nin(self, request: IdentityRequest) -> IdentityResponse:
        """
        Verify NIN (National Identification Number)
        
        Args:
            request: Identity verification request containing NIN and demographic data
            
        Returns:
            IdentityResponse: Standardized verification response
            
        Raises:
            ProviderError: If verification fails due to provider issues
        """
        pass
    
    @abstractmethod
    async def verify_bvn(self, request: IdentityRequest) -> IdentityResponse:
        """
        Verify BVN (Bank Verification Number)
        
        Args:
            request: Identity verification request containing BVN and demographic data
            
        Returns:
            IdentityResponse: Standardized verification response
            
        Raises:
            ProviderError: If verification fails due to provider issues
        """
        pass
    
    @abstractmethod
    async def verify_face_match(
        self, 
        selfie_image: bytes, 
        reference_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Perform facial recognition/matching
        
        Args:
            selfie_image: User selfie image bytes
            reference_image: Reference image from ID document (optional)
            
        Returns:
            Dict containing match results with confidence scores
            
        Raises:
            ProviderError: If face matching fails due to provider issues
        """
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if provider is healthy and accessible
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_operations(self) -> list[str]:
        """
        Get list of supported operations by this provider
        
        Returns:
            List of supported operation names
        """
        pass
    
    def mask_sensitive_data(self, data: str, mask_char: str = "*", visible_chars: int = 3) -> str:
        """
        Mask sensitive data for logging purposes
        
        Args:
            data: Sensitive data to mask
            mask_char: Character to use for masking
            visible_chars: Number of characters to keep visible at start
            
        Returns:
            Masked string suitable for logging
        """
        if len(data) <= visible_chars:
            return mask_char * len(data)
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information and capabilities
        
        Returns:
            Dict containing provider metadata
        """
        return {
            "name": self.name,
            "healthy": self.is_healthy(),
            "supported_operations": self.get_supported_operations(),
            "config": {
                "enabled": self.config.enabled,
                # Don't expose sensitive config in production
            }
        }


class ProviderError(Exception):
    """Custom exception for provider-specific errors"""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "error": self.message,
            "provider": self.provider,
            "error_code": self.error_code,
            "details": self.details
        }

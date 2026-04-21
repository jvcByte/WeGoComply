"""
Dojah identity verification provider.

This module implements the IdentityProvider interface for Dojah API,
providing NIN and BVN verification capabilities with facial matching.
"""

from __future__ import annotations

import httpx
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.services.identity.providers.base import IdentityProvider, ProviderConfig, ProviderError
from app.schemas.identity import (
    IdentityRequest, 
    IdentityResponse, 
    MatchScore, 
    IdentityData, 
    RiskAssessment,
    VerificationType
)

logger = logging.getLogger(__name__)


class DojahProvider(IdentityProvider):
    """Dojah identity verification provider implementation"""
    
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.api_key = config.config.get("api_key")
        self.app_id = config.config.get("app_id")
        self.base_url = config.config.get("base_url", "https://api.dojah.io")
        self.timeout = config.config.get("timeout", 30)
        
        if not self.api_key or not self.app_id:
            raise ProviderError(
                "Dojah provider requires api_key and app_id",
                "dojah",
                "missing_credentials"
            )
    
    async def verify_nin(self, request: IdentityRequest) -> IdentityResponse:
        """Verify NIN using Dojah API"""
        try:
            # Validate NIN format
            if not request.identifier or len(request.identifier) != 11:
                raise ProviderError(
                    "NIN must be 11 digits",
                    "dojah",
                    "invalid_nin_format"
                )
            
            url = f"{self.base_url}/v1/general/verification"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "AppId": self.app_id,
                "Content-Type": "application/json"
            }
            
            payload = {
                "nin": request.identifier
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 401:
                    raise ProviderError(
                        "Invalid Dojah credentials",
                        "dojah",
                        "authentication_failed"
                    )
                elif response.status_code == 404:
                    return self._create_not_found_response(request)
                elif response.status_code >= 500:
                    raise ProviderError(
                        "Dojah service unavailable",
                        "dojah",
                        "service_unavailable"
                    )
                
                data = response.json()
                return self._map_dojah_response(request, data, VerificationType.NIN)
                
        except httpx.TimeoutException:
            raise ProviderError(
                "Dojah API timeout",
                "dojah",
                "timeout"
            )
        except httpx.NetworkError as e:
            raise ProviderError(
                f"Network error: {e}",
                "dojah",
                "network_error"
            )
    
    async def verify_bvn(self, request: IdentityRequest) -> IdentityResponse:
        """Verify BVN using Dojah API"""
        try:
            # Validate BVN format
            if not request.identifier or len(request.identifier) != 11:
                raise ProviderError(
                    "BVN must be 11 digits",
                    "dojah",
                    "invalid_bvn_format"
                )
            
            url = f"{self.base_url}/v1/general/verification"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "AppId": self.app_id,
                "Content-Type": "application/json"
            }
            
            payload = {
                "bvn": request.identifier
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 401:
                    raise ProviderError(
                        "Invalid Dojah credentials",
                        "dojah",
                        "authentication_failed"
                    )
                elif response.status_code == 404:
                    return self._create_not_found_response(request)
                elif response.status_code >= 500:
                    raise ProviderError(
                        "Dojah service unavailable",
                        "dojah",
                        "service_unavailable"
                    )
                
                data = response.json()
                return self._map_dojah_response(request, data, VerificationType.BVN)
                
        except httpx.TimeoutException:
            raise ProviderError(
                "Dojah API timeout",
                "dojah",
                "timeout"
            )
        except httpx.NetworkError as e:
            raise ProviderError(
                f"Network error: {e}",
                "dojah",
                "network_error"
            )
    
    async def verify_face_match(
        self, 
        selfie_image: bytes, 
        reference_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Perform facial recognition using Dojah API"""
        try:
            url = f"{self.base_url}/v1/face/compare"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "AppId": self.app_id,
            }
            
            files = {}
            if selfie_image:
                files["selfie"] = ("selfie.jpg", selfie_image, "image/jpeg")
            if reference_image:
                files["reference"] = ("reference.jpg", reference_image, "image/jpeg")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, files=files)
                
                if response.status_code == 401:
                    raise ProviderError(
                        "Invalid Dojah credentials",
                        "dojah",
                        "authentication_failed"
                    )
                elif response.status_code >= 500:
                    raise ProviderError(
                        "Dojah face service unavailable",
                        "dojah",
                        "service_unavailable"
                    )
                
                data = response.json()
                return self._map_face_response(data)
                
        except httpx.TimeoutException:
            raise ProviderError(
                "Dojah face API timeout",
                "dojah",
                "timeout"
            )
        except httpx.NetworkError as e:
            raise ProviderError(
                f"Network error: {e}",
                "dojah",
                "network_error"
            )
    
    def is_healthy(self) -> bool:
        """Check if Dojah provider is healthy"""
        try:
            url = f"{self.base_url}/v1/general/verification"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "AppId": self.app_id,
            }
            
            # Use a test NIN that should return 404 (service is up)
            test_payload = {"nin": "00000000000"}
            
            with httpx.Client(timeout=10) as client:
                response = client.post(url, headers=headers, json=test_payload)
                # 404 means service is up, NIN not found
                return response.status_code in [404, 401, 400]
                
        except Exception:
            return False
    
    def get_supported_operations(self) -> list[str]:
        """Get list of supported operations"""
        return ["verify_nin", "verify_bvn", "verify_face_match"]
    
    def _create_not_found_response(self, request: IdentityRequest) -> IdentityResponse:
        """Create response for NIN/BVN not found"""
        return IdentityResponse(
            success=False,
            provider=self.name,
            verification_type=request.verification_type,
            identifier=request.identifier,
            match_score=MatchScore(),
            identity=IdentityData(),
            verification_reference=f"DOJAH_NOT_FOUND_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            error_message="Identity not found in Dojah database",
            error_code="not_found"
        )
    
    def _map_dojah_response(
        self, 
        request: IdentityRequest, 
        data: Dict[str, Any], 
        verification_type: VerificationType
    ) -> IdentityResponse:
        """Map Dojah response to standardized format"""
        try:
            entity = data.get("entity", {})
            
            # Extract identity data
            identity_data = IdentityData(
                nin=entity.get("nin"),
                bvn=entity.get("bvn"),
                firstname=entity.get("firstname"),
                lastname=entity.get("lastname"),
                middlename=entity.get("middlename"),
                phone=entity.get("phone"),
                email=entity.get("email"),
                gender=entity.get("gender"),
                birthdate=entity.get("dob"),
                photo_base64=entity.get("photo"),
                address={
                    "street": entity.get("residential_address"),
                    "city": entity.get("city"),
                    "state": entity.get("state"),
                    "country": entity.get("country")
                } if entity.get("residential_address") else None
            )
            
            # Create match score (Dojah doesn't provide field-level matching)
            match_score = MatchScore(
                firstname=None,  # Dojah doesn't provide this
                lastname=None,    # Dojah doesn't provide this
                dob=None,         # Dojah doesn't provide this
                overall_confidence=0.95 if data.get("status") == "success" else 0.0
            )
            
            # Risk assessment
            risk_assessment = RiskAssessment(
                risk_level="LOW" if data.get("status") == "success" else "HIGH",
                risk_score=0.1 if data.get("status") == "success" else 0.9,
                risk_factors=[],
                recommendations=[]
            )
            
            return IdentityResponse(
                success=data.get("status") == "success",
                provider=self.name,
                verification_type=verification_type,
                identifier=request.identifier,
                match_score=match_score,
                identity=identity_data,
                risk_assessment=risk_assessment,
                verification_reference=f"DOJAH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                raw_response=data
            )
            
        except Exception as e:
            logger.error(f"Error mapping Dojah response: {e}")
            raise ProviderError(
                "Error processing Dojah response",
                "dojah",
                "response_mapping_error",
                {"original_error": str(e)}
            )
    
    def _map_face_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map Dojah face comparison response"""
        return {
            "match": data.get("match", False),
            "confidence": data.get("confidence", 0.0),
            "similarity": data.get("similarity", 0.0),
            "raw_response": data
        }

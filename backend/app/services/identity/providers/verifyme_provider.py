"""
VerifyMe identity verification provider.

This module implements IdentityProvider interface for VerifyMe API,
providing NIN verification with demographic matching.
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


class VerifyMeProvider(IdentityProvider):
    """VerifyMe identity verification provider implementation"""
    
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.secret_key = config.config.get("secret_key")
        self.base_url = config.config.get("base_url", "https://vapi.verifyme.ng/v1/verifications/identities")
        self.timeout = config.config.get("timeout", 30)
        
        if not self.secret_key:
            raise ProviderError(
                "VerifyMe provider requires secret_key",
                "verifyme",
                "missing_credentials"
            )
    
    async def verify_nin(self, request: IdentityRequest) -> IdentityResponse:
        """Verify NIN using VerifyMe API"""
        try:
            # Validate NIN format
            if not request.identifier or len(request.identifier) != 11:
                raise ProviderError(
                    "NIN must be 11 digits",
                    "verifyme",
                    "invalid_nin_format"
                )
            
            # VerifyMe requires firstname, lastname, and dob
            if not all([request.firstname, request.lastname, request.dob]):
                raise ProviderError(
                    "VerifyMe requires firstname, lastname, and dob for NIN verification",
                    "verifyme",
                    "missing_required_fields"
                )
            
            url = f"{self.base_url}/nin/{request.identifier}"
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "firstname": request.firstname.strip(),
                "lastname": request.lastname.strip(),
                "dob": request.dob.strip()
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling VerifyMe API for NIN: {self.mask_sensitive_data(request.identifier)}")
                
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 400:
                    logger.error(f"VerifyMe 400: {response.text}")
                    raise ProviderError(
                        "Invalid request parameters",
                        "verifyme",
                        "invalid_request"
                    )
                elif response.status_code == 401:
                    logger.error("VerifyMe 401: Invalid API key")
                    raise ProviderError(
                        "Invalid VerifyMe credentials",
                        "verifyme",
                        "authentication_failed"
                    )
                elif response.status_code == 404:
                    logger.info(f"VerifyMe 404: NIN {self.mask_sensitive_data(request.identifier)} not found")
                    return self._create_not_found_response(request)
                elif response.status_code == 429:
                    logger.error("VerifyMe 429: Rate limit exceeded")
                    raise ProviderError(
                        "Rate limit exceeded. Please try again later",
                        "verifyme",
                        "rate_limit_exceeded"
                    )
                elif response.status_code >= 500:
                    logger.error(f"VerifyMe {response.status_code}: {response.text}")
                    raise ProviderError(
                        "VerifyMe service temporarily unavailable",
                        "verifyme",
                        "service_unavailable"
                    )
                
                data = response.json()
                logger.info(f"VerifyMe verification completed for NIN: {self.mask_sensitive_data(request.identifier)}")
                
                return self._map_verifyme_response(request, data)
                
        except httpx.TimeoutException:
            logger.error("VerifyMe API timeout")
            raise ProviderError(
                "Verification service timeout",
                "verifyme",
                "timeout"
            )
        except httpx.NetworkError as e:
            logger.error(f"VerifyMe network error: {e}")
            raise ProviderError(
                "Network error during verification",
                "verifyme",
                "network_error"
            )
    
    async def verify_bvn(self, request: IdentityRequest) -> IdentityResponse:
        """VerifyMe doesn't support BVN verification"""
        raise ProviderError(
            "VerifyMe provider does not support BVN verification",
            "verifyme",
            "unsupported_operation"
        )
    
    async def verify_face_match(
        self, 
        selfie_image: bytes, 
        reference_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """VerifyMe doesn't support face matching"""
        raise ProviderError(
            "VerifyMe provider does not support face matching",
            "verifyme",
            "unsupported_operation"
        )
    
    def is_healthy(self) -> bool:
        """Check if VerifyMe provider is healthy"""
        try:
            # Use a test endpoint or simple health check
            url = f"{self.base_url}/nin/10000000001"  # Test NIN
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "firstname": "John",
                "lastname": "Doe", 
                "dob": "17/01/1988"
            }
            
            with httpx.Client(timeout=10) as client:
                response = client.post(url, headers=headers, json=test_payload)
                # 404 means service is up, test NIN not found
                return response.status_code in [404, 401, 400]
                
        except Exception:
            return False
    
    def get_supported_operations(self) -> list[str]:
        """Get list of supported operations"""
        return ["verify_nin"]
    
    def _create_not_found_response(self, request: IdentityRequest) -> IdentityResponse:
        """Create response for NIN not found"""
        return IdentityResponse(
            success=False,
            provider=self.name,
            verification_type=request.verification_type,
            identifier=request.identifier,
            match_score=MatchScore(),
            identity=IdentityData(),
            verification_reference=f"VERIFYME_NOT_FOUND_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            error_message="NIN not found in VerifyMe database",
            error_code="not_found"
        )
    
    def _map_verifyme_response(
        self, 
        request: IdentityRequest, 
        data: Dict[str, Any]
    ) -> IdentityResponse:
        """Map VerifyMe response to standardized format"""
        try:
            # Extract data section
            response_data = data.get("data", {})
            
            # Extract field matches (handle both spellings)
            field_matches_raw = response_data.get("fieldMatches", {})
            
            # Create match score
            match_score = MatchScore(
                firstname=field_matches_raw.get("firstname") or field_matches_raw.get("firsname"),
                lastname=field_matches_raw.get("lastname"),
                dob=field_matches_raw.get("dob"),
                phone=None,  # VerifyMe doesn't provide phone matching
                email=None   # VerifyMe doesn't provide email matching
            )
            
            # Extract identity data
            identity_data = IdentityData(
                nin=str(response_data.get("nin", "")),
                firstname=response_data.get("firstname"),
                lastname=response_data.get("lastname"),
                middlename=response_data.get("middlename"),
                phone=response_data.get("phone"),
                gender=response_data.get("gender"),
                birthdate=response_data.get("birthdate"),
                photo_base64=response_data.get("photo"),
                document_number=response_data.get("nin"),
                issuing_authority="NIMC"
            )
            
            # Determine success based on status
            status = data.get("status", "").lower()
            success = status == "success"
            
            # Risk assessment
            risk_assessment = RiskAssessment(
                risk_level="LOW" if success else "HIGH",
                risk_score=0.1 if success else 0.9,
                risk_factors=["NIN verification failed"] if not success else [],
                recommendations=["Verify NIN manually"] if not success else []
            )
            
            return IdentityResponse(
                success=success,
                provider=self.name,
                verification_type=request.verification_type,
                identifier=request.identifier,
                match_score=match_score,
                identity=identity_data,
                risk_assessment=risk_assessment,
                verification_reference=f"VERIFYME_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                raw_response=data
            )
            
        except Exception as e:
            logger.error(f"Error mapping VerifyMe response: {e}")
            raise ProviderError(
                "Error processing VerifyMe response",
                "verifyme",
                "response_mapping_error",
                {"original_error": str(e)}
            )

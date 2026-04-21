"""
Mock identity verification provider.

This module implements IdentityProvider interface for testing and development,
providing deterministic responses without calling external APIs.
"""

from __future__ import annotations

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


class MockProvider(IdentityProvider):
    """Mock identity verification provider for testing"""
    
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.mock_data = config.config.get("mock_data", {})
        self.always_succeed = config.config.get("always_succeed", True)
        
        # Test data for known NINs/BVNs
        self.known_nins = {
            "10000000001": {
                "firstname": "John",
                "lastname": "Doe",
                "middlename": "Jane",
                "phone": "08066676673",
                "gender": "male",
                "dob": "17/01/1988",
                "photo": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            },
            "22222222222": {
                "firstname": "Jane",
                "lastname": "Smith",
                "middlename": "Mary",
                "phone": "08055512345",
                "gender": "female",
                "dob": "25/12/1990",
                "photo": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
        }
    
    async def verify_nin(self, request: IdentityRequest) -> IdentityResponse:
        """Mock NIN verification"""
        try:
            # Validate NIN format
            if not request.identifier or len(request.identifier) != 11:
                raise ProviderError(
                    "NIN must be 11 digits",
                    "mock",
                    "invalid_nin_format"
                )
            
            # Check if NIN is known
            known_data = self.known_nins.get(request.identifier)
            
            if known_data:
                # Simulate field matching
                match_score = MatchScore(
                    firstname=request.firstname == known_data["firstname"],
                    lastname=request.lastname == known_data["lastname"],
                    dob=request.dob == known_data["dob"],
                    overall_confidence=0.95
                )
                
                identity_data = IdentityData(
                    nin=request.identifier,
                    firstname=known_data["firstname"],
                    lastname=known_data["lastname"],
                    middlename=known_data["middlename"],
                    phone=known_data["phone"],
                    gender=known_data["gender"],
                    birthdate=known_data["dob"],
                    photo_base64=known_data["photo"],
                    document_number=request.identifier,
                    issuing_authority="NIMC"
                )
                
                risk_assessment = RiskAssessment(
                    risk_level="LOW",
                    risk_score=0.1,
                    risk_factors=[],
                    recommendations=[]
                )
                
                return IdentityResponse(
                    success=True,
                    provider=self.name,
                    verification_type=request.verification_type,
                    identifier=request.identifier,
                    match_score=match_score,
                    identity=identity_data,
                    risk_assessment=risk_assessment,
                    verification_reference=f"MOCK_SUCCESS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    timestamp=datetime.now().isoformat()
                )
            else:
                # Unknown NIN
                return self._create_not_found_response(request)
                
        except Exception as e:
            logger.error(f"Mock NIN verification error: {e}")
            raise ProviderError(
                "Mock verification error",
                "mock",
                "verification_error"
            )
    
    async def verify_bvn(self, request: IdentityRequest) -> IdentityResponse:
        """Mock BVN verification"""
        try:
            # Validate BVN format
            if not request.identifier or len(request.identifier) != 11:
                raise ProviderError(
                    "BVN must be 11 digits",
                    "mock",
                    "invalid_bvn_format"
                )
            
            # Use same mock data for BVN (in real system they'd be different)
            known_data = self.known_nins.get(request.identifier)
            
            if known_data:
                match_score = MatchScore(
                    firstname=request.firstname == known_data["firstname"],
                    lastname=request.lastname == known_data["lastname"],
                    overall_confidence=0.92
                )
                
                identity_data = IdentityData(
                    bvn=request.identifier,
                    firstname=known_data["firstname"],
                    lastname=known_data["lastname"],
                    middlename=known_data["middlename"],
                    phone=known_data["phone"],
                    gender=known_data["gender"],
                    birthdate=known_data["dob"],
                    photo_base64=known_data["photo"],
                    document_number=request.identifier,
                    issuing_authority="CBN"
                )
                
                risk_assessment = RiskAssessment(
                    risk_level="LOW",
                    risk_score=0.15,
                    risk_factors=[],
                    recommendations=[]
                )
                
                return IdentityResponse(
                    success=True,
                    provider=self.name,
                    verification_type=request.verification_type,
                    identifier=request.identifier,
                    match_score=match_score,
                    identity=identity_data,
                    risk_assessment=risk_assessment,
                    verification_reference=f"MOCK_SUCCESS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    timestamp=datetime.now().isoformat()
                )
            else:
                return self._create_not_found_response(request)
                
        except Exception as e:
            logger.error(f"Mock BVN verification error: {e}")
            raise ProviderError(
                "Mock verification error",
                "mock",
                "verification_error"
            )
    
    async def verify_face_match(
        self, 
        selfie_image: bytes, 
        reference_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Mock face matching"""
        try:
            # Simulate face matching with random confidence
            import random
            confidence = random.uniform(0.7, 0.98)
            match = confidence > 0.8
            
            return {
                "match": match,
                "confidence": confidence,
                "similarity": confidence,
                "provider": "mock",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Mock face matching error: {e}")
            raise ProviderError(
                "Mock face matching error",
                "mock",
                "face_match_error"
            )
    
    def is_healthy(self) -> bool:
        """Mock provider is always healthy"""
        return True
    
    def get_supported_operations(self) -> list[str]:
        """Get list of supported operations"""
        return ["verify_nin", "verify_bvn", "verify_face_match"]
    
    def _create_not_found_response(self, request: IdentityRequest) -> IdentityResponse:
        """Create response for NIN/BVN not found"""
        risk_assessment = RiskAssessment(
            risk_level="HIGH",
            risk_score=0.9,
            risk_factors=["Identity not found in database"],
            recommendations=["Verify identity manually", "Contact customer for correct ID"]
        )
        
        return IdentityResponse(
            success=False,
            provider=self.name,
            verification_type=request.verification_type,
            identifier=request.identifier,
            match_score=MatchScore(),
            identity=IdentityData(),
            risk_assessment=risk_assessment,
            verification_reference=f"MOCK_NOT_FOUND_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            error_message="Identity not found in mock database",
            error_code="not_found"
        )

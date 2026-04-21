"""
Unified identity verification schemas.

This module defines standardized request/response models for identity verification
across all providers, ensuring consistent API contracts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class VerificationType(str, Enum):
    """Supported verification types"""
    NIN = "nin"
    BVN = "bvn"
    FACE_MATCH = "face_match"


class IdentityRequest(BaseModel):
    """Standardized identity verification request"""
    verification_type: VerificationType
    identifier: str = Field(..., description="NIN, BVN, or other identifier")
    firstname: Optional[str] = Field(None, description="First name for verification")
    lastname: Optional[str] = Field(None, description="Last name for verification")
    dob: Optional[str] = Field(None, description="Date of birth in DD/MM/YYYY format")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    selfie_image: Optional[bytes] = Field(None, description="Selfie image for face matching")
    reference_image: Optional[bytes] = Field(None, description="Reference image from ID document")
    
    class Config:
        # Allow bytes for image data
        arbitrary_types_allowed = True


class MatchScore(BaseModel):
    """Standardized field matching scores"""
    firstname: Optional[bool] = None
    lastname: Optional[bool] = None
    dob: Optional[bool] = None
    phone: Optional[bool] = None
    email: Optional[bool] = None
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class IdentityData(BaseModel):
    """Standardized identity information"""
    nin: Optional[str] = None
    bvn: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    middlename: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    photo_base64: Optional[str] = None
    signature_base64: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    document_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    expiry_date: Optional[str] = None


class RiskAssessment(BaseModel):
    """Risk assessment results"""
    risk_level: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH)$")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class IdentityResponse(BaseModel):
    """Standardized identity verification response"""
    success: bool
    provider: str
    verification_type: VerificationType
    identifier: str
    match_score: MatchScore
    identity: IdentityData
    risk_assessment: Optional[RiskAssessment] = None
    verification_reference: Optional[str] = None
    timestamp: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    class Config:
        # For datetime serialization
        json_encoders = {
            # Add any custom encoders if needed
        }


class ProviderHealth(BaseModel):
    """Provider health check response"""
    provider: str
    healthy: bool
    response_time_ms: Optional[float] = None
    last_check: str
    supported_operations: List[str]
    error_message: Optional[str] = None


class VerificationHistory(BaseModel):
    """Verification history entry"""
    id: str
    provider: str
    verification_type: VerificationType
    identifier: str
    success: bool
    timestamp: str
    user_id: str
    risk_assessment: Optional[RiskAssessment] = None


class BulkVerificationRequest(BaseModel):
    """Request for bulk identity verification"""
    verifications: List[IdentityRequest]
    callback_url: Optional[str] = None
    priority: Optional[str] = Field("normal", pattern="^(low|normal|high)$")


class BulkVerificationResponse(BaseModel):
    """Response for bulk verification"""
    batch_id: str
    total_count: int
    processed_count: int
    successful_count: int
    failed_count: int
    results: List[IdentityResponse]
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class ProviderConfig(BaseModel):
    """Provider configuration model"""
    name: str
    enabled: bool
    priority: int = Field(1, ge=1, le=10)
    config: Dict[str, Any] = Field(default_factory=dict)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    timeout_seconds: int = Field(30, ge=5, le=300)

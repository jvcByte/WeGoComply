from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from schemas.common import BaseSchema


class VerifyMeNinRequest(BaseSchema):
    """Request body for VerifyMe NIN verification"""
    firstname: str = Field(..., min_length=1, max_length=100)
    lastname: str = Field(..., min_length=1, max_length=100)
    dob: str = Field(..., description="Date of birth in DD/MM/YYYY format")


class VerifyMeFieldMatches(BaseSchema):
    """Field matching results from VerifyMe"""
    firsname: Optional[bool] = None  # Note: VerifyMe misspells as "firsname"
    firstname: Optional[bool] = None
    lastname: Optional[bool] = None
    dob: Optional[bool] = None


class VerifyMeIdentityData(BaseSchema):
    """Identity data returned by VerifyMe"""
    nin: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    middlename: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    photo: Optional[str] = None  # Base64 encoded


class VerifyMeResponse(BaseSchema):
    """Raw response from VerifyMe API"""
    status: str
    data: Optional[Dict[str, Any]] = None
    code: Optional[str] = None
    message: Optional[str] = None


class NormalizedMatchScore(BaseSchema):
    """Normalized match scores for frontend consumption"""
    firstname: Optional[bool] = None
    lastname: Optional[bool] = None
    dob: Optional[bool] = None


class NormalizedIdentity(BaseSchema):
    """Normalized identity data for frontend consumption"""
    nin: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    middlename: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    photo_base64: Optional[str] = None


class VerifyMeNinVerificationResponse(BaseSchema):
    """Normalized response for NIN verification"""
    success: bool
    match_score: NormalizedMatchScore
    identity: NormalizedIdentity
    raw_message: Optional[str] = None
    verification_reference: Optional[str] = None

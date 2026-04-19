from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Form
from pydantic import Field

from schemas.common import BaseSchema


class KYCVerificationInput(BaseSchema):
    nin: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")
    bvn: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")

    @classmethod
    def as_form(
        cls,
        nin: Annotated[str, Form(...)],
        bvn: Annotated[str, Form(...)],
    ) -> "KYCVerificationInput":
        return cls(nin=nin, bvn=bvn)


class KYCRiskScoreRequest(BaseSchema):
    nin_verified: bool = False
    bvn_verified: bool = False
    face_match: bool = False
    face_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class KYCRiskScoreResponse(BaseSchema):
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


class KYCVerificationDetails(BaseSchema):
    nin_verified: bool
    bvn_verified: bool
    face_match: bool
    face_confidence: float = Field(..., ge=0.0, le=1.0)
    name: str = ""
    dob: str = ""
    phone: str = ""


class KYCVerificationResponse(BaseSchema):
    status: Literal["VERIFIED", "FAILED"]
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    details: KYCVerificationDetails


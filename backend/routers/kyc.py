from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from dependencies import get_kyc_service
from schemas.common import ErrorResponse
from schemas.kyc import (
    KYCVerificationInput,
    KYCVerificationResponse,
    KYCRiskScoreRequest,
    KYCRiskScoreResponse,
)
from services.kyc_service import KYCService

router = APIRouter()
ERROR_RESPONSES = {
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.post("/verify", response_model=KYCVerificationResponse, responses=ERROR_RESPONSES)
async def verify_customer(
    payload: Annotated[KYCVerificationInput, Depends(KYCVerificationInput.as_form)],
    selfie: UploadFile = File(...),
    service: KYCService = Depends(get_kyc_service),
) -> KYCVerificationResponse:
    return await service.verify_identity(payload, selfie)


@router.post("/risk-score", response_model=KYCRiskScoreResponse, responses=ERROR_RESPONSES)
async def get_risk_score(
    customer_data: KYCRiskScoreRequest,
    service: KYCService = Depends(get_kyc_service),
) -> KYCRiskScoreResponse:
    return service.get_risk_score(customer_data)

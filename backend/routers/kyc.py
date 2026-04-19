from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile

from core.masking import mask_identifier
from core.security import require_roles
from dependencies import get_audit_service, get_kyc_service
from schemas.common import ErrorResponse
from schemas.kyc import (
    KYCVerificationInput,
    KYCVerificationResponse,
    KYCRiskScoreRequest,
    KYCRiskScoreResponse,
)
from schemas.security import AuthenticatedUser, UserRole
from services.audit_service import AuditService
from services.kyc_service import KYCService

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.post("/verify", response_model=KYCVerificationResponse, responses=ERROR_RESPONSES)
async def verify_customer(
    request: Request,
    payload: Annotated[KYCVerificationInput, Depends(KYCVerificationInput.as_form)],
    selfie: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: KYCService = Depends(get_kyc_service),
) -> KYCVerificationResponse:
    masked_nin = mask_identifier(payload.nin)
    masked_bvn = mask_identifier(payload.bvn)
    try:
        result = await service.verify_identity(payload, selfie)
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_identity",
            resource_type="kyc_case",
            resource_id=masked_nin,
            status="succeeded",
            details={
                "nin": masked_nin,
                "bvn": masked_bvn,
                "result": result.status,
                "risk_level": result.risk_level,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_identity",
            resource_type="kyc_case",
            resource_id=masked_nin,
            status="failed",
            details={
                "nin": masked_nin,
                "bvn": masked_bvn,
                "error": getattr(exc, "code", exc.__class__.__name__),
            },
        )
        raise


@router.post("/risk-score", response_model=KYCRiskScoreResponse, responses=ERROR_RESPONSES)
async def get_risk_score(
    request: Request,
    customer_data: KYCRiskScoreRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: KYCService = Depends(get_kyc_service),
) -> KYCRiskScoreResponse:
    try:
        result = service.get_risk_score(customer_data)
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.calculate_risk_score",
            resource_type="kyc_risk_assessment",
            status="succeeded",
            details={
                "risk_score": result.risk_score,
                "risk_level": result.risk_level,
                "nin_verified": customer_data.nin_verified,
                "bvn_verified": customer_data.bvn_verified,
                "face_match": customer_data.face_match,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.calculate_risk_score",
            resource_type="kyc_risk_assessment",
            status="failed",
            details={"error": getattr(exc, "code", exc.__class__.__name__)},
        )
        raise

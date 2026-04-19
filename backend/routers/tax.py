from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core.masking import mask_identifier
from core.security import require_roles
from dependencies import get_audit_service, get_tax_service
from schemas.common import ErrorResponse
from schemas.tax import BulkTINRequest, BulkTINResponse, TINRecord, TINVerificationResult
from schemas.security import AuthenticatedUser, UserRole
from services.audit_service import AuditService
from services.tax_service import TaxService

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.post("/verify-tin", response_model=TINVerificationResult, responses=ERROR_RESPONSES)
async def verify_single_tin(
    request: Request,
    record: TINRecord,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: TaxService = Depends(get_tax_service),
) -> TINVerificationResult:
    masked_tin = mask_identifier(record.tin)
    try:
        result = await service.verify_tin(record)
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="tax.verify_tin",
            resource_type="tin_record",
            resource_id=masked_tin,
            status="succeeded",
            details={
                "tin": masked_tin,
                "status": result.status,
                "match_confidence": result.match_confidence,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="tax.verify_tin",
            resource_type="tin_record",
            resource_id=masked_tin,
            status="failed",
            details={
                "tin": masked_tin,
                "error": getattr(exc, "code", exc.__class__.__name__),
            },
        )
        raise


@router.post("/bulk-verify", response_model=BulkTINResponse, responses=ERROR_RESPONSES)
async def bulk_tin_verification(
    http_request: Request,
    payload: BulkTINRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: TaxService = Depends(get_tax_service),
) -> BulkTINResponse:
    try:
        result = await service.bulk_verify_tin(payload.records)
        audit_service.log_action(
            request=http_request,
            actor=current_user,
            action="tax.bulk_verify_tin",
            resource_type="tin_batch",
            status="succeeded",
            details={
                "records_submitted": len(payload.records),
                "matched": result.matched,
                "failed": result.failed,
                "deadline_risk": result.deadline_risk,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=http_request,
            actor=current_user,
            action="tax.bulk_verify_tin",
            resource_type="tin_batch",
            status="failed",
            details={
                "records_submitted": len(payload.records),
                "error": getattr(exc, "code", exc.__class__.__name__),
            },
        )
        raise

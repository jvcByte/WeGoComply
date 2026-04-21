from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core.masking import mask_identifier
from core.security import require_roles
from dependencies import get_audit_service, get_tax_service
from schemas.common import ErrorResponse
from schemas.tax import (
    AnnualReturnRequest, AnnualReturnSummary,
    BillReportRequest, BillReportResponse,
    BulkTINRequest, BulkTINResponse,
    TINRecord, TINVerificationResult,
)
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
            request=request, actor=current_user,
            action="tax.verify_tin", resource_type="tin_record",
            resource_id=masked_tin, status="succeeded",
            details={"tin": masked_tin, "status": result.status, "match_confidence": result.match_confidence},
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request, actor=current_user,
            action="tax.verify_tin", resource_type="tin_record",
            resource_id=masked_tin, status="failed",
            details={"tin": masked_tin, "error": getattr(exc, "code", exc.__class__.__name__)},
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
            request=http_request, actor=current_user,
            action="tax.bulk_verify_tin", resource_type="tin_batch",
            status="succeeded",
            details={"records_submitted": len(payload.records), "matched": result.matched,
                     "failed": result.failed, "deadline_risk": result.deadline_risk},
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=http_request, actor=current_user,
            action="tax.bulk_verify_tin", resource_type="tin_batch",
            status="failed",
            details={"records_submitted": len(payload.records), "error": getattr(exc, "code", exc.__class__.__name__)},
        )
        raise


@router.post("/report-bill", response_model=BillReportResponse, responses=ERROR_RESPONSES)
async def report_bill(
    request: Request,
    payload: BillReportRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: TaxService = Depends(get_tax_service),
) -> BillReportResponse:
    """
    Submit a receipt/bill to FIRS ATRS.

    Flow:
      1. WeGoComply generates MD5 SID from bill fields
      2. POST to FIRS ATRS /v1/bills/report
      3. FIRS validates and returns UID (proof of submission)
      4. UID stored in audit log and returned to institution

    Payment types: C=Cash T=BankTransfer K=CreditCard D=DebitCard P=PostPayment O=Other
    """
    try:
        result = await service.report_bill(payload)
        audit_service.log_action(
            request=request, actor=current_user,
            action="tax.report_bill", resource_type="firs_bill",
            resource_id=payload.bill_number, status="succeeded",
            details={
                "bill_number": payload.bill_number,
                "total_value": payload.total_value,
                "firs_uid": result.uid,
                "status": result.status,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request, actor=current_user,
            action="tax.report_bill", resource_type="firs_bill",
            resource_id=payload.bill_number, status="failed",
            details={"bill_number": payload.bill_number, "error": getattr(exc, "code", exc.__class__.__name__)},
        )
        raise


@router.post("/annual-return", response_model=AnnualReturnSummary, responses=ERROR_RESPONSES)
async def get_annual_return(
    request: Request,
    payload: AnnualReturnRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: TaxService = Depends(get_tax_service),
) -> AnnualReturnSummary:
    """
    Generate annual tax return summary for a given institution and tax year.

    Aggregates all monthly FIRS bill submissions into a single report
    ready for upload to TaxPro Max (https://taxpromax.firs.gov.ng).

    Response includes:
      - Total revenue, VAT collected, VAT remitted
      - Monthly breakdown with FIRS UIDs as proof of submission
      - Outstanding filings (months with missing submissions)
      - Compliance status: COMPLIANT / OUTSTANDING_VAT / MISSING_SUBMISSIONS
      - taxpromax_upload_ready flag
    """
    try:
        result = await service.get_annual_return_summary(payload)
        audit_service.log_action(
            request=request, actor=current_user,
            action="tax.annual_return", resource_type="annual_return",
            resource_id=payload.institution_id, status="succeeded",
            details={
                "tax_year": payload.tax_year,
                "tin": mask_identifier(payload.tin),
                "compliance_status": result.compliance_status,
                "total_revenue": result.total_revenue,
                "vat_outstanding": result.vat_outstanding,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request, actor=current_user,
            action="tax.annual_return", resource_type="annual_return",
            resource_id=payload.institution_id, status="failed",
            details={"error": getattr(exc, "code", exc.__class__.__name__)},
        )
        raise


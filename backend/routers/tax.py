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


@router.post(
    "/verify-tin",
    response_model=TINVerificationResult,
    responses=ERROR_RESPONSES,
    summary="Verify Single TIN Against FIRS",
    description="""
Verify a single customer's Tax Identification Number (TIN) against the FIRS ATRS database.

**FIRS ATRS endpoint:** `GET /v1/taxpayer/verify?tin={tin}`

**Response statuses:**
- `MATCHED` — TIN found and name matches (confidence > 0.7)
- `NAME_MISMATCH` — TIN found but name doesn't match FIRS records
- `NOT_FOUND` — TIN not registered with FIRS

**If NOT_FOUND:** Direct customer to register free TIN at https://jtb.gov.ng (5 minutes with NIN).

**Mock mode:** TINs ending in `55` → NOT_FOUND · ending in `99` → NAME_MISMATCH · others → MATCHED.

**Regulatory basis:** Nigeria Tax Administration Act 2025 — all accounts must have verified TIN.

**Required roles:** `admin`, `compliance_officer`, `analyst`
""",
)
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


@router.post(
    "/bulk-verify",
    response_model=BulkTINResponse,
    responses=ERROR_RESPONSES,
    summary="Bulk TIN Verification",
    description="""
Verify multiple customer TINs against FIRS in a single request.

**Use case:** Institutions with large customer bases needing to meet the FIRS TIN mandate
before the April 1, 2026 deadline.

**Response includes:**
- Per-record status: MATCHED / NOT_FOUND / NAME_MISMATCH
- Overall match rate and deadline risk assessment
- `deadline_risk: HIGH` if match rate < 80%

**Recommended action for failed records:**
Send SMS: *"Register your free TIN at jtb.gov.ng using your NIN to avoid account restrictions."*

**Required roles:** `admin`, `compliance_officer`, `analyst`
""",
)
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


@router.post(
    "/report-bill",
    response_model=BillReportResponse,
    responses=ERROR_RESPONSES,
    summary="Submit Bill/Receipt to FIRS ATRS",
    description="""
Submit a receipt or bill to FIRS ATRS for real-time tax remittance reporting.

**FIRS ATRS endpoint:** `POST /v1/bills/report`

**Process:**
1. WeGoComply generates MD5 SID: `MD5(client_secret + vat_number + business_place + business_device + bill_number + bill_datetime + total_value)`
2. Full payload POSTed to FIRS ATRS with SID as `security_code`
3. FIRS validates SID and records the bill
4. FIRS returns `uid` (Unique Identifier) — **proof of submission**
5. UID stored in audit log and returned to institution

**Payment type codes:**
- `C` — Cash
- `T` — Bank Transfer
- `K` — Credit Card
- `D` — Debit Card
- `P` — Post Payment (credit)
- `O` — Other

**VAT rate:** 7.5% (Nigerian standard rate)

**Store the UID** — it is required for annual return reconciliation.

**Mock mode:** Returns `MOCK-UID-{bill_number}` without calling FIRS.

**Required roles:** `admin`, `compliance_officer`
""",
)
async def report_bill(
    request: Request,
    payload: BillReportRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: TaxService = Depends(get_tax_service),
) -> BillReportResponse:
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


@router.post(
    "/annual-return",
    response_model=AnnualReturnSummary,
    responses=ERROR_RESPONSES,
    summary="Generate Annual Tax Return Summary",
    description="""
Aggregate all monthly FIRS bill submissions for a tax year into a complete annual return
summary ready for upload to TaxPro Max.

**Process:**
1. WeGoComply queries all monthly bill submissions for the institution and tax year
2. Aggregates: total revenue, VAT collected, VAT remitted, outstanding VAT
3. Identifies months with missing FIRS submissions
4. Calculates compliance status
5. Returns TaxPro Max-ready summary

**Compliance statuses:**
- `COMPLIANT` — all VAT remitted, all months submitted → ready for TaxPro Max
- `OUTSTANDING_VAT` — VAT collected but not remitted → settle before filing
- `MISSING_SUBMISSIONS` — one or more months have no FIRS submission

**After generating:**
1. Resolve any outstanding VAT payments
2. Upload summary to https://taxpromax.firs.gov.ng
3. File Company Income Tax (CIT) return
4. Receive Tax Clearance Certificate (TCC)

**Annual CIT deadline:** June 30 each year.

**Required roles:** `admin`, `compliance_officer`
""",
)
async def get_annual_return(
    request: Request,
    payload: AnnualReturnRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: TaxService = Depends(get_tax_service),
) -> AnnualReturnSummary:
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


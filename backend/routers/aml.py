from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core.security import require_roles
from dependencies import get_aml_service, get_audit_service
from schemas.aml import AMLMonitorResponse, STRReportResponse, Transaction, TransactionBatchRequest
from schemas.common import ErrorResponse
from schemas.security import AuthenticatedUser, UserRole
from services.aml_service import AMLService
from services.audit_service import AuditService

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.post("/monitor", response_model=AMLMonitorResponse, responses=ERROR_RESPONSES)
async def monitor_transactions(
    request: Request,
    batch: TransactionBatchRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: AMLService = Depends(get_aml_service),
) -> AMLMonitorResponse:
    try:
        result = service.analyze_transactions(batch.transactions)
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="aml.monitor_transactions",
            resource_type="transaction_batch",
            status="succeeded",
            details={
                "total_analyzed": result.total_analyzed,
                "flagged_count": result.flagged_count,
                "clean_count": result.clean_count,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="aml.monitor_transactions",
            resource_type="transaction_batch",
            status="failed",
            details={"error": getattr(exc, "code", exc.__class__.__name__)},
        )
        raise


@router.post("/generate-str/{transaction_id}", response_model=STRReportResponse, responses=ERROR_RESPONSES)
async def create_str(
    request: Request,
    transaction_id: str,
    transaction: Transaction,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: AMLService = Depends(get_aml_service),
) -> STRReportResponse:
    try:
        result = await service.generate_str(transaction_id, transaction)
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="aml.generate_str",
            resource_type="transaction",
            resource_id=transaction_id,
            status="succeeded",
            details={
                "customer_id": transaction.customer_id,
                "report_reference": result.report_reference,
            },
        )
        return result
    except Exception as exc:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="aml.generate_str",
            resource_type="transaction",
            resource_id=transaction_id,
            status="failed",
            details={
                "customer_id": transaction.customer_id,
                "error": getattr(exc, "code", exc.__class__.__name__),
            },
        )
        raise

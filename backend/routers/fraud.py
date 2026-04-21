from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core.security import require_roles
from dependencies import get_audit_service, get_fraud_service
from schemas.common import ErrorResponse
from schemas.fraud import (
    FraudAnalysisResponse,
    FraudExplanationRequest,
    FraudExplanationResponse,
    FraudModelInfo,
    FraudTransactionBatchRequest,
)
from schemas.security import AuthenticatedUser, UserRole
from services.audit_service import AuditService
from services.fraud_service import FraudService

router = APIRouter()

ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.post("/analyze", response_model=FraudAnalysisResponse, responses=ERROR_RESPONSES)
async def analyze_fraud(
    request: Request,
    batch: FraudTransactionBatchRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    fraud_service: FraudService = Depends(get_fraud_service),
) -> FraudAnalysisResponse:
    """Analyze a batch of transactions for fraud using the hybrid ML model."""
    try:
        transactions = [tx.model_dump() for tx in batch.transactions]
        result = fraud_service.analyze_transactions(transactions)
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="fraud.analyze_transactions",
            resource_type="transaction_batch",
            status="succeeded",
            details={
                "total_analyzed": result["total_analyzed"],
                "high_risk_count": result["high_risk_count"],
            },
        )
        return FraudAnalysisResponse.model_validate(result)
    except Exception as exc:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="fraud.analyze_transactions",
            resource_type="transaction_batch",
            status="failed",
            details={"error": str(exc)},
        )
        raise


@router.post("/explain", response_model=FraudExplanationResponse, responses=ERROR_RESPONSES)
async def explain_fraud(
    request: Request,
    explanation_request: FraudExplanationRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    fraud_service: FraudService = Depends(get_fraud_service),
) -> FraudExplanationResponse:
    """Get ML-based explanation for why a transaction was flagged."""
    transaction = explanation_request.transaction.model_dump()
    result = fraud_service.explain_transaction(transaction)
    return FraudExplanationResponse.model_validate(result)


@router.get("/model-info", response_model=FraudModelInfo, responses=ERROR_RESPONSES)
async def get_model_info(
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    fraud_service: FraudService = Depends(get_fraud_service),
) -> FraudModelInfo:
    """Get metadata about the loaded fraud detection model."""
    result = fraud_service.get_model_info()
    return FraudModelInfo.model_validate(result)

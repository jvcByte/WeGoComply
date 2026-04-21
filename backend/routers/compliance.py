from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from core.security import require_roles
from dependencies import get_audit_service, get_compliance_service
from schemas.compliance import (
    AMLEMetrics,
    ComplianceScoreRequest,
    ComplianceScoreResponse,
    KYCMetrics,
    ReportingMetrics,
    TINMetrics,
)
from schemas.common import ErrorResponse
from schemas.security import AuthenticatedUser, UserRole
from services.audit_service import AuditService
from services.compliance_service import ComplianceService

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.post("/score", response_model=ComplianceScoreResponse, responses=ERROR_RESPONSES)
async def calculate_compliance_score(
    request: Request,
    payload: ComplianceScoreRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: ComplianceService = Depends(get_compliance_service),
) -> ComplianceScoreResponse:
    """Calculate overall compliance posture score across all 4 pillars"""
    try:
        result = service.calculate_overall_score(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="compliance.calculate_score",
            resource_type="compliance_posture",
            details={
                "overall_score": result.compliance_posture.overall_score,
                "compliance_level": result.compliance_posture.compliance_level,
                "kyc_score": result.compliance_posture.kyc_score.score,
                "aml_score": result.compliance_posture.aml_score.score,
                "tin_score": result.compliance_posture.tin_score.score,
                "reporting_score": result.compliance_posture.reporting_score.score,
            }
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="compliance.calculate_score",
            resource_type="compliance_posture",
            success=False,
            details={"error": str(e)}
        )
        raise


@router.get("/metrics/kyc", response_model=KYCMetrics, responses=ERROR_RESPONSES)
async def get_kyc_metrics(
    request: Request,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> KYCMetrics:
    """Get current KYC compliance metrics"""
    # This would typically fetch from database
    # For now, return mock data that matches real-world scenarios
    audit_service.log_action(
        request=request,
        actor=current_user,
        action="compliance.get_kyc_metrics",
        resource_type="compliance_metrics",
    )
    
    return KYCMetrics(
        total_customers=5000,
        verified_nin_customers=4500,
        verified_bvn_customers=4400,
        face_match_customers=4300,
        high_risk_customers_reviewed_24h=8,
        high_risk_customers_total=10,
        average_onboarding_time_minutes=2.5,
    )


@router.get("/metrics/aml", response_model=AMLEMetrics, responses=ERROR_RESPONSES)
async def get_aml_metrics(
    request: Request,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> AMLEMetrics:
    """Get current AML compliance metrics"""
    audit_service.log_action(
        request=request,
        actor=current_user,
        action="compliance.get_aml_metrics",
        resource_type="compliance_metrics",
    )
    
    return AMLEMetrics(
        total_transactions=50000,
        monitored_transactions=48500,
        flagged_transactions=125,
        flagged_reviewed_24h=110,
        str_filed_total=25,
        str_filed_on_time=23,
        false_negative_count=2,
    )


@router.get("/metrics/tin", response_model=TINMetrics, responses=ERROR_RESPONSES)
async def get_tin_metrics(
    request: Request,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> TINMetrics:
    """Get current TIN compliance metrics"""
    audit_service.log_action(
        request=request,
        actor=current_user,
        action="compliance.get_tin_metrics",
        resource_type="compliance_metrics",
    )
    
    return TINMetrics(
        total_customers=5000,
        verified_tin_customers=4550,
        accounts_restricted_missing_tin=50,
        days_until_firs_deadline=15,
    )


@router.get("/metrics/reporting", response_model=ReportingMetrics, responses=ERROR_RESPONSES)
async def get_reporting_metrics(
    request: Request,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> ReportingMetrics:
    """Get current regulatory reporting metrics"""
    audit_service.log_action(
        request=request,
        actor=current_user,
        action="compliance.get_reporting_metrics",
        resource_type="compliance_metrics",
    )
    
    return ReportingMetrics(
        total_required_actions=12,
        completed_actions=10,
        regulatory_updates_acknowledged=8,
        total_regulatory_updates=10,
        missed_deadlines=1,
    )

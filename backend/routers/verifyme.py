from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse

from core.security import require_roles
from dependencies import get_audit_service, get_verifyme_service
from schemas.common import ErrorResponse
from schemas.verifyme import VerifyMeNinVerificationResponse, VerifyMeNinRequest
from schemas.security import AuthenticatedUser, UserRole
from services.audit_service import AuditService
from services.verifyme_service import VerifyMeService

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.post("/verify-nin", response_model=VerifyMeNinVerificationResponse, responses=ERROR_RESPONSES)
async def verify_nin(
    request: Request,
    payload: VerifyMeNinRequest,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    service: VerifyMeService = Depends(get_verifyme_service),
) -> VerifyMeNinVerificationResponse:
    """
    Verify NIN using VerifyMe API
    
    This endpoint integrates with VerifyMe for Nigerian NIN verification.
    It accepts NIN, firstname, lastname, and DOB from the user and
    returns normalized verification results.
    """
    try:
        # Log the verification attempt
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="verifyme.verify_nin",
            resource_type="nin_verification",
            details={
                "nin": payload.nin[:6] + "******",  # Mask NIN in logs
                "firstname": payload.firstname,
                "lastname": payload.lastname,
                "dob": payload.dob,
            }
        )
        
        # Call VerifyMe service
        result = await service.verify_nin(
            nin=payload.nin,
            firstname=payload.firstname,
            lastname=payload.lastname,
            dob=payload.dob,
        )
        
        # Log successful verification
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="verifyme.verify_nin_completed",
            resource_type="nin_verification",
            details={
                "success": result.success,
                "verification_reference": result.verification_reference,
                "has_match_data": any([
                    result.match_score.firstname is not None,
                    result.match_score.lastname is not None,
                    result.match_score.dob is not None,
                ]),
            }
        )
        
        return result
        
    except Exception as e:
        # Log error
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="verifyme.verify_nin",
            resource_type="nin_verification",
            success=False,
            details={"error": str(e)}
        )
        
        # Return appropriate HTTP status
        if "Invalid input" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        elif "Invalid VerifyMe credentials" in str(e):
            raise HTTPException(status_code=500, detail="Identity verification service configuration error")
        elif "Rate limit exceeded" in str(e):
            raise HTTPException(status_code=429, detail="Too many verification requests. Please try again later.")
        elif "NIN not found" in str(e):
            # Return 200 with success=False for NIN not found
            return VerifyMeNinVerificationResponse(
                success=False,
                match_score=result.match_score if 'result' in locals() else None,
                identity=result.identity if 'result' in locals() else None,
                raw_message="NIN not found in verification system",
                verification_reference=f"NOT_FOUND_{payload.nin[:6]}******"
            )
        else:
            raise HTTPException(status_code=500, detail="Identity verification service temporarily unavailable")


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for VerifyMe integration"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "verifyme",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )

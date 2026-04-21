"""
Unified KYC verification routes.

This module provides the main KYC verification endpoint using the new
provider-agnostic architecture, replacing the old provider-specific routes.
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from core.security import require_roles
from dependencies import get_audit_service
from app.services.identity.service import IdentityService
from app.schemas.identity import (
    IdentityRequest, 
    IdentityResponse, 
    VerificationType,
    ProviderHealth
)
from schemas.security import AuthenticatedUser, UserRole
from services.audit_service import AuditService

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}

# Global identity service instance
_identity_service: Optional[IdentityService] = None


def get_identity_service() -> IdentityService:
    """Get singleton instance of IdentityService"""
    global _identity_service
    if _identity_service is None:
        _identity_service = IdentityService()
    return _identity_service


@router.post("/verify", response_model=IdentityResponse, responses=ERROR_RESPONSES)
async def verify_kyc(
    request: Request,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    audit_service: AuditService = Depends(get_audit_service),
    verification_type: str = Form(...),
    identifier: str = Form(...),
    firstname: Optional[str] = Form(None),
    lastname: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    selfie: Optional[UploadFile] = File(None),
    provider_name: Optional[str] = Form(None),
) -> IdentityResponse:
    """
    Unified KYC verification endpoint
    
    This endpoint replaces provider-specific endpoints and uses the
    provider-agnostic architecture to support multiple identity providers.
    
    Automatic provider selection:
    - If provider_name is specified, use that provider
    - Otherwise, select best provider for the verification type
    """
    try:
        # Create identity request
        identity_request = IdentityRequest(
            verification_type=VerificationType(verification_type.lower()),
            identifier=identifier.strip(),
            firstname=firstname.strip() if firstname else None,
            lastname=lastname.strip() if lastname else None,
            dob=dob.strip() if dob else None,
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            selfie_image=await selfie.read() if selfie else None
        )
        
        # Get identity service
        service = get_identity_service()
        
        # Log verification attempt
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_kyc_unified",
            resource_type="identity_verification",
            details={
                "verification_type": verification_type,
                "identifier": identifier[:3] + "******",  # Mask sensitive data
                "provider_requested": provider_name,
                "has_selfie": selfie is not None,
            }
        )
        
        # Perform verification
        result = await service.verify_identity(identity_request, provider_name)
        
        # Add face matching if selfie provided and verification was successful
        if (selfie and identity_request.selfie_image and 
            result.success and result.identity.photo_base64):
            try:
                face_result = await service.verify_face_match(
                    identity_request.selfie_image,
                    result.identity.photo_base64,
                    provider_name
                )
                
                # Update result with face match info
                if result.match_score:
                    result.match_score.overall_confidence = face_result.get("confidence", 0.0)
                
                # Log face match result
                audit_service.log_action(
                    request=request,
                    actor=current_user,
                    action="kyc.face_match_completed",
                    resource_type="identity_verification",
                    details={
                        "provider": result.provider,
                        "face_match_confidence": face_result.get("confidence", 0.0),
                        "face_match_success": face_result.get("match", False),
                    }
                )
                
            except Exception as e:
                # Log face matching error but don't fail the whole verification
                audit_service.log_action(
                    request=request,
                    actor=current_user,
                    action="kyc.face_match_failed",
                    resource_type="identity_verification",
                    success=False,
                    details={
                        "error": str(e),
                        "provider": result.provider,
                    }
                )
        
        # Log successful verification
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_kyc_completed_unified",
            resource_type="identity_verification",
            details={
                "success": result.success,
                "provider": result.provider,
                "verification_reference": result.verification_reference,
                "risk_level": result.risk_assessment.risk_level if result.risk_assessment else None,
                "has_face_match": result.match_score.overall_confidence is not None,
            }
        )
        
        return result
        
    except Exception as e:
        # Log error
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_kyc_unified",
            resource_type="identity_verification",
            success=False,
            details={"error": str(e)}
        )
        
        # Handle provider-specific errors
        error_message = str(e)
        
        if "configuration error" in error_message.lower():
            raise HTTPException(status_code=500, detail="Identity verification service configuration error")
        elif "invalid" in error_message.lower() and ("format" in error_message.lower() or "required" in error_message.lower()):
            raise HTTPException(status_code=422, detail=error_message)
        elif "unsupported" in error_message.lower():
            raise HTTPException(status_code=400, detail=error_message)
        elif "rate limit" in error_message.lower():
            raise HTTPException(status_code=429, detail="Too many verification requests. Please try again later.")
        elif "not found" in error_message.lower():
            # Return success=False for not found (not a server error)
            service = get_identity_service()
            return await service.verify_identity(
                IdentityRequest(
                    verification_type=VerificationType(verification_type.lower()),
                    identifier=identifier.strip(),
                ),
                provider_name
            )
        elif "unavailable" in error_message.lower() or "timeout" in error_message.lower():
            raise HTTPException(status_code=503, detail="Identity verification service temporarily unavailable")
        else:
            raise HTTPException(status_code=500, detail="Identity verification service error")


@router.get("/providers", response_model=list[dict])
async def get_providers(
    request: Request,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> list[dict]:
    """Get list of configured identity providers"""
    try:
        service = get_identity_service()
        providers = service.get_providers()
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.list_providers_unified",
            resource_type="identity_providers",
        )
        
        return providers
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.list_providers_unified",
            resource_type="identity_providers",
            success=False,
            details={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail="Failed to retrieve providers")


@router.get("/health", response_model=list[ProviderHealth])
async def health_check(
    request: Request,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    audit_service: AuditService = Depends(get_audit_service),
) -> list[ProviderHealth]:
    """Check health of all identity providers"""
    try:
        service = get_identity_service()
        providers_health = service.check_provider_health()
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.health_check_unified",
            resource_type="identity_providers",
            details={
                "healthy_providers": [p.provider for p in providers_health if p.healthy],
                "unhealthy_providers": [p.provider for p in providers_health if not p.healthy],
            }
        )
        
        return providers_health
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.health_check_unified",
            resource_type="identity_providers",
            success=False,
            details={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail="Failed to check provider health")

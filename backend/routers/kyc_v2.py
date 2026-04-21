"""
KYC verification routes v2 - Provider-agnostic implementation.

This module provides KYC verification endpoints using the new provider-agnostic
architecture, supporting multiple identity providers through a unified interface.
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from core.security import require_roles
from dependencies import get_audit_service
from app.services.identity import get_identity_factory
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


@router.post("/verify", response_model=IdentityResponse, responses=ERROR_RESPONSES)
async def verify_identity(
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
    Verify identity using configured provider
    
    This endpoint uses the provider factory to select the appropriate
    identity verification provider based on configuration and operation type.
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
        
        # Get appropriate provider
        factory = get_identity_factory()
        provider = factory.get_provider_for_operation(f"verify_{verification_type.lower()}")
        
        # Log verification attempt
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_identity_v2",
            resource_type="identity_verification",
            details={
                "verification_type": verification_type,
                "identifier": provider.mask_sensitive_data(identifier),
                "provider": provider.name,
                "user_provided_provider": provider_name,
            }
        )
        
        # Perform verification
        if verification_type.lower() == "nin":
            result = await provider.verify_nin(identity_request)
        elif verification_type.lower() == "bvn":
            result = await provider.verify_bvn(identity_request)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported verification type: {verification_type}"
            )
        
        # Add face matching if selfie provided
        if selfie and identity_request.selfie_image:
            try:
                face_result = await provider.verify_face_match(
                    identity_request.selfie_image,
                    result.identity.photo_base64
                )
                
                # Update result with face match info
                result.match_score.overall_confidence = face_result.get("confidence", 0.0)
                
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
                        "provider": provider.name,
                    }
                )
        
        # Log successful verification
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_identity_completed_v2",
            resource_type="identity_verification",
            details={
                "success": result.success,
                "provider": provider.name,
                "verification_reference": result.verification_reference,
                "risk_level": result.risk_assessment.risk_level if result.risk_assessment else None,
            }
        )
        
        return result
        
    except Exception as e:
        # Log error
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.verify_identity_v2",
            resource_type="identity_verification",
            success=False,
            details={"error": str(e)}
        )
        
        # Handle provider-specific errors
        if hasattr(e, 'provider'):
            # ProviderError
            if hasattr(e, 'error_code'):
                error_code = e.error_code
                if error_code == "missing_credentials":
                    raise HTTPException(status_code=500, detail="Identity verification service configuration error")
                elif error_code == "invalid_nin_format" or error_code == "invalid_bvn_format":
                    raise HTTPException(status_code=422, detail=str(e))
                elif error_code == "unsupported_operation":
                    raise HTTPException(status_code=400, detail=str(e))
                elif error_code == "rate_limit_exceeded":
                    raise HTTPException(status_code=429, detail="Too many verification requests. Please try again later.")
                elif error_code == "service_unavailable":
                    raise HTTPException(status_code=503, detail="Identity verification service temporarily unavailable")
            
            # Generic provider error
            raise HTTPException(status_code=500, detail="Identity verification service error")
        
        # Generic error
        raise HTTPException(status_code=500, detail="Internal server error")


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
        factory = get_identity_factory()
        providers = factory.get_all_providers()
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.list_providers",
            resource_type="identity_providers",
        )
        
        return providers
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.list_providers",
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
        factory = get_identity_factory()
        health_status = factory.health_check()
        
        # Convert to ProviderHealth format
        providers_health = []
        for name, healthy in health_status.items():
            providers_health.append(ProviderHealth(
                provider=name,
                healthy=healthy,
                last_check="2024-01-01T00:00:00Z",  # Would be actual timestamp
                supported_operations=[],  # Would be populated from provider
                error_message=None if healthy else "Health check failed"
            ))
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.health_check",
            resource_type="identity_providers",
            details={"health_status": health_status}
        )
        
        return providers_health
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="kyc.health_check",
            resource_type="identity_providers",
            success=False,
            details={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail="Failed to check provider health")

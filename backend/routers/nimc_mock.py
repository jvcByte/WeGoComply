"""
NIMC Mock Debug Routes.

This module provides debug routes for testing the NIMC mock provider
in development mode. These routes mirror the NIMC eNVS API structure
for comprehensive testing.
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.security import require_roles
from dependencies import get_audit_service
from schemas.security import AuthenticatedUser, UserRole
from services.audit_service import AuditService
from app.schemas.nimc import (
    NIMCCreateTokenRequest,
    NIMCTokenObject,
    NIMCSearchByNINRequest,
    NIMCSearchByDemoRequest,
    NIMCSearchByPhoneRequest,
    NIMCSearchByDocumentRequest,
    NIMCSearchByFingerRequest,
    NIMCVerifyFingerRequest,
    NIMCResponse,
    FingerPositionCode,
)

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": dict},
    403: {"model": dict},
    422: {"model": dict},
    429: {"model": dict},
    500: {"model": dict},
}


def get_nimc_mock_provider():
    """Get NIMC mock provider instance"""
    from app.services.identity.providers.nimc_mock_provider import NIMCMockProvider
    return NIMCMockProvider()


def is_mock_mode() -> bool:
    """Check if system is in mock mode"""
    settings = get_settings()
    return getattr(settings, 'identity_mode', 'mock') == 'mock'


def require_mock_mode():
    """Require mock mode for debug routes"""
    if not is_mock_mode():
        raise HTTPException(
            status_code=403,
            detail="NIMC debug routes only available in mock mode"
        )


@router.post("/create-token", responses=ERROR_RESPONSES)
async def create_token(
    request: Request,
    payload: NIMCCreateTokenRequest,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
) -> NIMCTokenObject:
    """Create NIMC authentication token"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.create_token(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.create_token",
            resource_type="nimc_token",
            details={"username": payload.username, "orgid": payload.orgid}
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.create_token",
            resource_type="nimc_token",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-by-nin", responses=ERROR_RESPONSES)
async def search_by_nin(
    request: Request,
    payload: NIMCSearchByNINRequest,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Search by NIN"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.search_by_nin(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_nin",
            resource_type="nimc_search",
            details={"nin": payload.nin[:3] + "******" + payload.nin[-2:] if len(payload.nin) >= 5 else "******"}
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_nin",
            resource_type="nimc_search",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-by-demo", responses=ERROR_RESPONSES)
async def search_by_demo(
    request: Request,
    payload: NIMCSearchByDemoRequest,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Search by demographics"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.search_by_demo(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_demo",
            resource_type="nimc_search",
            details={
                "firstname": payload.firstname,
                "lastname": payload.lastname,
                "gender": payload.gender
            }
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_demo",
            resource_type="nimc_search",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-by-phone", responses=ERROR_RESPONSES)
async def search_by_phone(
    request: Request,
    payload: NIMCSearchByPhoneRequest,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Search by phone number"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.search_by_demo_phone(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_phone",
            resource_type="nimc_search",
            details={"phone": payload.telephoneno[:3] + "******" + payload.telephoneno[-2:] if len(payload.telephoneno) >= 5 else "******"}
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_phone",
            resource_type="nimc_search",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-by-document", responses=ERROR_RESPONSES)
async def search_by_document(
    request: Request,
    payload: NIMCSearchByDocumentRequest,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Search by document number"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.search_by_document_number(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_document",
            resource_type="nimc_search",
            details={"document": payload.documentno[:3] + "******" + payload.documentno[-2:] if len(payload.documentno) >= 5 else "******"}
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_document",
            resource_type="nimc_search",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-by-finger", responses=ERROR_RESPONSES)
async def search_by_finger(
    request: Request,
    payload: NIMCSearchByFingerRequest,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Search by fingerprint"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.search_by_finger(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_finger",
            resource_type="nimc_search",
            details={"finger_position": payload.fingerPosition}
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.search_by_finger",
            resource_type="nimc_search",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-finger", responses=ERROR_RESPONSES)
async def verify_finger(
    request: Request,
    payload: NIMCVerifyFingerRequest,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
) -> NIMCResponse:
    """Verify fingerprint with NIN data"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.verify_finger_with_data(payload)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.verify_finger",
            resource_type="nimc_verification",
            details={
                "nin": payload.nin[:3] + "******" + payload.nin[-2:] if len(payload.nin) >= 5 else "******",
                "finger_position": payload.fingerPosition
            }
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.verify_finger",
            resource_type="nimc_verification",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permissions/{level}", responses=ERROR_RESPONSES)
async def get_permissions(
    request: Request,
    level: int,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Get permissions by level"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.get_permission_by_level(level)
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.get_permissions",
            resource_type="nimc_permissions",
            details={"level": level}
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.get_permissions",
            resource_type="nimc_permissions",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", responses=ERROR_RESPONSES)
async def get_provider_info(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Get NIMC mock provider information"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        result = provider.get_provider_info()
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.get_info",
            resource_type="nimc_info",
        )
        
        return result
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.get_info",
            resource_type="nimc_info",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records", responses=ERROR_RESPONSES)
async def list_mock_records(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
    audit_service: AuditService = Depends(get_audit_service),
):
    """List all mock records (for testing)"""
    require_mock_mode()
    
    try:
        provider = get_nimc_mock_provider()
        records = provider._records
        
        # Return only basic info for privacy
        basic_records = [
            {
                "nin": record.nin[:3] + "******" + record.nin[-2:] if record.nin and len(record.nin) >= 5 else "******",
                "firstname": record.firstname,
                "surname": record.surname,
                "gender": record.gender,
                "state": record.residence_state,
                "trackingId": record.trackingId
            }
            for record in records
        ]
        
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.list_records",
            resource_type="nimc_records",
            details={"count": len(records)}
        )
        
        return {
            "total_records": len(records),
            "records": basic_records
        }
        
    except Exception as e:
        audit_service.log_action(
            request=request,
            actor=current_user,
            action="nimc_mock.list_records",
            resource_type="nimc_records",
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

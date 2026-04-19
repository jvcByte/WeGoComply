from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_tax_service
from schemas.common import ErrorResponse
from schemas.tax import BulkTINRequest, BulkTINResponse, TINRecord, TINVerificationResult
from services.tax_service import TaxService

router = APIRouter()
ERROR_RESPONSES = {
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.post("/verify-tin", response_model=TINVerificationResult, responses=ERROR_RESPONSES)
async def verify_single_tin(
    record: TINRecord,
    service: TaxService = Depends(get_tax_service),
) -> TINVerificationResult:
    return await service.verify_tin(record)


@router.post("/bulk-verify", response_model=BulkTINResponse, responses=ERROR_RESPONSES)
async def bulk_tin_verification(
    request: BulkTINRequest,
    service: TaxService = Depends(get_tax_service),
) -> BulkTINResponse:
    return await service.bulk_verify_tin(request.records)

from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_regulatory_service
from schemas.common import ErrorResponse
from schemas.regulatory import RegulatorySummary, RegulatorySummaryRequest, RegulatoryUpdatesResponse
from services.regulatory_service import RegulatoryService

router = APIRouter()
ERROR_RESPONSES = {
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.get("/updates", response_model=RegulatoryUpdatesResponse, responses=ERROR_RESPONSES)
async def get_regulatory_updates(
    service: RegulatoryService = Depends(get_regulatory_service),
) -> RegulatoryUpdatesResponse:
    return await service.get_latest_updates()


@router.post("/summarize", response_model=RegulatorySummary, responses=ERROR_RESPONSES)
async def summarize_regulation(
    payload: RegulatorySummaryRequest,
    service: RegulatoryService = Depends(get_regulatory_service),
) -> RegulatorySummary:
    return await service.summarize_circular(payload)

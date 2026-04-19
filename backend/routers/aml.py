from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies import get_aml_service
from schemas.aml import AMLMonitorResponse, STRReportResponse, Transaction, TransactionBatchRequest
from schemas.common import ErrorResponse
from services.aml_service import AMLService

router = APIRouter()
ERROR_RESPONSES = {
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.post("/monitor", response_model=AMLMonitorResponse, responses=ERROR_RESPONSES)
async def monitor_transactions(
    batch: TransactionBatchRequest,
    service: AMLService = Depends(get_aml_service),
) -> AMLMonitorResponse:
    return service.analyze_transactions(batch.transactions)


@router.post("/generate-str/{transaction_id}", response_model=STRReportResponse, responses=ERROR_RESPONSES)
async def create_str(
    transaction_id: str,
    transaction: Transaction,
    service: AMLService = Depends(get_aml_service),
) -> STRReportResponse:
    return await service.generate_str(transaction_id, transaction)

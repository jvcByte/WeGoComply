from __future__ import annotations

from fastapi import APIRouter, Depends

from core.security import require_roles
from dependencies import get_regulatory_service
from schemas.common import ErrorResponse
from schemas.regulatory import RegulatorySummary, RegulatorySummaryRequest, RegulatoryUpdatesResponse
from schemas.security import AuthenticatedUser, UserRole
from services.regulatory_service import RegulatoryService

router = APIRouter()
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}


@router.get(
    "/updates",
    response_model=RegulatoryUpdatesResponse,
    responses=ERROR_RESPONSES,
    summary="Get Latest Regulatory Updates",
    description="""
Returns AI-summarized regulatory updates from CBN, FIRS, SEC, FCCPC, and NITDA.

Each update includes:
- **summary** — plain English, 2 sentences max
- **action_required** — what your institution must do
- **deadline** — extracted deadline date (if any)
- **affected_operations** — e.g. `["AML", "KYC", "Tax Compliance"]`
- **urgency** — `HIGH` / `MEDIUM` / `LOW`

**AI:** Azure OpenAI GPT-4o reads full circular text and extracts structured compliance obligations.

**Mock mode:** Returns 4 pre-loaded Nigerian regulatory updates (CBN, FIRS, FCCPC, CBN Open Banking).

**Required roles:** `admin`, `compliance_officer`, `analyst`, `viewer`
""",
)
async def get_regulatory_updates(
    _current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST, UserRole.VIEWER)
    ),
    service: RegulatoryService = Depends(get_regulatory_service),
) -> RegulatoryUpdatesResponse:
    return await service.get_latest_updates()


@router.post(
    "/summarize",
    response_model=RegulatorySummary,
    responses=ERROR_RESPONSES,
    summary="Summarize a Regulatory Circular",
    description="""
Paste any regulatory circular text and receive an AI-generated structured summary.

**Input:** Raw text of a CBN, FIRS, SEC, FCCPC, or NITDA circular (minimum 20 characters).

**Output:**
- `summary` — 2-sentence plain English summary
- `action_required` — specific steps your institution must take
- `deadline` — extracted deadline date or null
- `affected_operations` — list of impacted business areas
- `urgency` — HIGH / MEDIUM / LOW

**AI:** Azure OpenAI GPT-4o with a Nigerian compliance expert system prompt.

**Mock mode:** Returns a generic summary without calling Azure OpenAI.

**Required roles:** `admin`, `compliance_officer`, `analyst`
""",
)
async def summarize_regulation(
    payload: RegulatorySummaryRequest,
    _current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER, UserRole.ANALYST)
    ),
    service: RegulatoryService = Depends(get_regulatory_service),
) -> RegulatorySummary:
    return await service.summarize_circular(payload)

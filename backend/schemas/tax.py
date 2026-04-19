from __future__ import annotations

from typing import Literal

from pydantic import Field

from schemas.common import BaseSchema


class TINRecord(BaseSchema):
    customer_id: str
    name: str
    tin: str = Field(..., min_length=10, max_length=15, pattern=r"^\d+$")


class TINVerificationResult(BaseSchema):
    customer_id: str
    tin: str
    status: Literal["MATCHED", "NOT_FOUND", "NAME_MISMATCH"]
    firs_name: str = ""
    submitted_name: str
    match_confidence: float = Field(..., ge=0.0, le=1.0)


class BulkTINRequest(BaseSchema):
    records: list[TINRecord]


class BulkTINResponse(BaseSchema):
    total: int
    matched: int
    failed: int
    match_rate: float = Field(..., ge=0.0, le=100.0)
    deadline_risk: Literal["LOW", "HIGH"]
    records: list[TINVerificationResult]


from __future__ import annotations

from typing import Literal

from pydantic import Field

from schemas.common import BaseSchema


class RegulatorySummaryRequest(BaseSchema):
    text: str = Field(..., min_length=20)


class RegulatorySummary(BaseSchema):
    summary: str
    action_required: str
    deadline: str | None = None
    affected_operations: list[str]
    urgency: Literal["HIGH", "MEDIUM", "LOW"]


class RegulatoryUpdate(RegulatorySummary):
    id: str
    source: str
    title: str
    date: str
    url: str


class RegulatoryUpdatesResponse(BaseSchema):
    updates: list[RegulatoryUpdate]


from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from schemas.common import BaseSchema


class Transaction(BaseSchema):
    transaction_id: str
    customer_id: str
    amount: float = Field(..., gt=0)
    currency: str = "NGN"
    timestamp: datetime
    transaction_type: Literal["transfer", "deposit", "withdrawal"]
    counterparty: str
    channel: Literal["mobile", "web", "pos", "atm"]


class TransactionBatchRequest(BaseSchema):
    transactions: list[Transaction]


class AMLFlaggedTransaction(BaseSchema):
    transaction_id: str
    customer_id: str
    amount: float
    timestamp: datetime
    transaction_type: Literal["transfer", "deposit", "withdrawal"]
    counterparty: str
    channel: Literal["mobile", "web", "pos", "atm"]
    anomaly_score: float
    rules_triggered: list[str]
    risk_level: Literal["HIGH", "MEDIUM"]
    recommended_action: Literal["GENERATE_STR", "REVIEW"]


class AMLMonitorResponse(BaseSchema):
    total_analyzed: int
    flagged_count: int
    clean_count: int
    flagged_transactions: list[AMLFlaggedTransaction]


class STRReportResponse(BaseSchema):
    report_reference: str
    reporting_institution: str
    subject_name: str
    transaction_summary: str
    grounds_for_suspicion: str
    recommended_action: str
    report_date: str

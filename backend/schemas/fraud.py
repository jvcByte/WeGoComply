from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from schemas.common import BaseSchema


class FraudTransaction(BaseSchema):
    step: int = Field(..., description="Transaction step / sequence number")
    type: Literal["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
    amount: float = Field(..., gt=0)
    oldbalanceOrg: float = Field(..., ge=0)
    newbalanceOrig: float = Field(..., ge=0)
    oldbalanceDest: float = Field(..., ge=0)
    newbalanceDest: float = Field(..., ge=0)
    isFlaggedFraud: int = Field(default=0, ge=0, le=1)
    transaction_id: str | None = Field(default=None)


class FraudTransactionBatchRequest(BaseSchema):
    transactions: list[FraudTransaction] = Field(..., min_length=1, max_length=1000)


class FraudAnalysisResult(BaseSchema):
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    isFlaggedFraud: int
    transaction_id: str | None = None
    classifier_score: float
    anomaly_score: float
    fraud_risk_score: float
    predicted_is_fraud: int
    risk_band: Literal["High Risk", "Review", "Watch", "Low Risk"]


class FraudAnalysisResponse(BaseSchema):
    model_config = ConfigDict(protected_namespaces=())

    total_analyzed: int
    high_risk_count: int
    review_count: int
    watch_count: int
    low_risk_count: int
    fraud_predicted_count: int
    transactions: list[FraudAnalysisResult]
    model_available: bool
    note: str | None = None


class FraudExplanationRequest(BaseSchema):
    transaction: FraudTransaction


class FraudExplanationResponse(BaseSchema):
    transaction_id: str
    risk_factors: list[str]
    note: str | None = None


class FraudModelInfo(BaseSchema):
    model_config = ConfigDict(protected_namespaces=())

    model_available: bool
    model_version: int | None = None
    classifier: str | None = None
    metrics: dict | None = None
    training_info: dict | None = None
    dataset_summary: dict | None = None
    message: str | None = None
    recommendation: str | None = None

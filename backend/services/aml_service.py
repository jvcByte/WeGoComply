from __future__ import annotations

import json
from datetime import datetime

import numpy as np
from openai import AzureOpenAI

from core.config import Settings
from core.errors import ExternalServiceError
from repositories.aml_repository import AMLModelRepository
from schemas.aml import (
    AMLFlaggedTransaction,
    AMLMonitorResponse,
    STRReportResponse,
    Transaction,
)


class AMLService:
    def __init__(self, settings: Settings, model_repository: AMLModelRepository) -> None:
        self.settings = settings
        self.model_repository = model_repository

    def analyze_transactions(self, transactions: list[Transaction]) -> AMLMonitorResponse:
        flagged: list[AMLFlaggedTransaction] = []
        clean_count = 0
        model = self.model_repository.get_model()

        for transaction in transactions:
            hour = transaction.timestamp.hour
            features = np.array([[transaction.amount, hour]])
            score = float(model.decision_function(features)[0])
            is_anomaly = model.predict(features)[0] == -1
            rules_triggered = self._check_rules(transaction)

            if is_anomaly or rules_triggered:
                flagged.append(
                    AMLFlaggedTransaction(
                        transaction_id=transaction.transaction_id,
                        customer_id=transaction.customer_id,
                        amount=transaction.amount,
                        timestamp=transaction.timestamp,
                        transaction_type=transaction.transaction_type,
                        counterparty=transaction.counterparty,
                        channel=transaction.channel,
                        anomaly_score=round(score, 4),
                        rules_triggered=rules_triggered,
                        risk_level="HIGH" if is_anomaly and rules_triggered else "MEDIUM",
                        recommended_action="GENERATE_STR" if is_anomaly else "REVIEW",
                    )
                )
            else:
                clean_count += 1

        return AMLMonitorResponse(
            total_analyzed=len(transactions),
            flagged_count=len(flagged),
            clean_count=clean_count,
            flagged_transactions=flagged,
        )

    async def generate_str(self, transaction_id: str, transaction: Transaction) -> STRReportResponse:
        if not self.settings.is_live:
            return self._mock_str_report(transaction_id, transaction)

        client = AzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint or "",
            api_key=self.settings.azure_openai_key or "",
            api_version="2024-02-01",
        )
        prompt = f"""
You are a compliance officer at a Nigerian financial institution.
Generate a Suspicious Transaction Report (STR) for submission to the NFIU.

Transaction details:
- ID: {transaction.transaction_id}
- Customer: {transaction.customer_id}
- Amount: N{transaction.amount:,.2f}
- Type: {transaction.transaction_type}
- Counterparty: {transaction.counterparty}
- Channel: {transaction.channel}
- Timestamp: {transaction.timestamp.isoformat()}

Return a JSON object with these fields:
- report_reference
- reporting_institution
- subject_name
- transaction_summary
- grounds_for_suspicion
- recommended_action
- report_date
"""

        try:
            response = client.chat.completions.create(
                model=self.settings.azure_openai_deployment or "",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return STRReportResponse.model_validate(json.loads(content))
        except Exception as exc:
            raise ExternalServiceError(
                "Failed to generate STR with Azure OpenAI.",
                code="AZURE_OPENAI_STR_GENERATION_FAILED",
            ) from exc

    @staticmethod
    def _check_rules(transaction: Transaction) -> list[str]:
        rules = []
        if transaction.amount >= 5_000_000:
            rules.append("LARGE_CASH_TRANSACTION")
        if transaction.timestamp.hour < 5 or transaction.timestamp.hour > 23:
            rules.append("UNUSUAL_HOURS")
        if transaction.transaction_type == "transfer" and transaction.amount > 1_000_000:
            rules.append("HIGH_VALUE_TRANSFER")
        return rules

    @staticmethod
    def _mock_str_report(transaction_id: str, transaction: Transaction) -> STRReportResponse:
        return STRReportResponse(
            report_reference=f"STR-{transaction_id[:8].upper()}",
            reporting_institution="WeGoComply Demo Bank",
            subject_name=transaction.customer_id,
            transaction_summary=(
                f"Customer conducted a {transaction.transaction_type} of "
                f"N{transaction.amount:,.2f} via {transaction.channel} at "
                f"{transaction.timestamp.strftime('%H:%M')}."
            ),
            grounds_for_suspicion=(
                "Transaction amount exceeds threshold and occurred outside "
                "normal banking hours."
            ),
            recommended_action=(
                "Freeze account pending investigation and file STR with NFIU within 24 hours."
            ),
            report_date=datetime.now().strftime("%Y-%m-%d"),
        )

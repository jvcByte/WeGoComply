from __future__ import annotations

import json

from openai import AzureOpenAI

from core.config import Settings
from core.errors import ExternalServiceError
from repositories.regulatory_repository import RegulatoryCircularRepository
from schemas.regulatory import (
    RegulatorySummary,
    RegulatorySummaryRequest,
    RegulatoryUpdate,
    RegulatoryUpdatesResponse,
)


class RegulatoryService:
    def __init__(
        self,
        settings: Settings,
        circular_repository: RegulatoryCircularRepository,
    ) -> None:
        self.settings = settings
        self.circular_repository = circular_repository

    async def get_latest_updates(self) -> RegulatoryUpdatesResponse:
        updates: list[RegulatoryUpdate] = []
        for circular in self.circular_repository.list_circulars():
            summary = await self.summarize_circular(RegulatorySummaryRequest(text=circular.raw_text))
            updates.append(
                RegulatoryUpdate(
                    id=circular.id,
                    source=circular.source,
                    title=circular.title,
                    date=circular.date,
                    url=circular.url,
                    **summary.model_dump(),
                )
            )
        return RegulatoryUpdatesResponse(updates=updates)

    async def summarize_circular(self, payload: RegulatorySummaryRequest) -> RegulatorySummary:
        if not self.settings.is_live:
            return self._mock_summary(payload.text)

        client = AzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint or "",
            api_key=self.settings.azure_openai_key or "",
            api_version="2024-02-01",
        )
        prompt = f"""
You are a Nigerian financial compliance expert.
Analyze this regulatory circular and return a JSON object with:
- summary
- action_required
- deadline
- affected_operations
- urgency

Circular text:
{payload.text}
"""

        try:
            response = client.chat.completions.create(
                model=self.settings.azure_openai_deployment or "",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return RegulatorySummary.model_validate(json.loads(content))
        except Exception as exc:
            raise ExternalServiceError(
                "Failed to summarize regulatory update with Azure OpenAI.",
                code="AZURE_OPENAI_REGULATORY_SUMMARY_FAILED",
            ) from exc

    @staticmethod
    def _mock_summary(text: str) -> RegulatorySummary:
        lowered = text.lower()
        if "aml" in lowered:
            return RegulatorySummary(
                summary=(
                    "All financial institutions must implement real-time AML "
                    "transaction monitoring by June 30, 2026."
                ),
                action_required=(
                    "Deploy automated AML monitoring and configure STR filing "
                    "within 24 hours of detection."
                ),
                deadline="2026-06-30",
                affected_operations=["AML", "Transaction Monitoring", "STR Filing"],
                urgency="HIGH",
            )
        if "tin" in lowered:
            return RegulatorySummary(
                summary=(
                    "Accounts without verified TINs will be restricted from "
                    "transactions above N500,000 from April 1, 2026."
                ),
                action_required=(
                    "Complete bulk TIN verification for existing customers and "
                    "enforce TIN collection during onboarding."
                ),
                deadline="2026-04-01",
                affected_operations=["KYC", "Account Management", "Tax Compliance"],
                urgency="HIGH",
            )
        return RegulatorySummary(
            summary="Digital lenders must complete FCCPC registration before the deadline.",
            action_required="Submit registration documents and confirm consumer protection controls.",
            deadline="2026-04-30",
            affected_operations=["Digital Lending", "Consumer Protection"],
            urgency="MEDIUM",
        )

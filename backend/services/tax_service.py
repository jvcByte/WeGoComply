from __future__ import annotations

import httpx

from core.config import Settings
from core.errors import ExternalServiceError
from schemas.tax import BulkTINResponse, TINRecord, TINVerificationResult


class TaxService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def verify_tin(self, record: TINRecord) -> TINVerificationResult:
        if not self.settings.is_live:
            return self._mock_verify_tin(record)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.dojah_base_url}/api/v1/kyc/tin",
                    params={"tin": record.tin},
                    headers=self._dojah_headers,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Failed to verify TIN with Dojah.",
                code="DOJAH_TIN_VERIFICATION_FAILED",
            ) from exc

        entity = data.get("entity", {})
        if not entity:
            return TINVerificationResult(
                customer_id=record.customer_id,
                tin=record.tin,
                status="NOT_FOUND",
                firs_name="",
                submitted_name=record.name,
                match_confidence=0.0,
            )

        firs_name = entity.get("taxpayer_name", "")
        confidence = self._similarity(record.name, firs_name)
        return TINVerificationResult(
            customer_id=record.customer_id,
            tin=record.tin,
            status="MATCHED" if confidence > 0.7 else "NAME_MISMATCH",
            firs_name=firs_name,
            submitted_name=record.name,
            match_confidence=confidence,
        )

    async def bulk_verify_tin(self, records: list[TINRecord]) -> BulkTINResponse:
        results = [await self.verify_tin(record) for record in records]
        total = len(records)
        matched = sum(1 for result in results if result.status == "MATCHED")
        match_rate = round((matched / total * 100), 2) if total else 0.0

        return BulkTINResponse(
            total=total,
            matched=matched,
            failed=total - matched,
            match_rate=match_rate,
            deadline_risk="HIGH" if total and (matched / total) < 0.8 else "LOW",
            records=results,
        )

    def _mock_verify_tin(self, record: TINRecord) -> TINVerificationResult:
        if record.tin.endswith("55"):
            return TINVerificationResult(
                customer_id=record.customer_id,
                tin=record.tin,
                status="NOT_FOUND",
                firs_name="",
                submitted_name=record.name,
                match_confidence=0.0,
            )

        if record.tin.endswith("99"):
            return TINVerificationResult(
                customer_id=record.customer_id,
                tin=record.tin,
                status="NAME_MISMATCH",
                firs_name=f"{record.name.split()[0]} Holdings",
                submitted_name=record.name,
                match_confidence=0.62,
            )

        return TINVerificationResult(
            customer_id=record.customer_id,
            tin=record.tin,
            status="MATCHED",
            firs_name=record.name,
            submitted_name=record.name,
            match_confidence=0.95,
        )

    @property
    def _dojah_headers(self) -> dict[str, str]:
        return {
            "AppId": self.settings.dojah_app_id or "",
            "Authorization": self.settings.dojah_api_key or "",
        }

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        a_tokens = set(a.lower().split())
        b_tokens = set(b.lower().split())
        if not a_tokens or not b_tokens:
            return 0.0
        overlap = len(a_tokens & b_tokens)
        return round(overlap / max(len(a_tokens), len(b_tokens)), 2)

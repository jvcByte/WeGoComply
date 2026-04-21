from __future__ import annotations

import httpx

from core.config import Settings
from core.errors import ExternalServiceError
from schemas.tax import BulkTINResponse, TINRecord, TINVerificationResult
from services.firs_client import FIRSClient


class TaxService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._firs = FIRSClient.from_env()

    async def verify_tin(self, record: TINRecord) -> TINVerificationResult:
        """
        Verify a single TIN against FIRS ATRS API.

        Provider: FIRS ATRS (https://atrs.firs.gov.ng)
        Auth:     OAuth 2.0 Bearer Token
        Mode:     mock (default) | live (set FIRS_MODE=live in .env)

        To switch to live FIRS data, set in .env:
            FIRS_MODE=live
            FIRS_CLIENT_ID=your_client_id
            FIRS_CLIENT_SECRET=your_client_secret
            FIRS_USERNAME=your_username
            FIRS_PASSWORD=your_password
            FIRS_VAT_NUMBER=your_vat_number
            FIRS_BUSINESS_PLACE=your_business_place
            FIRS_BUSINESS_DEVICE=your_device_id
        """
        try:
            response = await self._firs.verify_tin(record.tin, record.name)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Failed to verify TIN with FIRS ATRS.",
                code="FIRS_TIN_VERIFICATION_FAILED",
            ) from exc

        # FIRS response: {"status": true/false, "data": {...} | null}
        if not response.get("status") or not response.get("data"):
            return TINVerificationResult(
                customer_id=record.customer_id,
                tin=record.tin,
                status="NOT_FOUND",
                firs_name="",
                submitted_name=record.name,
                match_confidence=0.0,
            )

        firs_name  = response["data"].get("taxpayer_name", "")
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
        total   = len(records)
        matched = sum(1 for r in results if r.status == "MATCHED")
        match_rate = round((matched / total * 100), 2) if total else 0.0

        return BulkTINResponse(
            total=total,
            matched=matched,
            failed=total - matched,
            match_rate=match_rate,
            deadline_risk="HIGH" if total and (matched / total) < 0.8 else "LOW",
            records=results,
        )

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

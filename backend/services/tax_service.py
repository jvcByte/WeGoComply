from __future__ import annotations

import httpx
from datetime import datetime

from core.config import Settings
from core.errors import ExternalServiceError
from schemas.tax import (
    AnnualReturnRequest, AnnualReturnSummary,
    BillReportRequest, BillReportResponse,
    BulkTINResponse, MonthlyBreakdown,
    TINRecord, TINVerificationResult,
)
from services.firs_client import FIRSClient


class TaxService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._firs = FIRSClient.from_env()

    # ------------------------------------------------------------------
    # TIN Verification
    # ------------------------------------------------------------------

    async def verify_tin(self, record: TINRecord) -> TINVerificationResult:
        """
        Verify a single TIN against FIRS ATRS API.
        FIRS_MODE=mock (default) → realistic mock responses
        FIRS_MODE=live           → real FIRS ATRS API
        """
        try:
            response = await self._firs.verify_tin(record.tin, record.name)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Failed to verify TIN with FIRS ATRS.",
                code="FIRS_TIN_VERIFICATION_FAILED",
            ) from exc

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
        results    = [await self.verify_tin(r) for r in records]
        total      = len(records)
        matched    = sum(1 for r in results if r.status == "MATCHED")
        match_rate = round((matched / total * 100), 2) if total else 0.0
        return BulkTINResponse(
            total=total,
            matched=matched,
            failed=total - matched,
            match_rate=match_rate,
            deadline_risk="HIGH" if total and (matched / total) < 0.8 else "LOW",
            records=results,
        )

    # ------------------------------------------------------------------
    # Bill / Receipt Reporting  →  FIRS ATRS POST /v1/bills/report
    # ------------------------------------------------------------------

    async def report_bill(self, payload: BillReportRequest) -> BillReportResponse:
        """
        Submit a single receipt/bill to FIRS ATRS.

        Flow:
          1. WeGoComply generates MD5 SID from bill fields + client_secret
          2. POST to FIRS ATRS /v1/bills/report with full payload
          3. FIRS validates SID, records the bill, returns UID
          4. WeGoComply stores UID as proof of submission
          5. UID is returned to the calling institution

        The UID is FIRS's acknowledgment — it proves the bill was received.
        Store it for audit trail and annual return reconciliation.
        """
        try:
            firs_response = await self._firs.report_bill(
                bill_number   = payload.bill_number,
                bill_datetime = payload.bill_datetime,
                total_value   = payload.total_value,
                items         = [item.model_dump() for item in payload.items],
            )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Failed to submit bill to FIRS ATRS.",
                code="FIRS_BILL_REPORT_FAILED",
            ) from exc

        # Regenerate SID for transparency — institution can verify it
        sid = self._firs._generate_sid(
            payload.bill_number,
            payload.bill_datetime,
            payload.total_value,
        )

        return BillReportResponse(
            status       = firs_response.get("status", False),
            uid          = firs_response.get("uid", ""),
            bill_number  = payload.bill_number,
            message      = firs_response.get("message", ""),
            security_code= sid,
            submitted_at = datetime.utcnow().isoformat() + "Z",
        )

    # ------------------------------------------------------------------
    # Annual Return Summary  →  for TaxPro Max upload
    # ------------------------------------------------------------------

    async def get_annual_return_summary(
        self, request: AnnualReturnRequest
    ) -> AnnualReturnSummary:
        """
        Aggregate all monthly bill submissions for a tax year into
        an annual return summary ready for TaxPro Max upload.

        In production: queries the database for all BillReportResponse
        records for this institution and tax year.
        Currently: returns realistic mock data for demo.

        The company takes this summary and uploads it to:
        https://taxpromax.firs.gov.ng
        to file their Company Income Tax (CIT) return.
        """
        if not self.settings.is_live:
            return self._mock_annual_return(request)

        # Production: query DB for all bill submissions this year
        # monthly_data = await db.get_bills_by_year(request.institution_id, request.tax_year)
        raise ExternalServiceError(
            "Annual return DB aggregation not yet implemented for live mode.",
            code="ANNUAL_RETURN_NOT_IMPLEMENTED",
        )

    # ------------------------------------------------------------------
    # Mock annual return — realistic Nigerian fintech figures
    # ------------------------------------------------------------------

    def _mock_annual_return(self, request: AnnualReturnRequest) -> AnnualReturnSummary:
        VAT_RATE = 0.075  # 7.5% Nigerian VAT

        monthly = []
        total_revenue = 0.0
        total_vat_collected = 0.0
        total_vat_remitted = 0.0
        total_tx = 0
        firs_submissions = []
        outstanding = []

        for month_num in range(1, 13):
            month_str = f"{request.tax_year}-{month_num:02d}"

            # Simulate realistic monthly revenue (₦300M–₦500M range)
            base_revenue = 350_000_000 + (month_num * 12_000_000)
            vat_collected = round(base_revenue * VAT_RATE, 2)

            # Simulate 2 months with late/missing remittance
            if month_num in (8, 11):
                vat_remitted = 0.0
                uid = None
                outstanding.append(month_str)
            else:
                vat_remitted = vat_collected
                uid = f"FIRS-UID-{request.tax_year}{month_num:02d}-{month_num:03d}"
                firs_submissions.append({
                    "uid": uid,
                    "month": month_str,
                    "amount": vat_remitted,
                    "status": "ACCEPTED",
                    "submitted_date": f"{request.tax_year}-{month_num:02d}-21",
                })

            tx_count = 1_200_000 + (month_num * 50_000)
            monthly.append(MonthlyBreakdown(
                month            = month_str,
                revenue          = base_revenue,
                vat_collected    = vat_collected,
                vat_remitted     = vat_remitted,
                transaction_count= tx_count,
                firs_uid         = uid,
            ))

            total_revenue       += base_revenue
            total_vat_collected += vat_collected
            total_vat_remitted  += vat_remitted
            total_tx            += tx_count

        vat_outstanding = round(total_vat_collected - total_vat_remitted, 2)

        if vat_outstanding > 0:
            compliance_status = "OUTSTANDING_VAT"
        elif outstanding:
            compliance_status = "MISSING_SUBMISSIONS"
        else:
            compliance_status = "COMPLIANT"

        return AnnualReturnSummary(
            institution_id        = request.institution_id,
            company_name          = request.company_name,
            tin                   = request.tin,
            tax_year              = request.tax_year,
            total_revenue         = round(total_revenue, 2),
            total_vat_collected   = round(total_vat_collected, 2),
            total_vat_remitted    = round(total_vat_remitted, 2),
            vat_outstanding       = vat_outstanding,
            total_transactions    = total_tx,
            taxable_transactions  = int(total_tx * 0.94),
            monthly_breakdown     = monthly,
            firs_submissions      = firs_submissions,
            total_firs_submissions= len(firs_submissions),
            compliance_status     = compliance_status,
            outstanding_filings   = outstanding,
            generated_at          = datetime.utcnow().isoformat() + "Z",
            taxpromax_upload_ready= compliance_status == "COMPLIANT",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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


from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegulatoryCircularRecord:
    id: str
    source: str
    title: str
    date: str
    raw_text: str
    url: str


class RegulatoryCircularRepository:
    def list_circulars(self) -> list[RegulatoryCircularRecord]:
        return [
            RegulatoryCircularRecord(
                id="CBN-2026-AML-001",
                source="CBN",
                title="Baseline Standards for Automated AML Solutions",
                date="2026-03-15",
                raw_text=(
                    "All deposit money banks, microfinance banks, and payment service providers "
                    "are required to implement real-time or near-real-time automated AML "
                    "transaction monitoring systems by June 30, 2026. Institutions must file "
                    "Suspicious Transaction Reports (STRs) within 24 hours of detection."
                ),
                url="https://cbn.gov.ng/circulars/2026/aml-baseline",
            ),
            RegulatoryCircularRecord(
                id="FIRS-2026-TIN-002",
                source="FIRS",
                title="Mandatory TIN Verification for Financial Accounts",
                date="2026-01-10",
                raw_text=(
                    "All financial institutions must verify and match Tax Identification Numbers "
                    "(TIN) for all existing and new customers. Accounts without verified TINs will "
                    "be restricted from transactions above N500,000 effective April 1, 2026."
                ),
                url="https://firs.gov.ng/notices/2026/tin-mandate",
            ),
            RegulatoryCircularRecord(
                id="FCCPC-2026-DL-003",
                source="FCCPC",
                title="Digital Lender Registration Deadline",
                date="2026-01-05",
                raw_text=(
                    "All digital money lenders must complete registration with the FCCPC by "
                    "April 30, 2026. Unregistered platforms will be delisted from app stores "
                    "and payment networks."
                ),
                url="https://fccpc.gov.ng/notices/2026/digital-lenders",
            ),
        ]


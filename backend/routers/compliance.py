from __future__ import annotations

from fastapi import APIRouter, Depends
from schemas.security import AuthenticatedUser, UserRole
from core.security import require_roles
from services.compliance_service import (
    get_compliance_posture,
    get_suptech_report,
    get_sector_heatmap,
)

router = APIRouter()


@router.get(
    "/posture/{institution_id}",
    summary="Get Institution Compliance Posture",
    description="""
Returns a real-time compliance posture score (0–100) for a specific institution,
broken down across 4 regulatory pillars.

**Scoring formula:**
```
Overall = (KYC × 30%) + (AML × 35%) + (TIN × 20%) + (Reporting × 15%)
```

**Pillar details:**

| Pillar | Weight | Framework |
|--------|--------|-----------|
| KYC | 30% | CBN KYC Guidelines |
| AML | 35% | CBN AML/CFT Rules + NFIU STR Requirements |
| TIN | 20% | FIRS TIN Mandate |
| Reporting | 15% | NITDA / CBN Reporting Requirements |

**Status thresholds:**
- `COMPLIANT` — score ≥ 80
- `AT RISK` — score 60–79
- `NON-COMPLIANT` — score < 60

**Response also includes** prioritized action items (CRITICAL / HIGH / MEDIUM).

**Available institution IDs (mock):** `inst-moniepoint`, `inst-kuda`, `inst-opay`
""",
)
async def compliance_posture(institution_id: str):
    return await get_compliance_posture(institution_id)


@router.get(
    "/suptech/report",
    summary="SupTech Sector Compliance Report (Regulator View)",
    description="""
**For CBN/NITDA regulators only.**

Returns sector-wide compliance posture across all monitored institutions,
replacing annual self-reporting with real-time data.

**Response includes:**
- Sector average compliance score
- Per-institution breakdown (sorted by score ascending — most at-risk first)
- Regulator alerts for CRITICAL and WARNING institutions
- Frameworks monitored

**This endpoint directly addresses NITDA Problem 2:**
*"Support real-time compliance assessment and reporting"*

Institutions submit structured compliance evidence via API → NITDA/CBN sees
real-time posture per institution per framework.
""",
)
async def suptech_report():
    return await get_suptech_report()


@router.get(
    "/suptech/heatmap",
    summary="Sector Compliance Heatmap",
    description="""
Returns compliance risk aggregated by industry sector.

Enables CBN/NITDA to identify which sectors carry the highest compliance risk
and prioritize regulatory intervention accordingly.

**Response:** List of sectors with average compliance score, risk level, and institution count.
""",
)
async def sector_heatmap():
    return await get_sector_heatmap()

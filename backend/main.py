from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from core.request_context import RequestContextMiddleware
from core.rate_limit import RateLimitMiddleware
from core.config import get_settings
from core.exception_handlers import register_exception_handlers
from dependencies import get_rate_limiter
from routers import aml, auth, compliance, fraud, kyc, regulatory, tax
from schemas.common import HealthResponse

settings = get_settings()

app = FastAPI(
    title="WeGoComply API",
    version="1.1.0",
    description="""
## WeGoComply — AI-Powered Compliance Platform for Nigerian Financial Institutions

WeGoComply automates KYC/KYB verification, real-time AML transaction monitoring,
TIN reconciliation, and regulatory intelligence for Nigerian fintechs, banks, and PSPs.

---

### Authentication

All endpoints (except `/`) require a **Bearer token** in the `Authorization` header.

**Mock mode** (default — no real token needed):
```
X-Mock-Roles: admin
X-Mock-User: demo-admin
```

**Live mode** (Azure AD B2C):
```
Authorization: Bearer <azure_ad_b2c_token>
```

---

### Modules

| Module | Prefix | Description |
|--------|--------|-------------|
| **KYC** | `/api/kyc` | Identity verification — NIN, BVN, facial match, risk scoring |
| **AML** | `/api/aml` | Transaction monitoring — anomaly detection, STR generation |
| **Tax** | `/api/tax` | TIN verification, bill reporting, annual return filing |
| **Regulatory** | `/api/regulatory` | AI-summarized CBN/FIRS/SEC/FCCPC updates |
| **Compliance** | `/api/compliance` | Real-time posture scoring + SupTech regulator view |
| **Fraud** | `/api/fraud` | XGBoost + Isolation Forest fraud detection |
| **Auth** | `/api/auth` | Session info |

---

### Regulatory Frameworks Covered

- **CBN** AML/CFT Rules · KYC Guidelines · Risk-Based Cybersecurity Framework 2024
- **FIRS** TIN Mandate · ATRS Bill Reporting · Annual Return (TaxPro Max)
- **NFIU** Suspicious Transaction Report (STR) requirements
- **NITDA** Code of Practice · Data Localisation Rules
- **NDPC** NDPA 2023 · GAID 2025

---

### External Integrations

- **Dojah API** — NIN/BVN verification
- **FIRS ATRS** — TIN verification, bill reporting (`FIRS_MODE=mock|live`)
- **Azure Face API** — Facial liveness + biometric verification
- **Azure Document Intelligence** — ID data extraction
- **Azure OpenAI GPT-4o** — STR generation, regulatory summarization

---

### Environment Modes

Set `WEGOCOMPLY_MODE=mock` (default) for demo/testing — all external API calls
return realistic mock responses. Set `WEGOCOMPLY_MODE=live` for production.
""",
    contact={
        "name": "WeGoComply Team",
        "email": "team@wegocomply.com",
        "url": "https://github.com/jvcByte/WeGoComply",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Auth",
            "description": "Authentication and session management. Returns current user info.",
        },
        {
            "name": "KYC",
            "description": """
**Know Your Customer / Know Your Business**

Multi-source identity verification using NIN, BVN, facial recognition, and AI risk scoring.

**Regulatory basis:** CBN KYC Guidelines, Section 2.1 — all financial institutions must
complete customer due diligence within 30 days of account opening.

**External APIs:** Dojah (NIN/BVN) · Azure Face API · Azure Document Intelligence
""",
        },
        {
            "name": "AML",
            "description": """
**Anti-Money Laundering Transaction Monitoring**

Real-time transaction analysis using Isolation Forest ML + CBN rule engine.
Auto-generates NFIU-compliant Suspicious Transaction Reports (STRs).

**Regulatory basis:** CBN AML/CFT Rules · CBN March 2026 Baseline Standards for
Automated AML Solutions · NFIU STR filing requirements (24-hour deadline).

**CBN Rules enforced:**
- `LARGE_CASH_TRANSACTION` — amount ≥ ₦5,000,000
- `UNUSUAL_HOURS` — transaction before 05:00 or after 23:00
- `HIGH_VALUE_TRANSFER` — transfer > ₦1,000,000

**AI:** Azure OpenAI GPT-4o for STR narrative generation.
""",
        },
        {
            "name": "Tax",
            "description": """
**Tax ID (TIN) Verification · Bill Reporting · Annual Returns**

Integrates with FIRS ATRS (Automated Tax Remittance System) for:
- TIN verification against FIRS database
- Real-time bill/receipt submission to FIRS
- Annual tax return aggregation for TaxPro Max upload

**Regulatory basis:** Nigeria Tax Administration Act 2025 · FIRS TIN Mandate
(accounts restricted above ₦500,000 without verified TIN from April 1, 2026).

**FIRS ATRS API:**
- Dev: `https://api-dev.i-fis.com`
- Prod: `https://atrs-api.firs.gov.ng`
- Auth: OAuth 2.0 Bearer Token
- Signing: MD5 SID (client_secret + bill fields)

Switch between mock and live: `FIRS_MODE=mock|live` in `.env`
""",
        },
        {
            "name": "Regulatory",
            "description": """
**Regulatory Intelligence Feed**

AI-powered monitoring and summarization of CBN, FIRS, SEC, FCCPC, and NITDA circulars.

**Features:**
- Latest regulatory updates with AI-extracted action items and deadlines
- Paste any regulatory circular text for instant plain-English summary
- Urgency classification: HIGH / MEDIUM / LOW
- Affected operations mapping

**AI:** Azure OpenAI GPT-4o for circular analysis and obligation extraction.
""",
        },
        {
            "name": "Compliance Posture",
            "description": """
**Real-Time Compliance Posture Scoring**

Calculates a 0–100 compliance score across 4 pillars for each institution.
Provides a SupTech view for CBN/NITDA regulators.

**Scoring formula:**
```
Overall = (KYC × 30%) + (AML × 35%) + (TIN × 20%) + (Reporting × 15%)
```

**Status thresholds:**
- ≥ 80 → COMPLIANT
- 60–79 → AT RISK
- < 60 → NON-COMPLIANT

**SupTech endpoints** provide sector-wide visibility for regulators,
replacing annual self-reporting with real-time data.
""",
        },
        {
            "name": "Fraud Detection",
            "description": """
**Advanced Fraud Detection**

XGBoost + Isolation Forest hybrid model for transaction fraud scoring.
Provides explainable fraud risk scores with feature importance.
""",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=list(settings.cors_methods),
    allow_headers=list(settings.cors_headers),
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=get_rate_limiter(),
    enabled=settings.rate_limit_enabled,
)

register_exception_handlers(app)

app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(kyc.router,        prefix="/api/kyc",        tags=["KYC"])
app.include_router(aml.router,        prefix="/api/aml",        tags=["AML"])
app.include_router(fraud.router,      prefix="/api/fraud",      tags=["Fraud Detection"])
app.include_router(tax.router,        prefix="/api/tax",        tags=["Tax"])
app.include_router(regulatory.router, prefix="/api/regulatory", tags=["Regulatory"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance Posture"])


@app.on_event("startup")
async def validate_settings() -> None:
    settings.validate_runtime()
    get_rate_limiter().validate_connection()


@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Auth"],
    summary="Health Check",
    description="Returns API status, version, and current operating mode (mock/live).",
)
def health() -> HealthResponse:
    return HealthResponse(
        status="WeGoComply running",
        version=settings.app_version,
        mode=settings.mode.value,
    )

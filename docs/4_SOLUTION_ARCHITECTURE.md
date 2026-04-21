# 4. Solution Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WeGoComply Platform                              │
│                    Azure-Native SaaS Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                    │
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Fintech App    │  │  Compliance      │  │  Regulator Dashboard    │  │
│  │  (API Consumer) │  │  Dashboard       │  │  (SupTech View)         │  │
│  │                 │  │  React + Tailwind│  │  CBN / NITDA            │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────────┬─────────────┘  │
└───────────┼─────────────────────┼────────────────────────┼────────────────┘
            │                     │                        │
            └─────────────────────┼────────────────────────┘
                                  │ HTTPS / REST API
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                               │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  FastAPI (Python) — Azure App Service                               │ │
│  │                                                                     │ │
│  │  Auth Middleware (OAuth2 / Mock)  │  Rate Limiter  │  Audit Logger  │ │
│  │                                                                     │ │
│  │  /api/kyc/*    /api/aml/*    /api/tax/*    /api/compliance/*        │ │
│  │  /api/regulatory/*                                                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐
│   KYC SERVICE     │  │   AML SERVICE     │  │   TAX SERVICE             │
│                   │  │                   │  │                           │
│ • NIN Verify      │  │ • Isolation Forest│  │ • FIRS ATRS Client        │
│ • BVN Verify      │  │   ML Model        │  │ • TIN Verification        │
│ • Face Match      │  │ • Rules Engine    │  │ • Bulk Verification       │
│ • Risk Scoring    │  │ • STR Generation  │  │ • Bill Reporting          │
│                   │  │                   │  │ • Annual Summary          │
└────────┬──────────┘  └────────┬──────────┘  └───────────┬───────────────┘
         │                      │                          │
         ▼                      ▼                          ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐
│  EXTERNAL APIs    │  │  AZURE AI LAYER   │  │  FIRS ATRS API            │
│                   │  │                   │  │                           │
│ • Dojah API       │  │ • Azure OpenAI    │  │ Dev:  api-dev.i-fis.com   │
│   NIN/BVN/TIN     │  │   GPT-4o          │  │ Prod: atrs-api.firs.gov.ng│
│ • NIMC NIN API    │  │ • Azure Face API  │  │                           │
│ • NIBSS BVN       │  │ • Azure Doc Intel │  │ Auth: OAuth2 Bearer Token │
│ • JTB TIN Portal  │  │ • Azure ML        │  │ Sign: MD5 SID             │
└───────────────────┘  └───────────────────┘  └───────────────────────────┘
                                  │
┌──────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                      │
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  PostgreSQL      │  │  Azure Blob     │  │  Audit Log              │  │
│  │  Azure Cosmos DB │  │  Storage        │  │  (JSONL)                │  │
│  │                  │  │                 │  │                         │  │
│  │  • customers     │  │  • ID documents │  │  • All API calls        │  │
│  │  • transactions  │  │  • Selfies      │  │  • User actions         │  │
│  │  • str_reports   │  │  • STR reports  │  │  • System events        │  │
│  │  • tin_verify    │  │                 │  │                         │  │
│  │  • institutions  │  │                 │  │                         │  │
│  │  • audit_logs    │  │                 │  │                         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Frontend (React + Tailwind CSS)

| Page | Purpose | Key Features |
|------|---------|--------------|
| Dashboard | Real-time overview | KYC count, flagged transactions, TIN rate, STRs |
| KYC | Customer verification | NIN/BVN input, selfie upload, risk score display |
| AML Monitor | Transaction analysis | Batch analysis, anomaly scores, STR generation |
| Tax/TIN | TIN verification | Bulk upload, match rate, deadline risk |
| Regulatory | Compliance intelligence | AI-summarized circulars, action items |
| Compliance Posture | Scoring dashboard | 4-pillar scores, SupTech regulator view |

### Backend (FastAPI + Python)

| Router | Endpoints | Service |
|--------|-----------|---------|
| `/api/kyc` | `/verify` | KYCService → Dojah + Azure Face |
| `/api/aml` | `/monitor`, `/generate-str` | AMLService → ML + Azure OpenAI |
| `/api/tax` | `/verify-tin`, `/bulk-verify` | TaxService → FIRSClient |
| `/api/compliance` | `/posture/{id}`, `/suptech/report` | ComplianceService |
| `/api/regulatory` | `/updates`, `/summarize` | RegulatoryService → Azure OpenAI |
| `/api/auth` | `/me` | AuthService → Mock / Azure AD B2C |

### ML Model (Isolation Forest)

```python
# Trained on normal Nigerian transaction patterns
# Features: [amount_ngn, hour_of_day]
# Contamination: 5% (expects 5% of transactions to be anomalous)

model = IsolationForest(contamination=0.05, random_state=42)
model.fit(normal_transactions)

# Output:
# score > 0  → CLEAN (normal pattern)
# score < 0  → ANOMALY (unusual pattern)
# score < -0.3 → HIGH CONFIDENCE ANOMALY
```

### FIRS ATRS Client

```
Authentication:  OAuth 2.0 password grant → Bearer token (24hr expiry)
TIN Verify:      GET /v1/taxpayer/verify?tin={tin}
Bill Report:     POST /v1/bills/report (with MD5 SID signature)
Mode Switch:     FIRS_MODE=mock → FIRS_MODE=live (zero code change)
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
│                                                             │
│  Layer 1: Transport    TLS 1.3 (all API calls)             │
│  Layer 2: Auth         OAuth2 Bearer / Azure AD B2C        │
│  Layer 3: Authorization RBAC (admin, compliance_officer,   │
│                         analyst, auditor, regulator)        │
│  Layer 4: Data         AES-256 at rest                     │
│  Layer 5: Audit        Immutable JSONL audit log           │
│  Layer 6: Rate Limit   60 requests/minute per client       │
│  Layer 7: Data Privacy NDPR compliant, PII masking         │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
GitHub Repository
      │
      ▼ GitHub Actions CI/CD
┌─────────────────────────────────────────────────────────────┐
│                    Azure Cloud                               │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │  Azure App       │    │  Azure Static Web Apps       │  │
│  │  Service         │    │  (React Frontend)            │  │
│  │  (FastAPI)       │    └──────────────────────────────┘  │
│  └──────────────────┘                                       │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │  Azure Cosmos DB │    │  Azure Blob Storage          │  │
│  │  (Data)          │    │  (Documents)                 │  │
│  └──────────────────┘    └──────────────────────────────┘  │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │  Azure OpenAI    │    │  Azure AI Services           │  │
│  │  (GPT-4o)        │    │  Face API + Doc Intelligence │  │
│  └──────────────────┘    └──────────────────────────────┘  │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │  Azure ML        │    │  Azure Key Vault             │  │
│  │  (AML Model)     │    │  (Secrets Management)        │  │
│  └──────────────────┘    └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18, Vite, Tailwind CSS | Dashboard UI |
| Charts | Recharts, RadialBarChart | Compliance visualizations |
| Backend | Python 3.12, FastAPI, Uvicorn | REST API |
| ML | scikit-learn (Isolation Forest) | AML anomaly detection |
| AI — STR | Azure OpenAI GPT-4o | Report generation |
| AI — KYC | Azure Face API | Facial verification |
| AI — Docs | Azure Document Intelligence | ID data extraction |
| Identity | Dojah API | NIN/BVN verification |
| Tax | FIRS ATRS API | TIN verification + bill reporting |
| Database | PostgreSQL / Azure Cosmos DB | Data persistence |
| Storage | Azure Blob Storage | Document storage |
| Auth | Azure AD B2C / Mock | Authentication |
| Secrets | Azure Key Vault | Credential management |
| Audit | JSONL file / Azure Monitor | Immutable audit trail |
| CI/CD | GitHub Actions | Automated deployment |

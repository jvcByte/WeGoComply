# WeGoComply — System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WeGoComply Platform                       │
│                     (Azure-Native SaaS)                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│   Fintech/Bank   │────────▶│  API Gateway     │
│   Integration    │         │  (Azure APIM)    │
└──────────────────┘         └──────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ KYC Module   │  │ AML Module   │  │ Tax Module   │
         └──────────────┘  └──────────────┘  └──────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
                         ┌─────────────────────┐
                         │  Azure AI Services  │
                         ├─────────────────────┤
                         │ • Document Intel    │
                         │ • Face API          │
                         │ • OpenAI GPT-4o     │
                         │ • ML Workspace      │
                         └─────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ Dojah API    │  │ Azure Cosmos │  │ Blob Storage │
         │ (NIN/BVN/TIN)│  │ DB           │  │ (Documents)  │
         └──────────────┘  └──────────────┘  └──────────────┘
```

## Component Breakdown

### 1. Frontend Layer
- **Technology**: React + Tailwind CSS on Azure Static Web Apps
- **Features**:
  - Compliance dashboard with real-time metrics
  - KYC onboarding interface
  - AML transaction monitor
  - TIN verification console
  - Regulatory intelligence feed

### 2. API Layer
- **Technology**: Python FastAPI on Azure App Service
- **Endpoints**:
  - `/api/kyc/verify` — Multi-source identity verification
  - `/api/aml/monitor` — Real-time transaction analysis
  - `/api/aml/generate-str` — Auto STR generation
  - `/api/tax/bulk-verify` — Bulk TIN reconciliation
  - `/api/regulatory/updates` — AI-summarized circulars

### 3. AI/ML Layer
- **Azure AI Document Intelligence**: Extract data from ID cards, driver's licenses
- **Azure Face API**: Facial verification + liveness detection
- **Azure OpenAI (GPT-4o)**: 
  - Generate explainable STR reports
  - Summarize CBN/FIRS/SEC circulars
  - Risk narrative generation
- **Azure ML**: Host Isolation Forest model for anomaly detection

### 4. Data Layer
- **Azure Cosmos DB**: Customer records, transaction logs, audit trails
- **Azure Blob Storage**: ID documents, selfies, compliance reports
- **Redis Cache**: Session management, rate limiting

### 5. External Integrations
- **Dojah API**: NIN lookup, BVN verification, TIN matching (Nigerian-specific)
- **CBN/FIRS APIs**: Direct regulatory data feeds (when available)

## Data Flow

### KYC Verification Flow
```
User Upload (NIN + BVN + Selfie)
    ↓
Azure Document Intelligence extracts ID data
    ↓
Dojah API verifies NIN + BVN
    ↓
Azure Face API performs facial match
    ↓
ML model calculates risk score
    ↓
Result: VERIFIED/FAILED + Risk Level (LOW/MEDIUM/HIGH)
```

### AML Monitoring Flow
```
Transaction batch submitted
    ↓
Azure ML Isolation Forest detects anomalies
    ↓
Rule engine checks CBN thresholds (₦5M+, unusual hours, etc.)
    ↓
Flagged transactions → Azure OpenAI generates STR
    ↓
STR stored in Cosmos DB + sent to compliance officer dashboard
```

### TIN Verification Flow
```
Bulk customer records uploaded
    ↓
Dojah API batch TIN verification
    ↓
Name matching algorithm (fuzzy match)
    ↓
Results: MATCHED/NOT_FOUND/NAME_MISMATCH
    ↓
Dashboard shows match rate + deadline risk assessment
```

## Security & Compliance

- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Authentication**: Azure AD B2C for institution login
- **Authorization**: Role-based access control (RBAC)
- **Audit**: Immutable logs in Cosmos DB with blockchain option
- **Data Residency**: Azure Nigeria regions (when available) or West Europe
- **Compliance**: NDPR (Nigeria Data Protection Regulation) compliant

## Scalability

- **Auto-scaling**: Azure App Service scales based on CPU/memory
- **Caching**: Redis for frequently accessed data
- **CDN**: Azure CDN for static assets
- **Load Balancing**: Azure Load Balancer for API traffic
- **Expected Load**: 10,000+ KYC verifications/day, 1M+ transactions/day

## Deployment

- **CI/CD**: GitHub Actions → Azure DevOps
- **Environments**: Dev, Staging, Production
- **Monitoring**: Azure Monitor + Application Insights
- **Alerting**: Real-time alerts for API failures, high error rates

## Cost Estimate (Azure Free Tier → Production)

| Service | Free Tier | Production (Est.) |
|---------|-----------|-------------------|
| App Service | Free | ~$50/month |
| Cosmos DB | Free 1000 RU/s | ~$100/month |
| AI Services | Free tier | ~$200/month |
| Blob Storage | 5GB free | ~$20/month |
| **Total** | **$0** | **~$370/month** |

Scales with usage. Enterprise pricing available for high-volume institutions.

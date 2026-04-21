# 3. Workflow & User Journey

## Overview

WeGoComply serves three user types with distinct journeys:
1. **End Customer** (Adaeze) — gets onboarded and transacts
2. **Compliance Officer** (Ngozi) — monitors and responds to alerts
3. **Regulator** (Dr. Adeyemi) — monitors sector-wide compliance

---

## Journey 1: End Customer Onboarding (KYC + TIN)

```
ADAEZE DOWNLOADS MONIEPOINT APP
              │
              ▼
    ┌─────────────────────┐
    │  Fills signup form  │
    │  Name, Phone, Email │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Enters NIN + BVN   │
    │  Uploads selfie     │
    └─────────────────────┘
              │
              ▼ Moniepoint calls WeGoComply API
    ┌─────────────────────────────────────────┐
    │         WeGoComply KYC Engine           │
    │                                         │
    │  1. Dojah API → verify NIN vs NIMC      │
    │  2. Dojah API → verify BVN vs CBN       │
    │  3. Azure Face API → match selfie to ID │
    │  4. ML model → calculate risk score     │
    └─────────────────────────────────────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
   VERIFIED      FAILED
   (87 secs)        │
        │           ▼
        │    Notify Adaeze:
        │    "Verification failed.
        │     Please retry or visit branch."
        ▼
    ┌─────────────────────┐
    │  Check TIN status   │
    └─────────────────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
   TIN EXISTS   NO TIN
        │           │
        ▼           ▼
   Verify TIN   Show message:
   vs FIRS      "Register free TIN
                 at jtb.gov.ng"
                     │
                     ▼
                User registers
                TIN (5 mins)
                     │
                     ▼
                Returns with TIN
                     │
                     ▼
              WeGoComply verifies
              TIN vs FIRS ATRS
                     │
              ┌──────┴──────┐
              ▼             ▼
           MATCHED      NOT FOUND /
              │         NAME MISMATCH
              ▼             │
    Account fully        Notify user
    activated ✓          to update FIRS
```

**Time: Under 2 minutes (vs 3-5 days manually)**

---

## Journey 2: Compliance Officer — AML Monitoring

```
NGOZI STARTS HER SHIFT AT 9:00 AM
              │
              ▼
    ┌─────────────────────────────┐
    │  Opens WeGoComply Dashboard │
    │  Sees overnight summary:    │
    │  • 1.5M transactions        │
    │  • 23 flagged               │
    │  • 7 STRs required          │
    └─────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  Clicks AML Monitor page    │
    │  Sees flagged transactions  │
    │  sorted by risk level       │
    └─────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  Reviews TXN-7891234        │
    │  ₦7.5M at 2:34 AM          │
    │  Rules: LARGE_CASH,         │
    │         UNUSUAL_HOURS,      │
    │         HIGH_VALUE_TRANSFER │
    │  Risk: HIGH                 │
    └─────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  Clicks "Generate STR"      │
    │                             │
    │  Azure OpenAI generates:    │
    │  • Report reference         │
    │  • Transaction summary      │
    │  • Grounds for suspicion    │
    │  • Recommended action       │
    └─────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  Ngozi reviews STR          │
    │  Freezes customer account   │
    │  Submits STR to NFIU        │
    │  (within 24hr CBN deadline) │
    └─────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  Checks Regulatory Feed     │
    │  Sees new CBN circular      │
    │  AI summary: 2 sentences    │
    │  Action: update by June 30  │
    └─────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  Checks Compliance Posture  │
    │  Overall score: 84.2/100    │
    │  Status: COMPLIANT ✓        │
    │  2 action items pending     │
    └─────────────────────────────┘
```

**Time: 30 minutes (vs 8 hours manually)**

---

## Journey 3: Regulator — SupTech Monitoring

```
DR. ADEYEMI OPENS WEGOCOMPLY SUPTECH VIEW
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Sector Overview Dashboard          │
    │  • 3 institutions monitored         │
    │  • Sector average: 67.9/100         │
    │  • 1 COMPLIANT, 2 AT RISK           │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Regulator Alerts                   │
    │  🔴 CRITICAL: OPay score 52.1/100   │
    │  ⚠  WARNING: Kuda score 67.3/100    │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Clicks OPay row                    │
    │  Sees pillar breakdown:             │
    │  • KYC: 63.4 (120 unreviewed HIGH)  │
    │  • AML: 44.5 (8 late STRs!)         │
    │  • TIN: 50.3 (850k restricted)      │
    │  • Reporting: 26.7 (2 missed)       │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Issues regulatory notice to OPay  │
    │  Schedules compliance audit         │
    │  Sets 30-day remediation deadline   │
    └─────────────────────────────────────┘
```

**Replaces: Annual self-reporting with real-time sector visibility**

---

## Journey 4: TIN Issuance & Annual Tax Filing

```
MONIEPOINT PREPARES ANNUAL TAX RETURN
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Compliance officer uploads         │
    │  10M customer records to            │
    │  WeGoComply bulk TIN verify         │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  WeGoComply authenticates           │
    │  with FIRS ATRS (OAuth 2.0)         │
    │  POST /oauth2/token                 │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Batch TIN verification             │
    │  GET /v1/taxpayer/verify?tin=...    │
    │  500 records/second                 │
    │  6 hours for 10M records            │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Results:                           │
    │  • 9.1M MATCHED (91%)               │
    │  • 900K NOT_FOUND                   │
    │  • SMS sent to 900K customers       │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Throughout the year:               │
    │  WeGoComply submits each            │
    │  taxable transaction to FIRS        │
    │  POST /v1/bills/report              │
    │  (with MD5 SID signature)           │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Year-end:                          │
    │  WeGoComply generates               │
    │  annual tax summary                 │
    │  GET /api/tax/annual-summary        │
    └─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Accountant uploads to              │
    │  TaxPro Max portal                  │
    │  Files CIT return                   │
    │  Gets Tax Clearance Certificate     │
    └─────────────────────────────────────┘
```

---

## System Integration Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    FINTECH (e.g. Moniepoint)                      │
│                                                                    │
│  Customer App  →  Moniepoint Backend  →  WeGoComply API          │
└──────────────────────────────────────────────────────────────────┘
                                                │
                              ┌─────────────────┼─────────────────┐
                              ▼                 ▼                 ▼
                    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                    │  KYC Module  │  │  AML Module  │  │  Tax Module  │
                    │              │  │              │  │              │
                    │ Dojah API    │  │ ML Model     │  │ FIRS ATRS    │
                    │ Azure Face   │  │ Rules Engine │  │ OAuth2 + MD5 │
                    │ Azure Doc    │  │ Azure OpenAI │  │              │
                    └──────────────┘  └──────────────┘  └──────────────┘
                              │                 │                 │
                              └─────────────────┼─────────────────┘
                                                │
                              ┌─────────────────┼─────────────────┐
                              ▼                 ▼                 ▼
                    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                    │  PostgreSQL  │  │  Audit Logs  │  │  Regulatory  │
                    │  Database    │  │              │  │  Feed        │
                    └──────────────┘  └──────────────┘  └──────────────┘
                                                │
                                                ▼
                              ┌─────────────────────────────────┐
                              │     Compliance Posture Score     │
                              │     (Real-time 0-100 score)      │
                              └─────────────────────────────────┘
                                                │
                              ┌─────────────────┴─────────────────┐
                              ▼                                   ▼
                    ┌──────────────────┐               ┌──────────────────┐
                    │  Institution     │               │  SupTech View    │
                    │  Dashboard       │               │  (CBN/NITDA)     │
                    └──────────────────┘               └──────────────────┘
```

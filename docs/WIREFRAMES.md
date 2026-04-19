# WeGoComply — UI Wireframes

## Dashboard (Home)

```
┌─────────────────────────────────────────────────────────────────┐
│ WeGoComply                                    [User] [Settings]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Compliance Overview                                              │
│  Real-time monitoring across KYC, AML, and Tax compliance        │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐│
│  │   1,284      │ │      23      │ │    91.4%     │ │    7    ││
│  │ KYC Verified │ │   Flagged    │ │  TIN Match   │ │  STRs   ││
│  │   Today      │ │ Transactions │ │     Rate     │ │Generated││
│  │   +12%       │ │   +3 new     │ │  ↑ from 87%  │ │This week││
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘│
│                                                                   │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐│
│  │ Transaction Monitoring      │ │ KYC Verifications Today     ││
│  │ (7 days)                    │ │                             ││
│  │                             │ │                             ││
│  │  [Bar Chart]                │ │  [Line Chart]               ││
│  │   Clean vs Flagged          │ │   Hourly trend              ││
│  │                             │ │                             ││
│  └─────────────────────────────┘ └─────────────────────────────┘│
│                                                                   │
│  Active Regulatory Alerts                                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [CBN] Real-time AML monitoring required by June 30    [HIGH]││
│  │ [FIRS] TIN verification mandate — restrictions Apr 1  [HIGH]││
│  │ [FCCPC] Digital lender registration deadline Apr 30 [MEDIUM]││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## KYC Verification Page

```
┌─────────────────────────────────────────────────────────────────┐
│ WeGoComply                                    [User] [Settings]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🛡 KYC Verification                                              │
│  Multi-source identity verification with AI risk scoring          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Verify New Customer                                          ││
│  │                                                              ││
│  │  NIN (National Identification Number)                       ││
│  │  [_____________________]                                    ││
│  │                                                              ││
│  │  BVN (Bank Verification Number)                             ││
│  │  [_____________________]                                    ││
│  │                                                              ││
│  │  Selfie / Photo ID                                          ││
│  │  [Choose File] No file chosen                               ││
│  │                                                              ││
│  │  [Verify Identity]                                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ✓ VERIFIED                                      [LOW RISK]  ││
│  │ Identity verification complete                              ││
│  │                                                              ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       ││
│  │  │ NIN Verified │ │ BVN Verified │ │  Face Match  │       ││
│  │  │   ✓ Yes      │ │   ✓ Yes      │ │   ✓ Yes      │       ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘       ││
│  │                                                              ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       ││
│  │  │Face Confidence│ │     Name     │ │  Risk Score  │       ││
│  │  │     94%      │ │  Demo User   │ │     0.12     │       ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## AML Transaction Monitor

```
┌─────────────────────────────────────────────────────────────────┐
│ WeGoComply                                    [User] [Settings]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ⚠ AML Transaction Monitor                                       │
│  AI anomaly detection + auto STR generation (NFIU-compliant)     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Sample transaction batch (5 transactions)  [Run Analysis]   ││
│  │                                                              ││
│  │  ID      Customer   Amount    Type      Time    Channel     ││
│  │  TXN-001 CUST-4421  7,500,000 transfer  02:34   mobile     ││
│  │  TXN-002 CUST-1102     45,000 deposit   10:15   web        ││
│  │  TXN-003 CUST-8834  2,300,000 withdraw  23:58   atm        ││
│  │  TXN-004 CUST-3310     12,000 transfer  14:22   pos        ││
│  │  TXN-005 CUST-9901  9,800,000 transfer  03:11   web        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                         │
│  │    5     │ │    3     │ │    2     │                         │
│  │ Analyzed │ │ Flagged  │ │  Clean   │                         │
│  └──────────┘ └──────────┘ └──────────┘                         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ TXN-001                                          [HIGH RISK] ││
│  │ Customer: CUST-4421 · ₦7,500,000 · 2026-04-16T02:34:00     ││
│  │ [LARGE_CASH_TRANSACTION] [UNUSUAL_HOURS]                    ││
│  │                                          [Generate STR]      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 📄 Suspicious Transaction Report (STR)                      ││
│  │                                                              ││
│  │  Report Reference: STR-TXN001                               ││
│  │  Reporting Institution: WeGoComply Demo Bank                ││
│  │  Subject Name: CUST-4421                                    ││
│  │  Transaction Summary: Customer conducted a transfer of      ││
│  │  ₦7,500,000 via mobile at 2:34am...                        ││
│  │  Grounds for Suspicion: Amount exceeds ₦5M threshold...     ││
│  │  Recommended Action: Freeze account pending investigation...││
│  │                                                              ││
│  │  Ready for submission to NFIU. Reference: STR-TXN001        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## TIN Verification

```
┌─────────────────────────────────────────────────────────────────┐
│ WeGoComply                                    [User] [Settings]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📄 Tax ID (TIN) Verification                                    │
│  Bulk TIN matching against FIRS — meet mandate before sanctions │
│                                                                   │
│  ⚠ FIRS Mandate: Accounts without verified TINs restricted      │
│     above ₦500,000 effective April 1, 2026                      │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Sample customer records (5)      [Run Bulk Verification]    ││
│  │                                                              ││
│  │  Customer ID   Name                    TIN                  ││
│  │  CUST-001      Adaeze Okonkwo         1234567890           ││
│  │  CUST-002      Emeka Nwosu            0987654321           ││
│  │  CUST-003      Fatima Aliyu           1122334455           ││
│  │  CUST-004      Chukwuemeka Eze        5566778899           ││
│  │  CUST-005      Ngozi Adeyemi          9988776655           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │    5     │ │    4     │ │    1     │ │  91.4%   │           │
│  │  Total   │ │ Matched  │ │  Failed  │ │Match Rate│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                   │
│  Deadline Risk: LOW — On track to meet FIRS mandate             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ✓ CUST-001  Adaeze Okonkwo              [MATCHED]  95%     ││
│  │ ✓ CUST-002  Emeka Nwosu                 [MATCHED]  95%     ││
│  │ ✗ CUST-003  Fatima Aliyu                [NOT_FOUND]  0%    ││
│  │ ✓ CUST-004  Chukwuemeka Eze             [MATCHED]  95%     ││
│  │ ✓ CUST-005  Ngozi Adeyemi               [MATCHED]  95%     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Regulatory Intelligence

```
┌─────────────────────────────────────────────────────────────────┐
│ WeGoComply                                    [User] [Settings]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🔔 Regulatory Intelligence                          [Refresh]   │
│  AI-summarized CBN, FIRS, SEC, FCCPC updates mapped to ops      │
│                                                                   │
│  [ALL] [HIGH] [MEDIUM] [LOW]                                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [CBN] Baseline Standards for Automated AML Solutions [HIGH] ││
│  │                                                   2026-03-15 ││
│  │                                                              ││
│  │ All financial institutions must implement real-time AML     ││
│  │ transaction monitoring by June 30, 2026.                    ││
│  │                                                              ││
│  │ Action Required:                                            ││
│  │ Deploy automated AML monitoring system and configure        ││
│  │ real-time STR filing within 24 hours of detection.          ││
│  │                                                              ││
│  │ Deadline: 2026-06-30                                        ││
│  │ [AML] [Transaction Monitoring] [STR Filing]                 ││
│  │                                                     [Source] ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [FIRS] Mandatory TIN Verification for Accounts      [HIGH] ││
│  │                                                   2026-01-10 ││
│  │                                                              ││
│  │ Accounts without verified TINs will be restricted from      ││
│  │ transactions above ₦500,000 from April 1, 2026.            ││
│  │                                                              ││
│  │ Action Required:                                            ││
│  │ Complete bulk TIN verification for all existing customers   ││
│  │ and enforce TIN collection for new onboarding.              ││
│  │                                                              ││
│  │ Deadline: 2026-04-01                                        ││
│  │ [KYC] [Account Management] [Tax Compliance]                 ││
│  │                                                     [Source] ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Mobile Responsive View

```
┌─────────────────────┐
│ WeGoComply      [≡] │
├─────────────────────┤
│                     │
│ Compliance Overview │
│                     │
│ ┌─────────────────┐ │
│ │     1,284       │ │
│ │  KYC Verified   │ │
│ │     Today       │ │
│ └─────────────────┘ │
│                     │
│ ┌─────────────────┐ │
│ │       23        │ │
│ │    Flagged      │ │
│ │  Transactions   │ │
│ └─────────────────┘ │
│                     │
│ ┌─────────────────┐ │
│ │     91.4%       │ │
│ │  TIN Match Rate │ │
│ └─────────────────┘ │
│                     │
│ [View Details]      │
│                     │
└─────────────────────┘
```

All screens are fully responsive and optimized for mobile compliance officers.

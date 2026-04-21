# 2. Policy Pack — Compliance Rules Engine

WeGoComply enforces 5 core compliance rules drawn directly from CBN, FIRS, and NFIU regulations.

---

## Policy Table

| # | Rule Name | Regulatory Source | Trigger Condition | Action | Severity |
|---|-----------|-------------------|-------------------|--------|----------|
| R1 | Large Cash Transaction | CBN AML/CFT Rules, Section 4.2 | Transaction amount ≥ ₦5,000,000 | Flag transaction, recommend STR | HIGH |
| R2 | Unusual Hours Transaction | CBN Risk-Based Cybersecurity Framework 2024 | Transaction timestamp: hour < 05:00 or hour > 23:00 | Flag transaction, escalate for review | MEDIUM |
| R3 | High-Value Transfer | CBN KYC Guidelines, Section 3.1 | Transfer type transaction AND amount > ₦1,000,000 | Flag transaction, verify counterparty | MEDIUM |
| R4 | Unverified TIN Account | FIRS TIN Mandate (Nigeria Tax Administration Act 2025) | Customer has no verified TIN AND transaction > ₦500,000 | Block transaction, notify customer | HIGH |
| R5 | KYC Incomplete | CBN KYC Guidelines, Section 2.1 | Customer NIN or BVN not verified after 30 days | Restrict account, trigger re-verification | HIGH |

---

## Rule Detail

### Rule R1 — Large Cash Transaction

```
IF transaction.amount >= 5,000,000 (NGN)
THEN
  → Add "LARGE_CASH_TRANSACTION" to rules_triggered
  → Set risk_level = "HIGH" (if also ML anomaly)
  → Set recommended_action = "GENERATE_STR"
  → Compliance officer must review within 24 hours
  → STR must be filed with NFIU within 24 hours of detection
```

**Regulatory Basis:**
CBN AML/CFT Regulations require all financial institutions to report cash transactions above ₦5 million to the Nigerian Financial Intelligence Unit (NFIU).

**Real Example:**
Chukwudi transfers ₦7.5M at 2:34 AM → R1 triggered → STR generated → NFIU notified.

---

### Rule R2 — Unusual Hours Transaction

```
IF transaction.timestamp.hour < 5 OR transaction.timestamp.hour > 23
THEN
  → Add "UNUSUAL_HOURS" to rules_triggered
  → Set risk_level = "MEDIUM" (escalates to HIGH if combined with R1 or R3)
  → Set recommended_action = "REVIEW"
  → Compliance officer must review within 24 hours
```

**Regulatory Basis:**
CBN Risk-Based Cybersecurity Framework 2024 requires monitoring of transactions outside normal business hours as a fraud and money laundering indicator.

**Real Example:**
₦50,000 transfer at 3:15 AM → R2 triggered → flagged for review (not STR, amount is low).

---

### Rule R3 — High-Value Transfer

```
IF transaction.transaction_type == "transfer"
AND transaction.amount > 1,000,000 (NGN)
THEN
  → Add "HIGH_VALUE_TRANSFER" to rules_triggered
  → Set risk_level = "MEDIUM"
  → Set recommended_action = "REVIEW"
  → Verify counterparty identity
  → Check source of funds if counterparty is unknown
```

**Regulatory Basis:**
CBN KYC Guidelines require enhanced due diligence for high-value transfers, particularly to unverified counterparties.

**Real Example:**
₦2.3M transfer to "Unknown Corp Ltd" → R3 triggered → counterparty verification required.

---

### Rule R4 — Unverified TIN Account

```
IF customer.tin_verified == FALSE
AND transaction.amount > 500,000 (NGN)
THEN
  → Block transaction
  → Return error: "TIN verification required for transactions above ₦500,000"
  → Send SMS/email to customer: "Register TIN at jtb.gov.ng"
  → Log restriction in compliance database
  → Notify compliance officer
```

**Regulatory Basis:**
Nigeria Tax Administration Act 2025 and FIRS mandate: accounts without verified TINs are restricted from transactions above ₦500,000 effective April 1, 2026.

**Real Example:**
Fatima tries to transfer ₦600,000 but has no TIN → R4 triggered → transaction blocked → SMS sent.

---

### Rule R5 — KYC Incomplete

```
IF customer.nin_verified == FALSE OR customer.bvn_verified == FALSE
AND customer.account_age_days > 30
THEN
  → Set account status = "RESTRICTED"
  → Block transactions above ₦50,000
  → Send notification: "Complete KYC to restore full account access"
  → Escalate to compliance officer if unresolved after 7 days
  → Flag in compliance posture score (KYC pillar penalty)
```

**Regulatory Basis:**
CBN KYC Guidelines require all financial institutions to complete customer due diligence within 30 days of account opening.

**Real Example:**
Emeka opened account 45 days ago but never completed NIN verification → R5 triggered → account restricted.

---

## Combined Rule Logic

When multiple rules trigger on the same transaction, the system escalates:

```
Single rule triggered:
  → risk_level = "MEDIUM"
  → recommended_action = "REVIEW"

Multiple rules triggered (2+):
  → risk_level = "HIGH"
  → recommended_action = "GENERATE_STR"

ML anomaly + any rule:
  → risk_level = "HIGH"
  → recommended_action = "GENERATE_STR"
  → Immediate compliance officer alert
```

**Example — Chukwudi's ₦7.5M at 2:34 AM:**
- R1 triggered (amount ≥ ₦5M) ✓
- R2 triggered (2:34 AM < 5:00 AM) ✓
- R3 triggered (transfer > ₦1M) ✓
- ML anomaly detected ✓
- Result: HIGH risk, GENERATE_STR, immediate alert

---

## Compliance Posture Scoring Formula

```
Overall Score = (KYC Score × 30%) + (AML Score × 35%) + (TIN Score × 20%) + (Reporting Score × 15%)

KYC Score   = avg(NIN rate, BVN rate, face rate) × 100 − (unreviewed_high_risk × 2)
AML Score   = (monitoring_coverage × 40%) + (review_rate × 30%) + (str_timeliness × 30%) − (late_strs × 5)
TIN Score   = (tin_verified / total_customers) × 100 − (restriction_rate × 50)
Rep Score   = (completed_actions / total_actions) × 100 − (missed_deadlines × 15)

COMPLIANT:     Score ≥ 80
AT RISK:       Score 60–79
NON-COMPLIANT: Score < 60
```

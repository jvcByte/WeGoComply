# 5. Rules Engine Logic Explanation

## Overview

WeGoComply's AML Rules Engine is a two-layer system that combines deterministic rule-based checks with probabilistic machine learning to detect suspicious transactions.

```
Transaction Input
      │
      ├──────────────────────────────────────┐
      ▼                                      ▼
┌─────────────────────┐          ┌─────────────────────────┐
│   ML Layer          │          │   Rules Layer           │
│   (Isolation Forest)│          │   (CBN Regulations)     │
│                     │          │                         │
│   Learns patterns   │          │   Enforces thresholds   │
│   Detects anomalies │          │   Guarantees compliance │
│   Reduces noise     │          │   Explainable results   │
└──────────┬──────────┘          └────────────┬────────────┘
           │                                  │
           └──────────────┬───────────────────┘
                          ▼
              ┌───────────────────────┐
              │   Decision Engine     │
              │                       │
              │   ML + Rules → Risk   │
              │   Level + Action      │
              └───────────────────────┘
```

---

## Layer 1: Machine Learning (Isolation Forest)

### What It Does

Isolation Forest is an unsupervised anomaly detection algorithm. It learns what "normal" looks like and flags anything that deviates significantly.

### How It Works

```
Training Phase (done once at startup):
─────────────────────────────────────
Normal Nigerian transaction patterns:
  [₦5,000 at 8am]   → NORMAL
  [₦10,000 at 2pm]  → NORMAL
  [₦50,000 at 11am] → NORMAL
  [₦100,000 at 3pm] → NORMAL
  [₦500,000 at 1pm] → NORMAL

Model learns: "Normal = ₦5k-₦1M during 8am-6pm"

Prediction Phase (every transaction):
──────────────────────────────────────
Input: [₦7,500,000, hour=2]

Model asks: "How many random splits needed to isolate this point?"
  → Few splits needed = ANOMALY (easy to isolate = unusual)
  → Many splits needed = NORMAL (hard to isolate = common)

Output:
  anomaly_score = -0.312  (negative = anomaly)
  is_anomaly = True
```

### Feature Extraction

```python
# Only 2 features used (keeps model fast and interpretable)
features = [
    transaction.amount,          # How much money
    transaction.timestamp.hour   # What time of day
]

# Example:
# Normal:    [50000, 14]   → score: +0.23  → CLEAN
# Suspicious: [7500000, 2] → score: -0.312 → ANOMALY
```

### Why Isolation Forest?

| Property | Benefit |
|----------|---------|
| Unsupervised | No labelled fraud data needed |
| Fast | O(n log n) — handles millions of transactions |
| Interpretable | Anomaly score is a clear number |
| Robust | Works even with imbalanced data (rare fraud) |
| Updatable | Retrain as new patterns emerge |

---

## Layer 2: Rules Engine (CBN Regulations)

### Rule Execution

```python
def _check_rules(transaction) -> list[str]:
    rules_triggered = []

    # Rule R1: CBN ₦5M threshold
    if transaction.amount >= 5_000_000:
        rules_triggered.append("LARGE_CASH_TRANSACTION")

    # Rule R2: Unusual hours
    hour = transaction.timestamp.hour
    if hour < 5 or hour > 23:
        rules_triggered.append("UNUSUAL_HOURS")

    # Rule R3: High-value transfer
    if transaction.transaction_type == "transfer" \
       and transaction.amount > 1_000_000:
        rules_triggered.append("HIGH_VALUE_TRANSFER")

    return rules_triggered
```

### Rule Execution Flow

```
Transaction arrives
        │
        ▼
Check R1: amount >= ₦5M?
  YES → add "LARGE_CASH_TRANSACTION"
  NO  → continue
        │
        ▼
Check R2: hour < 5 OR hour > 23?
  YES → add "UNUSUAL_HOURS"
  NO  → continue
        │
        ▼
Check R3: type=="transfer" AND amount > ₦1M?
  YES → add "HIGH_VALUE_TRANSFER"
  NO  → continue
        │
        ▼
Return list of triggered rules
```

---

## Layer 3: Decision Engine

### Risk Classification

```python
# Combine ML + Rules for final decision
if is_anomaly and rules_triggered:
    risk_level = "HIGH"
    recommended_action = "GENERATE_STR"

elif is_anomaly or rules_triggered:
    risk_level = "MEDIUM"
    recommended_action = "REVIEW"

else:
    risk_level = "LOW"
    recommended_action = "APPROVE"
```

### Decision Matrix

| ML Anomaly | Rules Triggered | Risk Level | Action | CBN Deadline |
|------------|----------------|------------|--------|--------------|
| ✓ Yes | ✓ Yes (2+) | HIGH | Generate STR | 24 hours |
| ✓ Yes | ✓ Yes (1) | HIGH | Generate STR | 24 hours |
| ✓ Yes | ✗ No | MEDIUM | Review | 24 hours |
| ✗ No | ✓ Yes (2+) | MEDIUM | Review | 24 hours |
| ✗ No | ✓ Yes (1) | MEDIUM | Review | 48 hours |
| ✗ No | ✗ No | LOW | Approve | N/A |

---

## Full Transaction Analysis Example

### Input: Chukwudi's Transaction

```json
{
  "transaction_id": "TXN-7891234",
  "customer_id": "CUST-4421",
  "amount": 7500000,
  "timestamp": "2026-04-21T02:34:00",
  "transaction_type": "transfer",
  "counterparty": "Unknown Corp Ltd",
  "channel": "mobile"
}
```

### Step 1: Feature Extraction

```python
features = [7500000, 2]  # [amount, hour]
```

### Step 2: ML Analysis

```python
score = model.decision_function([[7500000, 2]])[0]
# score = -0.312 (anomaly)

is_anomaly = model.predict([[7500000, 2]])[0] == -1
# is_anomaly = True
```

### Step 3: Rules Check

```python
rules = _check_rules(transaction)
# R1: 7500000 >= 5000000 → "LARGE_CASH_TRANSACTION" ✓
# R2: hour=2 < 5 → "UNUSUAL_HOURS" ✓
# R3: type="transfer" AND 7500000 > 1000000 → "HIGH_VALUE_TRANSFER" ✓
# rules = ["LARGE_CASH_TRANSACTION", "UNUSUAL_HOURS", "HIGH_VALUE_TRANSFER"]
```

### Step 4: Decision

```python
# is_anomaly=True AND rules_triggered=3
risk_level = "HIGH"
recommended_action = "GENERATE_STR"
```

### Output

```json
{
  "transaction_id": "TXN-7891234",
  "customer_id": "CUST-4421",
  "amount": 7500000,
  "anomaly_score": -0.312,
  "rules_triggered": [
    "LARGE_CASH_TRANSACTION",
    "UNUSUAL_HOURS",
    "HIGH_VALUE_TRANSFER"
  ],
  "risk_level": "HIGH",
  "recommended_action": "GENERATE_STR"
}
```

---

## Why Two Layers?

### ML Alone is Not Enough

```
Problem: ML might miss a ₦6M transfer at 2pm
  → Amount is unusual but time is normal
  → ML score: -0.05 (borderline)
  → ML says: CLEAN

But CBN Rule R1 catches it:
  → ₦6M >= ₦5M threshold
  → Rule says: LARGE_CASH_TRANSACTION
  → Final: MEDIUM risk, REVIEW
```

### Rules Alone is Not Enough

```
Problem: Rules miss a ₦50,000 transfer at 3am
  → Amount is below all thresholds
  → Rules say: CLEAN

But ML catches it:
  → Customer NEVER transacts at 3am
  → ML score: -0.28 (anomaly)
  → Final: MEDIUM risk, REVIEW
```

### Combined = Best of Both

```
ML catches:  Unknown patterns, behavioral anomalies
Rules catch: Known CBN violations, regulatory thresholds
Together:    High accuracy, low false positives, guaranteed compliance
```

---

## Compliance Posture Scoring Engine

The rules engine also powers the compliance posture score:

```
Overall Score = Σ(pillar_score × pillar_weight)

KYC Score (30%):
  base = avg(NIN_rate, BVN_rate, face_rate) × 100
  penalty = unreviewed_high_risk × 2 (max 20)
  score = max(base - penalty, 0)

AML Score (35%):
  base = (monitoring_coverage × 40%)
       + (review_rate × 30%)
       + (str_timeliness × 30%)
  penalty = late_strs × 5
  score = max(base - penalty, 0)

TIN Score (20%):
  base = (tin_verified / total_customers) × 100
  penalty = restriction_rate × 50
  score = max(base - penalty, 0)

Reporting Score (15%):
  base = (completed_actions / total_actions) × 100
  penalty = missed_deadlines × 15
  score = max(base - penalty, 0)

Classification:
  ≥ 80 → COMPLIANT  (green)
  60-79 → AT RISK   (yellow)
  < 60  → NON-COMPLIANT (red)
```

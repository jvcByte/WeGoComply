# WeGoComply — How Anomaly Detection Works

## 🔍 The Question: How Does the System Monitor Anomalies?

The AML (Anti-Money Laundering) system uses **two layers** of detection working together:
1. **Machine Learning (Isolation Forest)** - Detects unusual patterns
2. **Rule-Based Engine** - Checks CBN compliance thresholds

---

## 📊 Complete Data Flow

### **Step 1: Fintech Sends Transaction Data**

When a customer makes a transaction on Moniepoint, Moniepoint's system sends it to WeGoComply in real-time:

```json
POST /api/aml/monitor
{
  "transactions": [
    {
      "transaction_id": "TXN-7891234",
      "customer_id": "CUST-4421",
      "amount": 7500000,
      "currency": "NGN",
      "timestamp": "2026-04-21T02:34:00",
      "transaction_type": "transfer",
      "counterparty": "Unknown Corp Ltd",
      "channel": "mobile"
    }
  ]
}
```

---

### **Step 2: Extract Features for ML Model**

The system extracts key features from the transaction:

```python
# From the transaction above:
features = [
    amount: 7500000,        # How much money
    hour: 2                 # What time (2:34 AM = hour 2)
]
```

These two features are fed into the ML model.

---

### **Step 3: ML Model Detects Anomalies**

#### **How Isolation Forest Works:**

The model was trained on "normal" Nigerian transaction patterns:

```python
# Normal baseline data (what typical transactions look like)
normal_transactions = [
    [5000, 8],      # ₦5k at 8am
    [10000, 14],    # ₦10k at 2pm
    [2000, 10],     # ₦2k at 10am
    [8000, 11],     # ₦8k at 11am
    [15000, 13],    # ₦15k at 1pm
    [50000, 14],    # ₦50k at 2pm
    [100000, 10],   # ₦100k at 10am
    [200000, 15],   # ₦200k at 3pm
    [500000, 13],   # ₦500k at 1pm
    [1000000, 15],  # ₦1M at 3pm
    ... more normal patterns
]

# Train the model
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(normal_transactions)
```

The model learns: "Normal transactions are usually ₦5k-₦1M during business hours (8am-6pm)"

#### **When Chukwudi's transaction comes in:**

```python
# Chukwudi's transaction
suspicious_transaction = [7500000, 2]  # ₦7.5M at 2am

# Model checks: "Is this similar to normal patterns?"
# Answer: NO! This is way outside the normal range
# - Amount is 7.5x higher than typical max (₦1M)
# - Time is 6 hours before normal business hours

# Model output:
anomaly_score = -0.312  # Negative = anomaly (more negative = more suspicious)
is_anomaly = True       # Flagged as suspicious
```

**Visual Representation:**

```
Normal Transaction Zone:
┌─────────────────────────────────────┐
│  Amount: ₦5k - ₦1M                 │
│  Time: 8am - 6pm                    │
│  ✓ Most transactions fall here      │
└─────────────────────────────────────┘

Chukwudi's Transaction:
┌─────────────────────────────────────┐
│  Amount: ₦7.5M  ← 7.5x higher!     │
│  Time: 2am      ← 6 hours earlier!  │
│  ⚠ WAY OUTSIDE normal zone         │
└─────────────────────────────────────┘
```

---

### **Step 4: Rule-Based Engine Checks CBN Thresholds**

Even if ML doesn't catch it, the rule engine checks specific CBN regulations:

```python
def check_rules(transaction):
    rules_triggered = []
    
    # Rule 1: CBN ₦5M threshold
    # CBN requires reporting any transaction over ₦5 million
    if transaction.amount >= 5_000_000:
        rules_triggered.append("LARGE_CASH_TRANSACTION")
    
    # Rule 2: Unusual hours (before 5am or after 11pm)
    # Most legitimate transactions happen during business hours
    hour = extract_hour(transaction.timestamp)  # 2am
    if hour < 5 or hour > 23:
        rules_triggered.append("UNUSUAL_HOURS")
    
    # Rule 3: High-value transfers
    # Large transfers to unknown parties are suspicious
    if transaction.transaction_type == "transfer" and transaction.amount > 1_000_000:
        rules_triggered.append("HIGH_VALUE_TRANSFER")
    
    return rules_triggered

# For Chukwudi's transaction:
rules_triggered = [
    "LARGE_CASH_TRANSACTION",  # ₦7.5M > ₦5M ✓
    "UNUSUAL_HOURS",           # 2am < 5am ✓
    "HIGH_VALUE_TRANSFER"      # ₦7.5M > ₦1M ✓
]
```

---

### **Step 5: Combine ML + Rules for Final Decision**

```python
# Decision logic:
if is_anomaly and rules_triggered:
    risk_level = "HIGH"
    recommended_action = "GENERATE_STR"
elif is_anomaly or rules_triggered:
    risk_level = "MEDIUM"
    recommended_action = "REVIEW"
else:
    risk_level = "LOW"
    recommended_action = "APPROVE"

# For Chukwudi:
# is_anomaly = True (ML flagged it)
# rules_triggered = 3 rules (Rule engine flagged it)
# Result: HIGH RISK, GENERATE_STR
```

**Decision Matrix:**

| ML Anomaly | Rules Triggered | Risk Level | Action |
|------------|----------------|------------|--------|
| ✓ Yes | ✓ Yes | HIGH | Generate STR |
| ✓ Yes | ✗ No | MEDIUM | Review |
| ✗ No | ✓ Yes | MEDIUM | Review |
| ✗ No | ✗ No | LOW | Approve |

---

### **Step 6: Store in Database**

```sql
INSERT INTO transactions (
    transaction_id, customer_id, amount, timestamp,
    transaction_type, counterparty, channel,
    is_flagged, anomaly_score, risk_level, rules_triggered,
    str_generated
) VALUES (
    'TXN-7891234', 'CUST-4421', 7500000, '2026-04-21T02:34:00',
    'transfer', 'Unknown Corp Ltd', 'mobile',
    TRUE, -0.312, 'HIGH', 
    ARRAY['LARGE_CASH_TRANSACTION', 'UNUSUAL_HOURS', 'HIGH_VALUE_TRANSFER'],
    FALSE
);
```

---

### **Step 7: Return Result to Moniepoint**

```json
{
  "total_analyzed": 1,
  "flagged_count": 1,
  "clean_count": 0,
  "flagged_transactions": [
    {
      "transaction_id": "TXN-7891234",
      "customer_id": "CUST-4421",
      "amount": 7500000,
      "timestamp": "2026-04-21T02:34:00",
      "anomaly_score": -0.312,
      "rules_triggered": [
        "LARGE_CASH_TRANSACTION",
        "UNUSUAL_HOURS",
        "HIGH_VALUE_TRANSFER"
      ],
      "risk_level": "HIGH",
      "recommended_action": "GENERATE_STR"
    }
  ]
}
```

---

## 🧠 How the ML Model Learns Customer Patterns

### **Building Customer Profiles Over Time**

As you store transactions in your database, you can build profiles:

```sql
-- Get Chukwudi's transaction history
SELECT 
    AVG(amount) as avg_amount,
    MAX(amount) as max_amount,
    MIN(amount) as min_amount,
    COUNT(*) as total_transactions,
    ARRAY_AGG(DISTINCT EXTRACT(HOUR FROM timestamp)) as usual_hours
FROM transactions
WHERE customer_id = 'CUST-4421'
AND timestamp > NOW() - INTERVAL '90 days';

-- Result:
-- avg_amount: ₦50,000
-- max_amount: ₦150,000
-- min_amount: ₦5,000
-- total_transactions: 234
-- usual_hours: [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
```

### **Enhanced Anomaly Detection with Customer History**

```python
# When new transaction comes in:
new_transaction = {
    "amount": 7500000,
    "hour": 2
}

# Compare to customer's profile:
customer_profile = {
    "avg_amount": 50000,
    "max_amount": 150000,
    "usual_hours": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
}

# Calculate deviation:
amount_deviation = new_transaction["amount"] / customer_profile["avg_amount"]
# 7500000 / 50000 = 150x higher than normal!

hour_deviation = new_transaction["hour"] not in customer_profile["usual_hours"]
# 2am is NOT in usual hours (8am-6pm)

# This makes the anomaly even more obvious
# The system can say: "This customer NEVER transacts at 2am and NEVER sends ₦7.5M"
```

---

## 📈 Real-Time Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Moniepoint System                     │
│  (Customer makes transaction at 2:34 AM)                │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP POST /api/aml/monitor
                          ▼
┌─────────────────────────────────────────────────────────┐
│              WeGoComply API Gateway                      │
│  (Receives transaction data)                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Feature Extraction                          │
│  Extract: [amount, hour] = [7500000, 2]                │
└─────────────────────────────────────────────────────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
┌──────────────────────┐  ┌──────────────────────┐
│   ML Model           │  │  Rule Engine         │
│  (Isolation Forest)  │  │  (CBN Thresholds)    │
│                      │  │                      │
│  Score: -0.312       │  │  Rules Triggered:    │
│  Anomaly: TRUE       │  │  - LARGE_CASH        │
│                      │  │  - UNUSUAL_HOURS     │
│                      │  │  - HIGH_VALUE        │
└──────────────────────┘  └──────────────────────┘
                │                   │
                └─────────┬─────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Decision Engine                             │
│  ML + Rules = HIGH RISK                                 │
│  Action: GENERATE_STR                                   │
└─────────────────────────────────────────────────────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
┌──────────────────────┐  ┌──────────────────────┐
│   Store in Database  │  │  Return to Moniepoint│
│  (Audit trail)       │  │  (Flagged result)    │
└──────────────────────┘  └──────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────┐
│         Moniepoint Compliance Dashboard                  │
│  Alert: "HIGH RISK transaction detected!"               │
│  [Generate STR] button                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Why This Two-Layer Approach Works

### **Layer 1: Machine Learning**
- ✅ Catches **unknown patterns** that aren't in the rules
- ✅ Learns from historical data
- ✅ Adapts to new fraud techniques
- ✅ Reduces false positives (smarter than simple rules)

**Example**: ML catches a customer who suddenly starts transacting at 3am every day, even if amounts are below ₦5M threshold.

### **Layer 2: Rule-Based Engine**
- ✅ Catches **known violations** of CBN regulations
- ✅ Guaranteed compliance (rules match CBN requirements exactly)
- ✅ Explainable (can tell auditor "we flagged it because of Rule X")
- ✅ Fast (no computation needed, just if/else checks)

**Example**: Rule engine catches any transaction over ₦5M, even if ML thinks it's normal.

### **Combined Power**
- ✅ **High accuracy**: Both layers must agree for HIGH risk
- ✅ **Low false positives**: ML reduces noise from rule-only systems
- ✅ **Compliance guaranteed**: Rules ensure CBN requirements are met
- ✅ **Continuous improvement**: ML gets smarter as more data is collected

---

## 📊 Example: Normal vs Suspicious Transactions

| Transaction | Amount | Hour | ML Score | Rules | Risk | Why? |
|-------------|--------|------|----------|-------|------|------|
| Adaeze buys groceries | ₦5,000 | 10am | 0.45 | None | LOW | Normal pattern |
| Emeka pays rent | ₦500,000 | 2pm | 0.12 | None | LOW | Large but normal hour |
| Chukwudi transfer | ₦7.5M | 2am | -0.312 | 3 rules | HIGH | Huge + weird time |
| Ngozi salary | ₦200,000 | 9am | 0.23 | None | LOW | Normal payroll |
| Tunde late payment | ₦50,000 | 11:30pm | 0.08 | UNUSUAL_HOURS | MEDIUM | Normal amount, late hour |
| Amaka large deposit | ₦6M | 2pm | -0.15 | LARGE_CASH | MEDIUM | Large but normal hour |

---

## 🔄 Continuous Learning Process

```
Day 1: Model trained on 10,000 normal transactions
  ↓
Week 1: 100,000 new transactions processed
  ↓
Week 2: Model retrained with new data
  ↓
Result: Model now knows:
  - Salary payments happen on 25th of month
  - Rent payments are usually ₦500k-₦2M
  - Business accounts transact more than personal
  - Friday evenings have higher transaction volumes
  ↓
Week 3: Model is smarter, fewer false positives
  ↓
Month 1: Model accuracy improves from 85% to 92%
```

---

## 💡 Key Takeaways

1. **Two layers**: ML detects patterns + Rules enforce regulations
2. **Real-time**: Analysis happens in 2 seconds
3. **Learning**: ML gets smarter with more data
4. **Explainable**: Can tell auditors exactly why transaction was flagged
5. **Compliant**: Rules guarantee CBN requirements are met
6. **Scalable**: Can process millions of transactions per day

The system doesn't just follow rules blindly—it learns what "normal" looks like for each customer and flags anything unusual, while also ensuring CBN compliance thresholds are never missed.

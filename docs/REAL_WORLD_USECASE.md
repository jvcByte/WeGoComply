# WeGoComply — Real-World Use Case

## 📱 Scenario: How Moniepoint Uses WeGoComply

**Background:**
Moniepoint is a Nigerian fintech with 10 million customers. They process ₦500 billion in transactions monthly. They face constant pressure from CBN to maintain compliance.

---

## 🎬 Day in the Life: Monday, April 21, 2026

### **9:00 AM - New Customer Signup**

**Meet Adaeze**, a 28-year-old entrepreneur in Lagos who wants to open a Moniepoint account to receive payments from customers.

#### Without WeGoComply (The Old Way):
1. Adaeze fills out form on Moniepoint app
2. Uploads ID card photo
3. Moniepoint compliance officer (human) manually:
   - Calls NIMC to verify NIN → 2 days wait
   - Calls bank to verify BVN → 1 day wait
   - Visually compares selfie to ID → prone to error
4. **Result**: Adaeze waits 3-5 days, gets frustrated, maybe switches to competitor
5. **Cost to Moniepoint**: ₦2,000 per verification (staff time)

#### With WeGoComply (The New Way):
1. Adaeze fills out form on Moniepoint app
2. Uploads NIN: `12345678901`, BVN: `22334455667`, selfie
3. Moniepoint app sends data to WeGoComply API:
```json
POST /api/kyc/verify
{
  "nin": "12345678901",
  "bvn": "22334455667",
  "selfie": "base64_image_data"
}
```
4. WeGoComply (in 87 seconds):
   - Calls Dojah API → verifies NIN against NIMC database ✓
   - Calls Dojah API → verifies BVN against CBN database ✓
   - Azure Face API → matches selfie to ID photo (94% confidence) ✓
   - ML model → calculates risk score: 0.12 (LOW RISK) ✓
5. WeGoComply responds:
```json
{
  "status": "VERIFIED",
  "risk_level": "LOW",
  "risk_score": 0.12,
  "details": {
    "nin_verified": true,
    "bvn_verified": true,
    "face_match": true,
    "name": "Adaeze Okonkwo",
    "phone": "08012345678"
  }
}
```
6. Moniepoint app shows: "Account approved! Start transacting now."
7. **Result**: Adaeze is onboarded in under 2 minutes, happy customer
8. **Cost to Moniepoint**: ₦200 per verification (API call)

**Savings**: 90% cost reduction, 99% time reduction, happier customers

---

### **2:34 AM - Suspicious Transaction**

**Meet Chukwudi**, a Moniepoint user who suddenly transfers ₦7.5 million to an unknown company at 2:34 AM.

#### Without WeGoComply (The Old Way):
1. Transaction goes through unnoticed
2. Days later, CBN auditor flags it during routine check
3. CBN fines Moniepoint ₦500 million for failing to detect suspicious activity
4. Moniepoint's reputation damaged in the news
5. Chukwudi might be a money launderer who got away

#### With WeGoComply (The New Way):
1. Transaction happens at 2:34 AM
2. Moniepoint's system sends transaction to WeGoComply API in real-time:
```json
POST /api/aml/monitor
{
  "transactions": [{
    "transaction_id": "TXN-7891234",
    "customer_id": "CUST-4421",
    "amount": 7500000,
    "timestamp": "2026-04-21T02:34:00",
    "transaction_type": "transfer",
    "counterparty": "Unknown Corp Ltd",
    "channel": "mobile"
  }]
}
```
3. WeGoComply (in 2 seconds):
   - ML model detects anomaly (₦7.5M is way above Chukwudi's normal ₦50k transfers)
   - Rule engine flags:
     - ✓ LARGE_CASH_TRANSACTION (over ₦5M CBN threshold)
     - ✓ UNUSUAL_HOURS (2:34 AM)
     - ✓ HIGH_VALUE_TRANSFER
   - Risk level: HIGH
4. WeGoComply responds:
```json
{
  "flagged_transactions": [{
    "transaction_id": "TXN-7891234",
    "risk_level": "HIGH",
    "anomaly_score": -0.312,
    "rules_triggered": ["LARGE_CASH_TRANSACTION", "UNUSUAL_HOURS"],
    "recommended_action": "GENERATE_STR"
  }]
}
```
5. Moniepoint compliance officer (Ngozi) gets instant alert on dashboard
6. Ngozi clicks "Generate STR" button
7. WeGoComply uses Azure OpenAI to generate full report:
```json
{
  "report_reference": "STR-20260421-001",
  "subject_name": "Chukwudi Eze",
  "transaction_summary": "Customer conducted a transfer of ₦7,500,000 to Unknown Corp Ltd via mobile banking at 2:34 AM, significantly exceeding normal transaction patterns.",
  "grounds_for_suspicion": "Transaction amount exceeds CBN ₦5M threshold, occurred outside normal banking hours (2-4 AM), counterparty is an unverified entity with no prior transaction history, and represents a 15,000% increase from customer's average transaction size.",
  "recommended_action": "Freeze account pending investigation. Contact customer for source of funds verification. File STR with NFIU within 24 hours per CBN guidelines.",
  "report_date": "2026-04-21"
}
```
8. Ngozi reviews, freezes Chukwudi's account, submits STR to NFIU
9. Investigation reveals Chukwudi's account was hacked
10. **Result**: Money laundering prevented, CBN compliance maintained, customer protected

**Impact**: Avoided ₦500M fine, protected customer, maintained reputation

---

### **10:00 AM - Quarterly TIN Verification**

**The Problem:**
FIRS mandates that all Moniepoint's 10 million customers must have verified Tax IDs. Accounts without verified TINs will be restricted from transactions above ₦500,000.

#### Without WeGoComply (The Old Way):
1. Moniepoint exports 10 million customer records to Excel
2. Hires 50 temporary staff
3. Each staff member manually:
   - Visits FIRS website
   - Enters TIN one by one
   - Checks if name matches
   - Records result in Excel
4. **Timeline**: 3 months
5. **Cost**: ₦20 million (staff salaries)
6. **Accuracy**: 60% (human error, typos, fatigue)
7. **Result**: 4 million accounts get restricted, angry customers

#### With WeGoComply (The New Way):
1. Moniepoint compliance officer uploads CSV file with 10 million records
2. WeGoComply API processes in batches:
```json
POST /api/tax/bulk-verify
{
  "records": [
    {"customer_id": "CUST-001", "name": "Adaeze Okonkwo", "tin": "1234567890"},
    {"customer_id": "CUST-002", "name": "Emeka Nwosu", "tin": "0987654321"},
    ... 10 million more
  ]
}
```
3. WeGoComply (over 6 hours):
   - Calls Dojah API to verify each TIN against FIRS database
   - Uses fuzzy matching algorithm to handle name variations
   - Processes 500 records per second
4. WeGoComply responds:
```json
{
  "total": 10000000,
  "matched": 9100000,
  "failed": 900000,
  "match_rate": 91.0,
  "deadline_risk": "LOW",
  "records": [
    {"customer_id": "CUST-001", "status": "MATCHED", "match_confidence": 0.95},
    {"customer_id": "CUST-002", "status": "NOT_FOUND"},
    ...
  ]
}
```
5. Dashboard shows:
   - 91% match rate ✓
   - 900,000 customers need to update TIN
   - Deadline risk: LOW (enough time to fix)
6. Moniepoint sends SMS to 900k customers: "Update your TIN to avoid restrictions"
7. **Timeline**: 6 hours
8. **Cost**: ₦500,000 (API calls)
9. **Accuracy**: 95%
10. **Result**: Only 50,000 accounts restricted (those who didn't respond), 99.5% customer satisfaction

**Savings**: 97.5% cost reduction, 99.9% time reduction, better accuracy

---

### **3:00 PM - New CBN Regulation**

**The Situation:**
CBN publishes a 45-page circular: "Updated Guidelines on Digital Lending Operations"

#### Without WeGoComply (The Old Way):
1. Compliance officer downloads PDF
2. Reads all 45 pages (takes 3 hours)
3. Tries to understand legal jargon
4. Misses key deadline buried on page 38
5. Moniepoint fails to comply
6. **Result**: ₦100 million fine

#### With WeGoComply (The New Way):
1. WeGoComply scrapes CBN website, detects new circular
2. Azure OpenAI reads the 45-page document
3. Generates summary:
```json
{
  "source": "CBN",
  "title": "Updated Guidelines on Digital Lending Operations",
  "summary": "All digital lenders must implement new customer protection measures including transparent interest rate disclosure and mandatory cooling-off periods.",
  "action_required": "Update loan application forms to show APR in bold. Implement 24-hour cooling-off period before loan disbursement. Train customer service staff on new complaint handling procedures.",
  "deadline": "2026-06-30",
  "affected_operations": ["Digital Lending", "Customer Service", "Compliance"],
  "urgency": "HIGH"
}
```
4. Compliance officer sees alert on dashboard
5. Reads 2-sentence summary instead of 45 pages
6. Creates action plan immediately
7. **Result**: Compliance maintained, no fine

**Impact**: Saved ₦100M fine, saved 3 hours of reading time

---

## 📊 End of Day Results for Moniepoint

| Metric | Without WeGoComply | With WeGoComply |
|--------|-------------------|-----------------|
| New customers onboarded | 500 (3-5 day delay) | 5,000 (instant) |
| Suspicious transactions caught | 0 (manual review missed it) | 23 (all flagged) |
| TIN verification progress | 0% (not started) | 91% (completed) |
| Regulatory compliance | At risk | 100% compliant |
| Compliance team stress | High (overwhelmed) | Low (automated) |
| Daily cost | ₦2M | ₦300k |

---

## 💡 The Bottom Line

**Moniepoint's CEO to the Board:**
"Before WeGoComply, we had 50 compliance staff working 12-hour days, still missing deadlines, and facing fines. Now we have 10 staff monitoring dashboards, zero fines, and we onboard 10x more customers. WeGoComply paid for itself in the first month."

---

## 🎯 Key Takeaways

1. **Speed**: 2 minutes vs 3-5 days for KYC
2. **Cost**: 90% reduction in compliance costs
3. **Accuracy**: 95% vs 60% for TIN verification
4. **Risk**: Catch suspicious transactions in real-time, not days later
5. **Compliance**: Never miss a regulatory deadline
6. **Scale**: Handle 10 million customers with 10 staff instead of 50

WeGoComply transforms compliance from a cost center to a competitive advantage.

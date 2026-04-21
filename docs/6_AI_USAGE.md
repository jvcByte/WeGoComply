# 6. AI Usage Explanation

## Overview

WeGoComply uses AI in four distinct ways, each solving a specific compliance problem that humans cannot solve at scale.

---

## AI Component 1: Isolation Forest (AML Anomaly Detection)

### What It Is
An unsupervised machine learning algorithm from scikit-learn that detects unusual transaction patterns without needing labelled fraud data.

### The Problem It Solves
A fintech processing 1.5 million transactions per day cannot have humans review every transaction. The ML model acts as a first-pass filter, flagging the 0.1-1% that need human attention.

### How It Works

```
Training:
  Model learns "normal" from historical transaction data
  Features: [transaction_amount, hour_of_day]
  Algorithm: Builds random decision trees, measures isolation depth
  Anomaly = transactions that are easy to isolate (few splits needed)

Inference (real-time, per transaction):
  Input:  [₦7,500,000, hour=2]
  Output: anomaly_score=-0.312, is_anomaly=True

  Input:  [₦50,000, hour=14]
  Output: anomaly_score=+0.23, is_anomaly=False
```

### Why This Model?

| Criterion | Isolation Forest | Alternative |
|-----------|-----------------|-------------|
| Labelled data needed | No | Yes (supervised models) |
| Speed | O(n log n) — very fast | Slower for deep learning |
| Interpretability | Score is a number | Black box (neural nets) |
| Cold start | Works immediately | Needs fraud history |
| False positive rate | Low (5% contamination) | Higher without tuning |

### Improvement Path
As transaction data accumulates in the database, the model can be retrained with:
- Customer-specific behavioral profiles
- Time-series patterns (salary day, month-end)
- Network analysis (counterparty relationships)
- Additional features (channel, counterparty, location)

---

## AI Component 2: Azure OpenAI GPT-4o (STR Generation)

### What It Is
Microsoft's GPT-4o model accessed via Azure OpenAI, used to generate Suspicious Transaction Reports (STRs) in NFIU-compliant format.

### The Problem It Solves
Writing an STR manually takes a compliance officer 2-4 hours. It requires:
- Precise legal language
- Specific NFIU-required fields
- Grounds for suspicion clearly articulated
- Recommended actions

GPT-4o generates a complete, professional STR in under 10 seconds.

### The Prompt

```python
prompt = f"""
You are a compliance officer at a Nigerian financial institution.
Generate a Suspicious Transaction Report (STR) for submission to the NFIU.

Transaction details:
- ID: {transaction.transaction_id}
- Customer: {transaction.customer_id}
- Amount: ₦{transaction.amount:,.2f}
- Type: {transaction.transaction_type}
- Counterparty: {transaction.counterparty}
- Channel: {transaction.channel}
- Timestamp: {transaction.timestamp.isoformat()}

Return a JSON object with these fields:
- report_reference
- reporting_institution
- subject_name
- transaction_summary
- grounds_for_suspicion
- recommended_action
- report_date
"""
```

### Sample Output

```json
{
  "report_reference": "STR-TXN78912",
  "reporting_institution": "WeGoComply Demo Bank",
  "subject_name": "CUST-4421",
  "transaction_summary": "Customer conducted a transfer of ₦7,500,000 to Unknown Corp Ltd via mobile banking at 2:34 AM, representing a 15,000% increase from their average transaction size of ₦50,000.",
  "grounds_for_suspicion": "Transaction amount exceeds CBN ₦5M reporting threshold. Transaction occurred at 2:34 AM, outside normal banking hours. Counterparty (Unknown Corp Ltd) has no prior transaction history with this customer. Amount is statistically anomalous based on customer's 90-day transaction profile.",
  "recommended_action": "Freeze account pending investigation. Contact customer for source of funds verification. File STR with NFIU within 24 hours per CBN AML/CFT Regulations.",
  "report_date": "2026-04-21"
}
```

### Why Azure OpenAI?

- **Microsoft AI Skills Week context**: Demonstrates deep Azure AI integration
- **Security**: Data stays within Azure tenant, not sent to third parties
- **Compliance**: Azure OpenAI has enterprise data protection agreements
- **Quality**: GPT-4o produces professional, legally appropriate language
- **Speed**: <10 seconds vs 2-4 hours manually

---

## AI Component 3: Azure Face API (KYC Facial Verification)

### What It Is
Microsoft's Azure Cognitive Services Face API, used to verify that a customer's selfie matches their government-issued ID photo.

### The Problem It Solves
Manual visual comparison of selfies to ID photos is:
- Slow (done by humans)
- Inconsistent (fatigue, bias)
- Easily fooled (printed photos, deepfakes)

Azure Face API provides:
- Liveness detection (real person, not a photo of a photo)
- Face comparison with confidence score
- Sub-second processing

### How It Works

```
Step 1: Detect face in selfie
  POST /face/v1.0/detect
  Body: [selfie image bytes]
  Response: [{faceId: "abc123", ...}]

Step 2: Detect face in ID photo
  POST /face/v1.0/detect
  Body: {url: "https://nimc.gov.ng/photo/..."}
  Response: [{faceId: "def456", ...}]

Step 3: Verify match
  POST /face/v1.0/verify
  Body: {faceId1: "abc123", faceId2: "def456"}
  Response: {
    isIdentical: true,
    confidence: 0.94
  }
```

### Confidence Thresholds

| Confidence | Decision | Action |
|------------|----------|--------|
| ≥ 0.90 | Strong match | Auto-approve |
| 0.70-0.89 | Probable match | Approve with flag |
| 0.50-0.69 | Weak match | Manual review |
| < 0.50 | No match | Reject, notify customer |

---

## AI Component 4: Azure OpenAI GPT-4o (Regulatory Intelligence)

### What It Is
The same GPT-4o model used to read, summarize, and extract action items from regulatory circulars published by CBN, FIRS, SEC, and FCCPC.

### The Problem It Solves
Nigerian regulators publish complex, lengthy circulars (40-100 pages) that compliance officers must read and interpret. A new CBN circular can take 3 hours to read and understand.

GPT-4o reads the full document and returns a structured summary in seconds.

### The Prompt

```python
prompt = f"""
You are a Nigerian financial compliance expert.
Analyze this regulatory circular and return a JSON object with:
- summary: plain English summary in 2 sentences max
- action_required: what the institution must do (1-2 sentences)
- deadline: deadline date if mentioned, else null
- affected_operations: list of affected business areas
- urgency: one of HIGH, MEDIUM, LOW

Circular text:
{circular_text}
"""
```

### Sample Output

```json
{
  "summary": "All financial institutions must implement real-time AML transaction monitoring by June 30, 2026, replacing manual batch review processes.",
  "action_required": "Deploy automated AML monitoring system capable of real-time transaction analysis and configure STR filing within 24 hours of suspicious activity detection.",
  "deadline": "2026-06-30",
  "affected_operations": ["AML", "Transaction Monitoring", "STR Filing", "Compliance Reporting"],
  "urgency": "HIGH"
}
```

### Value Delivered

| Without AI | With AI |
|------------|---------|
| 3 hours reading per circular | 10 seconds |
| Risk of missing key deadlines | Deadlines auto-extracted |
| Legal jargon confuses staff | Plain English summary |
| Manual action item tracking | Structured action items |
| Reactive (discover at audit) | Proactive (real-time alerts) |

---

## AI Component 5: Azure AI Document Intelligence (ID Extraction)

### What It Is
Azure's document analysis service that extracts structured data from identity documents (NIN slips, driver's licenses, international passports).

### The Problem It Solves
Customers upload photos of their ID documents. Manually reading and typing the data is slow and error-prone. Document Intelligence extracts all fields automatically.

### How It Works

```
Input: Photo of NIN slip or ID card

Azure Document Intelligence:
  → Detects document type
  → Extracts fields:
     - Full name
     - Date of birth
     - NIN number
     - Address
     - Issue date
     - Expiry date

Output:
{
  "document_type": "NIN_SLIP",
  "fields": {
    "full_name": "Adaeze Okonkwo",
    "nin": "12345678901",
    "date_of_birth": "1996-03-15",
    "gender": "Female",
    "address": "12 Broad Street, Lagos"
  },
  "confidence": 0.97
}
```

---

## AI Summary Table

| Component | Technology | Problem Solved | Speed Improvement |
|-----------|-----------|----------------|-------------------|
| AML Detection | Isolation Forest (scikit-learn) | Detect suspicious transactions | 1.5M tx/day vs 0 manually |
| STR Generation | Azure OpenAI GPT-4o | Write NFIU-compliant reports | 10 sec vs 2-4 hours |
| Facial Verification | Azure Face API | Match selfie to ID photo | 2 sec vs 5 min manually |
| Regulatory Intelligence | Azure OpenAI GPT-4o | Summarize CBN/FIRS circulars | 10 sec vs 3 hours |
| ID Data Extraction | Azure Document Intelligence | Extract data from ID documents | 3 sec vs 10 min manually |

---

## AI Ethics & Compliance

### Data Privacy (NDPR Compliance)
- Biometric data (face images) processed in Azure, not stored permanently
- PII masked in audit logs (NIN shown as `123****901`)
- Customer consent obtained before biometric processing
- Data residency: Azure West Europe (Nigeria region when available)

### Bias Mitigation
- Azure Face API tested across diverse Nigerian demographics
- Confidence thresholds set conservatively to reduce false rejections
- Human review required for borderline cases (confidence 0.50-0.89)
- Regular model audits for demographic performance disparities

### Explainability
- ML anomaly scores are numerical and interpretable
- Rules engine decisions are fully explainable (specific rule cited)
- STR reports include explicit grounds for suspicion
- All AI decisions logged in immutable audit trail

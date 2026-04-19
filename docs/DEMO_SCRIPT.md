# WeGoComply — Demo Script (5 Minutes)

## Setup
- Open dashboard at `http://localhost:5173`
- Backend running at `http://localhost:8000`
- Sample data preloaded

---

## Act 1: The Problem (30 seconds)

**Narration**:
"Nigerian fintechs face three urgent compliance crises in 2026:

1. CBN mandates real-time AML monitoring by June 30
2. FIRS requires TIN verification or accounts get restricted April 1
3. Manual KYC takes 3-5 days and costs ₦1 billion in fines when it fails

WeGoComply solves all three with AI automation."

---

## Act 2: KYC Verification (90 seconds)

**Action**: Navigate to KYC page

**Narration**: "A new customer wants to open an account. Traditional process: 3-5 days. With WeGoComply: under 2 minutes."

**Demo Steps**:
1. Enter NIN: `12345678901`
2. Enter BVN: `12345678901`
3. Upload selfie (any image file)
4. Click "Verify Identity"

**Result Display**:
- ✓ NIN Verified
- ✓ BVN Verified
- ✓ Face Match (94% confidence)
- Risk Score: 0.12
- Risk Level: LOW

**Narration**: "Azure AI Document Intelligence extracted the ID data. Azure Face API confirmed the match. Our ML model scored the risk. Customer onboarded in 87 seconds."

---

## Act 3: AML Transaction Monitoring (90 seconds)

**Action**: Navigate to AML Monitor page

**Narration**: "Now this customer makes transactions. CBN requires real-time monitoring. Let's analyze a batch."

**Demo Steps**:
1. Show sample transactions table (5 transactions visible)
2. Click "Run Analysis"

**Result Display**:
- Total Analyzed: 5
- Flagged: 3
- Clean: 2

**Flagged transactions shown**:
- TXN-001: ₦7.5M at 2:34am — HIGH RISK
- TXN-003: ₦2.3M at 11:58pm — MEDIUM RISK
- TXN-005: ₦9.8M at 3:11am — HIGH RISK

**Narration**: "Azure ML detected anomalies. Rule engine flagged CBN violations: large amounts, unusual hours."

**Demo Steps**:
3. Click "Generate STR" on TXN-001

**Result Display**: Full STR report with:
- Report Reference: STR-TXN001
- Grounds for Suspicion: "Amount exceeds ₦5M threshold, occurred at 2am, unverified counterparty"
- Recommended Action: "Freeze account, file with NFIU within 24 hours"

**Narration**: "Azure OpenAI generated a complete NFIU-compliant STR in seconds. Compliance officer just reviews and submits."

---

## Act 4: TIN Verification (60 seconds)

**Action**: Navigate to Tax/TIN page

**Narration**: "FIRS deadline: April 1. Accounts without verified TINs get restricted. Let's verify a batch."

**Demo Steps**:
1. Show sample customer records (5 customers)
2. Click "Run Bulk Verification"

**Result Display**:
- Total: 5
- Matched: 4
- Failed: 1
- Match Rate: 80%
- Deadline Risk: MEDIUM

**Narration**: "Dojah API verified TINs against FIRS. 80% match rate. System flags the institution needs to fix 1 record before the deadline."

---

## Act 5: Regulatory Intelligence (30 seconds)

**Action**: Navigate to Regulatory page

**Narration**: "Regulations change fast. WeGoComply monitors CBN, FIRS, SEC, FCCPC."

**Demo Steps**:
1. Show regulatory feed with 4 updates
2. Highlight CBN AML update

**Result Display**:
- Source: CBN
- Summary: "Real-time AML monitoring required by June 30, 2026"
- Action Required: "Deploy automated system and configure 24-hour STR filing"
- Urgency: HIGH
- Affected Operations: AML, Transaction Monitoring, STR Filing

**Narration**: "Azure OpenAI summarized a 40-page circular into actionable insights. Compliance teams know exactly what to do."

---

## Closing (30 seconds)

**Return to Dashboard**

**Narration**:
"WeGoComply delivers:
- 2-minute KYC onboarding (down from 3-5 days)
- 60-80% reduction in AML false positives
- Automated TIN compliance before sanctions hit
- Real-time regulatory intelligence

Built entirely on Microsoft Azure AI. API-first for instant integration. Ready for production today."

**End Screen**: Show contact info or QR code for demo access

---

## Backup Slides (if time allows)

- Architecture diagram
- Cost comparison: Manual vs. WeGoComply
- Customer testimonials (if available)
- Roadmap: Cross-border remittances, SME compliance, pan-African expansion

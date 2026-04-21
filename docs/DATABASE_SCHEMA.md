# WeGoComply — Database Schema & Data Storage

## 🤔 The Question: What Do We Store If Dojah Provides the Data?

Even though Dojah provides identity verification data, WeGoComply still needs its own database. Here's what we store and why.

---

## 🗄️ Complete Database Schema

### **1. Customers Table**
Stores verification results and risk profiles for each customer.

```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,  -- From fintech (e.g., "CUST-4421")
    institution_id UUID NOT NULL,              -- Which fintech owns this customer
    
    -- Identity Data (from Dojah)
    nin VARCHAR(11),
    bvn VARCHAR(11),
    tin VARCHAR(10),
    full_name VARCHAR(255),
    date_of_birth DATE,
    phone_number VARCHAR(20),
    
    -- Verification Results
    nin_verified BOOLEAN DEFAULT FALSE,
    bvn_verified BOOLEAN DEFAULT FALSE,
    tin_verified BOOLEAN DEFAULT FALSE,
    face_match_verified BOOLEAN DEFAULT FALSE,
    face_match_confidence DECIMAL(3,2),
    
    -- Risk Assessment
    risk_score DECIMAL(3,2),
    risk_level VARCHAR(10),  -- LOW, MEDIUM, HIGH
    
    -- Metadata
    verification_date TIMESTAMP,
    last_updated TIMESTAMP,
    status VARCHAR(20),  -- ACTIVE, SUSPENDED, FLAGGED
    
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
```

**Why store this?**
- ✅ **Audit trail**: Prove to CBN you verified this customer on this date
- ✅ **Historical tracking**: See if customer's risk level changed over time
- ✅ **Quick lookups**: Don't re-verify every time, check your database first
- ✅ **Compliance reporting**: Generate reports for regulators
- ✅ **Cost optimization**: Don't pay Dojah to verify same customer 100 times

**Example Record:**
```json
{
  "id": "uuid-adaeze",
  "customer_id": "MONIE-12345",
  "institution_id": "uuid-moniepoint",
  "nin": "12345678901",
  "bvn": "22334455667",
  "tin": "1234567890",
  "full_name": "Adaeze Okonkwo",
  "date_of_birth": "1996-03-15",
  "phone_number": "08012345678",
  "nin_verified": true,
  "bvn_verified": true,
  "tin_verified": true,
  "face_match_verified": true,
  "face_match_confidence": 0.94,
  "risk_score": 0.12,
  "risk_level": "LOW",
  "verification_date": "2026-04-21T09:15:23",
  "status": "ACTIVE"
}
```

---

### **2. Transactions Table**
Stores all transactions analyzed for AML monitoring.

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID NOT NULL,
    institution_id UUID NOT NULL,
    
    -- Transaction Details
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'NGN',
    transaction_type VARCHAR(20),  -- transfer, deposit, withdrawal
    counterparty VARCHAR(255),
    channel VARCHAR(20),  -- mobile, web, pos, atm
    timestamp TIMESTAMP NOT NULL,
    
    -- AML Analysis Results
    is_flagged BOOLEAN DEFAULT FALSE,
    anomaly_score DECIMAL(5,4),
    risk_level VARCHAR(10),  -- LOW, MEDIUM, HIGH
    rules_triggered TEXT[],  -- ["LARGE_CASH_TRANSACTION", "UNUSUAL_HOURS"]
    
    -- Actions Taken
    str_generated BOOLEAN DEFAULT FALSE,
    str_reference VARCHAR(50),
    reviewed_by UUID,  -- compliance officer
    review_date TIMESTAMP,
    review_notes TEXT,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
```

**Why store this?**
- ✅ **Audit trail**: CBN asks "Did you monitor this transaction?" → Yes, here's the record
- ✅ **Pattern analysis**: ML model learns from historical data to improve detection
- ✅ **Investigation**: When customer is flagged, review all their past transactions
- ✅ **Compliance reporting**: Generate monthly AML reports for NFIU
- ✅ **Legal evidence**: If customer sues, you have proof you followed procedures

**Example Record:**
```json
{
  "id": "uuid-txn-001",
  "transaction_id": "TXN-7891234",
  "customer_id": "uuid-chukwudi",
  "institution_id": "uuid-moniepoint",
  "amount": 7500000,
  "currency": "NGN",
  "transaction_type": "transfer",
  "counterparty": "Unknown Corp Ltd",
  "channel": "mobile",
  "timestamp": "2026-04-21T02:34:00",
  "is_flagged": true,
  "anomaly_score": -0.312,
  "risk_level": "HIGH",
  "rules_triggered": ["LARGE_CASH_TRANSACTION", "UNUSUAL_HOURS", "HIGH_VALUE_TRANSFER"],
  "str_generated": true,
  "str_reference": "STR-20260421-001",
  "reviewed_by": "uuid-ngozi",
  "review_date": "2026-04-21T02:36:15",
  "review_notes": "Account frozen. Customer contacted. STR filed with NFIU."
}
```

---

### **3. STR Reports Table**
Stores all Suspicious Transaction Reports generated.

```sql
CREATE TABLE str_reports (
    id UUID PRIMARY KEY,
    report_reference VARCHAR(50) UNIQUE NOT NULL,
    transaction_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    institution_id UUID NOT NULL,
    
    -- Report Content
    subject_name VARCHAR(255),
    transaction_summary TEXT,
    grounds_for_suspicion TEXT,
    recommended_action TEXT,
    
    -- Submission Details
    generated_date TIMESTAMP NOT NULL,
    submitted_to_nfiu BOOLEAN DEFAULT FALSE,
    submission_date TIMESTAMP,
    nfiu_acknowledgment VARCHAR(100),
    
    -- Follow-up
    investigation_status VARCHAR(20),  -- PENDING, ONGOING, CLOSED
    outcome TEXT,
    
    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
```

**Why store this?**
- ✅ **Legal requirement**: Must keep STR records for 7 years (CBN regulation)
- ✅ **Audit trail**: Prove you filed STRs on time
- ✅ **Investigation tracking**: Follow up on what happened after filing
- ✅ **Analytics**: How many STRs per month? Are they increasing?

---

### **4. TIN Verifications Table**
Stores bulk TIN verification results.

```sql
CREATE TABLE tin_verifications (
    id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,
    institution_id UUID NOT NULL,
    
    -- TIN Data
    tin VARCHAR(10) NOT NULL,
    submitted_name VARCHAR(255),
    firs_name VARCHAR(255),
    
    -- Verification Result
    status VARCHAR(20),  -- MATCHED, NOT_FOUND, NAME_MISMATCH
    match_confidence DECIMAL(3,2),
    
    -- Metadata
    verification_date TIMESTAMP NOT NULL,
    last_checked TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
```

**Why store this?**
- ✅ **Compliance proof**: Show FIRS you verified TINs before deadline
- ✅ **Re-verification tracking**: Check TINs quarterly without re-calling Dojah
- ✅ **Cost optimization**: Don't pay Dojah to verify same TIN twice
- ✅ **Customer communication**: Know which customers need to update TINs

---

### **5. Institutions Table**
Stores fintech/bank clients using WeGoComply.

```sql
CREATE TABLE institutions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    institution_type VARCHAR(50),  -- FINTECH, BANK, PSP, MFB
    
    -- Contact Info
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    
    -- Licensing
    cbn_license_number VARCHAR(50),
    license_type VARCHAR(50),
    license_expiry DATE,
    
    -- Subscription
    subscription_tier VARCHAR(20),  -- STARTER, GROWTH, ENTERPRISE
    monthly_fee DECIMAL(10,2),
    api_key VARCHAR(255) UNIQUE,
    
    -- Usage Limits
    kyc_quota INTEGER,
    kyc_used INTEGER DEFAULT 0,
    aml_quota INTEGER,
    aml_used INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20),  -- ACTIVE, SUSPENDED, TRIAL
    created_date TIMESTAMP,
    last_active TIMESTAMP
);
```

**Why store this?**
- ✅ **Multi-tenancy**: Each fintech sees only their own data
- ✅ **Billing**: Track usage for invoicing
- ✅ **Access control**: API key authentication
- ✅ **Compliance**: Know which institutions are using your platform

---

### **6. Regulatory Updates Table**
Stores AI-summarized regulatory circulars.

```sql
CREATE TABLE regulatory_updates (
    id UUID PRIMARY KEY,
    
    -- Source Info
    source VARCHAR(10),  -- CBN, FIRS, SEC, FCCPC
    circular_id VARCHAR(50),
    title VARCHAR(500),
    url TEXT,
    published_date DATE,
    
    -- AI Summary
    summary TEXT,
    action_required TEXT,
    deadline DATE,
    affected_operations TEXT[],
    urgency VARCHAR(10),  -- HIGH, MEDIUM, LOW
    
    -- Tracking
    created_date TIMESTAMP,
    institutions_notified INTEGER DEFAULT 0
);
```

**Why store this?**
- ✅ **Historical record**: Track regulatory changes over time
- ✅ **Notification tracking**: Which institutions have been notified?
- ✅ **Analytics**: How many HIGH urgency updates per month?
- ✅ **Search**: Compliance officers can search past regulations

---

### **7. Audit Logs Table**
Stores every action taken on the platform.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    institution_id UUID NOT NULL,
    user_id UUID,
    
    -- Action Details
    action_type VARCHAR(50),  -- KYC_VERIFY, AML_FLAG, STR_GENERATE
    resource_type VARCHAR(50),  -- CUSTOMER, TRANSACTION, REPORT
    resource_id UUID,
    
    -- Request/Response
    request_data JSONB,
    response_data JSONB,
    
    -- Metadata
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL,
    
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
```

**Why store this?**
- ✅ **Security**: Detect unauthorized access
- ✅ **Compliance**: CBN audits require full audit trail
- ✅ **Debugging**: Trace what happened when something goes wrong
- ✅ **Legal protection**: Prove you followed procedures if sued

---

## 📊 Data Flow Example

**When Moniepoint verifies Adaeze:**

### Step 1: Moniepoint calls WeGoComply API
```json
POST /api/kyc/verify
{
  "customer_id": "MONIE-12345",
  "nin": "12345678901",
  "bvn": "22334455667",
  "selfie": "base64_image"
}
```

### Step 2: WeGoComply calls Dojah API
```json
GET https://api.dojah.io/api/v1/kyc/nin?nin=12345678901
Response: {
  "firstname": "Adaeze",
  "lastname": "Okonkwo",
  "birthdate": "1996-03-15",
  "photo": "https://..."
}
```

### Step 3: WeGoComply stores in database
```sql
INSERT INTO customers (
    customer_id, institution_id, nin, bvn, full_name, 
    date_of_birth, nin_verified, bvn_verified, 
    face_match_verified, face_match_confidence,
    risk_score, risk_level, verification_date, status
) VALUES (
    'MONIE-12345', 'uuid-moniepoint', '12345678901', '22334455667',
    'Adaeze Okonkwo', '1996-03-15', TRUE, TRUE, TRUE, 0.94,
    0.12, 'LOW', NOW(), 'ACTIVE'
);
```

### Step 4: WeGoComply logs the action
```sql
INSERT INTO audit_logs (
    institution_id, action_type, resource_type, resource_id,
    request_data, response_data, timestamp
) VALUES (
    'uuid-moniepoint', 'KYC_VERIFY', 'CUSTOMER', 'uuid-adaeze',
    '{"nin": "12345678901", ...}', '{"status": "VERIFIED", ...}', NOW()
);
```

### Step 5: WeGoComply returns to Moniepoint
```json
{
  "status": "VERIFIED",
  "risk_level": "LOW",
  "risk_score": 0.12
}
```

---

## 🔑 Key Reasons to Store Data

1. **Compliance**: CBN requires 7-year record retention
2. **Audit Trail**: Prove you did your job if questioned
3. **Performance**: Don't re-verify same customer 100 times
4. **Analytics**: Improve ML models with historical data
5. **Billing**: Track API usage for invoicing
6. **Legal Protection**: Evidence in court if needed
7. **Customer Service**: Investigate disputes quickly

---

## 💾 What You DON'T Store

- ❌ **Raw ID card images**: Too much storage, privacy risk (store only verification result)
- ❌ **Dojah's internal data**: You don't need their database, just the verification result
- ❌ **Sensitive PII you don't need**: Minimize data collection (NDPR compliance)

---

## 📈 Database Growth Estimates

For a fintech with 1 million customers:

| Table | Records | Size | Growth Rate |
|-------|---------|------|-------------|
| Customers | 1M | 500 MB | +10k/day |
| Transactions | 100M | 50 GB | +1M/day |
| STR Reports | 5k | 50 MB | +50/day |
| TIN Verifications | 1M | 200 MB | Quarterly |
| Audit Logs | 500M | 100 GB | +5M/day |

**Total**: ~150 GB for 1M customers, growing ~10 GB/month

---

## 🔒 Data Security & Compliance

- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access Control**: Role-based access (RBAC)
- **Data Residency**: Azure Nigeria regions (when available)
- **Retention**: 7 years for compliance records
- **NDPR Compliance**: Data minimization, consent management
- **Backup**: Daily automated backups with 30-day retention

---

## 💡 The Bottom Line

**You store:**
- Verification results (not raw data from Dojah)
- Transaction analysis results
- Compliance reports
- Audit trails

**You DON'T store:**
- Dojah's raw database
- Unnecessary PII
- Raw images (only verification results)

This gives you compliance, performance, and cost optimization while respecting privacy.

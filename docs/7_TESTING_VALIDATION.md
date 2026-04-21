# 7. Testing & Validation Cases

## Overview

WeGoComply uses three levels of testing:
1. **Unit Tests** — individual service functions
2. **Integration Tests** — API endpoints end-to-end
3. **Validation Cases** — real-world scenario testing

---

## KYC Validation Cases

| Test ID | Input | Expected Output | Pass Condition |
|---------|-------|-----------------|----------------|
| KYC-01 | Valid NIN + BVN + matching selfie | `status: VERIFIED, risk_level: LOW` | nin_verified=true, bvn_verified=true, face_match=true |
| KYC-02 | Valid NIN + BVN + non-matching selfie | `status: FAILED, risk_level: HIGH` | face_match=false, confidence < 0.5 |
| KYC-03 | Invalid NIN (not in NIMC) | `status: FAILED` | nin_verified=false |
| KYC-04 | Valid NIN + invalid BVN | `status: FAILED` | bvn_verified=false |
| KYC-05 | All valid, HIGH risk profile | `status: VERIFIED, risk_level: HIGH` | risk_score > 0.7 |
| KYC-06 | Missing selfie | `422 Unprocessable Entity` | Validation error returned |
| KYC-07 | NIN format invalid (not 11 digits) | `422 Unprocessable Entity` | Schema validation error |

### KYC Test Execution

```bash
# Test KYC-01: Valid verification
curl -X POST http://localhost:8000/api/kyc/verify \
  -H "X-Mock-Roles: admin" \
  -F "nin=12345678901" \
  -F "bvn=22334455667" \
  -F "selfie=@test_selfie.jpg"

# Expected:
{
  "status": "VERIFIED",
  "risk_level": "LOW",
  "risk_score": 0.12,
  "details": {
    "nin_verified": true,
    "bvn_verified": true,
    "face_match": true,
    "face_confidence": 0.94
  }
}
```

---

## AML Validation Cases

| Test ID | Transaction | ML Score | Rules Triggered | Expected Risk | Expected Action |
|---------|-------------|----------|-----------------|---------------|-----------------|
| AML-01 | ₦5,000 at 10am, deposit | +0.45 | None | LOW | APPROVE |
| AML-02 | ₦7,500,000 at 2:34am, transfer | -0.312 | R1, R2, R3 | HIGH | GENERATE_STR |
| AML-03 | ₦2,300,000 at 11:58pm, withdrawal | -0.198 | R2 | MEDIUM | REVIEW |
| AML-04 | ₦9,800,000 at 3:11am, transfer | -0.421 | R1, R2, R3 | HIGH | GENERATE_STR |
| AML-05 | ₦45,000 at 10:15am, deposit | +0.23 | None | LOW | APPROVE |
| AML-06 | ₦1,500,000 at 2pm, transfer | -0.05 | R3 | MEDIUM | REVIEW |
| AML-07 | ₦5,000,000 exactly at 9am | -0.08 | R1 | MEDIUM | REVIEW |
| AML-08 | ₦500 at 4:59am, POS | +0.31 | None | LOW | APPROVE |
| AML-09 | ₦200,000 at 4:30am, mobile | -0.15 | R2 | MEDIUM | REVIEW |
| AML-10 | Batch of 5 mixed transactions | Mixed | Mixed | 3 flagged, 2 clean | Per transaction |

### AML Test Execution

```bash
# Test AML-10: Batch analysis
curl -X POST http://localhost:8000/api/aml/monitor \
  -H "Content-Type: application/json" \
  -H "X-Mock-Roles: admin" \
  -d '{
    "transactions": [
      {"transaction_id": "TXN-001", "customer_id": "CUST-4421", "amount": 7500000,
       "currency": "NGN", "timestamp": "2026-04-21T02:34:00",
       "transaction_type": "transfer", "counterparty": "Unknown Corp", "channel": "mobile"},
      {"transaction_id": "TXN-002", "customer_id": "CUST-1102", "amount": 45000,
       "currency": "NGN", "timestamp": "2026-04-21T10:15:00",
       "transaction_type": "deposit", "counterparty": "Salary", "channel": "web"},
      {"transaction_id": "TXN-003", "customer_id": "CUST-8834", "amount": 2300000,
       "currency": "NGN", "timestamp": "2026-04-21T23:58:00",
       "transaction_type": "withdrawal", "counterparty": "ATM Lagos", "channel": "atm"},
      {"transaction_id": "TXN-004", "customer_id": "CUST-3310", "amount": 12000,
       "currency": "NGN", "timestamp": "2026-04-21T14:22:00",
       "transaction_type": "transfer", "counterparty": "John Doe", "channel": "pos"},
      {"transaction_id": "TXN-005", "customer_id": "CUST-9901", "amount": 9800000,
       "currency": "NGN", "timestamp": "2026-04-21T03:11:00",
       "transaction_type": "transfer", "counterparty": "Shell Company XYZ", "channel": "web"}
    ]
  }'

# Expected:
{
  "total_analyzed": 5,
  "flagged_count": 3,
  "clean_count": 2,
  "flagged_transactions": [
    {"transaction_id": "TXN-001", "risk_level": "HIGH", "recommended_action": "GENERATE_STR"},
    {"transaction_id": "TXN-003", "risk_level": "MEDIUM", "recommended_action": "REVIEW"},
    {"transaction_id": "TXN-005", "risk_level": "HIGH", "recommended_action": "GENERATE_STR"}
  ]
}
```

---

## TIN Validation Cases

| Test ID | TIN | Submitted Name | FIRS Name | Expected Status | Confidence |
|---------|-----|----------------|-----------|-----------------|------------|
| TIN-01 | `1234567890` | Adaeze Okonkwo | Adaeze Okonkwo | MATCHED | 1.00 |
| TIN-02 | `0987654321` | Emeka Nwosu | Emeka Nwosu | MATCHED | 1.00 |
| TIN-03 | `1122334455` | Fatima Aliyu | (not found) | NOT_FOUND | 0.00 |
| TIN-04 | `9988776655` | Ngozi Adeyemi | (not found) | NOT_FOUND | 0.00 |
| TIN-05 | `5566778899` | Chukwuemeka Eze | Chukwuemeka Holdings Ltd | NAME_MISMATCH | 0.62 |
| TIN-06 | `1234567890` | Adaeze O. | Adaeze Okonkwo | MATCHED | 0.75 (partial) |
| TIN-07 | `abc123` | Test User | N/A | 422 Validation Error | N/A |
| TIN-08 | (empty) | Test User | N/A | 422 Validation Error | N/A |

### TIN Test Execution

```bash
# Test TIN-01: Single verification
curl -X POST http://localhost:8000/api/tax/verify-tin \
  -H "Content-Type: application/json" \
  -H "X-Mock-Roles: admin" \
  -d '{"customer_id": "CUST-001", "name": "Adaeze Okonkwo", "tin": "1234567890"}'

# Expected:
{
  "customer_id": "CUST-001",
  "tin": "1234567890",
  "status": "MATCHED",
  "firs_name": "Adaeze Okonkwo",
  "submitted_name": "Adaeze Okonkwo",
  "match_confidence": 1.0
}

# Test TIN-03: NOT_FOUND (TIN ends in 55)
curl -X POST http://localhost:8000/api/tax/verify-tin \
  -H "Content-Type: application/json" \
  -H "X-Mock-Roles: admin" \
  -d '{"customer_id": "CUST-003", "name": "Fatima Aliyu", "tin": "1122334455"}'

# Expected:
{
  "customer_id": "CUST-003",
  "tin": "1122334455",
  "status": "NOT_FOUND",
  "firs_name": "",
  "submitted_name": "Fatima Aliyu",
  "match_confidence": 0.0
}
```

---

## Compliance Posture Validation Cases

| Test ID | Institution | Expected Score | Expected Status | Key Factors |
|---------|-------------|----------------|-----------------|-------------|
| CP-01 | inst-moniepoint | 84.2 | COMPLIANT | High KYC/AML rates, 1 late STR |
| CP-02 | inst-kuda | 67.3 | AT RISK | Low TIN rate, 2 late STRs |
| CP-03 | inst-opay | 52.1 | NON-COMPLIANT | 8 late STRs, 850k restricted accounts |
| CP-04 | inst-unknown | Error | N/A | Institution not found |

### Compliance Posture Test Execution

```bash
# Test CP-01: Moniepoint
curl http://localhost:8000/api/compliance/posture/inst-moniepoint \
  -H "X-Mock-Roles: admin"

# Expected:
{
  "overall_score": 84.2,
  "status": "COMPLIANT",
  "pillars": {
    "kyc": {"score": 89.6},
    "aml": {"score": 83.5},
    "tin": {"score": 86.5},
    "reporting": {"score": 71.7}
  }
}

# Test CP-03: OPay (non-compliant)
curl http://localhost:8000/api/compliance/posture/inst-opay \
  -H "X-Mock-Roles: admin"

# Expected:
{
  "overall_score": 52.1,
  "status": "NON-COMPLIANT",
  "action_items": [
    {"priority": "CRITICAL", "action": "File 8 overdue STRs with NFIU immediately"}
  ]
}
```

---

## FIRS ATRS Client Validation Cases

| Test ID | Mode | Input | Expected Output |
|---------|------|-------|-----------------|
| FIRS-01 | Mock | Authenticate | `mock_bearer_token_wegocomply` |
| FIRS-02 | Mock | TIN `1234567890` | `status: true, taxpayer_name: "Adaeze Okonkwo"` |
| FIRS-03 | Mock | TIN ending `55` | `status: false, data: null` |
| FIRS-04 | Mock | TIN ending `99` | `status: true, name: "X Holdings Ltd"` |
| FIRS-05 | Mock | Report bill ₦15,000 | `status: true, uid: "MOCK-UID-INV-001"` |
| FIRS-06 | Mock | SID generation | MD5 hash of concatenated fields |

### SID Generation Test

```python
import hashlib

# Test FIRS-06: Verify SID calculation
client_secret   = "testpass"
vat_number      = "1234567890"
business_place  = "WGCMPLY"
business_device = "WGC-001"
bill_number     = "INV-001"
bill_datetime   = "2026-04-21T09:00:00"
total_value     = "15000.0"

buffer = client_secret + vat_number + business_place + \
         business_device + bill_number + bill_datetime + total_value

expected_sid = hashlib.md5(buffer.encode()).hexdigest()
print(f"SID: {expected_sid}")
# Verify this matches what FIRSClient._generate_sid() returns
```

---

## SupTech Report Validation

| Test ID | Expected | Pass Condition |
|---------|----------|----------------|
| ST-01 | 3 institutions in report | `total_institutions == 3` |
| ST-02 | Sector average ~67.9 | `67 <= sector_average_score <= 69` |
| ST-03 | OPay listed first (lowest score) | `institutions[0].name == "OPay Digital Services"` |
| ST-04 | 2 regulator alerts | `len(regulator_alerts) == 2` |
| ST-05 | OPay alert is CRITICAL | `regulator_alerts[0].severity == "CRITICAL"` |

```bash
# Test ST-01 to ST-05
curl http://localhost:8000/api/compliance/suptech/report \
  -H "X-Mock-Roles: admin"
```

---

## Mock Data Behavior Reference

| Condition | Mock Behavior |
|-----------|---------------|
| TIN ends in `55` | NOT_FOUND |
| TIN ends in `99` | NAME_MISMATCH (returns "X Holdings Ltd") |
| Any other TIN | MATCHED (returns submitted name) |
| `FIRS_MODE=mock` | All FIRS calls return mock responses |
| `FIRS_MODE=live` | All FIRS calls hit real ATRS API |
| `AUTH_MODE=mock` | No real token needed, reads X-Mock-Roles header |
| `WEGOCOMPLY_MODE=mock` | Uses mock data for all external services |

---

## Running All Tests

```bash
# Start backend
cd backend
source venv/bin/activate
uvicorn main:app --reload

# In another terminal, run test suite
cd backend
python -m pytest tests/ -v

# Or test individual endpoints manually
# See curl commands above for each test case
```

---

## Performance Benchmarks

| Operation | Target | Actual (Mock) |
|-----------|--------|---------------|
| KYC verification | < 2 minutes | ~87 seconds |
| Single TIN verify | < 1 second | ~50ms |
| Bulk TIN (1000 records) | < 30 seconds | ~25 seconds |
| AML batch (100 transactions) | < 5 seconds | ~200ms |
| STR generation | < 30 seconds | ~10 seconds (live) / ~1ms (mock) |
| Compliance posture score | < 1 second | ~50ms |
| Regulatory summary | < 30 seconds | ~8 seconds (live) / ~1ms (mock) |

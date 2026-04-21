# WeGoComply — FIRS TIN Issuance & Annual Tax Filing Guide

## Overview

This document explains how a fintech or bank using WeGoComply helps their users:
1. **Get a TIN** (Tax Identification Number) — required for all bank accounts from January 2026
2. **Verify an existing TIN** — match customer records against FIRS
3. **File annual tax returns** — submit VAT and transaction reports to FIRS via ATRS API

WeGoComply acts as the compliance middleware between the fintech and FIRS.

---

## Part 1: TIN Issuance — How a User Gets a TIN

### Who Needs a TIN?
Under the Nigeria Tax Administration Act 2025, **every Nigerian** must have a TIN to:
- Open or operate a bank account
- Transact above ₦500,000
- Receive salary payments
- Register a business

### How WeGoComply Helps Fintechs Issue TINs to Users

WeGoComply does **not** issue TINs directly — only FIRS/JTB can do that. What WeGoComply does is:
1. Check if the user already has a TIN
2. If not, guide them through the JTB registration process
3. Verify the TIN once obtained
4. Store the verified TIN in the fintech's compliance records

---

### Flow 1: New User Onboarding (No TIN Yet)

```
User opens Moniepoint app
        │
        ▼
Moniepoint calls WeGoComply:
POST /api/tax/verify-tin
{
  "customer_id": "CUST-001",
  "name": "Adaeze Okonkwo",
  "tin": ""   ← empty, user doesn't have one
}
        │
        ▼
WeGoComply checks FIRS ATRS:
GET https://atrs-api.firs.gov.ng/v1/taxpayer/verify?tin=
        │
        ▼
Response: {"status": false, "data": null}
        │
        ▼
WeGoComply returns to Moniepoint:
{
  "status": "NOT_FOUND",
  "action_required": "TIN_REGISTRATION",
  "registration_url": "https://jtb.gov.ng",
  "instructions": "User must register for TIN at JTB portal"
}
        │
        ▼
Moniepoint shows user:
"You need a TIN to complete your account setup.
 Register free at jtb.gov.ng — takes 5 minutes."
```

### How the User Gets Their TIN (JTB Portal)

The user visits **https://jtb.gov.ng** and:

1. Clicks "Register for TIN"
2. Selects type: Individual or Business
3. Provides:
   - Full name (must match BVN)
   - Date of birth
   - NIN (National Identification Number)
   - Phone number
   - Email address
   - State of residence
4. Submits — TIN is issued **instantly** (free of charge)
5. TIN is a 10-digit number e.g. `1234567890`

### Flow 2: User Returns with TIN

```
User enters TIN in Moniepoint app: "1234567890"
        │
        ▼
Moniepoint calls WeGoComply:
POST /api/tax/verify-tin
{
  "customer_id": "CUST-001",
  "name": "Adaeze Okonkwo",
  "tin": "1234567890"
}
        │
        ▼
WeGoComply authenticates with FIRS ATRS:
POST https://atrs-api.firs.gov.ng/oauth2/token
{
  "client_id": "wegocomply_client",
  "client_secret": "secret",
  "grant_type": "password",
  "username": "wegocomply_user",
  "password": "password"
}
Response: {"access_token": "7856444b9e5cc5a9d57f75c989ff1b0140ed1340", ...}
        │
        ▼
WeGoComply verifies TIN with FIRS:
GET https://atrs-api.firs.gov.ng/v1/taxpayer/verify?tin=1234567890
Authorization: Bearer 7856444b9e5cc5a9d57f75c989ff1b0140ed1340

Response:
{
  "status": true,
  "data": {
    "tin": "1234567890",
    "taxpayer_name": "Adaeze Okonkwo",
    "tax_office": "Lagos Island",
    "registration_date": "2020-03-10",
    "status": "ACTIVE"
  }
}
        │
        ▼
WeGoComply name-matches:
"Adaeze Okonkwo" vs "Adaeze Okonkwo" → 100% match
        │
        ▼
WeGoComply returns to Moniepoint:
{
  "customer_id": "CUST-001",
  "tin": "1234567890",
  "status": "MATCHED",
  "firs_name": "Adaeze Okonkwo",
  "submitted_name": "Adaeze Okonkwo",
  "match_confidence": 1.0
}
        │
        ▼
Moniepoint stores verified TIN in database
Account fully activated ✓
```

---

## Part 2: Bulk TIN Verification (Existing Customers)

For fintechs with millions of existing customers who need TIN verification:

### API Call

```http
POST /api/tax/bulk-verify
Authorization: Bearer <token>
Content-Type: application/json

{
  "records": [
    {"customer_id": "CUST-001", "name": "Adaeze Okonkwo",  "tin": "1234567890"},
    {"customer_id": "CUST-002", "name": "Emeka Nwosu",     "tin": "0987654321"},
    {"customer_id": "CUST-003", "name": "Fatima Aliyu",    "tin": "1122334455"},
    {"customer_id": "CUST-004", "name": "Chukwuemeka Eze", "tin": "5566778899"},
    {"customer_id": "CUST-005", "name": "Ngozi Adeyemi",   "tin": "9988776655"}
  ]
}
```

### Response

```json
{
  "total": 5,
  "matched": 3,
  "failed": 2,
  "match_rate": 60.0,
  "deadline_risk": "HIGH",
  "records": [
    {
      "customer_id": "CUST-001",
      "tin": "1234567890",
      "status": "MATCHED",
      "firs_name": "Adaeze Okonkwo",
      "submitted_name": "Adaeze Okonkwo",
      "match_confidence": 1.0
    },
    {
      "customer_id": "CUST-002",
      "tin": "0987654321",
      "status": "MATCHED",
      "firs_name": "Emeka Nwosu",
      "submitted_name": "Emeka Nwosu",
      "match_confidence": 1.0
    },
    {
      "customer_id": "CUST-003",
      "tin": "1122334455",
      "status": "NOT_FOUND",
      "firs_name": "",
      "submitted_name": "Fatima Aliyu",
      "match_confidence": 0.0
    },
    {
      "customer_id": "CUST-004",
      "tin": "5566778899",
      "status": "MATCHED",
      "firs_name": "Chukwuemeka Eze",
      "submitted_name": "Chukwuemeka Eze",
      "match_confidence": 1.0
    },
    {
      "customer_id": "CUST-005",
      "tin": "9988776655",
      "status": "NOT_FOUND",
      "firs_name": "",
      "submitted_name": "Ngozi Adeyemi",
      "match_confidence": 0.0
    }
  ]
}
```

### What Happens After

| Status | Action |
|--------|--------|
| `MATCHED` | Account fully active, TIN stored |
| `NOT_FOUND` | Send SMS/email: "Register TIN at jtb.gov.ng" |
| `NAME_MISMATCH` | Contact customer to confirm legal name |

---

## Part 3: Annual Tax Filing via FIRS ATRS

### What is ATRS?

FIRS ATRS (Automated Tax Remittance System) is the official FIRS API for submitting:
- **VAT returns** — monthly, on all taxable transactions
- **Receipt/bill reports** — real-time transaction reporting
- **Annual tax remittances** — yearly compliance submissions

### How WeGoComply Submits Bills to FIRS

Every time a fintech processes a taxable transaction, WeGoComply can report it to FIRS automatically.

#### Step 1: Authenticate with FIRS

```http
POST https://atrs-api.firs.gov.ng/oauth2/token
Content-Type: application/x-www-form-urlencoded

client_id=wegocomply_client
&client_secret=your_secret
&grant_type=password
&username=your_username
&password=your_password
```

Response:
```json
{
  "access_token": "7856444b9e5cc5a9d57f75c989ff1b0140ed1340",
  "expires_in": 86400,
  "token_type": "Bearer",
  "refresh_token": "124c82b2c8d72b6aef49f7d0f1b221d27c0c71ca"
}
```

Token is valid for **24 hours** (`expires_in: 86400` seconds).

#### Step 2: Generate Security Code (SID)

Before submitting a bill, generate the MD5 security signature:

```python
import hashlib

def generate_sid(
    client_secret: str,
    vat_number: str,
    business_place: str,
    business_device: str,
    bill_number: str,
    bill_datetime: str,
    total_value: float
) -> str:
    buffer = (
        client_secret
        + vat_number
        + business_place
        + business_device
        + bill_number
        + bill_datetime
        + str(total_value)
    )
    return hashlib.md5(buffer.encode()).hexdigest()

# Example:
sid = generate_sid(
    client_secret  = "your_secret",
    vat_number     = "1234567890",
    business_place = "WGCMPLY",
    business_device= "WGC-001",
    bill_number    = "INV-2026-001",
    bill_datetime  = "2026-04-21T09:00:00",
    total_value    = 15000.00
)
# Result: "a3f5c8d2e1b4a7f9c2d5e8b1a4f7c0d3" (example)
```

#### Step 3: Submit Bill to FIRS

```http
POST https://atrs-api.firs.gov.ng/v1/bills/report
Authorization: Bearer 7856444b9e5cc5a9d57f75c989ff1b0140ed1340
Content-Type: application/json

{
  "vat_number":       "1234567890",
  "business_place":   "WGCMPLY",
  "business_device":  "WGC-001",
  "bill_number":      "INV-2026-001",
  "bill_datetime":    "2026-04-21T09:00:00",
  "total_value":      15000.00,
  "tax_free":         0.00,
  "payment_type":     "T",
  "security_code":    "a3f5c8d2e1b4a7f9c2d5e8b1a4f7c0d3",
  "currency_code":    "NGN",
  "client_vat_number":"9876543210",
  "rate":             7.5,
  "base_value":       13953.49,
  "value":            1046.51,
  "resend":           0,
  "bill_taxes": [
    {
      "name":     "VAT",
      "rate":     7.5,
      "base":     13953.49,
      "amount":   1046.51
    }
  ],
  "items": [
    {
      "name":     "Compliance Service Fee",
      "quantity": 1,
      "price":    15000.00,
      "vat":      1046.51
    }
  ]
}
```

#### FIRS Response

```json
{
  "status": true,
  "uid": "FIRS-UID-20260421-001",
  "created_at": "2026-04-21T09:00:05Z",
  "payment_code": "FIRS-UID-20260421-001"
}
```

The `uid` (Unique Identifier) is FIRS's acknowledgment. Store it — it's your proof of submission.

---

### Payment Type Codes

| Code | Meaning |
|------|---------|
| `C` | Cash |
| `T` | Bank transfer |
| `K` | Credit card |
| `D` | Debit card |
| `P` | Post payment (credit) |
| `O` | Other / mixed |

---

## Part 4: Annual Tax Return Filing (TaxPro Max)

For annual Company Income Tax (CIT) and VAT returns, FIRS uses **TaxPro Max** — a separate portal from ATRS.

### How WeGoComply Supports Annual Filing

WeGoComply aggregates all transaction data throughout the year and generates a pre-filled annual return report that the fintech's accountant can upload to TaxPro Max.

#### Step 1: WeGoComply Generates Annual Summary

```http
GET /api/tax/annual-summary?year=2025&institution_id=inst-moniepoint
Authorization: Bearer <token>
```

Response:
```json
{
  "institution": "Moniepoint MFB",
  "tax_year": 2025,
  "tin": "1234567890",
  "summary": {
    "total_revenue":        5000000000.00,
    "total_vat_collected":    375000000.00,
    "total_vat_remitted":     370000000.00,
    "vat_outstanding":          5000000.00,
    "total_transactions":      12500000,
    "taxable_transactions":    11800000,
    "tax_exempt_transactions":   700000
  },
  "monthly_breakdown": [
    {"month": "2025-01", "revenue": 380000000, "vat": 28500000, "remitted": 28500000},
    {"month": "2025-02", "revenue": 390000000, "vat": 29250000, "remitted": 29250000},
    ...
  ],
  "firs_submissions": [
    {"uid": "FIRS-UID-20250131-001", "date": "2025-01-31", "amount": 28500000, "status": "ACCEPTED"},
    ...
  ],
  "compliance_status": "COMPLIANT",
  "outstanding_filings": []
}
```

#### Step 2: File on TaxPro Max

1. Go to **https://taxpromax.firs.gov.ng**
2. Login with FIRS credentials
3. Select "File Returns" → "Company Income Tax"
4. Upload the annual summary generated by WeGoComply
5. Review pre-filled figures
6. Submit and download Tax Clearance Certificate (TCC)

---

## Part 5: WeGoComply API Reference for TIN & Tax

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tax/verify-tin` | Verify single TIN against FIRS |
| `POST` | `/api/tax/bulk-verify` | Bulk TIN verification |
| `POST` | `/api/tax/report-bill` | Submit transaction bill to FIRS ATRS |
| `GET`  | `/api/tax/annual-summary` | Generate annual tax summary |

### Environment Variables

```bash
# FIRS ATRS Configuration
FIRS_MODE=mock              # mock | live
FIRS_CLIENT_ID=testclient   # From FIRS registration
FIRS_CLIENT_SECRET=testpass # From FIRS registration
FIRS_USERNAME=admin         # From FIRS registration
FIRS_PASSWORD=admin123      # From FIRS registration
FIRS_VAT_NUMBER=0000000000  # Your institution's VAT/TIN
FIRS_BUSINESS_PLACE=WGCMPLY # Short code from FIRS registration
FIRS_BUSINESS_DEVICE=WGC-001 # Device/system identifier
```

### Switching from Mock to Live

```bash
# In backend/.env, change:
FIRS_MODE=mock   →   FIRS_MODE=live

# Add real credentials from https://atrs.firs.gov.ng/getting-started/
FIRS_CLIENT_ID=your_real_client_id
FIRS_CLIENT_SECRET=your_real_secret
FIRS_USERNAME=your_username
FIRS_PASSWORD=your_password
FIRS_VAT_NUMBER=your_tin
FIRS_BUSINESS_PLACE=your_place_code
FIRS_BUSINESS_DEVICE=your_device_id
```

Zero code changes needed. The `FIRSClient` handles the switch automatically.

---

## Part 6: FIRS API Environments

| Environment | Base URL | Use For |
|-------------|----------|---------|
| Development | `https://api-dev.i-fis.com` | Testing with mock credentials |
| Production | `https://atrs-api.firs.gov.ng` | Live submissions |

### Dev Credentials (for testing)

```
client_id:     testclient
client_secret: testpass
username:      admin
password:      admin123
```

These are public test credentials from the FIRS documentation. They work on the dev environment only.

---

## Part 7: Error Handling

### Common FIRS API Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid business place!` | Wrong `business_place` code | Register at atrs.firs.gov.ng and use the assigned code |
| `Invalid security code` | Wrong MD5 signature | Check field order in SID generation |
| `TIN not found` | TIN not registered with FIRS | User must register at jtb.gov.ng |
| `Name mismatch` | Name doesn't match FIRS records | Customer must update name with FIRS |
| `401 Unauthorized` | Token expired | Re-authenticate (token valid 24hrs) |
| `400 Bad Request` | Missing grant_type | Set `grant_type=password` in auth request |

---

## Part 8: Compliance Timeline

| Date | Requirement | WeGoComply Action |
|------|-------------|-------------------|
| January 1, 2026 | All bank accounts must have TIN | Bulk verify existing customers |
| April 1, 2026 | Accounts without TIN restricted above ₦500k | Flag non-compliant accounts |
| Monthly | VAT returns due by 21st of following month | Auto-submit via ATRS API |
| June 30 each year | Annual CIT return deadline | Generate annual summary report |
| Ongoing | Real-time transaction reporting | Submit bills to ATRS on each transaction |

---

## Summary

```
User needs TIN
      │
      ▼
WeGoComply checks FIRS → Not found
      │
      ▼
User registers at jtb.gov.ng (free, 5 mins)
      │
      ▼
User provides TIN to fintech
      │
      ▼
WeGoComply verifies TIN with FIRS ATRS
      │
      ├── MATCHED → Account activated, TIN stored
      ├── NOT_FOUND → User re-registers
      └── NAME_MISMATCH → User updates name with FIRS
            │
            ▼
Fintech processes transactions
            │
            ▼
WeGoComply reports each bill to FIRS ATRS (real-time)
            │
            ▼
WeGoComply generates annual summary
            │
            ▼
Fintech files annual return on TaxPro Max
            │
            ▼
Tax Clearance Certificate issued ✓
```

---

## Resources

- FIRS ATRS API Docs: https://atrs.firs.gov.ng/docs/category/api-documentation-for-devs/
- FIRS ATRS Registration: https://atrs.firs.gov.ng/getting-started/
- FIRS Dev Swagger: https://api-dev.i-fis.com/doc
- JTB TIN Registration: https://jtb.gov.ng
- TaxPro Max (Annual Returns): https://taxpromax.firs.gov.ng
- FIRS Support: support@atrs.firs.gov.ng

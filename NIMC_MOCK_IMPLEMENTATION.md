# NIMC Mock Implementation Guide

This document provides comprehensive instructions for running and testing the NIMC mock implementation in WeGoComply.

## Overview

The NIMC mock provider simulates the NIMC eNVS API structure while maintaining the provider-agnostic architecture. It provides realistic Nigerian identity data and authentication flows for development and testing.

## Architecture

### Backend Components

1. **NIMC Mock Provider** (`backend/app/services/identity/providers/nimc_mock_provider.py`)
   - Implements full eNVS API structure
   - Token simulation with expiry
   - 25+ realistic Nigerian identity records
   - Deterministic fingerprint matching

2. **NIMC Schemas** (`backend/app/schemas/nimc.py`)
   - Complete Pydantic models mirroring NIMC eNVS
   - Preserves original field naming
   - Type validation and serialization

3. **Mock Data** (`backend/app/mock_data/nimc_records.json`)
   - 25 realistic Nigerian identity records
   - Complete demographic data
   - Various states, professions, and backgrounds

4. **Debug Routes** (`backend/routers/nimc_mock.py`)
   - Raw NIMC API endpoints for testing
   - Provider information endpoints
   - Mock record listing

### Frontend Components

1. **Identity Types** (`frontend/src/types/identity.ts`)
   - TypeScript interfaces for unified responses
   - NIMC-specific request/response types

2. **KYC Component** (`frontend/src/pages/KYC.jsx`)
   - Updated for NIN verification with demographics
   - Provider status indicators
   - Raw response inspection (dev mode)

## Configuration

### Backend Environment

Update your `.env` file:

```bash
# Identity Provider Configuration
IDENTITY_MODE=mock
IDENTITY_PROVIDER=nimc_mock

# NIMC Mock Configuration
NIMC_MOCK_USERNAME=demo_user
NIMC_MOCK_PASSWORD=demo_pass
NIMC_MOCK_ORGID=demo_org
NIMC_MOCK_TOKEN_EXPIRY_MINUTES=30
```

### Frontend Environment

Update your `.env` file:

```bash
# Frontend Environment Variables
VITE_AUTH_MODE=mock
VITE_API_BASE_URL=http://localhost:8000
```

## Running the Application

### Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

### Frontend

```bash
cd frontend
npm run dev
```

## Testing Guide

### 1. Basic NIN Verification

**Request:**
```bash
curl -X POST http://localhost:8000/api/kyc/verify \
  -H "Content-Type: multipart/form-data" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Email: admin@wegocomply.local" \
  -H "X-Mock-Name: Demo Admin" \
  -H "X-Mock-Roles: admin" \
  -F "verification_type=nin" \
  -F "identifier=12345678901" \
  -F "firstname=Adeola" \
  -F "lastname=Ojukwu" \
  -F "dob=15/03/1985"
```

**Expected Response:**
```json
{
  "success": true,
  "provider": "nimc_mock",
  "match_score": {
    "firstname": true,
    "lastname": true,
    "dob": true
  },
  "identity": {
    "nin": "12345678901",
    "firstname": "Adeola",
    "lastname": "Ojukwu",
    "gender": "Female",
    "birthdate": "15/03/1985",
    "phone": "08023456789",
    "address": {
      "state": "Lagos",
      "city": "Lekki"
    },
    "profession": "Software Engineer"
  },
  "raw": {
    "nimc_response": {
      "data": { /* full NIMC record */ },
      "returnMessage": "Success"
    }
  }
}
```

### 2. NIMC Token Creation

**Request:**
```bash
curl -X POST http://localhost:8000/api/mock/nimc/create-token \
  -H "Content-Type: application/json" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin" \
  -d '{
    "username": "demo_user",
    "password": "demo_pass",
    "orgid": "demo_org"
  }'
```

**Expected Response:**
```json
{
  "loginMessage": {
    "loginString": "NIMC-TOKEN-ABC123...",
    "expireTime": "2024-01-01T12:30:00",
    "loginObject": {
      "username": "demo_user",
      "orgid": "demo_org",
      "loginTime": "2024-01-01T12:00:00",
      "loginExpiryTimeInMinutes": 30
    }
  },
  "loginString": "NIMC-TOKEN-ABC123..."
}
```

### 3. Search by NIN (Raw NIMC API)

**Request:**
```bash
# First get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/mock/nimc/create-token \
  -H "Content-Type: application/json" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin" \
  -d '{"username": "demo_user", "password": "demo_pass", "orgid": "demo_org"}' | \
  jq -r '.loginString')

# Then search by NIN
curl -X POST http://localhost:8000/api/mock/nimc/search-by-nin \
  -H "Content-Type: application/json" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin" \
  -d "{\"token\": \"$TOKEN\", \"nin\": \"12345678901\"}"
```

### 4. Search by Demographics

**Request:**
```bash
curl -X POST http://localhost:8000/api/mock/nimc/search-by-demo \
  -H "Content-Type: application/json" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin" \
  -d '{
    "token": "NIMC-TOKEN-ABC123...",
    "firstname": "Adeola",
    "lastname": "Ojukwu",
    "gender": "Female",
    "dateOfBirth": "15/03/1985"
  }'
```

### 5. Provider Information

**Request:**
```bash
curl http://localhost:8000/api/mock/nimc/info \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin"
```

**Expected Response:**
```json
{
  "name": "NIMC Mock Provider",
  "version": "1.0.0",
  "supported_operations": ["verify_nin"],
  "features": ["mock_auth", "token_simulation", "realistic_data"],
  "mode": "mock"
}
```

### 6. List Mock Records

**Request:**
```bash
curl http://localhost:8000/api/mock/nimc/records \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin"
```

## Available Test NINs

The mock system includes these test NINs:

| NIN | First Name | Last Name | Gender | State |
|-----|------------|-----------|--------|-------|
| 12345678901 | Adeola | Ojukwu | Female | Lagos |
| 12345678902 | Ibrahim | Mohammed | Male | Kano |
| 12345678903 | Funke | Adebayo | Female | Oyo |
| 12345678904 | Chidi | Okoro | Male | Rivers |
| 12345678905 | Fatima | Danladi | Female | Plateau |
| 12345678906 | Osayi | Emwantor | Male | Edo |
| 12345678907 | Aisha | Yusuf | Female | Kaduna |
| 12345678908 | Chukwuemeka | Obi | Male | Anambra |
| 12345678909 | Zainab | Ali | Female | Borno |
| 12345678910 | Babatunde | Adeyemi | Male | Osun |

## Frontend Testing

### 1. Navigate to KYC Page

1. Open http://localhost:5173/
2. Click "KYC Verification" in the sidebar
3. Look for "Mock Mode" indicator

### 2. Test NIN Verification

1. Enter NIN: `12345678901`
2. Enter First Name: `Adeola`
3. Enter Last Name: `Ojukwu`
4. Enter Date of Birth: `15/03/1985`
5. Click "Verify Identity"

### 3. Verify Results

- Check provider shows "nimc_mock"
- Verify match scores are displayed
- Check identity information is populated
- Toggle "Show Raw Response" to see NIMC data

## Error Scenarios

### Invalid NIN

```bash
curl -X POST http://localhost:8000/api/kyc/verify \
  -H "Content-Type: multipart/form-data" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin" \
  -F "verification_type=nin" \
  -F "identifier=99999999999" \
  -F "firstname=Invalid" \
  -F "lastname=Name"
```

**Expected Response:** `404 Not Found` with error message

### Demographic Mismatch

```bash
curl -X POST http://localhost:8000/api/kyc/verify \
  -H "Content-Type: multipart/form-data" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Roles: admin" \
  -F "verification_type=nin" \
  -F "identifier=12345678901" \
  -F "firstname=Wrong" \
  -F "lastname=Name"
```

**Expected Response:** Success with `match_score` showing `false` for mismatched fields

### Expired Token

Use a token that has expired (after 30 minutes) or an invalid token format.

## Development Features

### Raw Response Inspection

In mock mode, the frontend shows a "Show Raw Response" button that displays the complete NIMC mock response structure.

### Provider Information

The KYC page displays current provider information including:
- Provider name and mode
- Supported operations
- Mock status indicator

### Token Simulation

The NIMC mock provider simulates:
- Token creation with realistic strings
- Token expiry (30 minutes default)
- Token validation and refresh

## Migration to Production

When ready to switch to real NIMC:

1. Update environment variables:
   ```bash
   IDENTITY_MODE=live
   IDENTITY_PROVIDER=nimc
   ```

2. Configure real NIMC credentials:
   ```bash
   NIMC_USERNAME=your_real_username
   NIMC_PASSWORD=your_real_password
   NIMC_ORGID=your_real_orgid
   ```

3. Replace mock provider with real NIMC provider implementation

4. Test with real NIMC endpoints

## Troubleshooting

### Common Issues

1. **404 Errors on KYC endpoints**
   - Check backend is running
   - Verify IDENTITY_PROVIDER=nimc_mock
   - Check authentication headers

2. **Frontend not showing provider info**
   - Verify VITE_API_BASE_URL is correct
   - Check browser console for errors
   - Ensure mock mode is enabled

3. **Token validation errors**
   - Check NIMC_MOCK_* credentials
   - Verify token hasn't expired
   - Check token format in requests

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will show detailed provider operations and token management.

## API Reference

### Main KYC Endpoint

```
POST /api/kyc/verify
Content-Type: multipart/form-data

Fields:
- verification_type: "nin"
- identifier: NIN number
- firstname: First name
- lastname: Last name
- dob: Date of birth (DD/MM/YYYY)
- phone: Phone number (optional)
- email: Email (optional)
- selfie: File upload (optional)
```

### NIMC Debug Endpoints

```
POST /api/mock/nimc/create-token
POST /api/mock/nimc/search-by-nin
POST /api/mock/nimc/search-by-demo
POST /api/mock/nimc/search-by-phone
POST /api/mock/nimc/search-by-document
POST /api/mock/nimc/search-by-finger
POST /api/mock/nimc/verify-finger
GET  /api/mock/nimc/permissions/{level}
GET  /api/mock/nimc/info
GET  /api/mock/nimc/records
```

All debug endpoints require:
- Mock mode enabled
- Admin role authentication
- Valid mock credentials

# VerifyMe NIN Verification Integration

This document explains how to set up and use VerifyMe NIN verification in WeGoComply.

## Overview

VerifyMe provides Nigerian NIN verification as an alternative to Dojah. The integration includes:
- NIN verification with demographic matching
- Field-level matching (firstname, lastname, DOB)
- Base64 photo retrieval
- Comprehensive error handling and audit logging

## Environment Configuration

Add these variables to your `backend/.env`:

```bash
# VerifyMe Configuration
VERIFYME_SECRET_KEY=your_verifyme_secret_key

# Keep existing Azure and other configurations
AZURE_OPENAI_ENDPOINT=https://wegocomply.openai.azure.com/
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_FACE_ENDPOINT=https://wegocomplyface.cognitiveservices.azure.com/
AZURE_FACE_KEY=your_key
```

### Getting VerifyMe Credentials

1. Sign up at [VerifyMe](https://verifyme.ng)
2. Request API access for NIN verification
3. Receive your secret key
4. Add it to `VERIFYME_SECRET_KEY`

## API Endpoints

### Verify NIN
```
POST /api/verifyme/verify-nin
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "nin": "10000000001",
  "firstname": "John",
  "lastname": "Doe",
  "dob": "17/01/1988"
}
```

### Response Format
```json
{
  "success": true,
  "match_score": {
    "firstname": true,
    "lastname": true,
    "dob": true
  },
  "identity": {
    "nin": "10000000001",
    "firstname": "John",
    "lastname": "Doe",
    "middlename": "Jane",
    "phone": "08066676673",
    "gender": "female",
    "birthdate": "17/01/1988",
    "photo_base64": "base64_encoded_photo_string"
  },
  "raw_message": null,
  "verification_reference": "VERIFYME_20240421_143022"
}
```

## Test Commands

### Test with Mock Data (John Doe)
```bash
curl -X POST http://localhost:8000/api/verifyme/verify-nin \
  -H "Authorization: Bearer your_mock_token" \
  -H "Content-Type: application/json" \
  -H "X-Mock-User: demo-admin" \
  -H "X-Mock-Email: admin@wegocomply.local" \
  -H "X-Mock-Name: Demo Admin" \
  -H "X-Mock-Roles: admin" \
  -d '{
    "nin": "10000000001",
    "firstname": "John",
    "lastname": "Doe",
    "dob": "17/01/1988"
  }'
```

### Test with Real NIN
```bash
curl -X POST http://localhost:8000/api/verifyme/verify-nin \
  -H "Authorization: Bearer your_real_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "nin": "real_nin_here",
    "firstname": "real_firstname",
    "lastname": "real_lastname",
    "dob": "dd/mm/yyyy"
  }'
```

## Error Handling

The system handles these errors:

| Error Type | HTTP Status | Description |
|------------|--------------|-------------|
| Invalid Input | 422 | Missing/invalid NIN, names, or DOB |
| Invalid Credentials | 500 | VerifyMe API key invalid |
| Rate Limit | 429 | Too many requests to VerifyMe |
| NIN Not Found | 200 | Returns success=false with message |
| Service Unavailable | 500 | VerifyMe service down |

## Security Features

- **Secret Key Protection**: VerifyMe key never exposed to frontend
- **Input Validation**: All inputs validated before API calls
- **Audit Logging**: All verification attempts logged
- **Rate Limiting**: Configurable rate limits
- **Error Sanitization**: Sensitive data masked in logs

## Integration with Existing KYC

The VerifyMe service integrates with existing KYC flow:

1. User enters NIN, firstname, lastname, DOB
2. Frontend calls `/api/verifyme/verify-nin`
3. Backend calls VerifyMe API
4. Response normalized and returned to frontend
5. Results可用于 compliance scoring

## Testing Checklist

- [ ] Add `VERIFYME_SECRET_KEY` to `.env`
- [ ] Test with John Doe test data
- [ ] Verify audit logs are created
- [ ] Test error cases (invalid NIN, missing fields)
- [ ] Verify rate limiting works
- [ ] Test with real NIN data
- [ ] Check frontend integration

## Common Failure Cases

1. **Missing VERIFYME_SECRET_KEY**
   - Error: "Identity verification service configuration error"
   - Fix: Add valid secret key to `.env`

2. **Invalid NIN Format**
   - Error: "Invalid input: NIN must be 11 digits"
   - Fix: Ensure NIN is exactly 11 digits

3. **Rate Limiting**
   - Error: "Too many verification requests. Please try again later."
   - Fix: Implement backoff strategy

4. **Network Issues**
   - Error: "Network error during verification"
   - Fix: Check internet connectivity and VerifyMe status

## Production Considerations

- **Monitoring**: Monitor VerifyMe API response times
- **Fallback**: Consider backup verification provider
- **Caching**: Cache successful verifications (with TTL)
- **Compliance**: Ensure all verifications are auditable
- **Scaling**: Handle concurrent verification requests

## Support

- VerifyMe Documentation: [VerifyMe API Docs](https://docs.verifyme.ng)
- WeGoComply Issues: [GitHub Issues](https://github.com/jvcByte/WeGoComply/issues)
- For technical support, include verification reference from API response

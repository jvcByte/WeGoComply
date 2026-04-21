# Frontend Testing Guide for NIMC Mock

## Quick Start

1. **Start the Backend**
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

2. **Start the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Navigate to KYC Page**
   - Open http://localhost:5173
   - Click "KYC Verification" in the sidebar
   - Look for "Mock Mode" indicator

## Test Data That Will Work

Use these exact test cases for guaranteed success:

### Test Case 1: Perfect Match
```
NIN: 12345678901
First Name: Adeola
Last Name: Ojukwu
Date of Birth: 15/03/1985
Phone: 08023456789 (optional)
```

### Test Case 2: Different State
```
NIN: 12345678902
First Name: Ibrahim
Last Name: Mohammed
Date of Birth: 22/07/1978
Phone: 08034567890 (optional)
```

### Test Case 3: Female from Oyo
```
NIN: 12345678903
First Name: Funke
Last Name: Adebayo
Date of Birth: 08/11/1992
Phone: 09012345678 (optional)
```

### Test Case 4: Male from Rivers
```
NIN: 12345678904
First Name: Chidi
Last Name: Okoro
Date of Birth: 30/04/1980
Phone: 08056789012 (optional)
```

### Test Case 5: Female from Plateau
```
NIN: 12345678905
First Name: Fatima
Last Name: Danladi
Date of Birth: 12/09/1995
Phone: 08067890123 (optional)
```

## All Available Test NINs

| NIN | First Name | Last Name | Gender | State | DOB |
|-----|------------|-----------|--------|-------|-----|
| 12345678901 | Adeola | Ojukwu | Female | Lagos | 15/03/1985 |
| 12345678902 | Ibrahim | Mohammed | Male | Kano | 22/07/1978 |
| 12345678903 | Funke | Adebayo | Female | Oyo | 08/11/1992 |
| 12345678904 | Chidi | Okoro | Male | Rivers | 30/04/1980 |
| 12345678905 | Fatima | Danladi | Female | Plateau | 12/09/1995 |
| 12345678906 | Osayi | Emwantor | Male | Edo | 25/02/1975 |
| 12345678907 | Aisha | Yusuf | Female | Kaduna | 18/06/1988 |
| 12345678908 | Chukwuemeka | Obi | Male | Anambra | 05/12/1990 |
| 12345678909 | Zainab | Ali | Female | Borno | 14/08/1983 |
| 12345678910 | Babatunde | Adeyemi | Male | Osun | 29/03/1972 |

## What You'll See

### 1. Mock Mode Indicator
- Purple badge showing "Mock Mode" 
- Provider information section

### 2. Successful Verification
- Green checkmark with "nimc_mock" provider
- Match scores showing which fields matched
- Complete identity information display
- Address and professional details

### 3. Raw Response (Development)
- "Show Raw Response" button
- Complete NIMC mock data structure
- Useful for debugging

## Error Testing

### Invalid NIN
```
NIN: 99999999999
First Name: Wrong
Last Name: Name
Date of Birth: 01/01/2000
```
**Expected:** "Not Found" error

### Demographic Mismatch
```
NIN: 12345678901
First Name: Wrong
Last Name: Name
Date of Birth: 01/01/2000
```
**Expected:** Success but with red X marks for mismatched fields

## Step-by-Step Testing

1. **Start both applications**
2. **Open browser to http://localhost:5173**
3. **Click "KYC Verification"**
4. **Verify you see "Mock Mode" indicator**
5. **Enter Test Case 1 data exactly as shown**
6. **Click "Verify Identity"**
7. **Check results show green success**
8. **Toggle "Show Raw Response" to see NIMC data**
9. **Try error cases to see failure handling**

## Troubleshooting

### Frontend Issues
- **White screen**: Check browser console for errors
- **API errors**: Verify backend is running on port 8000
- **No Mock Mode**: Check VITE_AUTH_MODE=mock in frontend .env

### Backend Issues
- **404 errors**: Check IDENTITY_PROVIDER=nimc_mock in backend .env
- **Authentication errors**: Verify mock headers are being sent
- **No data**: Check mock data file exists and loads correctly

### Success Indicators
- Backend console shows "Provider loaded with 25 records"
- Frontend shows purple "Mock Mode" badge
- Verification returns green checkmarks
- Raw response shows NIMC data structure

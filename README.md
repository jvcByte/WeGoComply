# WeGoComply — AI-Powered AML/KYC & Tax Compliance Platform

## Project Structure
```
wegocomply/
├── backend/          # FastAPI Python backend
├── frontend/         # React + Tailwind dashboard
└── ml/               # Anomaly detection model
```

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Demo Flow
1. Onboard a customer (KYC) → NIN/BVN verify → facial match → risk score
2. Monitor transactions → anomaly flagged → STR auto-generated
3. Regulatory feed → CBN/FIRS circulars summarized by AI

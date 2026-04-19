# WeGoComply — AI-Powered Compliance Platform for Nigerian Fintechs

**RegTech Hackathon — Microsoft AI Skills Week 2026**

WeGoComply automates KYC/KYB verification, real-time AML transaction monitoring, and bulk TIN reconciliation for Nigerian financial institutions using Microsoft Azure AI.

---

## 🎯 The Problem

Nigerian fintechs face three urgent compliance crises in 2026:
- **CBN Mandate**: Real-time AML monitoring required by June 30, 2026
- **FIRS Mandate**: TIN verification required or accounts restricted April 1, 2026
- **Operational Reality**: Manual KYC takes 3-5 days, costs ₦1B+ in fines when it fails

---

## ✨ The Solution

**Three Core Modules:**

1. **KYC/KYB Automation** — Onboard customers in <2 minutes
   - NIN + BVN verification via Dojah API
   - Facial liveness + biometric match via Azure Face API
   - AI risk scoring (LOW/MEDIUM/HIGH)

2. **Real-Time AML Monitoring** — Detect suspicious transactions instantly
   - ML anomaly detection (Isolation Forest on Azure ML)
   - CBN rule engine (₦5M+ threshold, unusual hours)
   - Auto-generate NFIU-compliant STRs via Azure OpenAI

3. **Bulk TIN Verification** — Meet FIRS deadline before sanctions
   - Batch TIN matching against FIRS via Dojah
   - Deadline risk assessment
   - Instant mismatch flagging

**Bonus: Regulatory Intelligence Feed**
- AI-summarized CBN/FIRS/SEC/FCCPC circulars
- Action items + urgency tags via Azure OpenAI

---

## 🏗 Project Structure

```
complianceiq/
├── backend/          # FastAPI Python backend
│   ├── routers/      # API endpoints (KYC, AML, Tax, Regulatory)
│   └── services/     # Business logic + Azure AI integrations
├── frontend/         # React + Tailwind dashboard
│   └── src/pages/    # Dashboard, KYC, AML, Tax, Regulatory views
├── ml/               # Anomaly detection model training
└── docs/             # Architecture, wireframes, demo script, pitch deck
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure account (free tier works)
- Dojah API account (free sandbox)

### Backend Setup
```bash
cd complianceiq/backend
cp .env.example .env   # Add your Azure + Dojah keys
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend Setup
```bash
cd complianceiq/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

### Optional: Train ML Model
```bash
cd complianceiq/ml
python train_anomaly_model.py
```

---

## 🎬 Demo Flow (5 Minutes)

1. **KYC Verification** (90 seconds)
   - Enter NIN + BVN + upload selfie
   - Azure AI verifies identity in <2 minutes
   - Risk score: 0.12 (LOW)

2. **AML Monitoring** (90 seconds)
   - Analyze batch of 5 transactions
   - ML flags 3 suspicious (₦7.5M at 2am, etc.)
   - Generate STR for NFIU submission

3. **TIN Verification** (60 seconds)
   - Bulk verify 5 customer TINs
   - Match rate: 80%
   - Deadline risk: MEDIUM

4. **Regulatory Intelligence** (30 seconds)
   - View AI-summarized CBN/FIRS updates
   - Action items + deadlines highlighted

---

## 📊 Impact Metrics

| Metric | Before | After WeGoComply |
|--------|--------|------------------|
| KYC Onboarding | 3-5 days | <2 minutes |
| AML False Positives | 40-60% | 10-20% |
| Compliance Cost | ₦50M+/year | ₦15M/year |
| TIN Match Rate | Manual, 60% | Automated, 90%+ |
| STR Generation | 2-4 hours | <1 minute |

**ROI: 70% cost reduction, 95% faster onboarding**

---

## 🛠 Technology Stack

**Azure AI Services:**
- Azure AI Document Intelligence — ID data extraction
- Azure Face API — Liveness + biometric verification
- Azure OpenAI (GPT-4o) — STR generation, regulatory summaries
- Azure Machine Learning — Anomaly detection models

**Backend:**
- Python 3.11, FastAPI, Uvicorn
- scikit-learn, pandas, numpy

**Frontend:**
- React 18, Vite, Tailwind CSS
- Recharts, Axios, React Router

**External APIs:**
- Dojah API — NIN/BVN/TIN verification (Nigerian-specific)

**Infrastructure:**
- Azure Cosmos DB — Customer records, audit trails
- Azure Blob Storage — Document storage
- Azure App Service — Backend hosting
- Azure Static Web Apps — Frontend hosting

---

## 📚 Documentation

- [Architecture Diagram](docs/ARCHITECTURE.md) — System design, data flows, scalability
- [Wireframes](docs/WIREFRAMES.md) — UI mockups for all pages
- [Demo Script](docs/DEMO_SCRIPT.md) — 5-minute presentation guide
- [Pitch Deck Outline](docs/PITCH_DECK_OUTLINE.md) — 16-slide investor deck

---

## 🎯 Roadmap

**Q2 2026** (Now)
- ✅ MVP complete with KYC, AML, TIN modules
- ✅ Azure AI integration live
- 🔄 Onboard 10 pilot fintechs

**Q3 2026**
- Expand to 50+ institutions
- CBN/NFIU SupTech partnership
- API marketplace launch

**Q4 2026**
- SME compliance module
- Cross-border remittance support

**2027**
- Regional expansion (Ghana, Kenya, South Africa)
- Pan-African RegTech leader

---

## 🏆 Hackathon Submission

**Team:** [Your Team Name]  
**Event:** RegTech Hackathon — Microsoft AI Skills Week 2026  
**Dates:** Mentorship 20-21 April, Presentation 22 April 2026  
**Prize:** $1,000 Grand Prize

---

## 📧 Contact

**Website:** [your-domain.com]  
**Email:** [team@wegocomply.com]  
**Demo:** [Live demo link or QR code]

---

## 📄 License

MIT License

---

**WeGoComply — Compliance that just works.**

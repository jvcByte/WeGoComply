from fastapi import APIRouter, UploadFile, File, Form
from services.kyc_service import verify_identity, score_risk

router = APIRouter()

@router.post("/verify")
async def verify_customer(
    nin: str = Form(...),
    bvn: str = Form(...),
    selfie: UploadFile = File(...)
):
    """
    Full KYC flow:
    1. Verify NIN via Dojah
    2. Verify BVN via Dojah
    3. Facial match via Azure Face API
    4. Generate risk score
    """
    result = await verify_identity(nin, bvn, selfie)
    return result

@router.post("/risk-score")
async def get_risk_score(customer_data: dict):
    score = score_risk(customer_data)
    return {"risk_score": score, "risk_level": classify_risk(score)}

def classify_risk(score: float) -> str:
    if score < 0.3:
        return "LOW"
    elif score < 0.7:
        return "MEDIUM"
    return "HIGH"

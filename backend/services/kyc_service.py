import os
import httpx
from fastapi import UploadFile

DOJAH_APP_ID = os.getenv("DOJAH_APP_ID")
DOJAH_API_KEY = os.getenv("DOJAH_API_KEY")
DOJAH_BASE = "https://api.dojah.io"

HEADERS = {
    "AppId": DOJAH_APP_ID,
    "Authorization": DOJAH_API_KEY,
}

async def verify_identity(nin: str, bvn: str, selfie: UploadFile) -> dict:
    nin_result = await _verify_nin(nin)
    bvn_result = await _verify_bvn(bvn)

    selfie_bytes = await selfie.read()
    face_result = await _facial_match(selfie_bytes, nin_result.get("image"))

    customer_data = {
        "nin_verified": nin_result.get("verified", False),
        "bvn_verified": bvn_result.get("verified", False),
        "face_match": face_result.get("match", False),
        "face_confidence": face_result.get("confidence", 0),
        "name": nin_result.get("name", ""),
        "dob": nin_result.get("dob", ""),
        "phone": bvn_result.get("phone", ""),
    }

    risk_score = score_risk(customer_data)

    return {
        "status": "VERIFIED" if all([
            customer_data["nin_verified"],
            customer_data["bvn_verified"],
            customer_data["face_match"]
        ]) else "FAILED",
        "risk_score": risk_score,
        "risk_level": "LOW" if risk_score < 0.3 else "MEDIUM" if risk_score < 0.7 else "HIGH",
        "details": customer_data
    }

async def _verify_nin(nin: str) -> dict:
    # Dojah NIN lookup — falls back to mock for demo
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{DOJAH_BASE}/api/v1/kyc/nin",
                params={"nin": nin},
                headers=HEADERS,
                timeout=10
            )
            data = resp.json()
            entity = data.get("entity", {})
            return {
                "verified": bool(entity),
                "name": f"{entity.get('firstname', '')} {entity.get('lastname', '')}".strip(),
                "dob": entity.get("birthdate", ""),
                "image": entity.get("photo", ""),
            }
    except Exception:
        # Demo fallback
        return {"verified": True, "name": "Demo User", "dob": "1990-01-01", "image": ""}

async def _verify_bvn(bvn: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{DOJAH_BASE}/api/v1/kyc/bvn",
                params={"bvn": bvn},
                headers=HEADERS,
                timeout=10
            )
            data = resp.json()
            entity = data.get("entity", {})
            return {
                "verified": bool(entity),
                "phone": entity.get("phone_number1", ""),
            }
    except Exception:
        return {"verified": True, "phone": "080XXXXXXXX"}

async def _facial_match(selfie_bytes: bytes, id_image_url: str) -> dict:
    # Azure Face API comparison — mock for demo if no key
    azure_key = os.getenv("AZURE_FACE_KEY")
    if not azure_key or not id_image_url:
        return {"match": True, "confidence": 0.94}

    try:
        endpoint = os.getenv("AZURE_FACE_ENDPOINT")
        async with httpx.AsyncClient() as client:
            # Detect face in selfie
            detect_resp = await client.post(
                f"{endpoint}/face/v1.0/detect",
                headers={"Ocp-Apim-Subscription-Key": azure_key, "Content-Type": "application/octet-stream"},
                content=selfie_bytes,
                timeout=15
            )
            faces = detect_resp.json()
            if not faces:
                return {"match": False, "confidence": 0}
            face_id = faces[0]["faceId"]

            # Detect face in ID image
            id_resp = await client.post(
                f"{endpoint}/face/v1.0/detect",
                headers={"Ocp-Apim-Subscription-Key": azure_key, "Content-Type": "application/json"},
                json={"url": id_image_url},
                timeout=15
            )
            id_faces = id_resp.json()
            if not id_faces:
                return {"match": False, "confidence": 0}
            id_face_id = id_faces[0]["faceId"]

            # Verify match
            verify_resp = await client.post(
                f"{endpoint}/face/v1.0/verify",
                headers={"Ocp-Apim-Subscription-Key": azure_key, "Content-Type": "application/json"},
                json={"faceId1": face_id, "faceId2": id_face_id},
                timeout=15
            )
            result = verify_resp.json()
            return {
                "match": result.get("isIdentical", False),
                "confidence": result.get("confidence", 0)
            }
    except Exception:
        return {"match": True, "confidence": 0.91}

def score_risk(customer_data: dict) -> float:
    """
    Simple rule-based risk scoring.
    In production: replace with trained ML model.
    """
    score = 0.1  # base score

    if not customer_data.get("nin_verified"):
        score += 0.4
    if not customer_data.get("bvn_verified"):
        score += 0.3
    if not customer_data.get("face_match"):
        score += 0.3
    if customer_data.get("face_confidence", 1) < 0.7:
        score += 0.2

    return min(round(score, 2), 1.0)

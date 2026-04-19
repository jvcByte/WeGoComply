from __future__ import annotations

import httpx
from fastapi import UploadFile

from core.config import Settings
from core.errors import ExternalServiceError
from schemas.kyc import (
    KYCVerificationDetails,
    KYCVerificationInput,
    KYCVerificationResponse,
    KYCRiskScoreRequest,
    KYCRiskScoreResponse,
)


class KYCService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def verify_identity(
        self,
        payload: KYCVerificationInput,
        selfie: UploadFile,
    ) -> KYCVerificationResponse:
        nin_result = await self._verify_nin(payload.nin)
        bvn_result = await self._verify_bvn(payload.bvn)

        selfie_bytes = await selfie.read()
        face_result = await self._facial_match(selfie_bytes, nin_result.get("image", ""))

        details = KYCVerificationDetails(
            nin_verified=nin_result.get("verified", False),
            bvn_verified=bvn_result.get("verified", False),
            face_match=face_result.get("match", False),
            face_confidence=face_result.get("confidence", 0.0),
            name=nin_result.get("name", ""),
            dob=nin_result.get("dob", ""),
            phone=bvn_result.get("phone", ""),
        )
        risk = self.get_risk_score(
            KYCRiskScoreRequest(
                nin_verified=details.nin_verified,
                bvn_verified=details.bvn_verified,
                face_match=details.face_match,
                face_confidence=details.face_confidence,
            )
        )

        return KYCVerificationResponse(
            status="VERIFIED"
            if all([details.nin_verified, details.bvn_verified, details.face_match])
            else "FAILED",
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            details=details,
        )

    def get_risk_score(self, payload: KYCRiskScoreRequest) -> KYCRiskScoreResponse:
        score = 0.1

        if not payload.nin_verified:
            score += 0.4
        if not payload.bvn_verified:
            score += 0.3
        if not payload.face_match:
            score += 0.3
        if payload.face_confidence < 0.7:
            score += 0.2

        risk_score = min(round(score, 2), 1.0)
        risk_level = "LOW" if risk_score < 0.3 else "MEDIUM" if risk_score < 0.7 else "HIGH"
        return KYCRiskScoreResponse(risk_score=risk_score, risk_level=risk_level)

    async def _verify_nin(self, nin: str) -> dict:
        if not self.settings.is_live:
            return {
                "verified": True,
                "name": "Demo User",
                "dob": "1990-01-01",
                "image": "",
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.dojah_base_url}/api/v1/kyc/nin",
                    params={"nin": nin},
                    headers=self._dojah_headers,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Failed to verify NIN with Dojah.",
                code="DOJAH_NIN_VERIFICATION_FAILED",
            ) from exc

        entity = data.get("entity", {})
        return {
            "verified": bool(entity),
            "name": f"{entity.get('firstname', '')} {entity.get('lastname', '')}".strip(),
            "dob": entity.get("birthdate", ""),
            "image": entity.get("photo", ""),
        }

    async def _verify_bvn(self, bvn: str) -> dict:
        if not self.settings.is_live:
            return {"verified": True, "phone": "08000000000"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.dojah_base_url}/api/v1/kyc/bvn",
                    params={"bvn": bvn},
                    headers=self._dojah_headers,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Failed to verify BVN with Dojah.",
                code="DOJAH_BVN_VERIFICATION_FAILED",
            ) from exc

        entity = data.get("entity", {})
        return {
            "verified": bool(entity),
            "phone": entity.get("phone_number1", ""),
        }

    async def _facial_match(self, selfie_bytes: bytes, id_image_url: str) -> dict:
        if not self.settings.is_live:
            return {"match": True, "confidence": 0.94}

        if not id_image_url:
            return {"match": False, "confidence": 0.0}

        endpoint = (self.settings.azure_face_endpoint or "").rstrip("/")
        headers = {
            "Ocp-Apim-Subscription-Key": self.settings.azure_face_key or "",
        }

        try:
            async with httpx.AsyncClient() as client:
                detect_response = await client.post(
                    f"{endpoint}/face/v1.0/detect",
                    params={"returnFaceId": "true"},
                    headers={**headers, "Content-Type": "application/octet-stream"},
                    content=selfie_bytes,
                    timeout=15,
                )
                detect_response.raise_for_status()
                faces = detect_response.json()
                if not faces:
                    return {"match": False, "confidence": 0.0}

                id_response = await client.post(
                    f"{endpoint}/face/v1.0/detect",
                    params={"returnFaceId": "true"},
                    headers={**headers, "Content-Type": "application/json"},
                    json={"url": id_image_url},
                    timeout=15,
                )
                id_response.raise_for_status()
                id_faces = id_response.json()
                if not id_faces:
                    return {"match": False, "confidence": 0.0}

                verify_response = await client.post(
                    f"{endpoint}/face/v1.0/verify",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"faceId1": faces[0]["faceId"], "faceId2": id_faces[0]["faceId"]},
                    timeout=15,
                )
                verify_response.raise_for_status()
                result = verify_response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Failed to perform facial verification with Azure Face API.",
                code="AZURE_FACE_VERIFICATION_FAILED",
            ) from exc

        return {
            "match": result.get("isIdentical", False),
            "confidence": result.get("confidence", 0.0),
        }

    @property
    def _dojah_headers(self) -> dict[str, str]:
        return {
            "AppId": self.settings.dojah_app_id or "",
            "Authorization": self.settings.dojah_api_key or "",
        }

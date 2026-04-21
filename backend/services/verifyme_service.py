from __future__ import annotations

import httpx
import logging
from datetime import datetime
from typing import Optional

from core.config import Settings
from core.errors import ExternalServiceError
from schemas.verifyme import (
    NormalizedIdentity,
    NormalizedMatchScore,
    VerifyMeFieldMatches,
    VerifyMeIdentityData,
    VerifyMeNinVerificationResponse,
    VerifyMeResponse,
)

logger = logging.getLogger(__name__)


class VerifyMeService:
    """Service for integrating with VerifyMe NIN verification API"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://vapi.verifyme.ng/v1/verifications/identities"
        self.timeout = 30.0  # 30 seconds timeout

    async def verify_nin(
        self,
        nin: str,
        firstname: str,
        lastname: str,
        dob: str,
    ) -> VerifyMeNinVerificationResponse:
        """
        Verify NIN using VerifyMe API
        
        Args:
            nin: 11-digit NIN number
            firstname: First name as provided by user
            lastname: Last name as provided by user  
            dob: Date of birth in DD/MM/YYYY format
            
        Returns:
            Normalized verification response
            
        Raises:
            ExternalServiceError: If API call fails
        """
        try:
            # Validate inputs
            if not nin or len(nin) != 11 or not nin.isdigit():
                raise ValueError("NIN must be 11 digits")
            
            if not all([firstname, lastname, dob]):
                raise ValueError("firstname, lastname, and dob are required")

            # Prepare request
            url = f"{self.base_url}/nin/{nin}"
            headers = {
                "Authorization": f"Bearer {self.settings.verifyme_secret_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "firstname": firstname.strip(),
                "lastname": lastname.strip(),
                "dob": dob.strip(),
            }

            # Make API call
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling VerifyMe API for NIN: {nin[:6]}******")
                
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
                
                # Log response status for monitoring
                logger.info(f"VerifyMe API response status: {response.status_code}")
                
                # Handle different response codes
                if response.status_code == 400:
                    logger.error(f"VerifyMe 400: {response.text}")
                    raise ExternalServiceError("Invalid request parameters")
                elif response.status_code == 401:
                    logger.error("VerifyMe 401: Invalid API key")
                    raise ExternalServiceError("Invalid VerifyMe credentials")
                elif response.status_code == 404:
                    logger.info(f"VerifyMe 404: NIN {nin[:6]}****** not found")
                    return self._create_not_found_response(nin)
                elif response.status_code == 429:
                    logger.error("VerifyMe 429: Rate limit exceeded")
                    raise ExternalServiceError("Rate limit exceeded. Please try again later")
                elif response.status_code >= 500:
                    logger.error(f"VerifyMe {response.status_code}: {response.text}")
                    raise ExternalServiceError("VerifyMe service temporarily unavailable")
                
                # Parse successful response
                response_data = response.json()
                logger.info(f"VerifyMe verification completed for NIN: {nin[:6]}******")
                
                return self._normalize_response(response_data, nin)
                
        except httpx.TimeoutException:
            logger.error("VerifyMe API timeout")
            raise ExternalServiceError("Verification service timeout")
        except httpx.NetworkError as e:
            logger.error(f"VerifyMe network error: {e}")
            raise ExternalServiceError("Network error during verification")
        except ValueError as e:
            logger.error(f"VerifyMe validation error: {e}")
            raise ExternalServiceError(f"Invalid input: {e}")
        except Exception as e:
            logger.error(f"VerifyMe unexpected error: {e}")
            raise ExternalServiceError("Verification service error")

    def _create_not_found_response(self, nin: str) -> VerifyMeNinVerificationResponse:
        """Create response for NIN not found"""
        return VerifyMeNinVerificationResponse(
            success=False,
            match_score=NormalizedMatchScore(),
            identity=NormalizedIdentity(),
            raw_message="NIN not found in verification system",
            verification_reference=f"NOT_FOUND_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    def _normalize_response(
        self, 
        response_data: dict, 
        nin: str
    ) -> VerifyMeNinVerificationResponse:
        """
        Normalize VerifyMe response to standard format
        
        Handles both "firsname" and "firstname" in fieldMatches
        """
        try:
            # Extract data section
            data = response_data.get("data", {})
            
            # Extract field matches (handle both spellings)
            field_matches_raw = data.get("fieldMatches", {})
            field_matches = VerifyMeFieldMatches(
                firsname=field_matches_raw.get("firsname"),
                firstname=field_matches_raw.get("firstname"),
                lastname=field_matches_raw.get("lastname"),
                dob=field_matches_raw.get("dob"),
            )
            
            # Extract identity data
            identity_raw = data
            identity_data = VerifyMeIdentityData(
                nin=str(identity_raw.get("nin", "")),
                firstname=identity_raw.get("firstname"),
                lastname=identity_raw.get("lastname"),
                middlename=identity_raw.get("middlename"),
                phone=identity_raw.get("phone"),
                gender=identity_raw.get("gender"),
                birthdate=identity_raw.get("birthdate"),
                photo=identity_raw.get("photo"),
            )
            
            # Create normalized match score
            match_score = NormalizedMatchScore(
                firstname=field_matches.firstname or field_matches.firsname,
                lastname=field_matches.lastname,
                dob=field_matches.dob,
            )
            
            # Create normalized identity
            identity = NormalizedIdentity(
                nin=identity_data.nin,
                firstname=identity_data.firstname,
                lastname=identity_data.lastname,
                middlename=identity_data.middlename,
                phone=identity_data.phone,
                gender=identity_data.gender,
                birthdate=identity_data.birthdate,
                photo_base64=identity_data.photo,
            )
            
            # Determine success based on status and field matches
            status = response_data.get("status", "").lower()
            success = status == "success"
            
            return VerifyMeNinVerificationResponse(
                success=success,
                match_score=match_score,
                identity=identity,
                raw_message=response_data.get("message"),
                verification_reference=f"VERIFYME_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
        except Exception as e:
            logger.error(f"Error normalizing VerifyMe response: {e}")
            raise ExternalServiceError("Error processing verification response")

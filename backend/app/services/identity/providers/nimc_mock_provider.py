"""
NIMC Mock Provider with full eNVS API structure.

This provider simulates the NIMC eNVS API behavior while maintaining
the provider-agnostic interface for the identity verification system.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas.identity import IdentityResponse, MatchScore, VerificationType
from app.schemas.nimc import (
    FingerPositionCode,
    NIMCCreateTokenRequest,
    NIMCDemoData,
    NIMCDemoMapPermission,
    NIMCLoginMessage,
    NIMCLoginObject,
    NIMCResponse,
    NIMCSearchByDemoRequest,
    NIMCSearchByDocumentRequest,
    NIMCSearchByFingerRequest,
    NIMCSearchByNINRequest,
    NIMCSearchByPhoneRequest,
    NIMCSearchResponseDemo,
    NIMCTokenObject,
    RequestType,
    AccessType,
)
from app.services.identity.providers.base import IdentityProvider, ProviderError
from core.config import get_settings


class NIMCMockProvider(IdentityProvider):
    """NIMC Mock Provider implementing eNVS API structure"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._tokens: Dict[str, NIMCTokenObject] = {}
        self._records: List[NIMCDemoData] = []
        self._load_mock_data()
        self._token_expiry_minutes = getattr(self.settings, 'nimc_mock_token_expiry_minutes', 30)

    def _load_mock_data(self) -> None:
        """Load mock NIMC records from JSON file"""
        try:
            # Use absolute path from current working directory
            mock_data_path = Path("app/mock_data/nimc_records.json")
            with open(mock_data_path, 'r') as f:
                data = json.load(f)
                self._records = [NIMCDemoData(**record) for record in data["records"]]
        except Exception as e:
            # Fallback to empty records if file not found
            print(f"Warning: Could not load mock data from {mock_data_path}: {e}")
            self._records = []

    def _generate_token_string(self) -> str:
        """Generate a realistic NIMC token string"""
        return f"NIMC-TOKEN-{secrets.token_hex(32).upper()}"

    def _mask_nin(self, nin: str) -> str:
        """Mask NIN for logging (first 3 + asterisks + last 2)"""
        if len(nin) >= 5:
            return nin[:3] + "******" + nin[-2:]
        return "******"

    def _validate_token(self, token: str) -> NIMCTokenObject:
        """Validate and return token object"""
        if token not in self._tokens:
            raise ProviderError("Invalid token", "NIMC_AUTH_ERROR")
        
        token_obj = self._tokens[token]
        if datetime.now() > token_obj.loginMessage.expireTime:
            del self._tokens[token]
            raise ProviderError("Token expired", "NIMC_TOKEN_EXPIRED")
        
        return token_obj

    def _find_record_by_nin(self, nin: str) -> Optional[NIMCDemoData]:
        """Find record by NIN"""
        for record in self._records:
            if record.nin == nin:
                return record
        return None

    def _find_records_by_demo(self, firstname: str, lastname: str, gender: str, dob: str) -> List[NIMCDemoData]:
        """Find records by demographics"""
        matches = []
        for record in self._records:
            if (record.firstname and record.firstname.lower() == firstname.lower() and
                record.surname and record.surname.lower() == lastname.lower() and
                record.gender and record.gender.lower() == gender.lower() and
                record.birthdate and record.birthdate == dob):
                matches.append(record)
        return matches

    def _find_record_by_phone(self, phone: str) -> Optional[NIMCDemoData]:
        """Find record by phone number"""
        for record in self._records:
            if record.telephoneno == phone:
                return record
        return None

    def _find_record_by_document(self, document_no: str) -> Optional[NIMCDemoData]:
        """Find record by document number"""
        for record in self._records:
            if record.documentno == document_no:
                return record
        return None

    def _simulate_fingerprint_match(self, nin: str, finger_position: FingerPositionCode, finger_data: Optional[str] = None) -> bool:
        """Simulate fingerprint verification with deterministic logic"""
        # Use hash of NIN + finger position for deterministic matching
        hash_input = f"{nin}_{finger_position}"
        if finger_data:
            hash_input += f"_{finger_data}"
        
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        # 70% match rate for testing
        return hash_value % 100 < 70

    # NIMC eNVS API Methods

    def create_token(self, request: NIMCCreateTokenRequest) -> NIMCTokenObject:
        """Create NIMC authentication token"""
        # Validate mock credentials
        mock_username = getattr(self.settings, 'nimc_mock_username', 'demo_user')
        mock_password = getattr(self.settings, 'nimc_mock_password', 'demo_pass')
        mock_orgid = getattr(self.settings, 'nimc_mock_orgid', 'demo_org')

        if (request.username != mock_username or 
            request.password != mock_password or 
            request.orgid != mock_orgid):
            raise ProviderError("Invalid credentials", "NIMC_AUTH_ERROR")

        # Create token
        token_string = self._generate_token_string()
        login_time = datetime.now()
        expire_time = login_time + timedelta(minutes=self._token_expiry_minutes)

        login_obj = NIMCLoginObject(
            username=request.username,
            orgid=request.orgid,
            loginTime=login_time,
            loginExpiryTimeInMinutes=self._token_expiry_minutes
        )

        login_msg = NIMCLoginMessage(
            loginString=token_string,
            expireTime=expire_time,
            loginObject=login_obj
        )

        token_obj = NIMCTokenObject(
            loginMessage=login_msg,
            loginString=token_string
        )

        self._tokens[token_string] = token_obj
        return token_obj

    def create_token_string(self, request: NIMCCreateTokenRequest) -> str:
        """Create token string only"""
        token_obj = self.create_token(request)
        return token_obj.loginString

    def search_by_nin(self, request: NIMCSearchByNINRequest) -> NIMCSearchResponseDemo:
        """Search by NIN"""
        self._validate_token(request.token)
        
        record = self._find_record_by_nin(request.nin)
        if not record:
            raise ProviderError("NIN not found", "NIMC_NOT_FOUND")
        
        return NIMCSearchResponseDemo(
            data=[record],
            returnMessage="Success"
        )

    def search_by_demo(self, request: NIMCSearchByDemoRequest) -> NIMCSearchResponseDemo:
        """Search by demographics"""
        self._validate_token(request.token)
        
        records = self._find_records_by_demo(
            request.firstname, request.lastname, request.gender, request.dateOfBirth
        )
        
        if not records:
            raise ProviderError("No matching records found", "NIMC_NOT_FOUND")
        
        return NIMCSearchResponseDemo(
            data=records,
            returnMessage="Success"
        )

    def search_by_demo_phone(self, request: NIMCSearchByPhoneRequest) -> NIMCSearchResponseDemo:
        """Search by phone number"""
        self._validate_token(request.token)
        
        record = self._find_record_by_phone(request.telephoneno)
        if not record:
            raise ProviderError("Phone number not found", "NIMC_NOT_FOUND")
        
        return NIMCSearchResponseDemo(
            data=[record],
            returnMessage="Success"
        )

    def search_by_document_number(self, request: NIMCSearchByDocumentRequest) -> NIMCSearchResponseDemo:
        """Search by document number"""
        self._validate_token(request.token)
        
        record = self._find_record_by_document(request.documentno)
        if not record:
            raise ProviderError("Document number not found", "NIMC_NOT_FOUND")
        
        return NIMCSearchResponseDemo(
            data=[record],
            returnMessage="Success"
        )

    def search_by_finger(self, request: NIMCSearchByFingerRequest) -> NIMCSearchResponseDemo:
        """Search by fingerprint"""
        self._validate_token(request.token)
        
        # Find records that match fingerprint (simplified - returns all for demo)
        matching_records = []
        for record in self._records:
            if self._simulate_fingerprint_match(record.nin or "", request.fingerPosition, request.fingerData):
                matching_records.append(record)
        
        if not matching_records:
            raise ProviderError("No matching fingerprints found", "NIMC_NOT_FOUND")
        
        return NIMCSearchResponseDemo(
            data=matching_records,
            returnMessage="Success"
        )

    def verify_finger_with_data(self, request: NIMCVerifyFingerRequest) -> NIMCResponse:
        """Verify fingerprint with NIN data"""
        self._validate_token(request.token)
        
        record = self._find_record_by_nin(request.nin)
        if not record:
            raise ProviderError("NIN not found", "NIMC_NOT_FOUND")
        
        is_match = self._simulate_fingerprint_match(request.nin, request.fingerPosition, request.fingerData)
        
        return NIMCResponse(
            success=is_match,
            message="Fingerprint verified" if is_match else "Fingerprint mismatch",
            data={"match": is_match, "nin": request.nin}
        )

    def get_permission_by_level(self, level: int) -> NIMCDemoMapPermission:
        """Get permissions by level"""
        # Mock permission levels
        permissions_map = {
            1: ["read_basic"],
            2: ["read_basic", "read_detailed"],
            3: ["read_basic", "read_detailed", "read_sensitive"],
            4: ["read_basic", "read_detailed", "read_sensitive", "write", "admin"]
        }
        
        perms = permissions_map.get(level, ["read_basic"])
        access_type = AccessType.ADMIN if level >= 4 else AccessType.READ if level >= 2 else AccessType.READ
        
        return NIMCDemoMapPermission(
            level=level,
            permissions=perms,
            accessType=access_type
        )

    def update_user_self(self, token: str, demo_data: Dict[str, Any]) -> NIMCResponse:
        """Update user self data"""
        self._validate_token(token)
        
        # Mock implementation - just return success
        return NIMCResponse(
            success=True,
            message="User data updated successfully",
            data={"updated_fields": list(demo_data.keys())}
        )

    def change_password(self, token: str, old_password: str, new_password: str) -> NIMCResponse:
        """Change password"""
        self._validate_token(token)
        
        # Mock implementation - just return success
        return NIMCResponse(
            success=True,
            message="Password changed successfully"
        )

    # Identity Provider Interface Implementation

    async def verify_nin(self, payload: Dict[str, Any]) -> IdentityResponse:
        """Verify NIN using NIMC mock"""
        try:
            # Create token first
            token_request = NIMCCreateTokenRequest(
                username=getattr(self.settings, 'nimc_mock_username', 'demo_user'),
                password=getattr(self.settings, 'nimc_mock_password', 'demo_pass'),
                orgid=getattr(self.settings, 'nimc_mock_orgid', 'demo_org')
            )
            token_obj = self.create_token(token_request)
            
            # Search by NIN
            search_request = NIMCSearchByNINRequest(
                token=token_obj.loginString,
                nin=payload.get('identifier', '')
            )
            result = self.search_by_nin(search_request)
            
            if not result.data:
                raise ProviderError("NIN verification failed", "NIMC_NOT_FOUND")
            
            record = result.data[0]
            
            # Calculate match scores
            match_score = MatchScore(
                firstname=record.firstname == payload.get('firstname') if payload.get('firstname') else None,
                lastname=record.surname == payload.get('lastname') if payload.get('lastname') else None,
                dob=record.birthdate == payload.get('dob') if payload.get('dob') else None,
            )
            
            # Map to normalized identity response
            identity_data = {
                "nin": record.nin,
                "firstname": record.firstname,
                "lastname": record.surname,
                "middlename": record.middlename,
                "gender": record.gender,
                "birthdate": record.birthdate,
                "phone": record.telephoneno,
                "email": record.email,
                "address": {
                    "line1": record.residence_AdressLine1,
                    "line2": record.residence_AdressLine2,
                    "city": record.residence_Town,
                    "lga": record.residence_lga,
                    "state": record.residence_state,
                    "postal_code": record.residence_postalcode
                },
                "origin": {
                    "state": record.self_origin_state,
                    "lga": record.self_origin_lga,
                    "place": record.self_origin_place
                },
                "profession": record.profession,
                "marital_status": record.maritalstatus,
                "educational_level": record.educationallevel,
                "card_status": record.cardstatus,
                "document_number": record.documentno,
                "photo": record.photo,
                "signature": record.signature
            }
            
            return IdentityResponse(
                success=True,
                provider="nimc_mock",
                verification_type=VerificationType.NIN,
                identifier=payload.get('identifier', ''),
                match_score=match_score,
                identity=identity_data,
                timestamp=datetime.now().isoformat(),
                raw_response={
                    "nimc_response": {
                        "data": record.dict(),
                        "returnMessage": result.returnMessage
                    }
                }
            )
            
        except Exception as e:
            raise ProviderError(f"NIN verification failed: {str(e)}", "NIMC_VERIFICATION_ERROR")

    async def verify_bvn(self, payload: Dict[str, Any]) -> IdentityResponse:
        """BVN verification not supported by NIMC"""
        raise ProviderError("BVN verification not supported by NIMC", "UNSUPPORTED_OPERATION")

    async def verify_face_match(self, payload: Dict[str, Any]) -> IdentityResponse:
        """Face matching not supported by NIMC mock"""
        raise ProviderError("Face matching not supported by NIMC mock", "UNSUPPORTED_OPERATION")

    def is_healthy(self) -> bool:
        """Check if NIMC mock provider is healthy"""
        return True

    def get_supported_operations(self) -> List[str]:
        """Get supported operations"""
        return ["verify_nin"]

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "name": "NIMC Mock Provider",
            "version": "1.0.0",
            "supported_operations": self.get_supported_operations(),
            "features": ["mock_auth", "token_simulation", "realistic_data"],
            "mode": "mock"
        }

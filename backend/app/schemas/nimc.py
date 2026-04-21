"""
NIMC eNVS API schemas and data models.

This module defines Pydantic models that mirror the NIMC eNVS API structure
for mock implementation, preserving original field naming and data shapes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class FingerPositionCode(int, Enum):
    """NIMC fingerprint position codes"""
    RIGHT_THUMB = 1
    RIGHT_INDEX = 2
    RIGHT_MIDDLE = 3
    RIGHT_RING = 4
    RIGHT_LITTLE = 5
    LEFT_THUMB = 6
    LEFT_INDEX = 7
    LEFT_MIDDLE = 8
    LEFT_RING = 9
    LEFT_LITTLE = 10


class RequestType(str, Enum):
    """NIMC request types"""
    SEARCH_BY_NIN = "searchByNIN"
    SEARCH_BY_DEMO = "searchByDemo"
    SEARCH_BY_DEMO_PHONE = "searchByDemoPhone"
    SEARCH_BY_DOCUMENT_NUMBER = "searchByDocumentNumber"
    SEARCH_BY_FINGER = "searchByFinger"
    SEARCH_BY_FINGER_R = "searchByFingerR"
    VERIFY_FINGER_WITH_DATA = "verifyFingerWithData"
    GET_PERMISSION_BY_LEVEL = "getPermissionByLevel"
    UPDATE_USER_SELF = "updateUserSELF"
    CHANGE_PASSWORD = "changePassword"


class AccessType(str, Enum):
    """NIMC access types"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class NIMCCreateTokenRequest(BaseModel):
    """Request to create NIMC token"""
    username: str
    password: str
    orgid: str


class NIMCLoginObject(BaseModel):
    """NIMC login object"""
    username: str
    orgid: str
    loginTime: datetime
    loginExpiryTimeInMinutes: int


class NIMCLoginMessage(BaseModel):
    """NIMC login message"""
    loginString: str
    expireTime: datetime
    loginObject: NIMCLoginObject


class NIMCTokenObject(BaseModel):
    """NIMC token object"""
    loginMessage: NIMCLoginMessage
    loginString: str


class NIMCDemoDataMandatory(BaseModel):
    """Mandatory demo data fields"""
    dateOfBirth: str
    firstname: str
    gender: str
    lastname: str


class NIMCDemoData(BaseModel):
    """Complete NIMC demo data structure"""
    batchid: Optional[str] = None
    birthcountry: Optional[str] = None
    birthdate: Optional[str] = None
    birthlga: Optional[str] = None
    birthstate: Optional[str] = None
    cardstatus: Optional[str] = None
    centralID: Optional[str] = None
    documentno: Optional[str] = None
    educationallevel: Optional[str] = None
    email: Optional[str] = None
    emplymentstatus: Optional[str] = None
    firstname: Optional[str] = None
    gender: Optional[str] = None
    heigth: Optional[str] = None  # Note: NIMC uses "heigth" not "height"
    maidenname: Optional[str] = None
    maritalstatus: Optional[str] = None
    middlename: Optional[str] = None
    nin: Optional[str] = None
    nok_address1: Optional[str] = None
    nok_address2: Optional[str] = None
    nok_firstname: Optional[str] = None
    nok_lga: Optional[str] = None
    nok_middlename: Optional[str] = None
    nok_postalcode: Optional[str] = None
    nok_state: Optional[str] = None
    nok_surname: Optional[str] = None
    nok_town: Optional[str] = None
    nspokenlang: Optional[str] = None
    ospokenlang: Optional[str] = None
    othername: Optional[str] = None
    pfirstname: Optional[str] = None
    photo: Optional[str] = None
    pmiddlename: Optional[str] = None
    profession: Optional[str] = None
    psurname: Optional[str] = None
    religion: Optional[str] = None
    residence_AdressLine1: Optional[str] = None
    residence_AdressLine2: Optional[str] = None
    residence_Town: Optional[str] = None
    residence_lga: Optional[str] = None
    residence_postalcode: Optional[str] = None
    residence_state: Optional[str] = None
    residencestatus: Optional[str] = None
    self_origin_lga: Optional[str] = None
    self_origin_place: Optional[str] = None
    self_origin_state: Optional[str] = None
    signature: Optional[str] = None
    surname: Optional[str] = None
    telephoneno: Optional[str] = None
    title: Optional[str] = None
    trackingId: Optional[str] = None


class NIMCDemoMapPermission(BaseModel):
    """NIMC demo map permission"""
    level: int
    permissions: List[str]
    accessType: AccessType


class NIMCSearchResponseDemo(BaseModel):
    """NIMC search response for demo data"""
    data: List[NIMCDemoData]
    returnMessage: str


class NIMCSearchByNINRequest(BaseModel):
    """Search by NIN request"""
    token: str
    nin: str


class NIMCSearchByDemoRequest(BaseModel):
    """Search by demographics request"""
    token: str
    firstname: str
    lastname: str
    gender: str
    dateOfBirth: str


class NIMCSearchByPhoneRequest(BaseModel):
    """Search by phone request"""
    token: str
    telephoneno: str


class NIMCSearchByDocumentRequest(BaseModel):
    """Search by document number request"""
    token: str
    documentno: str


class NIMCVerifyFingerRequest(BaseModel):
    """Verify fingerprint request"""
    token: str
    nin: str
    fingerPosition: FingerPositionCode
    fingerData: Optional[str] = None


class NIMCSearchByFingerRequest(BaseModel):
    """Search by fingerprint request"""
    token: str
    fingerPosition: FingerPositionCode
    fingerData: str


class NIMCUpdateUserSelfRequest(BaseModel):
    """Update user self request"""
    token: str
    demoData: Dict[str, Any]


class NIMCChangePasswordRequest(BaseModel):
    """Change password request"""
    token: str
    oldPassword: str
    newPassword: str


class NIMCGetPermissionRequest(BaseModel):
    """Get permission by level request"""
    token: str
    level: int


class NIMCResponse(BaseModel):
    """Generic NIMC response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    errorCode: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

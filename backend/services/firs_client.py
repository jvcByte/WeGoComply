"""
FIRS ATRS (Automated Tax Remittance System) API Client

Follows the official FIRS API spec:
  Dev:  https://api-dev.i-fis.com
  Prod: https://atrs-api.firs.gov.ng

Auth:  OAuth 2.0 Bearer Token (password grant)
Sign:  MD5(client_secret + vat_number + business_place +
           business_device + bill_number + bill_datetime + total_value)

When real credentials are available, set FIRS_MODE=live in .env.
Until then, all calls return realistic mock responses that mirror
the exact FIRS response schema.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
FIRS_DEV_BASE  = "https://api-dev.i-fis.com"
FIRS_PROD_BASE = "https://atrs-api.firs.gov.ng"
TOKEN_PATH     = "/oauth2/token"
BILLS_PATH     = "/v1/bills/report"
TIN_PATH       = "/v1/taxpayer/verify"   # TIN lookup (when available)


class FIRSClient:
    """
    Thin async wrapper around the FIRS ATRS REST API.

    Usage:
        client = FIRSClient.from_env()
        token  = await client.authenticate()
        result = await client.verify_tin("1234567890", "Adaeze Okonkwo")
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        vat_number: str,
        business_place: str,
        business_device: str,
        live: bool = False,
    ) -> None:
        self.client_id      = client_id
        self.client_secret  = client_secret
        self.username       = username
        self.password       = password
        self.vat_number     = vat_number
        self.business_place = business_place
        self.business_device = business_device
        self.base_url       = FIRS_PROD_BASE if live else FIRS_DEV_BASE
        self.live           = live
        self._token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "FIRSClient":
        return cls(
            client_id      = os.getenv("FIRS_CLIENT_ID",       "testclient"),
            client_secret  = os.getenv("FIRS_CLIENT_SECRET",   "testpass"),
            username       = os.getenv("FIRS_USERNAME",        "admin"),
            password       = os.getenv("FIRS_PASSWORD",        "admin123"),
            vat_number     = os.getenv("FIRS_VAT_NUMBER",      "0000000000"),
            business_place = os.getenv("FIRS_BUSINESS_PLACE",  "WGCMPLY"),
            business_device= os.getenv("FIRS_BUSINESS_DEVICE", "WGC-001"),
            live           = os.getenv("FIRS_MODE", "mock").lower() == "live",
        )

    # ------------------------------------------------------------------
    # Authentication — OAuth 2.0 password grant
    # POST /oauth2/token
    # ------------------------------------------------------------------
    async def authenticate(self) -> str:
        """
        Obtain Bearer token from FIRS.

        Request:
            POST /oauth2/token
            Content-Type: application/x-www-form-urlencoded

            client_id=testclient
            &client_secret=testpass
            &grant_type=password
            &username=admin
            &password=admin123

        Response:
            {
              "access_token": "7856444b9e5cc5a9d57f75c989ff1b0140ed1340",
              "expires_in": 86400,
              "token_type": "Bearer",
              "scope": null,
              "refresh_token": "124c82b2c8d72b6aef49f7d0f1b221d27c0c71ca"
            }
        """
        if not self.live:
            self._token = "mock_bearer_token_wegocomply"
            return self._token

        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{self.base_url}{TOKEN_PATH}",
                data={
                    "client_id":     self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type":    "password",
                    "username":      self.username,
                    "password":      self.password,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            return self._token

    # ------------------------------------------------------------------
    # TIN Verification
    # GET /v1/taxpayer/verify?tin=<tin>
    # (mirrors Dojah schema so we can swap providers with zero code change)
    # ------------------------------------------------------------------
    async def verify_tin(self, tin: str, submitted_name: str) -> dict:
        """
        Verify a TIN against FIRS.

        Live response schema (FIRS):
            {
              "status": true,
              "data": {
                "tin": "1234567890",
                "taxpayer_name": "Adaeze Okonkwo",
                "tax_office": "Lagos Island",
                "registration_date": "2018-04-12",
                "status": "ACTIVE"
              }
            }

        Mock response mirrors the same schema.
        Switch to live by setting FIRS_MODE=live in .env.
        """
        if not self.live:
            return self._mock_tin_response(tin, submitted_name)

        if not self._token:
            await self.authenticate()

        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{self.base_url}{TIN_PATH}",
                params={"tin": tin},
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=15,
            )
            if resp.status_code == 404:
                return {"status": False, "data": None}
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Bill/Receipt Reporting
    # POST /v1/bills/report
    # ------------------------------------------------------------------
    async def report_bill(
        self,
        bill_number: str,
        bill_datetime: str,
        total_value: float,
        items: list[dict],
    ) -> dict:
        """
        Submit a receipt/bill to FIRS ATRS.

        Request body:
            {
              "vat_number":      "1234567890",
              "business_place":  "AABBCC",
              "business_device": "POS-001",
              "bill_number":     "INV-001",
              "bill_datetime":   "2026-04-21T09:00:00+01:00",
              "total_value":     15000.00,
              "security_code":   "<MD5 SID>",
              "items": [
                {
                  "name":     "Compliance Service Fee",
                  "quantity": 1,
                  "price":    15000.00,
                  "vat":      1350.00
                }
              ]
            }

        Response:
            {
              "status": true,
              "uid":    "FIRS-UID-20260421-001",
              "message": "Bill reported successfully"
            }
        """
        if not self.live:
            return {
                "status": True,
                "uid": f"MOCK-UID-{bill_number}",
                "message": "Bill reported successfully (mock)"
            }

        if not self._token:
            await self.authenticate()

        sid = self._generate_sid(bill_number, bill_datetime, total_value)

        payload = {
            "vat_number":      self.vat_number,
            "business_place":  self.business_place,
            "business_device": self.business_device,
            "bill_number":     bill_number,
            "bill_datetime":   bill_datetime,
            "total_value":     total_value,
            "security_code":   sid,
            "items":           items,
        }

        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{self.base_url}{BILLS_PATH}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type":  "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # SID (Security Identifier) — MD5 signature
    # ------------------------------------------------------------------
    def _generate_sid(
        self,
        bill_number: str,
        bill_datetime: str,
        total_value: float,
    ) -> str:
        """
        SID = MD5(client_secret + vat_number + business_place +
                  business_device + bill_number + bill_datetime + total_value)

        Per FIRS signing spec: https://atrs.firs.gov.ng/docs/signing-the-data
        """
        buffer = (
            self.client_secret
            + self.vat_number
            + self.business_place
            + self.business_device
            + bill_number
            + bill_datetime
            + str(total_value)
        )
        return hashlib.md5(buffer.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Mock responses — mirrors exact FIRS response schema
    # ------------------------------------------------------------------
    def _mock_tin_response(self, tin: str, submitted_name: str) -> dict:
        """
        Returns a mock FIRS TIN verification response.
        Simulates realistic outcomes:
          - TIN ending in '55' → NOT FOUND
          - TIN ending in '99' → NAME MISMATCH
          - All others         → MATCHED
        """
        if tin.endswith("55"):
            return {"status": False, "data": None}

        if tin.endswith("99"):
            return {
                "status": True,
                "data": {
                    "tin":               tin,
                    "taxpayer_name":     f"{submitted_name.split()[0]} Holdings Ltd",
                    "tax_office":        "Abuja Municipal",
                    "registration_date": "2019-06-15",
                    "status":            "ACTIVE",
                }
            }

        return {
            "status": True,
            "data": {
                "tin":               tin,
                "taxpayer_name":     submitted_name,
                "tax_office":        "Lagos Island",
                "registration_date": "2020-03-10",
                "status":            "ACTIVE",
            }
        }

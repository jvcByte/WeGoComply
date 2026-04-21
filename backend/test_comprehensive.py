"""
WeGoComply Comprehensive API Test Suite  (mock mode)
Uses asyncio + httpx.AsyncClient to avoid BaseHTTPMiddleware deadlocks.
"""
from __future__ import annotations
import asyncio
import sys
from datetime import datetime, timezone
import httpx

BASE_URL = "http://localhost:8000"
TIMEOUT  = 20.0

GREEN="\033[92m"; RED="\033[91m"; YELLOW="\033[93m"; CYAN="\033[96m"; BOLD="\033[1m"; RESET="\033[0m"
passed=0; failed=0; results=[]

def _s(ok): return f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"

def record(name, ok, reason=""):
    global passed, failed
    if ok:
        print(f"  {CYAN}>{RESET} {name} ... {_s(True)}")
        passed += 1
        results.append({"name": name, "status": "PASS"})
    else:
        print(f"  {CYAN}>{RESET} {name} ... {_s(False)}  ->  {reason}")
        failed += 1
        results.append({"name": name, "status": "FAIL", "reason": reason})

def section(t):
    print(f"\n{BOLD}{YELLOW}{'='*60}{RESET}\n{BOLD}{YELLOW}  {t}{RESET}\n{BOLD}{YELLOW}{'='*60}{RESET}")

TS = datetime.now(timezone.utc).isoformat()
ADMIN  = {"X-Mock-Roles":"admin","X-Mock-User":"test-admin-001","X-Mock-Email":"admin@wegocomply.test"}
ANALYST= {"X-Mock-Roles":"analyst","X-Mock-User":"test-analyst-001"}
VIEWER = {"X-Mock-Roles":"viewer","X-Mock-User":"test-viewer-001"}
COMPLY = {"X-Mock-Roles":"compliance_officer","X-Mock-User":"test-comply-001"}
TX = {"transaction_id":"TXN-001","customer_id":"CUST-001","amount":150000.0,"currency":"NGN",
      "timestamp":TS,"transaction_type":"transfer","counterparty":"CUST-002","channel":"mobile"}
TIN = {"customer_id":"CUST-TAX-001","name":"Adebayo Okafor","tin":"1234567890"}


async def run_all():
    # Use a single async client — httpx.AsyncClient works correctly with async FastAPI
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as c:

        async def t(name, coro):
            global passed, failed
            print(f"  {CYAN}>{RESET} {name} ... ", end="", flush=True)
            try:
                await coro
                print(_s(True))
                passed += 1
                results.append({"name": name, "status": "PASS"})
            except AssertionError as e:
                print(f"{_s(False)}  ->  {e}")
                failed += 1
                results.append({"name": name, "status": "FAIL", "reason": str(e)})
            except Exception as e:
                print(f"{_s(False)}  ->  {type(e).__name__}: {e}")
                failed += 1
                results.append({"name": name, "status": "FAIL", "reason": f"{type(e).__name__}: {e}"})

        # ── 1. Health ────────────────────────────────────────────────────────
        section("1. Health Check")

        async def health():
            r = await c.get("/")
            assert r.status_code == 200, f"Got {r.status_code}"
            b = r.json()
            assert b.get("mode") == "mock", f"mode={b.get('mode')}"
            assert "version" in b and "status" in b
        await t("GET / returns 200 with mode=mock", health())

        # ── 2. Authentication ────────────────────────────────────────────────
        section("2. Authentication")

        async def auth_admin():
            r = await c.get("/api/auth/me", headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert b["user_id"] == "test-admin-001"
            assert "admin" in b["roles"]
            assert b["auth_mode"] == "mock"
        await t("Admin authenticated correctly", auth_admin())

        async def auth_analyst():
            r = await c.get("/api/auth/me", headers=ANALYST)
            assert r.status_code == 200
            assert "analyst" in r.json()["roles"]
        await t("Analyst authenticated correctly", auth_analyst())

        async def auth_viewer():
            r = await c.get("/api/auth/me", headers=VIEWER)
            assert r.status_code == 200
            assert "viewer" in r.json()["roles"]
        await t("Viewer authenticated correctly", auth_viewer())

        async def auth_multi():
            r = await c.get("/api/auth/me", headers={"X-Mock-Roles": "admin,analyst"})
            assert r.status_code == 200
            roles = r.json()["roles"]
            assert "admin" in roles and "analyst" in roles
        await t("Multiple roles parsed correctly", auth_multi())

        async def auth_bad_role():
            r = await c.get("/api/auth/me", headers={"X-Mock-Roles": "superuser"})
            assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        await t("Unrecognised role returns 401", auth_bad_role())

        async def auth_empty_role():
            r = await c.get("/api/auth/me", headers={"X-Mock-Roles": ""})
            assert r.status_code == 200
            assert "admin" in r.json()["roles"]
        await t("Empty roles falls back to mock defaults (200)", auth_empty_role())

        async def auth_no_headers():
            r = await c.get("/api/auth/me")
            assert r.status_code == 200
        await t("No headers falls back to mock defaults (200)", auth_no_headers())

        # ── 3. RBAC ──────────────────────────────────────────────────────────
        section("3. Role-Based Access Control")

        async def rbac_viewer_monitor():
            r = await c.post("/api/aml/monitor", json={"transactions": [TX]}, headers=VIEWER)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
        await t("Viewer blocked from AML monitor (403)", rbac_viewer_monitor())

        async def rbac_viewer_str():
            r = await c.post("/api/aml/generate-str/TXN-001", json=TX, headers=VIEWER)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
        await t("Viewer blocked from STR generation (403)", rbac_viewer_str())

        async def rbac_analyst_str():
            r = await c.post("/api/aml/generate-str/TXN-001", json=TX, headers=ANALYST)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
        await t("Analyst blocked from STR generation (403)", rbac_analyst_str())

        async def rbac_viewer_reg():
            r = await c.get("/api/regulatory/updates", headers=VIEWER)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        await t("Viewer can read regulatory updates (200)", rbac_viewer_reg())

        async def rbac_viewer_summarize():
            r = await c.post("/api/regulatory/summarize",
                             json={"text": "This is a test regulatory circular with sufficient length for validation."},
                             headers=VIEWER)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
        await t("Viewer blocked from regulatory summarize (403)", rbac_viewer_summarize())

        # ── 4. KYC ───────────────────────────────────────────────────────────
        section("4. KYC")

        async def kyc_verified():
            r = await c.post("/api/kyc/risk-score",
                             json={"nin_verified": True, "bvn_verified": True,
                                   "face_match": True, "face_confidence": 0.95},
                             headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert b["risk_level"] in ("LOW", "MEDIUM", "HIGH")
            assert 0.0 <= b["risk_score"] <= 1.0
        await t("KYC risk score - fully verified customer", kyc_verified())

        async def kyc_unverified():
            r = await c.post("/api/kyc/risk-score",
                             json={"nin_verified": False, "bvn_verified": False,
                                   "face_match": False, "face_confidence": 0.0},
                             headers=ADMIN)
            assert r.status_code == 200
            assert r.json()["risk_level"] == "HIGH", f"Expected HIGH, got {r.json()['risk_level']}"
        await t("KYC risk score - unverified returns HIGH", kyc_unverified())

        async def kyc_bad_confidence():
            r = await c.post("/api/kyc/risk-score",
                             json={"face_confidence": 1.5}, headers=ADMIN)
            assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        await t("KYC risk score - confidence > 1.0 returns 422", kyc_bad_confidence())

        async def kyc_viewer_blocked():
            r = await c.post("/api/kyc/risk-score",
                             json={"nin_verified": True, "bvn_verified": True,
                                   "face_match": True, "face_confidence": 0.9},
                             headers=VIEWER)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
        await t("KYC risk score - viewer returns 403", kyc_viewer_blocked())

        # ── 5. AML ───────────────────────────────────────────────────────────
        section("5. AML")

        async def aml_single():
            r = await c.post("/api/aml/monitor", json={"transactions": [TX]}, headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert b["total_analyzed"] == 1
            assert b["flagged_count"] + b["clean_count"] == 1
        await t("AML monitor - single transaction", aml_single())

        async def aml_batch():
            batch = {"transactions": [
                TX,
                {**TX, "transaction_id": "TXN-002", "amount": 5_000_000.0},
                {**TX, "transaction_id": "TXN-003", "amount": 250.0},
            ]}
            r = await c.post("/api/aml/monitor", json=batch, headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert b["total_analyzed"] == 3
            assert b["flagged_count"] + b["clean_count"] == 3
        await t("AML monitor - batch of 3", aml_batch())

        async def aml_empty():
            r = await c.post("/api/aml/monitor", json={"transactions": []}, headers=ADMIN)
            assert r.status_code in (200, 422), f"Unexpected {r.status_code}"
        await t("AML monitor - empty batch handled", aml_empty())

        async def aml_neg_amount():
            r = await c.post("/api/aml/monitor",
                             json={"transactions": [{**TX, "amount": -100}]}, headers=ADMIN)
            assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        await t("AML monitor - negative amount returns 422", aml_neg_amount())

        async def aml_bad_channel():
            r = await c.post("/api/aml/monitor",
                             json={"transactions": [{**TX, "channel": "fax"}]}, headers=ADMIN)
            assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        await t("AML monitor - invalid channel returns 422", aml_bad_channel())

        async def aml_str_admin():
            r = await c.post("/api/aml/generate-str/TXN-STR-001", json=TX, headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert "report_reference" in b
            assert "grounds_for_suspicion" in b
        await t("AML STR - admin can generate", aml_str_admin())

        async def aml_str_comply():
            r = await c.post("/api/aml/generate-str/TXN-STR-002", json=TX, headers=COMPLY)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
        await t("AML STR - compliance_officer can generate", aml_str_comply())

        # ── 6. Tax ───────────────────────────────────────────────────────────
        section("6. Tax Verification")

        async def tax_valid():
            r = await c.post("/api/tax/verify-tin", json=TIN, headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert b["status"] in ("MATCHED", "NOT_FOUND", "NAME_MISMATCH")
            assert 0.0 <= b["match_confidence"] <= 1.0
        await t("Tax verify TIN - valid TIN", tax_valid())

        async def tax_non_numeric():
            r = await c.post("/api/tax/verify-tin",
                             json={"customer_id": "C1", "name": "Test", "tin": "ABC123"},
                             headers=ADMIN)
            assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        await t("Tax verify TIN - non-numeric returns 422", tax_non_numeric())

        async def tax_too_short():
            r = await c.post("/api/tax/verify-tin",
                             json={"customer_id": "C1", "name": "Test", "tin": "12345"},
                             headers=ADMIN)
            assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        await t("Tax verify TIN - too short returns 422", tax_too_short())

        async def tax_bulk():
            payload = {"records": [
                {"customer_id": "C1", "name": "Adebayo Okafor", "tin": "1234567890"},
                {"customer_id": "C2", "name": "Ngozi Adeyemi",  "tin": "0987654321"},
                {"customer_id": "C3", "name": "Emeka Nwosu",    "tin": "1122334455"},
            ]}
            r = await c.post("/api/tax/bulk-verify", json=payload, headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert b["total"] == 3
            assert b["matched"] + b["failed"] == 3
            assert b["deadline_risk"] in ("LOW", "HIGH")
        await t("Tax bulk verify - 3 records", tax_bulk())

        async def tax_viewer():
            r = await c.post("/api/tax/verify-tin", json=TIN, headers=VIEWER)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}"
        await t("Tax verify TIN - viewer returns 403", tax_viewer())

        # ── 7. Regulatory ────────────────────────────────────────────────────
        section("7. Regulatory")

        async def reg_updates():
            r = await c.get("/api/regulatory/updates", headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            assert "updates" in r.json()
        await t("Regulatory updates - returns list", reg_updates())

        async def reg_summarize():
            r = await c.post("/api/regulatory/summarize",
                             json={"text": (
                                 "The Central Bank of Nigeria directs all deposit money banks "
                                 "to implement enhanced AML transaction monitoring for all "
                                 "transactions above NGN 5000000. Compliance required within 30 days."
                             )},
                             headers=ADMIN)
            assert r.status_code == 200, f"{r.status_code}: {r.text}"
            b = r.json()
            assert "summary" in b
            assert b["urgency"] in ("HIGH", "MEDIUM", "LOW")
        await t("Regulatory summarize - returns structured summary", reg_summarize())

        async def reg_too_short():
            r = await c.post("/api/regulatory/summarize",
                             json={"text": "Too short"}, headers=ADMIN)
            assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        await t("Regulatory summarize - too short returns 422", reg_too_short())

        # ── 8. Rate Limiting ─────────────────────────────────────────────────
        section("8. Rate Limiting")

        async def rate_limit():
            r = await c.post("/api/kyc/risk-score",
                             json={"nin_verified": True, "bvn_verified": True,
                                   "face_match": True, "face_confidence": 0.9},
                             headers={"X-Mock-Roles": "admin", "X-Mock-User": "rl-probe-99"})
            assert r.status_code == 200
            has_rl = any(h.lower().startswith("x-ratelimit") for h in r.headers)
            assert has_rl, f"No X-RateLimit-* headers. Got: {list(r.headers.keys())}"
        await t("Rate limit headers present on responses", rate_limit())

        # ── 9. Error Format ──────────────────────────────────────────────────
        section("9. Error Response Format")

        async def err_403():
            r = await c.post("/api/aml/monitor",
                             json={"transactions": [TX]}, headers=VIEWER)
            assert r.status_code == 403
            b = r.json()
            assert "error" in b or "detail" in b, f"Missing error/detail: {b}"
        await t("403 response has error/detail field", err_403())

        async def err_422():
            r = await c.post("/api/kyc/risk-score",
                             json={"face_confidence": 99}, headers=ADMIN)
            assert r.status_code == 422
            b = r.json()
            assert "error" in b or "detail" in b, f"Missing error/detail: {b}"
        await t("422 response has error/detail field", err_422())

        async def err_404():
            r = await c.get("/api/nonexistent")
            assert r.status_code == 404, f"Expected 404, got {r.status_code}"
        await t("Unknown route returns 404", err_404())

        # ── 10. OpenAPI / Docs ───────────────────────────────────────────────
        section("10. OpenAPI / Docs")

        async def openapi():
            r = await c.get("/openapi.json")
            assert r.status_code == 200
            paths = r.json().get("paths", {})
            for route in ("/api/auth/me", "/api/aml/monitor", "/api/kyc/risk-score",
                          "/api/tax/verify-tin", "/api/regulatory/updates"):
                assert route in paths, f"Route {route} missing from OpenAPI schema"
        await t("OpenAPI schema includes all major routes", openapi())

        async def swagger():
            r = await c.get("/docs")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        await t("Swagger UI accessible at /docs", swagger())


asyncio.run(run_all())

total = passed + failed
print(f"\n{BOLD}{'='*60}{RESET}\n{BOLD}  TEST SUMMARY{RESET}\n{BOLD}{'='*60}{RESET}")
print(f"  Total :  {total}\n  {GREEN}Passed:  {passed}{RESET}\n  {RED}Failed:  {failed}{RESET}\n{BOLD}{'='*60}{RESET}\n")
if failed:
    print(f"{RED}{BOLD}  FAILED TESTS:{RESET}")
    for res in results:
        if res["status"] == "FAIL":
            print(f"  {RED}x{RESET} {res['name']}\n    {YELLOW}-> {res.get('reason','unknown')}{RESET}")
    print()
sys.exit(0 if failed == 0 else 1)

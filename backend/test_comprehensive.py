"""
WeGoComply Comprehensive API Test Suite  (mock mode)

Mock-mode behaviours accounted for:
  - No Bearer token required; auth driven by X-Mock-* headers.
  - Empty/absent X-Mock-Roles falls back to MOCK_AUTH_ROLES from .env (admin).
    This is intentional — it does NOT return 401 in mock mode.
  - Fraud model artifact may be absent; repo falls back to deterministic mock
    (risk_band='Low Risk', mock=True, decision='APPROVED').
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import httpx

BASE_URL = "http://localhost:8000"
TIMEOUT  = 30.0

# ── colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed  = 0
failed  = 0
results: list[dict] = []


def _status(ok: bool) -> str:
    return f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"


def run_test(name: str, fn):
    global passed, failed
    print(f"  {CYAN}>{RESET} {name} ... ", end="", flush=True)
    try:
        fn()
        print(_status(True))
        passed += 1
        results.append({"name": name, "status": "PASS"})
    except AssertionError as exc:
        print(f"{_status(False)}  ->  {exc}")
        failed += 1
        results.append({"name": name, "status": "FAIL", "reason": str(exc)})
    except Exception as exc:
        print(f"{_status(False)}  ->  {type(exc).__name__}: {exc}")
        failed += 1
        results.append({"name": name, "status": "FAIL", "reason": f"{type(exc).__name__}: {exc}"})


def section(title: str):
    print(f"\n{BOLD}{YELLOW}{'='*60}{RESET}")
    print(f"{BOLD}{YELLOW}  {title}{RESET}")
    print(f"{BOLD}{YELLOW}{'='*60}{RESET}")


# ── shared fixtures ───────────────────────────────────────────────────────────
ADMIN_HEADERS = {
    "X-Mock-Roles": "admin",
    "X-Mock-User":  "test-admin-001",
    "X-Mock-Email": "admin@wegocomply.test",
    "X-Mock-Name":  "Test Admin",
}
ANALYST_HEADERS = {
    "X-Mock-Roles": "analyst",
    "X-Mock-User":  "test-analyst-001",
    "X-Mock-Email": "analyst@wegocomply.test",
}
VIEWER_HEADERS = {
    "X-Mock-Roles": "viewer",
    "X-Mock-User":  "test-viewer-001",
    "X-Mock-Email": "viewer@wegocomply.test",
}
COMPLIANCE_HEADERS = {"X-Mock-Roles": "compliance_officer"}

TS = datetime.now(timezone.utc).isoformat()

SAMPLE_TX = {
    "transaction_id":   "TXN-TEST-001",
    "customer_id":      "CUST-001",
    "amount":           150_000.0,
    "currency":         "NGN",
    "timestamp":        TS,
    "transaction_type": "transfer",
    "counterparty":     "CUST-002",
    "channel":          "mobile",
}

HIGH_RISK_TX = {
    **SAMPLE_TX,
    "transaction_id":          "TXN-HIGH-001",
    "amount":                  9_500_000.0,
    "old_balance_origin":      10_000_000.0,
    "new_balance_origin":      0.0,
    "old_balance_destination": 0.0,
    "new_balance_destination": 9_500_000.0,
}

# =============================================================================
# 1. HEALTH CHECK
# =============================================================================
section("1. Health Check")

def test_health():
    r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    b = r.json()
    assert b.get("mode") == "mock", f"Expected mode=mock, got {b.get('mode')}"
    assert "version" in b
    assert "status" in b

run_test("GET / returns 200 with status/version/mode=mock", test_health)

# =============================================================================
# 2. AUTHENTICATION  /api/auth/me
# =============================================================================
section("2. Authentication — /api/auth/me")

def test_auth_admin():
    r = httpx.get(f"{BASE_URL}/api/auth/me", headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert b["user_id"] == "test-admin-001"
    assert b["email"]   == "admin@wegocomply.test"
    assert "admin" in b["roles"]
    assert b["auth_mode"] == "mock"

run_test("Admin user authenticated correctly", test_auth_admin)

def test_auth_analyst():
    r = httpx.get(f"{BASE_URL}/api/auth/me", headers=ANALYST_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    assert "analyst" in r.json()["roles"]

run_test("Analyst user authenticated correctly", test_auth_analyst)

def test_auth_viewer():
    r = httpx.get(f"{BASE_URL}/api/auth/me", headers=VIEWER_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    assert "viewer" in r.json()["roles"]

run_test("Viewer user authenticated correctly", test_auth_viewer)

def test_auth_multiple_roles():
    r = httpx.get(f"{BASE_URL}/api/auth/me",
                  headers={"X-Mock-Roles": "admin,analyst"}, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    roles = r.json()["roles"]
    assert "admin"   in roles
    assert "analyst" in roles

run_test("Multiple roles in header parsed correctly", test_auth_multiple_roles)

def test_auth_invalid_role_returns_401():
    # "superuser" is not a valid UserRole — all roles stripped → 401
    r = httpx.get(f"{BASE_URL}/api/auth/me",
                  headers={"X-Mock-Roles": "superuser"}, timeout=TIMEOUT)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"

run_test("Unrecognised role name returns 401", test_auth_invalid_role_returns_401)

def test_auth_empty_roles_falls_back_to_defaults():
    # Empty X-Mock-Roles → MockIdentityProvider falls back to settings.mock_auth_roles
    # which is 'admin' by default — so 200 is the correct mock-mode behaviour
    r = httpx.get(f"{BASE_URL}/api/auth/me",
                  headers={"X-Mock-Roles": ""}, timeout=TIMEOUT)
    assert r.status_code == 200, f"Expected 200 (fallback to default roles), got {r.status_code}"
    assert "admin" in r.json()["roles"]

run_test("Empty X-Mock-Roles falls back to default mock roles (200)", test_auth_empty_roles_falls_back_to_defaults)

def test_auth_no_headers_falls_back_to_defaults():
    # No mock headers at all → falls back to settings defaults → 200
    r = httpx.get(f"{BASE_URL}/api/auth/me", timeout=TIMEOUT)
    assert r.status_code == 200, f"Expected 200 (mock fallback), got {r.status_code}: {r.text}"

run_test("No auth headers falls back to mock defaults (200)", test_auth_no_headers_falls_back_to_defaults)

# =============================================================================
# 3. ROLE-BASED ACCESS CONTROL
# =============================================================================
section("3. Role-Based Access Control")

def test_viewer_blocked_from_aml_screen():
    r = httpx.post(f"{BASE_URL}/api/aml/screen", json=SAMPLE_TX,
                   headers=VIEWER_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

run_test("Viewer blocked from AML screen (403)", test_viewer_blocked_from_aml_screen)

def test_viewer_blocked_from_str():
    r = httpx.post(f"{BASE_URL}/api/aml/generate-str/TXN-001", json=SAMPLE_TX,
                   headers=VIEWER_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

run_test("Viewer blocked from STR generation (403)", test_viewer_blocked_from_str)

def test_analyst_blocked_from_str():
    r = httpx.post(f"{BASE_URL}/api/aml/generate-str/TXN-001", json=SAMPLE_TX,
                   headers=ANALYST_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

run_test("Analyst blocked from STR generation (403)", test_analyst_blocked_from_str)

def test_viewer_can_read_regulatory():
    r = httpx.get(f"{BASE_URL}/api/regulatory/updates",
                  headers=VIEWER_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

run_test("Viewer can read regulatory updates (200)", test_viewer_can_read_regulatory)

def test_viewer_blocked_from_regulatory_summarize():
    r = httpx.post(
        f"{BASE_URL}/api/regulatory/summarize",
        json={"text": "This is a test regulatory circular with sufficient length for validation."},
        headers=VIEWER_HEADERS, timeout=TIMEOUT,
    )
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

run_test("Viewer blocked from regulatory summarize (403)", test_viewer_blocked_from_regulatory_summarize)

# =============================================================================
# 4. KYC  /api/kyc
# =============================================================================
section("4. KYC — /api/kyc")

def test_kyc_risk_score_fully_verified():
    r = httpx.post(
        f"{BASE_URL}/api/kyc/risk-score",
        json={"nin_verified": True, "bvn_verified": True,
              "face_match": True, "face_confidence": 0.95},
        headers=ADMIN_HEADERS, timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert b["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert 0.0 <= b["risk_score"] <= 1.0

run_test("KYC risk score — fully verified customer", test_kyc_risk_score_fully_verified)

def test_kyc_risk_score_unverified_is_high():
    r = httpx.post(
        f"{BASE_URL}/api/kyc/risk-score",
        json={"nin_verified": False, "bvn_verified": False,
              "face_match": False, "face_confidence": 0.0},
        headers=ADMIN_HEADERS, timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    assert r.json()["risk_level"] == "HIGH", f"Expected HIGH, got {r.json()['risk_level']}"

run_test("KYC risk score — unverified customer returns HIGH", test_kyc_risk_score_unverified_is_high)

def test_kyc_risk_score_invalid_confidence():
    r = httpx.post(
        f"{BASE_URL}/api/kyc/risk-score",
        json={"nin_verified": True, "bvn_verified": True,
              "face_match": True, "face_confidence": 1.5},
        headers=ADMIN_HEADERS, timeout=TIMEOUT,
    )
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

run_test("KYC risk score — face_confidence > 1.0 returns 422", test_kyc_risk_score_invalid_confidence)

def test_kyc_risk_score_viewer_blocked():
    r = httpx.post(
        f"{BASE_URL}/api/kyc/risk-score",
        json={"nin_verified": True, "bvn_verified": True,
              "face_match": True, "face_confidence": 0.9},
        headers=VIEWER_HEADERS, timeout=TIMEOUT,
    )
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

run_test("KYC risk score — viewer role returns 403", test_kyc_risk_score_viewer_blocked)

# =============================================================================
# 5. AML  /api/aml
# =============================================================================
section("5. AML — /api/aml")

def test_aml_screen_normal():
    r = httpx.post(f"{BASE_URL}/api/aml/screen", json=SAMPLE_TX,
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert b["transaction_id"] == "TXN-TEST-001"
    assert b["decision"] in ("APPROVED", "DECLINED", "REVIEW")
    assert 0.0 <= b["fraud_risk_score"] <= 1.0
    assert b["risk_band"] in ("Low Risk", "Watch", "Review", "High Risk",
                               "LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert isinstance(b["reasons"], list)
    assert isinstance(b["mock"], bool)

run_test("AML screen — normal transaction returns valid decision", test_aml_screen_normal)

def test_aml_screen_high_risk():
    r = httpx.post(f"{BASE_URL}/api/aml/screen", json=HIGH_RISK_TX,
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    # With real model: DECLINED or REVIEW; with mock fallback: APPROVED is also valid
    assert r.json()["decision"] in ("APPROVED", "DECLINED", "REVIEW")

run_test("AML screen — high-risk transaction returns a decision", test_aml_screen_high_risk)

def test_aml_screen_negative_amount():
    r = httpx.post(f"{BASE_URL}/api/aml/screen",
                   json={**SAMPLE_TX, "amount": -100},
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

run_test("AML screen — negative amount returns 422", test_aml_screen_negative_amount)

def test_aml_screen_invalid_channel():
    r = httpx.post(f"{BASE_URL}/api/aml/screen",
                   json={**SAMPLE_TX, "channel": "fax"},
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

run_test("AML screen — invalid channel returns 422", test_aml_screen_invalid_channel)

def test_aml_monitor_batch():
    batch = {"transactions": [
        SAMPLE_TX,
        {**SAMPLE_TX, "transaction_id": "TXN-TEST-002", "amount": 5_000_000.0},
        {**SAMPLE_TX, "transaction_id": "TXN-TEST-003", "amount": 250.0},
    ]}
    r = httpx.post(f"{BASE_URL}/api/aml/monitor", json=batch,
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert b["total_analyzed"] == 3
    assert b["flagged_count"] + b["clean_count"] == 3
    assert isinstance(b["flagged_transactions"], list)

run_test("AML monitor — batch of 3 transactions analyzed", test_aml_monitor_batch)

def test_aml_monitor_empty_batch():
    r = httpx.post(f"{BASE_URL}/api/aml/monitor",
                   json={"transactions": []},
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code in (200, 422), f"Unexpected {r.status_code}: {r.text}"

run_test("AML monitor — empty batch handled gracefully", test_aml_monitor_empty_batch)

def test_aml_str_admin():
    r = httpx.post(f"{BASE_URL}/api/aml/generate-str/TXN-STR-001",
                   json=SAMPLE_TX, headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert "report_reference"      in b
    assert "reporting_institution" in b
    assert "grounds_for_suspicion" in b
    assert "recommended_action"    in b

run_test("AML STR generation — admin can generate STR", test_aml_str_admin)

def test_aml_str_compliance_officer():
    r = httpx.post(f"{BASE_URL}/api/aml/generate-str/TXN-STR-002",
                   json=SAMPLE_TX, headers=COMPLIANCE_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"

run_test("AML STR generation — compliance_officer can generate STR", test_aml_str_compliance_officer)

# =============================================================================
# 6. TAX VERIFICATION  /api/tax
# =============================================================================
section("6. Tax Verification — /api/tax")

SAMPLE_TIN = {"customer_id": "CUST-TAX-001", "name": "Adebayo Okafor", "tin": "1234567890"}

def test_tax_verify_tin():
    r = httpx.post(f"{BASE_URL}/api/tax/verify-tin", json=SAMPLE_TIN,
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert b["customer_id"] == "CUST-TAX-001"
    assert b["status"] in ("MATCHED", "NOT_FOUND", "NAME_MISMATCH")
    assert 0.0 <= b["match_confidence"] <= 1.0
    assert "submitted_name" in b

run_test("Tax verify TIN — valid TIN returns result", test_tax_verify_tin)

def test_tax_verify_tin_non_numeric():
    r = httpx.post(f"{BASE_URL}/api/tax/verify-tin",
                   json={"customer_id": "C1", "name": "Test", "tin": "ABC123"},
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

run_test("Tax verify TIN — non-numeric TIN returns 422", test_tax_verify_tin_non_numeric)

def test_tax_verify_tin_too_short():
    r = httpx.post(f"{BASE_URL}/api/tax/verify-tin",
                   json={"customer_id": "C1", "name": "Test", "tin": "12345"},
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

run_test("Tax verify TIN — TIN too short returns 422", test_tax_verify_tin_too_short)

def test_tax_bulk_verify():
    payload = {"records": [
        {"customer_id": "C1", "name": "Adebayo Okafor", "tin": "1234567890"},
        {"customer_id": "C2", "name": "Ngozi Adeyemi",  "tin": "0987654321"},
        {"customer_id": "C3", "name": "Emeka Nwosu",    "tin": "1122334455"},
    ]}
    r = httpx.post(f"{BASE_URL}/api/tax/bulk-verify", json=payload,
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert b["total"] == 3
    assert b["matched"] + b["failed"] == 3
    assert 0.0 <= b["match_rate"] <= 100.0
    assert b["deadline_risk"] in ("LOW", "HIGH")
    assert len(b["records"]) == 3

run_test("Tax bulk verify — 3 records processed correctly", test_tax_bulk_verify)

def test_tax_viewer_blocked():
    r = httpx.post(f"{BASE_URL}/api/tax/verify-tin", json=SAMPLE_TIN,
                   headers=VIEWER_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

run_test("Tax verify TIN — viewer role returns 403", test_tax_viewer_blocked)

# =============================================================================
# 7. REGULATORY  /api/regulatory
# =============================================================================
section("7. Regulatory — /api/regulatory")

def test_regulatory_updates():
    r = httpx.get(f"{BASE_URL}/api/regulatory/updates",
                  headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert "updates" in b
    assert isinstance(b["updates"], list)

run_test("Regulatory updates — returns list of updates", test_regulatory_updates)

def test_regulatory_summarize():
    r = httpx.post(
        f"{BASE_URL}/api/regulatory/summarize",
        json={"text": (
            "The Central Bank of Nigeria hereby directs all deposit money banks to implement "
            "enhanced customer due diligence procedures for all transactions above NGN 5,000,000. "
            "Compliance is required within 30 days of this circular."
        )},
        headers=ADMIN_HEADERS, timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    b = r.json()
    assert "summary"            in b
    assert "action_required"    in b
    assert b["urgency"] in ("HIGH", "MEDIUM", "LOW")
    assert isinstance(b["affected_operations"], list)

run_test("Regulatory summarize — returns structured summary", test_regulatory_summarize)

def test_regulatory_summarize_too_short():
    r = httpx.post(f"{BASE_URL}/api/regulatory/summarize",
                   json={"text": "Too short"},
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

run_test("Regulatory summarize — text too short returns 422", test_regulatory_summarize_too_short)

# =============================================================================
# 8. RATE LIMITING HEADERS
# =============================================================================
section("8. Rate Limiting")

def test_rate_limit_headers():
    r = httpx.get(f"{BASE_URL}/api/auth/me", headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200
    has_rl = any(h.lower().startswith("x-ratelimit") for h in r.headers)
    assert has_rl, f"No X-RateLimit-* headers found. Got: {list(r.headers.keys())}"

run_test("Rate limit headers present on responses", test_rate_limit_headers)

# =============================================================================
# 9. ERROR RESPONSE FORMAT
# =============================================================================
section("9. Error Response Format")

def test_403_error_format():
    r = httpx.post(f"{BASE_URL}/api/aml/screen", json=SAMPLE_TX,
                   headers=VIEWER_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 403
    b = r.json()
    assert "error" in b or "detail" in b, f"Missing error/detail: {b}"

run_test("403 response has error/detail field", test_403_error_format)

def test_422_error_format():
    r = httpx.post(f"{BASE_URL}/api/kyc/risk-score",
                   json={"face_confidence": 99},
                   headers=ADMIN_HEADERS, timeout=TIMEOUT)
    assert r.status_code == 422
    b = r.json()
    assert "error" in b or "detail" in b, f"Missing error/detail: {b}"

run_test("422 response has error/detail field", test_422_error_format)

def test_404_unknown_route():
    r = httpx.get(f"{BASE_URL}/api/nonexistent", timeout=TIMEOUT)
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"

run_test("Unknown route returns 404", test_404_unknown_route)

# =============================================================================
# 10. OPENAPI / DOCS
# =============================================================================
section("10. OpenAPI / Docs")

def test_openapi_schema():
    r = httpx.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}"
    paths = r.json().get("paths", {})
    for route in ("/api/auth/me", "/api/aml/screen", "/api/kyc/risk-score",
                  "/api/tax/verify-tin", "/api/regulatory/updates"):
        assert route in paths, f"Route {route} missing from OpenAPI schema"

run_test("OpenAPI schema includes all major routes", test_openapi_schema)

def test_swagger_ui():
    r = httpx.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"

run_test("Swagger UI accessible at /docs", test_swagger_ui)

# =============================================================================
# SUMMARY
# =============================================================================
total = passed + failed
print(f"\n{BOLD}{'='*60}{RESET}")
print(f"{BOLD}  TEST SUMMARY{RESET}")
print(f"{BOLD}{'='*60}{RESET}")
print(f"  Total :  {total}")
print(f"  {GREEN}Passed:  {passed}{RESET}")
print(f"  {RED}Failed:  {failed}{RESET}")
print(f"{BOLD}{'='*60}{RESET}\n")

if failed:
    print(f"{RED}{BOLD}  FAILED TESTS:{RESET}")
    for res in results:
        if res["status"] == "FAIL":
            print(f"  {RED}x{RESET} {res['name']}")
            print(f"    {YELLOW}-> {res.get('reason', 'unknown')}{RESET}")
    print()

sys.exit(0 if failed == 0 else 1)

 
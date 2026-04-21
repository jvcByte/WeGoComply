"""
Compliance Posture Scoring Service

Determines whether a fintech/bank is compliant by measuring
4 pillars: KYC, AML, TIN, and Regulatory Reporting.

Each pillar pulls from real transaction/verification data stored
in the database. For demo, we use realistic mock data.
"""

from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Pillar weights (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "kyc":       0.30,   # CBN KYC Guidelines
    "aml":       0.35,   # CBN AML/CFT Rules + NFIU STR requirements
    "tin":       0.20,   # FIRS TIN mandate
    "reporting": 0.15,   # NITDA/CBN regulatory reporting
}

# ---------------------------------------------------------------------------
# Mock institution data — replace with real DB queries in production
# ---------------------------------------------------------------------------
MOCK_INSTITUTIONS = {
    "inst-moniepoint": {
        "name": "Moniepoint MFB",
        "type": "FINTECH",
        "sector": "Digital Banking",
        "cbn_license": "MFB/2019/001",
        "kyc": {
            "total_customers": 10_000_000,
            "nin_verified": 9_200_000,
            "bvn_verified": 9_500_000,
            "face_verified": 8_800_000,
            "high_risk_unreviewed": 12,        # HIGH risk customers not reviewed in 24hrs
            "avg_onboarding_minutes": 2.3,
        },
        "aml": {
            "total_transactions_today": 1_500_000,
            "monitored_realtime": 1_500_000,   # 100% monitored
            "flagged_today": 23,
            "reviewed_within_24hrs": 21,        # 2 not reviewed yet
            "strs_required": 7,
            "strs_filed_on_time": 6,            # 1 filed late
            "strs_filed_late": 1,
        },
        "tin": {
            "total_customers": 10_000_000,
            "tin_verified": 9_100_000,
            "accounts_restricted": 45_000,
            "days_to_deadline": 0,              # Deadline passed
        },
        "reporting": {
            "total_required_actions": 12,
            "completed_actions": 10,
            "missed_deadlines": 0,
            "pending_actions": 2,
        }
    },
    "inst-kuda": {
        "name": "Kuda Bank",
        "type": "FINTECH",
        "sector": "Digital Banking",
        "cbn_license": "MFB/2020/002",
        "kyc": {
            "total_customers": 5_000_000,
            "nin_verified": 4_100_000,
            "bvn_verified": 4_800_000,
            "face_verified": 3_900_000,
            "high_risk_unreviewed": 45,
            "avg_onboarding_minutes": 3.1,
        },
        "aml": {
            "total_transactions_today": 800_000,
            "monitored_realtime": 720_000,      # 90% monitored
            "flagged_today": 15,
            "reviewed_within_24hrs": 9,
            "strs_required": 4,
            "strs_filed_on_time": 2,
            "strs_filed_late": 2,
        },
        "tin": {
            "total_customers": 5_000_000,
            "tin_verified": 3_500_000,
            "accounts_restricted": 180_000,
            "days_to_deadline": 0,
        },
        "reporting": {
            "total_required_actions": 12,
            "completed_actions": 7,
            "missed_deadlines": 1,
            "pending_actions": 5,
        }
    },
    "inst-opay": {
        "name": "OPay Digital Services",
        "type": "PSP",
        "sector": "Payment Services",
        "cbn_license": "PSP/2018/003",
        "kyc": {
            "total_customers": 35_000_000,
            "nin_verified": 28_000_000,
            "bvn_verified": 30_000_000,
            "face_verified": 25_000_000,
            "high_risk_unreviewed": 120,
            "avg_onboarding_minutes": 4.5,
        },
        "aml": {
            "total_transactions_today": 5_000_000,
            "monitored_realtime": 4_000_000,    # 80% monitored
            "flagged_today": 89,
            "reviewed_within_24hrs": 55,
            "strs_required": 22,
            "strs_filed_on_time": 14,
            "strs_filed_late": 8,
        },
        "tin": {
            "total_customers": 35_000_000,
            "tin_verified": 22_000_000,
            "accounts_restricted": 850_000,
            "days_to_deadline": 0,
        },
        "reporting": {
            "total_required_actions": 12,
            "completed_actions": 5,
            "missed_deadlines": 2,
            "pending_actions": 7,
        }
    }
}


async def get_compliance_posture(institution_id: str) -> dict:
    """
    Calculate real-time compliance posture score for an institution.

    Data sources:
    - KYC: customers table (nin_verified, bvn_verified, face_match_verified)
    - AML: transactions table (is_flagged, review_date, str_generated)
    - TIN: tin_verifications table (status, verification_date)
    - Reporting: regulatory_updates table (completed_actions, deadlines)
    """
    inst = MOCK_INSTITUTIONS.get(institution_id)
    if not inst:
        return {"error": "Institution not found"}

    kyc_score   = _score_kyc(inst["kyc"])
    aml_score   = _score_aml(inst["aml"])
    tin_score   = _score_tin(inst["tin"])
    rep_score   = _score_reporting(inst["reporting"])

    overall = round(
        kyc_score   * WEIGHTS["kyc"]  +
        aml_score   * WEIGHTS["aml"]  +
        tin_score   * WEIGHTS["tin"]  +
        rep_score   * WEIGHTS["reporting"],
        1
    )

    status, color = _classify(overall)

    return {
        "institution_id": institution_id,
        "institution_name": inst["name"],
        "institution_type": inst["type"],
        "cbn_license": inst["cbn_license"],
        "as_of": datetime.now().isoformat(),

        # Overall
        "overall_score": overall,
        "status": status,
        "color": color,

        # Pillar breakdown
        "pillars": {
            "kyc": {
                "score": kyc_score,
                "weight": "30%",
                "label": "KYC / Identity Verification",
                "framework": "CBN KYC Guidelines",
                "details": _kyc_details(inst["kyc"])
            },
            "aml": {
                "score": aml_score,
                "weight": "35%",
                "label": "AML / Transaction Monitoring",
                "framework": "CBN AML/CFT Rules + NFIU STR Requirements",
                "details": _aml_details(inst["aml"])
            },
            "tin": {
                "score": tin_score,
                "weight": "20%",
                "label": "Tax ID (TIN) Verification",
                "framework": "FIRS TIN Mandate",
                "details": _tin_details(inst["tin"])
            },
            "reporting": {
                "score": rep_score,
                "weight": "15%",
                "label": "Regulatory Reporting",
                "framework": "NITDA / CBN Reporting Requirements",
                "details": _reporting_details(inst["reporting"])
            }
        },

        # Action items
        "action_items": _get_action_items(inst, kyc_score, aml_score, tin_score, rep_score)
    }


async def get_suptech_report() -> dict:
    """
    SupTech report for CBN/NITDA regulators.
    Aggregates compliance posture across all institutions.
    Replaces annual self-reporting with real-time sector view.
    """
    institutions = []
    scores = []

    for inst_id, inst in MOCK_INSTITUTIONS.items():
        kyc   = _score_kyc(inst["kyc"])
        aml   = _score_aml(inst["aml"])
        tin   = _score_tin(inst["tin"])
        rep   = _score_reporting(inst["reporting"])
        overall = round(kyc * WEIGHTS["kyc"] + aml * WEIGHTS["aml"] +
                        tin * WEIGHTS["tin"] + rep * WEIGHTS["reporting"], 1)
        status, color = _classify(overall)
        scores.append(overall)

        institutions.append({
            "institution_id": inst_id,
            "name": inst["name"],
            "type": inst["type"],
            "sector": inst["sector"],
            "overall_score": overall,
            "status": status,
            "color": color,
            "kyc_score": kyc,
            "aml_score": aml,
            "tin_score": tin,
            "reporting_score": rep,
            "cbn_license": inst["cbn_license"],
        })

    # Sort by score ascending (most at-risk first)
    institutions.sort(key=lambda x: x["overall_score"])

    sector_avg = round(sum(scores) / len(scores), 1) if scores else 0
    at_risk    = [i for i in institutions if i["overall_score"] < 60]
    compliant  = [i for i in institutions if i["overall_score"] >= 80]

    return {
        "report_type": "SupTech Sector Compliance Report",
        "generated_by": "WeGoComply",
        "as_of": datetime.now().isoformat(),
        "frameworks_monitored": ["CBN AML/CFT Rules", "CBN KYC Guidelines",
                                  "FIRS TIN Mandate", "NITDA Reporting Requirements"],
        "summary": {
            "total_institutions": len(institutions),
            "sector_average_score": sector_avg,
            "compliant_count": len(compliant),
            "at_risk_count": len(at_risk),
            "sector_status": _classify(sector_avg)[0],
        },
        "institutions": institutions,
        "regulator_alerts": _get_regulator_alerts(institutions),
    }


async def get_sector_heatmap() -> dict:
    """
    Sector heatmap — shows compliance risk by industry type.
    Enables NITDA/CBN to identify which sectors need intervention.
    """
    sector_data = {}

    for inst_id, inst in MOCK_INSTITUTIONS.items():
        sector = inst["sector"]
        kyc    = _score_kyc(inst["kyc"])
        aml    = _score_aml(inst["aml"])
        tin    = _score_tin(inst["tin"])
        rep    = _score_reporting(inst["reporting"])
        overall = round(kyc * WEIGHTS["kyc"] + aml * WEIGHTS["aml"] +
                        tin * WEIGHTS["tin"] + rep * WEIGHTS["reporting"], 1)

        if sector not in sector_data:
            sector_data[sector] = {"scores": [], "institutions": []}
        sector_data[sector]["scores"].append(overall)
        sector_data[sector]["institutions"].append(inst["name"])

    heatmap = []
    for sector, data in sector_data.items():
        avg = round(sum(data["scores"]) / len(data["scores"]), 1)
        status, color = _classify(avg)
        heatmap.append({
            "sector": sector,
            "average_score": avg,
            "status": status,
            "color": color,
            "institution_count": len(data["institutions"]),
            "institutions": data["institutions"],
            "risk_level": "HIGH" if avg < 60 else "MEDIUM" if avg < 80 else "LOW"
        })

    heatmap.sort(key=lambda x: x["average_score"])

    return {
        "report_type": "Sector Compliance Heatmap",
        "as_of": datetime.now().isoformat(),
        "sectors": heatmap
    }


# ---------------------------------------------------------------------------
# Scoring functions — each maps raw data to 0-100 score
# ---------------------------------------------------------------------------

def _score_kyc(d: dict) -> float:
    total = d["total_customers"]
    if total == 0:
        return 0.0

    # Base: average of NIN, BVN, face verification rates
    nin_rate  = d["nin_verified"]  / total
    bvn_rate  = d["bvn_verified"]  / total
    face_rate = d["face_verified"] / total
    base = ((nin_rate + bvn_rate + face_rate) / 3) * 100

    # Penalty: unreviewed HIGH risk customers
    penalty = min(d["high_risk_unreviewed"] * 2, 20)

    return round(max(base - penalty, 0), 1)


def _score_aml(d: dict) -> float:
    total_tx = d["total_transactions_today"]
    if total_tx == 0:
        return 0.0

    # Component 1: real-time monitoring coverage (40%)
    monitoring_rate = (d["monitored_realtime"] / total_tx) * 100

    # Component 2: flagged transaction review rate (30%)
    flagged = d["flagged_today"]
    review_rate = (d["reviewed_within_24hrs"] / flagged * 100) if flagged > 0 else 100

    # Component 3: STR filing timeliness (30%)
    strs = d["strs_required"]
    str_rate = (d["strs_filed_on_time"] / strs * 100) if strs > 0 else 100

    base = (monitoring_rate * 0.4) + (review_rate * 0.3) + (str_rate * 0.3)

    # Hard penalty: late STRs (CBN requires within 24hrs)
    penalty = d["strs_filed_late"] * 5

    return round(max(base - penalty, 0), 1)


def _score_tin(d: dict) -> float:
    total = d["total_customers"]
    if total == 0:
        return 0.0

    base = (d["tin_verified"] / total) * 100

    # Penalty: restricted accounts
    restriction_rate = d["accounts_restricted"] / total
    penalty = restriction_rate * 50  # Heavy penalty for restricted accounts

    # Deadline penalty
    if d["days_to_deadline"] < 0:
        penalty += 10  # Deadline passed

    return round(max(base - penalty, 0), 1)


def _score_reporting(d: dict) -> float:
    total = d["total_required_actions"]
    if total == 0:
        return 100.0

    base = (d["completed_actions"] / total) * 100

    # Hard penalty: missed deadlines
    penalty = d["missed_deadlines"] * 15

    return round(max(base - penalty, 0), 1)


# ---------------------------------------------------------------------------
# Detail builders
# ---------------------------------------------------------------------------

def _kyc_details(d: dict) -> dict:
    total = d["total_customers"]
    return {
        "total_customers": total,
        "nin_verified": d["nin_verified"],
        "nin_rate": f"{d['nin_verified']/total*100:.1f}%",
        "bvn_verified": d["bvn_verified"],
        "bvn_rate": f"{d['bvn_verified']/total*100:.1f}%",
        "face_verified": d["face_verified"],
        "face_rate": f"{d['face_verified']/total*100:.1f}%",
        "high_risk_unreviewed": d["high_risk_unreviewed"],
        "avg_onboarding_minutes": d["avg_onboarding_minutes"],
    }


def _aml_details(d: dict) -> dict:
    flagged = d["flagged_today"]
    strs    = d["strs_required"]
    return {
        "total_transactions_today": d["total_transactions_today"],
        "monitored_realtime": d["monitored_realtime"],
        "monitoring_coverage": f"{d['monitored_realtime']/d['total_transactions_today']*100:.1f}%",
        "flagged_today": flagged,
        "reviewed_within_24hrs": d["reviewed_within_24hrs"],
        "review_rate": f"{d['reviewed_within_24hrs']/flagged*100:.1f}%" if flagged else "N/A",
        "strs_required": strs,
        "strs_filed_on_time": d["strs_filed_on_time"],
        "strs_filed_late": d["strs_filed_late"],
        "str_timeliness": f"{d['strs_filed_on_time']/strs*100:.1f}%" if strs else "N/A",
    }


def _tin_details(d: dict) -> dict:
    total = d["total_customers"]
    return {
        "total_customers": total,
        "tin_verified": d["tin_verified"],
        "tin_rate": f"{d['tin_verified']/total*100:.1f}%",
        "accounts_restricted": d["accounts_restricted"],
        "restriction_rate": f"{d['accounts_restricted']/total*100:.2f}%",
        "days_to_deadline": d["days_to_deadline"],
        "deadline_status": "PASSED" if d["days_to_deadline"] <= 0 else f"{d['days_to_deadline']} days remaining",
    }


def _reporting_details(d: dict) -> dict:
    return {
        "total_required_actions": d["total_required_actions"],
        "completed_actions": d["completed_actions"],
        "pending_actions": d["pending_actions"],
        "missed_deadlines": d["missed_deadlines"],
        "completion_rate": f"{d['completed_actions']/d['total_required_actions']*100:.1f}%",
    }


def _get_action_items(inst: dict, kyc: float, aml: float, tin: float, rep: float) -> list:
    """Generate prioritized action items based on scores."""
    items = []

    if kyc < 80:
        items.append({
            "priority": "HIGH",
            "pillar": "KYC",
            "action": f"Verify NIN/BVN for {inst['kyc']['total_customers'] - inst['kyc']['nin_verified']:,} unverified customers",
            "framework": "CBN KYC Guidelines",
            "deadline": "Immediate"
        })
    if inst["kyc"]["high_risk_unreviewed"] > 0:
        items.append({
            "priority": "HIGH",
            "pillar": "KYC",
            "action": f"Review {inst['kyc']['high_risk_unreviewed']} HIGH risk customers within 24 hours",
            "framework": "CBN KYC Guidelines",
            "deadline": "24 hours"
        })
    if aml < 80:
        items.append({
            "priority": "HIGH",
            "pillar": "AML",
            "action": f"Review {inst['aml']['flagged_today'] - inst['aml']['reviewed_within_24hrs']} unreviewed flagged transactions",
            "framework": "CBN AML/CFT Rules",
            "deadline": "24 hours"
        })
    if inst["aml"]["strs_filed_late"] > 0:
        items.append({
            "priority": "CRITICAL",
            "pillar": "AML",
            "action": f"File {inst['aml']['strs_filed_late']} overdue STR(s) with NFIU immediately",
            "framework": "NFIU STR Requirements",
            "deadline": "Immediate"
        })
    if tin < 80:
        items.append({
            "priority": "HIGH",
            "pillar": "TIN",
            "action": f"Verify TIN for {inst['tin']['total_customers'] - inst['tin']['tin_verified']:,} customers to avoid account restrictions",
            "framework": "FIRS TIN Mandate",
            "deadline": "Immediate"
        })
    if rep < 80:
        items.append({
            "priority": "MEDIUM",
            "pillar": "Reporting",
            "action": f"Complete {inst['reporting']['pending_actions']} pending regulatory action items",
            "framework": "NITDA / CBN Reporting",
            "deadline": "This week"
        })

    return sorted(items, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["priority"], 3))


def _get_regulator_alerts(institutions: list) -> list:
    """Generate alerts for CBN/NITDA regulators about at-risk institutions."""
    alerts = []
    for inst in institutions:
        if inst["overall_score"] < 60:
            alerts.append({
                "severity": "CRITICAL",
                "institution": inst["name"],
                "score": inst["overall_score"],
                "message": f"{inst['name']} compliance score is critically low ({inst['overall_score']}/100). Immediate regulatory intervention recommended.",
            })
        elif inst["overall_score"] < 75:
            alerts.append({
                "severity": "WARNING",
                "institution": inst["name"],
                "score": inst["overall_score"],
                "message": f"{inst['name']} compliance score is below acceptable threshold ({inst['overall_score']}/100). Follow-up required.",
            })
    return alerts


def _classify(score: float) -> tuple:
    if score >= 80:
        return "COMPLIANT", "green"
    elif score >= 60:
        return "AT RISK", "yellow"
    else:
        return "NON-COMPLIANT", "red"

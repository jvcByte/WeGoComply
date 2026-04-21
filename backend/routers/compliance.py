from fastapi import APIRouter
from services.compliance_service import (
    get_compliance_posture,
    get_suptech_report,
    get_sector_heatmap
)

router = APIRouter()

@router.get("/posture/{institution_id}")
async def compliance_posture(institution_id: str):
    """
    Returns real-time compliance posture score for an institution.
    Covers KYC, AML, TIN, and Reporting pillars.
    Used by institution's compliance dashboard.
    """
    return await get_compliance_posture(institution_id)

@router.get("/suptech/report")
async def suptech_report():
    """
    SupTech endpoint — for CBN/NITDA regulators.
    Returns sector-wide compliance posture across all institutions.
    Replaces manual annual self-reporting with real-time data.
    """
    return await get_suptech_report()

@router.get("/suptech/heatmap")
async def sector_heatmap():
    """
    Sector heatmap — shows which industries carry highest compliance risk.
    Enables proactive regulatory intervention before fines are issued.
    """
    return await get_sector_heatmap()

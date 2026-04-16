from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List
from services.tax_service import verify_tin, bulk_verify_tin

router = APIRouter()

class TINRecord(BaseModel):
    customer_id: str
    name: str
    tin: str

class BulkTINRequest(BaseModel):
    records: List[TINRecord]

@router.post("/verify-tin")
async def verify_single_tin(record: TINRecord):
    """Verify a single TIN against FIRS system."""
    result = await verify_tin(record.tin, record.name)
    return {"customer_id": record.customer_id, **result}

@router.post("/bulk-verify")
async def bulk_tin_verification(request: BulkTINRequest):
    """
    Bulk TIN verification for institutions with large customer bases.
    Returns match rate, failures, and deadline risk assessment.
    """
    results = await bulk_verify_tin(request.records)
    total = len(request.records)
    matched = sum(1 for r in results if r["status"] == "MATCHED")
    return {
        "total": total,
        "matched": matched,
        "failed": total - matched,
        "match_rate": round(matched / total * 100, 2),
        "deadline_risk": "HIGH" if (matched / total) < 0.8 else "LOW",
        "records": results
    }

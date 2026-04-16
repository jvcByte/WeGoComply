from fastapi import APIRouter
from services.regulatory_service import get_latest_updates, summarize_circular

router = APIRouter()

@router.get("/updates")
async def get_regulatory_updates():
    """
    Returns latest regulatory updates from CBN, SEC, FIRS, FCCPC.
    Each update is AI-summarized and tagged with action required.
    """
    updates = await get_latest_updates()
    return {"updates": updates}

@router.post("/summarize")
async def summarize_regulation(payload: dict):
    """
    Takes raw regulatory circular text and returns:
    - Plain English summary
    - Action items for the institution
    - Deadline (if any)
    - Affected operations
    """
    text = payload.get("text", "")
    summary = await summarize_circular(text)
    return summary

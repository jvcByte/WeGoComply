from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.aml_service import analyze_transactions, generate_str

router = APIRouter()

class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    currency: str = "NGN"
    timestamp: str
    transaction_type: str  # transfer, deposit, withdrawal
    counterparty: str
    channel: str  # mobile, web, pos, atm

class TransactionBatch(BaseModel):
    transactions: List[Transaction]

@router.post("/monitor")
async def monitor_transactions(batch: TransactionBatch):
    """
    Run anomaly detection on a batch of transactions.
    Returns flagged transactions with risk scores.
    """
    results = analyze_transactions(batch.transactions)
    return results

@router.post("/generate-str/{transaction_id}")
async def create_str(transaction_id: str, transaction: Transaction):
    """
    Auto-generate a Suspicious Transaction Report (STR)
    in NFIU-compliant format.
    """
    str_report = await generate_str(transaction_id, transaction)
    return str_report

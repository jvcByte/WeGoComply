import os
import numpy as np
from datetime import datetime
from openai import AzureOpenAI
from sklearn.ensemble import IsolationForest

# Train a simple anomaly model on startup with synthetic baseline data
_model = IsolationForest(contamination=0.05, random_state=42)
_baseline = np.array([
    [5000, 8], [10000, 14], [2000, 10], [8000, 11],
    [3000, 9], [15000, 13], [1000, 16], [7000, 10],
    [4500, 12], [6000, 15], [9000, 8], [12000, 11],
])
_model.fit(_baseline)

def analyze_transactions(transactions: list) -> dict:
    flagged = []
    clean = []

    for tx in transactions:
        hour = _extract_hour(tx.timestamp)
        features = np.array([[tx.amount, hour]])
        score = _model.decision_function(features)[0]
        is_anomaly = _model.predict(features)[0] == -1

        # Additional rule-based checks
        rules_triggered = _check_rules(tx)

        if is_anomaly or rules_triggered:
            flagged.append({
                "transaction_id": tx.transaction_id,
                "customer_id": tx.customer_id,
                "amount": tx.amount,
                "timestamp": tx.timestamp,
                "anomaly_score": round(float(score), 4),
                "rules_triggered": rules_triggered,
                "risk_level": "HIGH" if (is_anomaly and rules_triggered) else "MEDIUM",
                "recommended_action": "GENERATE_STR" if is_anomaly else "REVIEW"
            })
        else:
            clean.append(tx.transaction_id)

    return {
        "total_analyzed": len(transactions),
        "flagged_count": len(flagged),
        "clean_count": len(clean),
        "flagged_transactions": flagged
    }

def _check_rules(tx) -> list:
    """CBN-aligned AML rule checks."""
    rules = []
    if tx.amount >= 5_000_000:  # ₦5M threshold
        rules.append("LARGE_CASH_TRANSACTION")
    hour = _extract_hour(tx.timestamp)
    if hour < 5 or hour > 23:
        rules.append("UNUSUAL_HOURS")
    if tx.transaction_type == "transfer" and tx.amount > 1_000_000:
        rules.append("HIGH_VALUE_TRANSFER")
    return rules

def _extract_hour(timestamp: str) -> int:
    try:
        return datetime.fromisoformat(timestamp).hour
    except Exception:
        return 12

async def generate_str(transaction_id: str, transaction) -> dict:
    """Use Azure OpenAI to generate a structured STR in NFIU format."""
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_key=os.getenv("AZURE_OPENAI_KEY", ""),
        api_version="2024-02-01"
    )

    prompt = f"""
You are a compliance officer at a Nigerian financial institution.
Generate a Suspicious Transaction Report (STR) for submission to the NFIU (Nigerian Financial Intelligence Unit).

Transaction details:
- ID: {transaction.transaction_id}
- Customer: {transaction.customer_id}
- Amount: ₦{transaction.amount:,.2f}
- Type: {transaction.transaction_type}
- Counterparty: {transaction.counterparty}
- Channel: {transaction.channel}
- Timestamp: {transaction.timestamp}

Return a JSON object with these fields:
- report_reference: unique reference
- reporting_institution: "ComplianceIQ Demo Bank"
- subject_name: customer ID as placeholder
- transaction_summary: 2-sentence description
- grounds_for_suspicion: specific reasons
- recommended_action: what the institution should do
- report_date: today's date
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception:
        # Demo fallback
        return {
            "report_reference": f"STR-{transaction_id[:8].upper()}",
            "reporting_institution": "ComplianceIQ Demo Bank",
            "subject_name": transaction.customer_id,
            "transaction_summary": f"Customer conducted a {transaction.transaction_type} of ₦{transaction.amount:,.2f} via {transaction.channel} at an unusual time.",
            "grounds_for_suspicion": "Transaction amount exceeds threshold and occurred outside normal banking hours.",
            "recommended_action": "Freeze account pending investigation and file STR with NFIU within 24 hours.",
            "report_date": datetime.now().strftime("%Y-%m-%d")
        }

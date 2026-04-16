import os
from openai import AzureOpenAI
from datetime import datetime

# Mock regulatory updates — in production, scrape CBN/SEC/FIRS websites
MOCK_CIRCULARS = [
    {
        "id": "CBN-2026-AML-001",
        "source": "CBN",
        "title": "Baseline Standards for Automated AML Solutions",
        "date": "2026-03-15",
        "raw_text": "All deposit money banks, microfinance banks, and payment service providers are required to implement real-time or near-real-time automated AML transaction monitoring systems by June 30, 2026. Institutions must file Suspicious Transaction Reports (STRs) within 24 hours of detection.",
        "url": "https://cbn.gov.ng/circulars/2026/aml-baseline"
    },
    {
        "id": "FIRS-2026-TIN-002",
        "source": "FIRS",
        "title": "Mandatory TIN Verification for Financial Accounts",
        "date": "2026-01-10",
        "raw_text": "All financial institutions must verify and match Tax Identification Numbers (TIN) for all existing and new customers. Accounts without verified TINs will be restricted from transactions above ₦500,000 effective April 1, 2026.",
        "url": "https://firs.gov.ng/notices/2026/tin-mandate"
    },
    {
        "id": "FCCPC-2026-DL-003",
        "source": "FCCPC",
        "title": "Digital Lender Registration Deadline",
        "date": "2026-01-05",
        "raw_text": "All digital money lenders must complete registration with the FCCPC by April 30, 2026. Unregistered platforms will be delisted from app stores and payment networks.",
        "url": "https://fccpc.gov.ng/notices/2026/digital-lenders"
    },
]

async def get_latest_updates() -> list:
    """Return AI-summarized regulatory updates."""
    summarized = []
    for circular in MOCK_CIRCULARS:
        summary = await summarize_circular(circular["raw_text"])
        summarized.append({
            "id": circular["id"],
            "source": circular["source"],
            "title": circular["title"],
            "date": circular["date"],
            "url": circular["url"],
            **summary
        })
    return summarized

async def summarize_circular(text: str) -> dict:
    """Use Azure OpenAI to summarize a regulatory circular."""
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_key=os.getenv("AZURE_OPENAI_KEY", ""),
        api_version="2024-02-01"
    )

    prompt = f"""
You are a Nigerian financial compliance expert.
Analyze this regulatory circular and return a JSON object with:
- summary: plain English summary in 2 sentences max
- action_required: what the institution must do (1-2 sentences)
- deadline: deadline date if mentioned, else null
- affected_operations: list of affected business areas (e.g. ["KYC", "AML", "Lending"])
- urgency: one of HIGH, MEDIUM, LOW

Circular text:
{text}
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
            "summary": "New regulatory requirement affecting compliance operations. Immediate action required.",
            "action_required": "Review your current systems and ensure compliance before the stated deadline.",
            "deadline": None,
            "affected_operations": ["AML", "KYC"],
            "urgency": "HIGH"
        }

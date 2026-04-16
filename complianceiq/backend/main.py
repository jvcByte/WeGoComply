from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import kyc, aml, tax, regulatory

app = FastAPI(title="ComplianceIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kyc.router, prefix="/api/kyc", tags=["KYC"])
app.include_router(aml.router, prefix="/api/aml", tags=["AML"])
app.include_router(tax.router, prefix="/api/tax", tags=["Tax"])
app.include_router(regulatory.router, prefix="/api/regulatory", tags=["Regulatory"])

@app.get("/")
def health():
    return {"status": "ComplianceIQ running", "version": "1.0.0"}

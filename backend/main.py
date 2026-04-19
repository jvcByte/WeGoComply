from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.exception_handlers import register_exception_handlers
from routers import aml, kyc, regulatory, tax
from schemas.common import HealthResponse

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(kyc.router, prefix="/api/kyc", tags=["KYC"])
app.include_router(aml.router, prefix="/api/aml", tags=["AML"])
app.include_router(tax.router, prefix="/api/tax", tags=["Tax"])
app.include_router(regulatory.router, prefix="/api/regulatory", tags=["Regulatory"])


@app.on_event("startup")
async def validate_settings() -> None:
    settings.validate_runtime()


@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="WeGoComply running",
        version=settings.app_version,
        mode=settings.mode.value,
    )

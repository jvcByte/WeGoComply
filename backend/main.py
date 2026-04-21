from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.request_context import RequestContextMiddleware
from core.rate_limit import RateLimitMiddleware
from core.config import get_settings
from core.exception_handlers import register_exception_handlers
from dependencies import get_rate_limiter
from routers import aml, auth, compliance, kyc, regulatory, tax, verifyme, nimc_mock
from schemas.common import HealthResponse

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=list(settings.cors_methods),
    allow_headers=list(settings.cors_headers),
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=get_rate_limiter(),
    enabled=settings.rate_limit_enabled,
)

register_exception_handlers(app)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(kyc.router, prefix="/api/kyc", tags=["KYC"])
app.include_router(aml.router, prefix="/api/aml", tags=["AML"])
app.include_router(tax.router, prefix="/api/tax", tags=["Tax"])
app.include_router(regulatory.router, prefix="/api/regulatory", tags=["Regulatory"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance Posture"])
app.include_router(verifyme.router, prefix="/api/verifyme", tags=["VerifyMe"])
app.include_router(nimc_mock.router, prefix="/api/mock/nimc", tags=["NIMC Mock"])


@app.on_event("startup")
async def validate_settings() -> None:
    settings.validate_runtime()
    get_rate_limiter().validate_connection()


@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="WeGoComply running",
        version=settings.app_version,
        mode=settings.mode.value,
    )

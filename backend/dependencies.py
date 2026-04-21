from __future__ import annotations

from functools import lru_cache

from core.config import get_settings
from core.rate_limit import InMemoryRateLimiter, RedisRateLimiter
from repositories.aml_repository import AMLModelRepository
from repositories.audit_repository import AppendOnlyAuditRepository
from repositories.fraud_repository import FraudModelRepository
from repositories.regulatory_repository import RegulatoryCircularRepository
from services.aml_service import AMLService
from services.audit_service import AuditService
from services.compliance_service import ComplianceService
from services.fraud_service import FraudService
from services.kyc_service import KYCService
from services.regulatory_service import RegulatoryService
from services.tax_service import TaxService
from services.verifyme_service import VerifyMeService


@lru_cache
def get_aml_model_repository() -> AMLModelRepository:
    return AMLModelRepository(get_settings().aml_model_path)


@lru_cache
def get_regulatory_repository() -> RegulatoryCircularRepository:
    return RegulatoryCircularRepository()


@lru_cache
def get_audit_repository() -> AppendOnlyAuditRepository:
    return AppendOnlyAuditRepository(get_settings().audit_log_path)


@lru_cache
def get_audit_service() -> AuditService:
    return AuditService(get_audit_repository())


@lru_cache
def get_rate_limiter():
    settings = get_settings()
    if settings.redis_url:
        return RedisRateLimiter(
            settings.redis_url,
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        )
    return InMemoryRateLimiter(
        settings.rate_limit_requests,
        settings.rate_limit_window_seconds,
    )


@lru_cache
def get_kyc_service() -> KYCService:
    return KYCService(get_settings())


@lru_cache
def get_aml_service() -> AMLService:
    return AMLService(get_settings(), get_aml_model_repository())


@lru_cache
def get_tax_service() -> TaxService:
    return TaxService(get_settings())


@lru_cache
def get_regulatory_service() -> RegulatoryService:
    return RegulatoryService(get_settings(), get_regulatory_repository())


@lru_cache
def get_compliance_service() -> ComplianceService:
    return ComplianceService()


@lru_cache
def get_verifyme_service() -> VerifyMeService:
    return VerifyMeService(get_settings())


@lru_cache
def get_fraud_model_repository() -> FraudModelRepository:
    settings = get_settings()
    model_path = str(settings.fraud_model_path) if settings.fraud_model_path else None
    return FraudModelRepository(model_path)


@lru_cache
def get_fraud_service() -> FraudService:
    return FraudService(get_settings(), get_fraud_model_repository())

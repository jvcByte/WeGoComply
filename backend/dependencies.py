from __future__ import annotations

from functools import lru_cache

from core.config import Settings, get_settings
from repositories.aml_repository import AMLModelRepository
from repositories.regulatory_repository import RegulatoryCircularRepository
from services.aml_service import AMLService
from services.kyc_service import KYCService
from services.regulatory_service import RegulatoryService
from services.tax_service import TaxService


@lru_cache
def get_aml_model_repository() -> AMLModelRepository:
    return AMLModelRepository(get_settings().aml_model_path)


@lru_cache
def get_regulatory_repository() -> RegulatoryCircularRepository:
    return RegulatoryCircularRepository()


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

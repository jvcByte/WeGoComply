from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from schemas.common import BaseSchema


class PillarScore(BaseSchema):
    """Individual compliance pillar score"""
    pillar_name: Literal["KYC", "AML", "TIN", "Reporting"]
    score: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    last_updated: datetime
    penalties_applied: list[str] = Field(default_factory=list)


class KYCMetrics(BaseSchema):
    """KYC compliance metrics"""
    total_customers: int = Field(..., ge=0)
    verified_nin_customers: int = Field(..., ge=0)
    verified_bvn_customers: int = Field(..., ge=0)
    face_match_customers: int = Field(..., ge=0)
    high_risk_customers_reviewed_24h: int = Field(..., ge=0)
    high_risk_customers_total: int = Field(..., ge=0)
    average_onboarding_time_minutes: float = Field(..., ge=0.0)

    @property
    def verified_customers_percentage(self) -> float:
        """Percentage of customers with complete KYC verification"""
        if self.total_customers == 0:
            return 0.0
        return (min(self.verified_nin_customers, self.verified_bvn_customers, self.face_match_customers) / self.total_customers) * 100

    @property
    def high_risk_review_penalty(self) -> float:
        """Penalty for unreviewed high-risk customers"""
        unreviewed_high_risk = self.high_risk_customers_total - self.high_risk_customers_reviewed_24h
        return unreviewed_high_risk * 10.0  # -10 points per unreviewed high-risk customer


class AMLEMetrics(BaseSchema):
    """AML compliance metrics"""
    total_transactions: int = Field(..., ge=0)
    monitored_transactions: int = Field(..., ge=0)
    flagged_transactions: int = Field(..., ge=0)
    flagged_reviewed_24h: int = Field(..., ge=0)
    str_filed_total: int = Field(..., ge=0)
    str_filed_on_time: int = Field(..., ge=0)
    false_negative_count: int = Field(..., ge=0)

    @property
    def monitoring_coverage(self) -> float:
        """Percentage of transactions monitored in real-time"""
        if self.total_transactions == 0:
            return 100.0
        return (self.monitored_transactions / self.total_transactions) * 100

    @property
    def flagged_review_rate(self) -> float:
        """Percentage of flagged transactions reviewed within 24h"""
        if self.flagged_transactions == 0:
            return 100.0
        return (self.flagged_reviewed_24h / self.flagged_transactions) * 100

    @property
    def str_timeliness_rate(self) -> float:
        """Percentage of STRs filed within 24hrs"""
        if self.str_filed_total == 0:
            return 100.0
        return (self.str_filed_on_time / self.str_filed_total) * 100

    @property
    def late_str_penalty(self) -> float:
        """Penalty for late STR filings"""
        late_strs = self.str_filed_total - self.str_filed_on_time
        return late_strs * 20.0  # -20 points per late STR


class TINMetrics(BaseSchema):
    """TIN compliance metrics"""
    total_customers: int = Field(..., ge=0)
    verified_tin_customers: int = Field(..., ge=0)
    accounts_restricted_missing_tin: int = Field(..., ge=0)
    days_until_firs_deadline: int = Field(..., ge=0)

    @property
    def tin_verification_rate(self) -> float:
        """Percentage of customers with verified TIN"""
        if self.total_customers == 0:
            return 0.0
        return (self.verified_tin_customers / self.total_customers) * 100

    @property
    def restricted_accounts_penalty(self) -> float:
        """Penalty for restricted accounts"""
        restricted_percentage = (self.accounts_restricted_missing_tin / self.total_customers) * 100 if self.total_customers > 0 else 0
        return restricted_percentage * 5.0  # -5 points per 1% of restricted accounts


class ReportingMetrics(BaseSchema):
    """Regulatory reporting compliance metrics"""
    total_required_actions: int = Field(..., ge=0)
    completed_actions: int = Field(..., ge=0)
    regulatory_updates_acknowledged: int = Field(..., ge=0)
    total_regulatory_updates: int = Field(..., ge=0)
    missed_deadlines: int = Field(..., ge=0)

    @property
    def action_completion_rate(self) -> float:
        """Percentage of required actions completed"""
        if self.total_required_actions == 0:
            return 100.0
        return (self.completed_actions / self.total_required_actions) * 100

    @property
    def missed_deadline_penalty(self) -> float:
        """Penalty for missed deadlines"""
        return self.missed_deadlines * 15.0  # -15 points per missed deadline


class CompliancePostureScore(BaseSchema):
    """Overall compliance posture score"""
    overall_score: float = Field(..., ge=0.0, le=100.0)
    kyc_score: PillarScore
    aml_score: PillarScore
    tin_score: PillarScore
    reporting_score: PillarScore
    last_calculated: datetime
    compliance_level: Literal["EXCELLENT", "GOOD", "FAIR", "POOR", "CRITICAL"]

    @classmethod
    def calculate_compliance_level(cls, score: float) -> Literal["EXCELLENT", "GOOD", "FAIR", "POOR", "CRITICAL"]:
        """Determine compliance level based on score"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "FAIR"
        elif score >= 40:
            return "POOR"
        else:
            return "CRITICAL"


class ComplianceScoreRequest(BaseSchema):
    """Request to calculate compliance scores"""
    kyc_metrics: KYCMetrics
    aml_metrics: AMLEMetrics
    tin_metrics: TINMetrics
    reporting_metrics: ReportingMetrics


class ComplianceScoreResponse(BaseSchema):
    """Response with calculated compliance scores"""
    compliance_posture: CompliancePostureScore
    pillar_breakdown: dict[str, dict]
    recommendations: list[str]
    critical_issues: list[str]

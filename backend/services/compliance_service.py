from __future__ import annotations

from datetime import datetime
from typing import Any

from schemas.compliance import (
    AMLEMetrics,
    CompliancePostureScore,
    ComplianceScoreRequest,
    ComplianceScoreResponse,
    KYCMetrics,
    PillarScore,
    ReportingMetrics,
    TINMetrics,
)


class ComplianceService:
    """Service for calculating 4-pillar compliance scores"""

    def __init__(self) -> None:
        pass

    def calculate_kyc_score(self, metrics: KYCMetrics) -> PillarScore:
        """Calculate KYC compliance score (30% weight)"""
        base_score = metrics.verified_customers_percentage
        
        # Apply penalties
        total_penalty = metrics.high_risk_review_penalty
        final_score = max(0.0, base_score - total_penalty)
        
        return PillarScore(
            pillar_name="KYC",
            score=final_score,
            weight=0.30,
            last_updated=datetime.now(),
            penalties_applied=[f"-{metrics.high_risk_review_penalty:.1f} points for {metrics.high_risk_customers_total - metrics.high_risk_customers_reviewed_24h} unreviewed HIGH risk customers"] if total_penalty > 0 else []
        )

    def calculate_aml_score(self, metrics: AMLEMetrics) -> PillarScore:
        """Calculate AML compliance score (35% weight)"""
        # CBN requirement: 50% for timely review, 50% for timely STR filing
        review_component = metrics.flagged_review_rate * 0.5
        str_component = metrics.str_timeliness_rate * 0.5
        base_score = review_component + str_component
        
        # Apply penalties
        total_penalty = metrics.late_str_penalty
        final_score = max(0.0, base_score - total_penalty)
        
        return PillarScore(
            pillar_name="AML",
            score=final_score,
            weight=0.35,
            last_updated=datetime.now(),
            penalties_applied=[f"-{total_penalty:.1f} points for {metrics.str_filed_total - metrics.str_filed_on_time} late STR filings"] if total_penalty > 0 else []
        )

    def calculate_tin_score(self, metrics: TINMetrics) -> PillarScore:
        """Calculate TIN compliance score (20% weight)"""
        base_score = metrics.tin_verification_rate
        
        # Apply penalties
        total_penalty = metrics.restricted_accounts_penalty
        final_score = max(0.0, base_score - total_penalty)
        
        return PillarScore(
            pillar_name="TIN",
            score=final_score,
            weight=0.20,
            last_updated=datetime.now(),
            penalties_applied=[f"-{total_penalty:.1f} points for {metrics.accounts_restricted_missing_tin} restricted accounts"] if total_penalty > 0 else []
        )

    def calculate_reporting_score(self, metrics: ReportingMetrics) -> PillarScore:
        """Calculate Regulatory Reporting compliance score (15% weight)"""
        base_score = metrics.action_completion_rate
        
        # Apply penalties
        total_penalty = metrics.missed_deadline_penalty
        final_score = max(0.0, base_score - total_penalty)
        
        return PillarScore(
            pillar_name="Reporting",
            score=final_score,
            weight=0.15,
            last_updated=datetime.now(),
            penalties_applied=[f"-{total_penalty:.1f} points for {metrics.missed_deadlines} missed deadlines"] if total_penalty > 0 else []
        )

    def calculate_overall_score(self, request: ComplianceScoreRequest) -> ComplianceScoreResponse:
        """Calculate overall compliance posture score"""
        # Calculate individual pillar scores
        kyc_score = self.calculate_kyc_score(request.kyc_metrics)
        aml_score = self.calculate_aml_score(request.aml_metrics)
        tin_score = self.calculate_tin_score(request.tin_metrics)
        reporting_score = self.calculate_reporting_score(request.reporting_metrics)

        # Calculate weighted overall score
        overall_score = (
            kyc_score.score * kyc_score.weight +
            aml_score.score * aml_score.weight +
            tin_score.score * tin_score.weight +
            reporting_score.score * reporting_score.weight
        )

        # Create compliance posture
        compliance_posture = CompliancePostureScore(
            overall_score=overall_score,
            kyc_score=kyc_score,
            aml_score=aml_score,
            tin_score=tin_score,
            reporting_score=reporting_score,
            last_calculated=datetime.now(),
            compliance_level=CompliancePostureScore.calculate_compliance_level(overall_score)
        )

        # Generate recommendations and critical issues
        recommendations = self._generate_recommendations(request, compliance_posture)
        critical_issues = self._identify_critical_issues(request, compliance_posture)

        # Create pillar breakdown for frontend
        pillar_breakdown = {
            "KYC": {
                "score": kyc_score.score,
                "weight": f"{kyc_score.weight * 100:.0f}%",
                "status": self._get_pillar_status(kyc_score.score),
                "metrics": {
                    "verified_customers_percentage": request.kyc_metrics.verified_customers_percentage,
                    "high_risk_review_penalty": request.kyc_metrics.high_risk_review_penalty,
                    "average_onboarding_time_minutes": request.kyc_metrics.average_onboarding_time_minutes
                }
            },
            "AML": {
                "score": aml_score.score,
                "weight": f"{aml_score.weight * 100:.0f}%",
                "status": self._get_pillar_status(aml_score.score),
                "metrics": {
                    "monitoring_coverage": request.aml_metrics.monitoring_coverage,
                    "flagged_review_rate": request.aml_metrics.flagged_review_rate,
                    "str_timeliness_rate": request.aml_metrics.str_timeliness_rate,
                    "late_str_penalty": request.aml_metrics.late_str_penalty
                }
            },
            "TIN": {
                "score": tin_score.score,
                "weight": f"{tin_score.weight * 100:.0f}%",
                "status": self._get_pillar_status(tin_score.score),
                "metrics": {
                    "tin_verification_rate": request.tin_metrics.tin_verification_rate,
                    "days_until_firs_deadline": request.tin_metrics.days_until_firs_deadline,
                    "restricted_accounts_penalty": request.tin_metrics.restricted_accounts_penalty
                }
            },
            "Reporting": {
                "score": reporting_score.score,
                "weight": f"{reporting_score.weight * 100:.0f}%",
                "status": self._get_pillar_status(reporting_score.score),
                "metrics": {
                    "action_completion_rate": request.reporting_metrics.action_completion_rate,
                    "missed_deadline_penalty": request.reporting_metrics.missed_deadline_penalty
                }
            }
        }

        return ComplianceScoreResponse(
            compliance_posture=compliance_posture,
            pillar_breakdown=pillar_breakdown,
            recommendations=recommendations,
            critical_issues=critical_issues
        )

    def _get_pillar_status(self, score: float) -> str:
        """Get status label for pillar score"""
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

    def _generate_recommendations(self, request: ComplianceScoreRequest, posture: CompliancePostureScore) -> list[str]:
        """Generate actionable recommendations based on compliance scores"""
        recommendations = []

        # KYC recommendations
        if posture.kyc_score.score < 75:
            if request.kyc_metrics.verified_customers_percentage < 90:
                recommendations.append("Increase KYC verification rate by implementing automated document verification")
            if request.kyc_metrics.high_risk_review_penalty > 0:
                recommendations.append("Review all HIGH risk customers within 24 hours to avoid penalties")
            if request.kyc_metrics.average_onboarding_time_minutes > 5:
                recommendations.append("Optimize KYC process to reduce onboarding time below 5 minutes")

        # AML recommendations
        if posture.aml_score.score < 75:
            if request.aml_metrics.monitoring_coverage < 95:
                recommendations.append("Implement real-time transaction monitoring for 100% coverage")
            if request.aml_metrics.flagged_review_rate < 90:
                recommendations.append("Establish 24/7 monitoring team to review flagged transactions within CBN's 24-hour requirement")
            if request.aml_metrics.late_str_penalty > 0:
                recommendations.append("Automate STR generation and filing to meet NFIU 24-hour deadline")

        # TIN recommendations
        if posture.tin_score.score < 75:
            if request.tin_metrics.tin_verification_rate < 90:
                recommendations.append("Launch bulk TIN verification campaign before FIRS deadline")
            if request.tin_metrics.days_until_firs_deadline < 30:
                recommendations.append("URGENT: Complete TIN verification before FIRS sanctions take effect")

        # Reporting recommendations
        if posture.reporting_score.score < 75:
            if request.reporting_metrics.action_completion_rate < 90:
                recommendations.append("Implement compliance task tracking system with deadline reminders")
            if request.reporting_metrics.missed_deadline_penalty > 0:
                recommendations.append("Assign dedicated compliance officer for regulatory reporting")

        return recommendations

    def _identify_critical_issues(self, request: ComplianceScoreRequest, posture: CompliancePostureScore) -> list[str]:
        """Identify critical compliance issues requiring immediate attention"""
        critical_issues = []

        # Critical KYC issues
        if request.kyc_metrics.verified_customers_percentage < 50:
            critical_issues.append("CRITICAL: Less than 50% of customers have complete KYC verification")
        if request.kyc_metrics.high_risk_review_penalty > 50:
            critical_issues.append("CRITICAL: Multiple HIGH risk customers unreviewed - immediate regulatory risk")

        # Critical AML issues
        if request.aml_metrics.monitoring_coverage < 80:
            critical_issues.append("CRITICAL: Inadequate transaction monitoring coverage")
        if request.aml_metrics.late_str_penalty > 100:
            critical_issues.append("CRITICAL: Multiple late STR filings - NFIU sanctions likely")

        # Critical TIN issues
        if request.tin_metrics.days_until_firs_deadline < 7:
            critical_issues.append("CRITICAL: FIRS deadline within 7 days - account restrictions imminent")
        if request.tin_metrics.restricted_accounts_penalty > 25:
            critical_issues.append("CRITICAL: High percentage of accounts restricted due to missing TIN")

        # Critical Reporting issues
        if request.reporting_metrics.missed_deadline_penalty > 50:
            critical_issues.append("CRITICAL: Multiple missed regulatory deadlines")

        return critical_issues

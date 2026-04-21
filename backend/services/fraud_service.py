from __future__ import annotations

from typing import Any

from core.config import Settings
from core.errors import ExternalServiceError
from repositories.fraud_repository import FraudModelRepository


class FraudService:
    def __init__(self, settings: Settings, fraud_repository: FraudModelRepository) -> None:
        self.settings = settings
        self.fraud_repository = fraud_repository

    def analyze_transactions(self, transactions: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.fraud_repository.is_model_available():
            raise ExternalServiceError(
                "Fraud detection model is not available. "
                "Run: python ml/train_fraud_model_synthetic.py",
                code="FRAUD_MODEL_NOT_FOUND",
            )
        try:
            service = self.fraud_repository.get_service()
            results_df = service.predict_records(transactions)
            results = results_df.to_dict(orient="records")
            high_risk = sum(1 for r in results if r["risk_band"] == "High Risk")
            review    = sum(1 for r in results if r["risk_band"] == "Review")
            watch     = sum(1 for r in results if r["risk_band"] == "Watch")
            low_risk  = sum(1 for r in results if r["risk_band"] == "Low Risk")
            return {
                "total_analyzed":        len(results),
                "high_risk_count":       high_risk,
                "review_count":          review,
                "watch_count":           watch,
                "low_risk_count":        low_risk,
                "fraud_predicted_count": sum(1 for r in results if r["predicted_is_fraud"] == 1),
                "transactions":          results,
                "model_available":       True,
            }
        except ExternalServiceError:
            raise
        except Exception as exc:
            raise ExternalServiceError(
                "Failed to analyze transactions.",
                code="FRAUD_DETECTION_FAILED",
            ) from exc

    def explain_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
        if not self.fraud_repository.is_model_available():
            raise ExternalServiceError(
                "Fraud detection model is not available. "
                "Run: python ml/train_fraud_model_synthetic.py",
                code="FRAUD_MODEL_NOT_FOUND",
            )
        try:
            service = self.fraud_repository.get_service()
            reasons = service.explain_prediction(transaction)
            return {
                "transaction_id": transaction.get("transaction_id", "unknown"),
                "risk_factors":   reasons,
            }
        except ExternalServiceError:
            raise
        except Exception as exc:
            raise ExternalServiceError(
                "Failed to explain transaction risk.",
                code="FRAUD_EXPLANATION_FAILED",
            ) from exc

    def get_model_info(self) -> dict[str, Any]:
        if not self.fraud_repository.is_model_available():
            return {
                "model_available":  False,
                "message":          "No trained model found.",
                "recommendation":   "Run: python ml/train_fraud_model_synthetic.py",
            }
        try:
            bundle = self.fraud_repository.get_bundle()
            return {
                "model_available": True,
                "model_version":   bundle["artifact_version"],
                "classifier":      bundle["metrics"]["classifier_name"],
                "metrics": {
                    "roc_auc":           bundle["metrics"]["roc_auc"],
                    "average_precision": bundle["metrics"]["average_precision"],
                    "f2_score":          bundle["metrics"]["best_f2"],
                    "threshold":         bundle["metrics"]["threshold"],
                },
                "training_info": {
                    "training_rows": bundle["metrics"]["training_rows"],
                    "test_rows":     bundle["metrics"]["test_rows"],
                    "feature_count": bundle["metrics"]["feature_count"],
                },
                "dataset_summary": bundle["dataset_summary"],
            }
        except Exception as exc:
            raise ExternalServiceError(
                "Failed to retrieve model information.",
                code="FRAUD_MODEL_INFO_FAILED",
            ) from exc

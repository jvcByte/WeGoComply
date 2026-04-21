from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    fbeta_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None

MODEL_ARTIFACT_VERSION = 1
RANDOM_STATE = 42
DATASET_SLUG = "sriharshaeedala/financial-fraud-detection-dataset"
DATASET_FILENAME = "Synthetic_Financial_datasets_log.csv"
ARTIFACT_PATH = Path("artifacts") / "fraud_dashboard_model.joblib"

TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

INPUT_COLUMNS = [
    "step", "type", "amount",
    "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
    "isFlaggedFraud",
]

DATASET_COLUMNS = (
    INPUT_COLUMNS[:2] + ["nameOrig"] + INPUT_COLUMNS[2:5]
    + ["nameDest"] + INPUT_COLUMNS[5:] + ["isFraud"]
)


class FraudDetectionService:
    def __init__(
        self,
        artifact_path: str | Path = ARTIFACT_PATH,
        random_state: int = RANDOM_STATE,
    ):
        self.artifact_path = Path(artifact_path)
        self.random_state = random_state
        self.bundle: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Dataset resolution
    # ------------------------------------------------------------------

    def resolve_dataset_path(self, explicit_path: str | None = None) -> Path:
        candidates: list[Path] = []
        if explicit_path:
            candidates.append(Path(explicit_path).expanduser())
        env_path = os.getenv("FRAUD_DATA_PATH")
        if env_path:
            candidates.append(Path(env_path).expanduser())
        candidates.append(
            Path.home()
            / ".cache" / "kagglehub" / "datasets"
            / "sriharshaeedala" / "financial-fraud-detection-dataset"
            / "versions" / "1" / DATASET_FILENAME
        )
        for c in candidates:
            if c.exists():
                return c
        try:
            import kagglehub
            dataset_dir = Path(kagglehub.dataset_download(DATASET_SLUG))
            dataset_path = dataset_dir / DATASET_FILENAME
            if dataset_path.exists():
                return dataset_path
        except Exception as exc:
            raise FileNotFoundError(
                "Could not find the fraud dataset. Set FRAUD_DATA_PATH or use synthetic training."
            ) from exc
        raise FileNotFoundError(
            "Could not find the fraud dataset. Set FRAUD_DATA_PATH or use synthetic training."
        )

    # ------------------------------------------------------------------
    # Load / train
    # ------------------------------------------------------------------

    def load_or_train(
        self, force_retrain: bool = False, dataset_path: str | None = None
    ) -> dict[str, Any]:
        if self.bundle is not None and not force_retrain:
            return self.bundle
        if not force_retrain and self.artifact_path.exists():
            bundle = joblib.load(self.artifact_path)
            if bundle.get("artifact_version") == MODEL_ARTIFACT_VERSION:
                self.bundle = bundle
                return bundle
        bundle = self.train(dataset_path=dataset_path)
        self.bundle = bundle
        return bundle

    def train(self, dataset_path: str | None = None) -> dict[str, Any]:
        source_path = self.resolve_dataset_path(dataset_path)
        sampled_df, summary = self._sample_training_data(source_path)
        sampled_df = sampled_df.sample(frac=1.0, random_state=self.random_state).reset_index(drop=True)

        feature_frame = self._build_feature_frame(sampled_df, feature_columns=None)
        feature_columns = list(feature_frame.columns)
        target = sampled_df["isFraud"].astype(int)

        X_train, X_test, y_train, y_test = train_test_split(
            feature_frame, target, test_size=0.2,
            random_state=self.random_state, stratify=target,
        )

        classifier = self._build_classifier(y_train)
        classifier.fit(X_train, y_train)
        classifier_scores = self._predict_proba(classifier, X_test)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled  = scaler.transform(X_test)

        anomaly_model = IsolationForest(
            n_estimators=150, contamination="auto",
            random_state=self.random_state, n_jobs=-1,
        )
        anomaly_model.fit(X_train_scaled[y_train.to_numpy() == 0])

        train_anomaly_raw = -anomaly_model.score_samples(X_train_scaled)
        anomaly_min = float(train_anomaly_raw.min())
        anomaly_max = float(train_anomaly_raw.max())

        anomaly_scores = self._normalize_scores(
            -anomaly_model.score_samples(X_test_scaled), anomaly_min, anomaly_max
        )
        combined_scores = (classifier_scores + anomaly_scores) / 2.0
        threshold, best_f2 = self._best_threshold(y_test, combined_scores)
        predicted = (combined_scores >= threshold).astype(int)
        confusion = confusion_matrix(y_test, predicted)

        profile = {
            "amount_p95":    float(sampled_df["amount"].quantile(0.95)),
            "amount_p99":    float(sampled_df["amount"].quantile(0.99)),
            "median_amount": float(sampled_df["amount"].median()),
        }
        examples = {
            "fraud": self._clean_example(
                sampled_df[sampled_df["isFraud"] == 1]
                .sample(n=1, random_state=self.random_state).iloc[0].to_dict()
            ),
            "safe": self._clean_example(
                sampled_df[sampled_df["isFraud"] == 0]
                .sample(n=1, random_state=self.random_state).iloc[0].to_dict()
            ),
        }

        bundle: dict[str, Any] = {
            "artifact_version": MODEL_ARTIFACT_VERSION,
            "dataset_path":     str(source_path),
            "classifier":       classifier,
            "anomaly_model":    anomaly_model,
            "anomaly_scaler":   scaler,
            "feature_columns":  feature_columns,
            "threshold":        float(threshold),
            "anomaly_min":      anomaly_min,
            "anomaly_max":      anomaly_max,
            "metrics": {
                "roc_auc":           float(roc_auc_score(y_test, combined_scores)),
                "average_precision": float(average_precision_score(y_test, combined_scores)),
                "best_f2":           float(best_f2),
                "threshold":         float(threshold),
                "training_rows":     int(len(sampled_df)),
                "test_rows":         int(len(y_test)),
                "feature_count":     int(len(feature_columns)),
                "classifier_name":   classifier.__class__.__name__,
                "confusion_matrix":  confusion.tolist(),
            },
            "dataset_summary": summary,
            "profile":         profile,
            "examples":        examples,
        }
        self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(bundle, self.artifact_path)
        return bundle

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_records(self, records: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
        bundle = self.load_or_train()
        original = pd.DataFrame(records).copy()
        prepared = self._prepare_input_frame(original)
        features = self._build_feature_frame(prepared, feature_columns=bundle["feature_columns"])

        classifier_score = self._predict_proba(bundle["classifier"], features)
        anomaly_input    = bundle["anomaly_scaler"].transform(features)
        anomaly_score    = self._normalize_scores(
            -bundle["anomaly_model"].score_samples(anomaly_input),
            bundle["anomaly_min"], bundle["anomaly_max"],
        )
        fraud_risk_score = (classifier_score + anomaly_score) / 2.0

        result = original.copy()
        for col in INPUT_COLUMNS:
            if col not in result.columns:
                result[col] = prepared[col]

        result["classifier_score"]  = np.round(classifier_score, 4)
        result["anomaly_score"]     = np.round(anomaly_score, 4)
        result["fraud_risk_score"]  = np.round(fraud_risk_score, 4)
        result["predicted_is_fraud"] = (fraud_risk_score >= bundle["threshold"]).astype(int)
        result["risk_band"] = [
            self._risk_band(s, bundle["threshold"]) for s in fraud_risk_score
        ]
        return result

    def explain_prediction(self, transaction: dict[str, Any]) -> list[str]:
        bundle  = self.load_or_train()
        profile = bundle["profile"]

        tx_type     = str(transaction.get("type", "")).upper()
        amount      = float(transaction.get("amount", 0))
        old_balance = float(transaction.get("oldbalanceOrg", 0))
        new_balance = float(transaction.get("newbalanceOrig", 0))
        old_dest    = float(transaction.get("oldbalanceDest", 0))
        new_dest    = float(transaction.get("newbalanceDest", 0))
        flagged     = int(float(transaction.get("isFlaggedFraud", 0) or 0))

        reasons: list[str] = []
        if tx_type in {"TRANSFER", "CASH_OUT"}:
            reasons.append("Transfers and cash-outs are the riskiest transaction types in the notebook dataset.")
        if amount >= profile["amount_p95"]:
            reasons.append("The amount is above the 95th percentile of the training sample.")
        if old_balance > 0 and new_balance == 0 and amount >= old_balance * 0.9:
            reasons.append("The sender balance is almost fully drained by this transaction.")
        if old_dest == 0 and new_dest > 0:
            reasons.append("The destination balance jumps from zero immediately after the transfer.")
        if flagged == 1:
            reasons.append("The source system already marked this transaction as flagged fraud.")
        if not reasons:
            reasons.append("No single hard rule dominates; the model score comes from the overall feature pattern.")
        return reasons[:4]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sample_training_data(
        self, dataset_path: Path, nonfraud_ratio: int = 4, chunk_size: int = 250_000
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        class_counts = (
            pd.read_csv(dataset_path, usecols=["isFraud"])["isFraud"]
            .value_counts().to_dict()
        )
        fraud_count    = int(class_counts.get(1, 0))
        nonfraud_count = int(class_counts.get(0, 0))
        total_rows     = fraud_count + nonfraud_count
        if fraud_count == 0:
            raise ValueError("The dataset does not contain any fraud examples.")

        sample_fraction = min(1.0, (fraud_count * nonfraud_ratio) / max(nonfraud_count, 1))
        type_counts: dict[str, int] = {t: 0 for t in TRANSACTION_TYPES}
        sampled_chunks: list[pd.DataFrame] = []
        sampled_rows = 0

        for chunk in pd.read_csv(dataset_path, usecols=DATASET_COLUMNS, chunksize=chunk_size):
            for t, c in chunk["type"].value_counts().to_dict().items():
                type_counts[t] = type_counts.get(t, 0) + int(c)
            fraud_chunk    = chunk[chunk["isFraud"] == 1]
            nonfraud_chunk = chunk[chunk["isFraud"] == 0]
            sampled_nonfraud = (
                nonfraud_chunk if sample_fraction >= 1.0
                else nonfraud_chunk.sample(frac=sample_fraction, random_state=self.random_state)
            )
            sampled_chunk = pd.concat([fraud_chunk, sampled_nonfraud], ignore_index=True)
            sampled_chunks.append(sampled_chunk)
            sampled_rows += len(sampled_chunk)

        sampled_df = pd.concat(sampled_chunks, ignore_index=True)
        summary = {
            "total_rows":    int(total_rows),
            "fraud_count":   int(fraud_count),
            "nonfraud_count": int(nonfraud_count),
            "fraud_rate":    float(fraud_count / total_rows),
            "training_rows": int(len(sampled_df)),
            "type_counts":   {k: int(v) for k, v in type_counts.items() if v},
        }
        return sampled_df, summary

    def _build_classifier(self, y_train: pd.Series):
        pos = int(y_train.sum())
        neg = int(len(y_train) - pos)
        spw = neg / max(pos, 1)
        if XGBClassifier is not None:
            return XGBClassifier(
                n_estimators=180, max_depth=5, learning_rate=0.08,
                subsample=0.9, colsample_bytree=0.9,
                objective="binary:logistic", eval_metric="auc",
                random_state=self.random_state, n_jobs=4,
                scale_pos_weight=spw,
            )
        return HistGradientBoostingClassifier(
            max_depth=6, learning_rate=0.08, max_iter=250,
            random_state=self.random_state,
        )

    def _prepare_input_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        prepared = frame.copy()
        required = [c for c in INPUT_COLUMNS if c != "isFlaggedFraud"]
        missing  = [c for c in required if c not in prepared.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        if "isFlaggedFraud" not in prepared.columns:
            prepared["isFlaggedFraud"] = 0
        prepared["type"] = prepared["type"].astype(str).str.upper().str.strip()
        invalid = sorted(set(prepared["type"]) - set(TRANSACTION_TYPES))
        if invalid:
            raise ValueError(f"Unsupported transaction type(s): {', '.join(invalid)}")
        numeric = [c for c in INPUT_COLUMNS if c != "type"]
        for col in numeric:
            prepared[col] = pd.to_numeric(prepared[col], errors="coerce")
        if prepared[numeric].isnull().any().any():
            raise ValueError("Some numeric inputs are empty or invalid.")
        return prepared[INPUT_COLUMNS].copy()

    def _build_feature_frame(
        self, frame: pd.DataFrame, feature_columns: list[str] | None
    ) -> pd.DataFrame:
        f = frame.copy()
        f["originBalanceDelta"]    = f["oldbalanceOrg"] - f["newbalanceOrig"]
        f["destBalanceDelta"]      = f["newbalanceDest"] - f["oldbalanceDest"]
        f["originBalanceEmptied"]  = ((f["oldbalanceOrg"] > 0) & (f["newbalanceOrig"] == 0)).astype(int)
        f["amountToOriginBalance"] = np.where(f["oldbalanceOrg"] > 0, f["amount"] / f["oldbalanceOrg"], 0.0)
        f["amountToDestBalance"]   = np.where(f["oldbalanceDest"] > 0, f["amount"] / f["oldbalanceDest"], 0.0)
        f["isCashOutOrTransfer"]   = f["type"].isin(["CASH_OUT", "TRANSFER"]).astype(int)
        f = f.drop(columns=[c for c in ["nameOrig", "nameDest", "isFraud"] if c in f.columns], errors="ignore")
        f = pd.get_dummies(f, columns=["type"], prefix="type")
        ordered = sorted(f.columns) if feature_columns is None else feature_columns
        return f.reindex(columns=ordered, fill_value=0.0).astype(float)

    def _predict_proba(self, classifier: Any, features: pd.DataFrame) -> np.ndarray:
        if hasattr(classifier, "predict_proba"):
            return classifier.predict_proba(features)[:, 1]
        return classifier.predict(features)

    def _normalize_scores(self, raw: np.ndarray, minimum: float, maximum: float) -> np.ndarray:
        return np.clip((raw - minimum) / (maximum - minimum + 1e-9), 0.0, 1.0)

    def _best_threshold(self, y_true: pd.Series, scores: np.ndarray) -> tuple[float, float]:
        _, _, thresholds = precision_recall_curve(y_true, scores)
        candidates = np.unique(np.concatenate([thresholds, [0.5]]))
        best_t, best_f2 = 0.5, -1.0
        for t in candidates:
            s = fbeta_score(y_true, (scores >= t).astype(int), beta=2)
            if s > best_f2:
                best_t, best_f2 = float(t), float(s)
        return best_t, best_f2

    def _risk_band(self, score: float, threshold: float) -> str:
        if score >= max(threshold, 0.75): return "High Risk"
        if score >= threshold:            return "Review"
        if score >= threshold * 0.7:      return "Watch"
        return "Low Risk"

    def _clean_example(self, row: dict[str, Any]) -> dict[str, Any]:
        clean = {c: row[c] for c in INPUT_COLUMNS}
        clean["step"]           = int(clean["step"])
        clean["amount"]         = float(clean["amount"])
        clean["oldbalanceOrg"]  = float(clean["oldbalanceOrg"])
        clean["newbalanceOrig"] = float(clean["newbalanceOrig"])
        clean["oldbalanceDest"] = float(clean["oldbalanceDest"])
        clean["newbalanceDest"] = float(clean["newbalanceDest"])
        clean["isFlaggedFraud"] = int(clean["isFlaggedFraud"])
        return clean

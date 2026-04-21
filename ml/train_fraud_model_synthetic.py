"""
Train the fraud detection model using synthetic data (no Kaggle dataset needed).
Run: python ml/train_fraud_model_synthetic.py
"""
from __future__ import annotations

import sys
from pathlib import Path

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
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

RANDOM_STATE = 42
MODEL_ARTIFACT_VERSION = 1
ARTIFACT_PATH = Path(__file__).resolve().parent.parent / "backend" / "artifacts" / "fraud_dashboard_model.joblib"
INPUT_COLUMNS = ["step", "type", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest", "isFlaggedFraud"]
TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


def generate_synthetic_data(n_samples: int = 10_000, fraud_rate: float = 0.05) -> pd.DataFrame:
    print(f"Generating {n_samples:,} synthetic transactions ({fraud_rate:.0%} fraud)...")
    np.random.seed(RANDOM_STATE)
    n_fraud  = int(n_samples * fraud_rate)
    n_normal = n_samples - n_fraud

    normal = []
    for _ in range(n_normal):
        tx_type = np.random.choice(["CASH_IN", "PAYMENT", "DEBIT"], p=[0.5, 0.3, 0.2])
        amount  = np.random.lognormal(10, 2)
        old_bal = np.random.lognormal(12, 2)
        new_bal = old_bal + amount if tx_type == "CASH_IN" else max(0, old_bal - amount)
        normal.append({
            "step": np.random.randint(1, 744), "type": tx_type, "amount": amount,
            "oldbalanceOrg": old_bal, "newbalanceOrig": new_bal,
            "oldbalanceDest": np.random.lognormal(11, 2),
            "newbalanceDest": np.random.lognormal(11, 2),
            "isFlaggedFraud": 0, "isFraud": 0,
        })

    fraud = []
    for _ in range(n_fraud):
        tx_type = np.random.choice(["TRANSFER", "CASH_OUT"], p=[0.6, 0.4])
        amount  = np.random.lognormal(14, 1.5)
        old_bal = amount * np.random.uniform(0.95, 1.05)
        new_bal = max(0, old_bal - amount)
        old_dest = 0 if np.random.random() < 0.7 else np.random.lognormal(10, 1)
        fraud.append({
            "step": np.random.randint(1, 744), "type": tx_type, "amount": amount,
            "oldbalanceOrg": old_bal, "newbalanceOrig": new_bal,
            "oldbalanceDest": old_dest, "newbalanceDest": old_dest + amount,
            "isFlaggedFraud": 1 if np.random.random() < 0.3 else 0, "isFraud": 1,
        })

    df = pd.DataFrame(normal + fraud).sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)
    print(f"  Normal: {n_normal:,}  |  Fraud: {n_fraud:,}")
    return df


def build_features(frame: pd.DataFrame, feature_columns: list[str] | None) -> pd.DataFrame:
    f = frame.copy()
    f["originBalanceDelta"]    = f["oldbalanceOrg"] - f["newbalanceOrig"]
    f["destBalanceDelta"]      = f["newbalanceDest"] - f["oldbalanceDest"]
    f["originBalanceEmptied"]  = ((f["oldbalanceOrg"] > 0) & (f["newbalanceOrig"] == 0)).astype(int)
    f["amountToOriginBalance"] = np.where(f["oldbalanceOrg"] > 0, f["amount"] / f["oldbalanceOrg"], 0.0)
    f["amountToDestBalance"]   = np.where(f["oldbalanceDest"] > 0, f["amount"] / f["oldbalanceDest"], 0.0)
    f["isCashOutOrTransfer"]   = f["type"].isin(["CASH_OUT", "TRANSFER"]).astype(int)
    f = f.drop(columns=["isFraud"], errors="ignore")
    f = pd.get_dummies(f, columns=["type"], prefix="type")
    ordered = sorted(f.columns) if feature_columns is None else feature_columns
    return f.reindex(columns=ordered, fill_value=0.0).astype(float)


def best_threshold(y_true: pd.Series, scores: np.ndarray) -> tuple[float, float]:
    _, _, thresholds = precision_recall_curve(y_true, scores)
    candidates = np.unique(np.concatenate([thresholds, [0.5]]))
    best_t, best_f2 = 0.5, -1.0
    for t in candidates:
        s = fbeta_score(y_true, (scores >= t).astype(int), beta=2)
        if s > best_f2:
            best_t, best_f2 = float(t), float(s)
    return best_t, best_f2


def train():
    print("\n" + "="*65)
    print("FRAUD DETECTION MODEL TRAINING  (synthetic data)")
    print("="*65)

    df = generate_synthetic_data()
    feature_frame   = build_features(df, None)
    feature_columns = list(feature_frame.columns)
    target          = df["isFraud"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        feature_frame, target, test_size=0.2,
        random_state=RANDOM_STATE, stratify=target,
    )
    print(f"\nFeatures: {len(feature_columns)}  |  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # Classifier
    pos, neg = int(y_train.sum()), int(len(y_train) - y_train.sum())
    if HAS_XGBOOST:
        print("Classifier: XGBoost")
        clf = XGBClassifier(
            n_estimators=180, max_depth=5, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9,
            objective="binary:logistic", eval_metric="auc",
            random_state=RANDOM_STATE, n_jobs=4,
            scale_pos_weight=neg / max(pos, 1),
        )
    else:
        print("Classifier: HistGradientBoosting (XGBoost not installed)")
        clf = HistGradientBoostingClassifier(
            max_depth=6, learning_rate=0.08, max_iter=250, random_state=RANDOM_STATE,
        )
    clf.fit(X_train, y_train)
    clf_scores = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else clf.predict(X_test)

    # Anomaly detector
    scaler = StandardScaler()
    Xtr_s  = scaler.fit_transform(X_train)
    Xte_s  = scaler.transform(X_test)
    iso    = IsolationForest(n_estimators=150, contamination="auto", random_state=RANDOM_STATE, n_jobs=-1)
    iso.fit(Xtr_s[y_train.to_numpy() == 0])

    raw_train   = -iso.score_samples(Xtr_s)
    a_min, a_max = float(raw_train.min()), float(raw_train.max())
    ano_scores  = np.clip((-iso.score_samples(Xte_s) - a_min) / (a_max - a_min + 1e-9), 0, 1)

    combined = (clf_scores + ano_scores) / 2.0
    threshold, best_f2 = best_threshold(y_test, combined)
    cm = confusion_matrix(y_test, (combined >= threshold).astype(int))

    bundle = {
        "artifact_version": MODEL_ARTIFACT_VERSION,
        "dataset_path":     "synthetic_data",
        "classifier":       clf,
        "anomaly_model":    iso,
        "anomaly_scaler":   scaler,
        "feature_columns":  feature_columns,
        "threshold":        threshold,
        "anomaly_min":      a_min,
        "anomaly_max":      a_max,
        "metrics": {
            "roc_auc":           float(roc_auc_score(y_test, combined)),
            "average_precision": float(average_precision_score(y_test, combined)),
            "best_f2":           float(best_f2),
            "threshold":         float(threshold),
            "training_rows":     int(len(df)),
            "test_rows":         int(len(y_test)),
            "feature_count":     int(len(feature_columns)),
            "classifier_name":   clf.__class__.__name__,
            "confusion_matrix":  cm.tolist(),
        },
        "dataset_summary": {
            "total_rows":    int(len(df)),
            "fraud_count":   int(df["isFraud"].sum()),
            "nonfraud_count": int((df["isFraud"] == 0).sum()),
            "fraud_rate":    float(df["isFraud"].mean()),
            "training_rows": int(len(df)),
            "type_counts":   df["type"].value_counts().to_dict(),
        },
        "profile": {
            "amount_p95":    float(df["amount"].quantile(0.95)),
            "amount_p99":    float(df["amount"].quantile(0.99)),
            "median_amount": float(df["amount"].median()),
        },
        "examples": {
            "fraud": {c: df[df["isFraud"] == 1].iloc[0][c] for c in INPUT_COLUMNS},
            "safe":  {c: df[df["isFraud"] == 0].iloc[0][c] for c in INPUT_COLUMNS},
        },
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, ARTIFACT_PATH)

    print(f"\nROC-AUC:  {bundle['metrics']['roc_auc']:.4f}")
    print(f"F2 Score: {bundle['metrics']['best_f2']:.4f}")
    print(f"Threshold:{bundle['metrics']['threshold']:.4f}")
    print(f"Confusion: TN={cm[0][0]:,}  FP={cm[0][1]:,}  FN={cm[1][0]:,}  TP={cm[1][1]:,}")
    print(f"\nSaved → {ARTIFACT_PATH}")
    print("="*65)
    print("✅  Model ready. Restart the backend server to load it.")
    print("="*65 + "\n")


if __name__ == "__main__":
    try:
        train()
    except Exception as exc:
        print(f"\n❌  Training failed: {exc}")
        import traceback; traceback.print_exc()
        sys.exit(1)

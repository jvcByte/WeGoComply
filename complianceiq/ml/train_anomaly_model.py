"""
Train and export the AML anomaly detection model.
Run once: python ml/train_anomaly_model.py
"""
import numpy as np
import pickle
from sklearn.ensemble import IsolationForest

# Synthetic baseline of normal Nigerian fintech transactions
# Features: [amount_ngn, hour_of_day]
normal_transactions = np.array([
    [5000, 8], [10000, 14], [2000, 10], [8000, 11],
    [3000, 9], [15000, 13], [1000, 16], [7000, 10],
    [4500, 12], [6000, 15], [9000, 8], [12000, 11],
    [25000, 9], [50000, 14], [100000, 10], [200000, 11],
    [500000, 13], [1000000, 15], [3000, 17], [8000, 18],
    [15000, 19], [5000, 20], [2000, 21], [10000, 22],
])

model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
model.fit(normal_transactions)

with open("ml/aml_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved to ml/aml_model.pkl")

# Quick test
test_cases = [
    ([5000, 10], "Normal transaction"),
    ([7500000, 2], "SUSPICIOUS: Large amount + unusual hour"),
    ([9800000, 3], "SUSPICIOUS: Very large + 3am"),
    ([45000, 14], "Normal: Mid-day transfer"),
]

for features, label in test_cases:
    score = model.decision_function([features])[0]
    prediction = model.predict([features])[0]
    status = "ANOMALY" if prediction == -1 else "CLEAN"
    print(f"{label}: {status} (score: {score:.3f})")

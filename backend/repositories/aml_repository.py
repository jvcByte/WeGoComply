from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest


class AMLModelRepository:
    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self._model: IsolationForest | None = None

    def get_model(self) -> IsolationForest:
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self) -> IsolationForest:
        if self.model_path.exists():
            with self.model_path.open("rb") as model_file:
                return pickle.load(model_file)
        return self._build_default_model()

    @staticmethod
    def _build_default_model() -> IsolationForest:
        baseline = np.array(
            [
                [5000, 8],
                [10000, 14],
                [2000, 10],
                [8000, 11],
                [3000, 9],
                [15000, 13],
                [1000, 16],
                [7000, 10],
                [4500, 12],
                [6000, 15],
                [9000, 8],
                [12000, 11],
            ]
        )
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(baseline)
        return model


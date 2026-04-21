from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ML_DIR = Path(__file__).resolve().parent.parent.parent / "ml"
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

try:
    from fraud_detection_service import FraudDetectionService
    _SERVICE_AVAILABLE = True
except ImportError:
    FraudDetectionService = None  # type: ignore[assignment,misc]
    _SERVICE_AVAILABLE = False


class FraudModelRepository:
    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path
        self._service: Any | None = None

    def get_service(self) -> Any:
        if not _SERVICE_AVAILABLE:
            raise ImportError(
                "FraudDetectionService not available. "
                "Ensure ml/fraud_detection_service.py exists."
            )
        if self._service is None:
            if self.model_path:
                self._service = FraudDetectionService(artifact_path=self.model_path)
            else:
                self._service = FraudDetectionService()
        return self._service

    def get_bundle(self) -> dict[str, Any]:
        return self.get_service().load_or_train()

    def is_model_available(self) -> bool:
        try:
            service = self.get_service()
            return Path(service.artifact_path).exists()
        except Exception:
            return False

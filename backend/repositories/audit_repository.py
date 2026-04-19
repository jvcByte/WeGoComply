from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class AppendOnlyAuditRepository:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self._lock = Lock()
        self._tail_hash = self._load_tail_hash()

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            entry = dict(event)
            entry["previous_hash"] = self._tail_hash
            entry_hash = self._compute_entry_hash(entry)
            entry["entry_hash"] = entry_hash

            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True, default=self._json_default))
                handle.write("\n")

            self._tail_hash = entry_hash
            return entry

    def _compute_entry_hash(self, entry: dict[str, Any]) -> str:
        payload = json.dumps(entry, sort_keys=True, separators=(",", ":"), default=self._json_default)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_tail_hash(self) -> str | None:
        if not self.log_path.exists():
            return None

        tail_hash: str | None = None
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                tail_hash = json.loads(line).get("entry_hash")
        return tail_hash

    @staticmethod
    def _json_default(value: Any) -> str:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return str(value)

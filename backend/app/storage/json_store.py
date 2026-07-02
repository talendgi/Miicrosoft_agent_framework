from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class JsonStore:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._lock = Lock()
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._write({"connections": [], "pipelines": [], "executions": []})

    def read(self) -> dict[str, Any]:
        with self._lock:
            return self._read()

    def write(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._write(payload)

    def _read(self) -> dict[str, Any]:
        with self._file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, payload: dict[str, Any]) -> None:
        with self._file_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)


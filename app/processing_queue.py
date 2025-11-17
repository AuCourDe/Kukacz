#!/usr/bin/env python3
"""
Kolejka przetwarzania plików audio dla interfejsu webowego.
"""
from __future__ import annotations

import math
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _estimate_minutes(size_bytes: int) -> int:
    """Szacuje czas przetwarzania – 1 minuta na każdy pełny megabajt."""
    megabytes = max(size_bytes / (1024 * 1024), 0)
    return max(1, math.ceil(megabytes))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class QueueItem:
    """Reprezentuje pojedyncze zadanie w kolejce przetwarzania."""

    id: str
    filename: str
    size_bytes: int
    input_path: Path
    status: str = "queued"
    created_at: datetime = field(default_factory=_utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    estimated_minutes: int = 1
    result_files: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        size_mb = self.size_bytes / (1024 * 1024) if self.size_bytes else 0.0
        return {
            "id": self.id,
            "filename": self.filename,
            "size_mb": round(size_mb, 2),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "estimated_minutes": self.estimated_minutes,
            "error": self.error,
            "result_files": self.result_files,
        }


class ProcessingQueue:
    """Prosta, jawna kolejka przetwarzania widoczna w interfejsie webowym."""

    def __init__(self) -> None:
        self._items: Dict[str, QueueItem] = {}
        self._order: List[str] = []
        self._lock = threading.Lock()

    def enqueue(self, file_path: Path) -> QueueItem:
        """Dodaje nowy plik do kolejki."""
        size = file_path.stat().st_size if file_path.exists() else 0
        item = QueueItem(
            id=str(uuid.uuid4()),
            filename=file_path.name,
            size_bytes=size,
            input_path=file_path,
            estimated_minutes=_estimate_minutes(size),
        )
        with self._lock:
            self._items[item.id] = item
            self._order.append(item.id)
        return item

    def get_item(self, item_id: str) -> Optional[QueueItem]:
        with self._lock:
            return self._items.get(item_id)

    def mark_processing(self, item_id: str) -> None:
        with self._lock:
            item = self._items.get(item_id)
            if item:
                item.status = "processing"
                item.started_at = _utcnow()
                item.error = None

    def mark_completed(self, item_id: str, result_files: Dict[str, str]) -> None:
        with self._lock:
            item = self._items.get(item_id)
            if item:
                item.status = "completed"
                item.finished_at = _utcnow()
                item.result_files = result_files
                item.error = None

    def mark_failed(self, item_id: str, error_message: str) -> None:
        with self._lock:
            item = self._items.get(item_id)
            if item:
                item.status = "failed"
                item.finished_at = _utcnow()
                item.error = error_message

    def serialize(self) -> List[Dict]:
        with self._lock:
            return [self._items[item_id].to_dict() for item_id in self._order]

    def get_result_file(self, item_id: str, file_type: str) -> Optional[str]:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return None
            return item.result_files.get(file_type)


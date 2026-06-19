from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.resume import ResumeAnalysis

STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "resume_analyses.jsonl"


@dataclass
class LocalResumeRecord:
    id: int
    user_id: str | None
    filename: str
    content_type: str
    s3_key: str | None
    extracted_text: str
    analysis: dict[str, Any]
    created_at: str


def save_local_resume_record(
    *,
    user_id: str | None,
    filename: str,
    content_type: str,
    s3_key: str | None,
    extracted_text: str,
    analysis: ResumeAnalysis,
) -> LocalResumeRecord:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    next_id = _next_id()
    record = LocalResumeRecord(
        id=next_id,
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        s3_key=s3_key,
        extracted_text=extracted_text,
        analysis=analysis.model_dump(mode="json"),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with STORE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.__dict__, ensure_ascii=True) + "\n")
    return record


def load_local_resume_records(limit: int = 500) -> list[LocalResumeRecord]:
    if not STORE_PATH.exists():
        return []

    records: list[LocalResumeRecord] = []
    with STORE_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                records.append(LocalResumeRecord(**payload))
            except (TypeError, json.JSONDecodeError):
                continue
    return sorted(records, key=lambda record: record.created_at, reverse=True)[:limit]


def _next_id() -> int:
    records = load_local_resume_records(limit=100000)
    return (max((record.id for record in records), default=0) + 1)

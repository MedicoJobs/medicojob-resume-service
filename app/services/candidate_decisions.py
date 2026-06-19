from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "candidate_decisions.jsonl"


def save_candidate_decision(candidate_id: int, hospital_id: str | None, status: str, note: str) -> dict:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    decision = {
        "candidate_id": candidate_id,
        "hospital_id": hospital_id,
        "status": status,
        "note": note.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with STORE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=True) + "\n")
    return decision


def latest_candidate_decision(candidate_id: int, hospital_id: str | None) -> dict | None:
    if not STORE_PATH.exists():
        return None

    latest = None
    with STORE_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                decision = json.loads(line)
            except json.JSONDecodeError:
                continue
            if decision.get("candidate_id") == candidate_id and decision.get("hospital_id") == hospital_id:
                latest = decision
    return latest

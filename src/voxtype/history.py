from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .config import data_dir


def history_path() -> Path:
    return data_dir() / "history.jsonl"


def append(text: str, seconds: float, language: str | None) -> None:
    path = history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "time": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        "seconds": round(seconds, 2),
        "language": language,
        "text": text.rstrip(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def recent(limit: int = 20) -> list[dict]:
    path = history_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    records = []
    for line in lines[-limit:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records

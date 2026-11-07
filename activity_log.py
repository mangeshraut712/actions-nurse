"""Privacy-conscious, append-only demo activity logging for Actions Nurse.

The log intentionally stores fingerprints and operational metadata rather than
raw CI logs, prompts, credentials, or a full memory payload. The tracked demo
trace is deliberately append-only: it is evidence of an actual local run.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parent
DEFAULT_TRACE = ROOT / "demo" / "activity" / "trace.jsonl"


def _trace_path() -> Path:
    configured = os.environ.get("NURSE_ACTIVITY_LOG", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_TRACE


def utc_timestamp() -> str:
    """Return an RFC 3339 timestamp that is easy to scan in a demo trace."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def input_fingerprint(value: str) -> dict[str, Any]:
    """Describe received text without retaining it in the activity log."""
    raw = value.encode("utf-8", errors="replace")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "chars": len(value), "bytes": len(raw)}


def append_activity(event: str, **fields: Any) -> dict[str, Any]:
    """Append one JSONL event and return the exact serialisable record.

    The API deliberately does not rotate or rewrite the file: a trace is an
    append-only account of what this local demo actually attempted.
    """
    record: dict[str, Any] = {
        "id": f"act-{uuid4().hex[:12]}",
        "timestamp": utc_timestamp(),
        "event": event,
        **fields,
    }
    path = _trace_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":"), default=str))
        stream.write("\n")
    return record


def latest_activity(limit: int = 20) -> list[dict[str, Any]]:
    """Return recent valid records, tolerating an interrupted or damaged row."""
    safe_limit = max(1, min(int(limit), 100))
    path = _trace_path()
    records: deque[dict[str, Any]] = deque(maxlen=safe_limit)
    try:
        # Decode each row separately so an incomplete UTF-8 sequence or JSON
        # append cannot hide earlier events. Retain only the requested history
        # and leave the append-only evidence file unchanged.
        with path.open("rb") as stream:
            for row in stream:
                try:
                    record = json.loads(row.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if isinstance(record, dict):
                    records.append(record)
    except OSError:
        return []
    return list(records)


def activity_status() -> dict[str, Any]:
    """Small status payload for health checks without exposing event content."""
    path = _trace_path()
    return {"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), "exists": path.is_file()}

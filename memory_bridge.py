"""Small, failure-tolerant Python bridge to the real Meterless H-MEM CLI.

The memory implementation remains in ``meterless/nurse-memory.ts``.  This
module only invokes that CLI and deliberately returns a labelled unavailable
result until the user has run its vendoring setup command.  It never provides a
Python look-alike or silent in-memory substitute.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
METERLESS_DIR = ROOT / "meterless"
VENDORED_ENGINE = METERLESS_DIR / "vendor" / "hmem" / "src" / "index.ts"
LOCAL_TSX = METERLESS_DIR / "node_modules" / ".bin" / "tsx"
MAX_ERROR_CHARS = 240

_TOKEN_PATTERN = re.compile(
    r"\b(?:ghp|github_pat|gho|ghu|ghs)_[A-Za-z0-9_\-]+\b|\b(?:Bearer|token|password|api[_ -]?key)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)


def _redact(value: Any, limit: int = 1_600) -> str:
    """Keep bridge payloads bounded and avoid persisting obvious secret forms."""
    return _TOKEN_PATTERN.sub("[redacted]", str(value or "")).strip()[:limit]


def status() -> dict[str, Any]:
    """Report readiness without attempting a Node process from a health check."""
    missing: list[str] = []
    if not METERLESS_DIR.is_dir():
        missing.append("meterless bridge files")
    if not VENDORED_ENGINE.is_file():
        missing.append("meterless/vendor/hmem (run npm run setup in meterless/)")
    if not LOCAL_TSX.is_file():
        missing.append("meterless/node_modules (run npm install in meterless/)")
    if not shutil.which("npm"):
        missing.append("npm")
    return {
        "ready": not missing,
        "mode": "hmem" if not missing else "setup_required",
        "engine_source": "vendor/hmem" if VENDORED_ENGINE.is_file() else None,
        "missing": missing,
    }


def _bridge_environment() -> dict[str, str]:
    """Pass only runtime essentials to the subprocess rather than app secrets."""
    environment = {"PATH": os.environ.get("PATH", ""), "NO_COLOR": "1"}
    # H-MEM itself allows an isolated persistent store for demo or test runs.
    if os.environ.get("NURSE_HMEM_DIR"):
        environment["NURSE_HMEM_DIR"] = os.environ["NURSE_HMEM_DIR"]
    if os.environ.get("HOME"):
        environment["HOME"] = os.environ["HOME"]
    return environment


def _invoke(
    command: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 12.0,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    ready = status()
    if not ready["ready"]:
        return {"ok": False, **ready}
    try:
        completed = subprocess.run(
            ["npm", "--silent", "run", "memory", "--", command, *(extra_args or []), "--json"],
            cwd=METERLESS_DIR,
            input=json.dumps(payload or {}),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=_bridge_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "mode": "unavailable",
            "engine_source": ready.get("engine_source"),
            "error": "H-MEM bridge timed out or could not start",
            "error_type": type(exc).__name__,
        }

    # npm --silent plus --json should emit one line. Parsing the final JSON line
    # still makes the bridge robust to a package-manager notice on a new npm.
    parsed: dict[str, Any] | None = None
    for line in reversed(completed.stdout.splitlines()):
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            parsed = candidate
            break
    if completed.returncode == 0 and parsed is not None:
        return parsed
    return {
        "ok": False,
        "mode": "unavailable",
        "engine_source": ready.get("engine_source"),
        "error": _redact(completed.stderr or "H-MEM bridge returned no usable JSON", MAX_ERROR_CHARS),
        "returncode": completed.returncode,
    }


def ask(query: str) -> dict[str, Any]:
    """Use H-MEM's MemoryRetrievalService through the real bridge."""
    return _invoke("ask", {"query": _redact(query, 500)})


def remember(diagnosis: dict[str, Any]) -> dict[str, Any]:
    """Use H-MEM's MemoryMiningService after an Actions Nurse diagnosis."""
    safe = {
        "failing_step": _redact(diagnosis.get("failing_step"), 200),
        "root_cause": _redact(diagnosis.get("root_cause"), 800),
        "patterns": [_redact(item, 180) for item in diagnosis.get("patterns", []) if item],
        "fixture": _redact(diagnosis.get("fixture"), 160),
        "provenance": {"fixture": _redact(diagnosis.get("fixture"), 160) or "triage"},
    }
    return _invoke("remember", safe)


def seed() -> dict[str, Any]:
    """Load the deliberately small, tracked CI diagnosis demo set."""
    return _invoke("seed")


def audit(memory_id: str) -> dict[str, Any]:
    """Expose the H-MEM TrustLedgerService for a specific recall ID."""
    return _invoke("audit", {"id": _redact(memory_id, 160)})


def sleep(preview: bool = True) -> dict[str, Any]:
    """Expose H-MEM's preview-first SleepCycleService."""
    # ``--preview`` is the default-safe path in the TypeScript CLI; the payload
    # is intentionally empty because it has no user-controlled text.
    return _invoke("sleep", extra_args=["--preview"] if preview else None)

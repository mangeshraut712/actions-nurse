"""Run an isolated two-pass H-MEM provenance proof for Actions Nurse.

The first Rules-only triage records a diagnosis. The second triage must retrieve
that same memory ID. This is evidence of prior-triage provenance, not evidence
that a proposed repair was applied or that diagnostic accuracy increased.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "npm-typecheck.txt"


def _ids(memory: dict[str, Any], key: str) -> list[str]:
    values = memory.get(key, [])
    return [str(value) for value in values if str(value)] if isinstance(values, list) else []


def run() -> int:
    sys.path.insert(0, str(ROOT))
    from memory_bridge import status as hmem_status

    readiness = hmem_status()
    if not readiness.get("ready"):
        print(json.dumps({
            "ok": False,
            "mode": "setup_required",
            "engine_source": readiness.get("engine_source"),
            "missing": readiness.get("missing", []),
            "notice": "No H-MEM demo was simulated; install the documented local engine before retrying.",
        }, sort_keys=True))
        return 2

    with tempfile.TemporaryDirectory(prefix="actions-nurse-hmem-two-pass-") as state_dir:
        prior = {
            "NURSE_HMEM_DIR": os.environ.get("NURSE_HMEM_DIR"),
            "NURSE_ACTIVITY_LOG": os.environ.get("NURSE_ACTIVITY_LOG"),
            "ZETARIS_FIXTURE_MODE": os.environ.get("ZETARIS_FIXTURE_MODE"),
        }
        os.environ["NURSE_HMEM_DIR"] = str(Path(state_dir) / "hmem")
        os.environ["NURSE_ACTIVITY_LOG"] = str(Path(state_dir) / "trace.jsonl")
        os.environ["ZETARIS_FIXTURE_MODE"] = "1"
        try:
            from nurse import enriched_triage

            log = FIXTURE.read_text(encoding="utf-8")
            first = enriched_triage(log, "rules-only", use_rules=True, route="hmem-two-pass-demo")
            first_ids = _ids(first.memory, "remembered_ids")
            hmem_dir = Path(os.environ["NURSE_HMEM_DIR"])
            state_file = hmem_dir / "state.json"
            ledger_file = hmem_dir / "ledger.jsonl"
            persisted_ids: list[str] = []
            if state_file.is_file():
                try:
                    state = json.loads(state_file.read_text(encoding="utf-8"))
                    persisted_ids = [
                        str(record.get("id"))
                        for record in state.get("records", [])
                        if isinstance(record, dict) and record.get("id")
                    ]
                except (OSError, json.JSONDecodeError, AttributeError):
                    persisted_ids = []
            persisted_state_verified = bool(
                first_ids
                and set(first_ids).intersection(persisted_ids)
                and ledger_file.is_file()
                and ledger_file.stat().st_size > 0
            )
            second = enriched_triage(log, "rules-only", use_rules=True, route="hmem-two-pass-demo")
        finally:
            for key, value in prior.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    recalled_ids = _ids(second.memory, "recall_ids")
    linked_ids = sorted(set(first_ids).intersection(recalled_ids))
    payload = {
        "ok": bool(linked_ids) and persisted_state_verified,
        "engine_source": second.memory.get("engine_source"),
        "first_pass_remembered_ids": first_ids,
        "persisted_prior_triage_ids": persisted_ids,
        "persisted_state_verified": persisted_state_verified,
        "second_pass_recall_ids": recalled_ids,
        "linked_prior_triage_ids": linked_ids,
        "services": {
            "remember": first.memory.get("remember_service"),
            "recall": second.memory.get("recall_service"),
        },
        "provenance_note": (
            "The linked IDs show retrieval of a prior triage record. They are provenance, "
            "not proof that a repair was applied or that diagnostic accuracy increased."
        ),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if linked_ids else 1


if __name__ == "__main__":
    raise SystemExit(run())

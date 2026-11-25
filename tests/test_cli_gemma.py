"""The GitHub Action CLI must treat Gemma output as strictly as the app does."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CLI_SPEC = importlib.util.spec_from_file_location("nurse_cli_gemma", ROOT / "action" / "nurse_cli.py")
assert CLI_SPEC and CLI_SPEC.loader
CLI = importlib.util.module_from_spec(CLI_SPEC)
CLI_SPEC.loader.exec_module(CLI)


class _Resp:
    def __init__(self, payload: dict) -> None:
        text = json.dumps(payload)
        self._body = json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode()

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False


class CliGemmaTests(unittest.TestCase):
    def triage(self, payload: dict):
        with patch.object(CLI.urllib.request, "urlopen", lambda *a, **k: _Resp(payload)):
            return CLI.gemma_triage("error: boom", "gemma-test", "test-key")

    def test_json_without_diagnosis_fields_falls_back_to_rules(self) -> None:
        self.assertIsNone(self.triage({"error": "quota exceeded"}))

    def test_confidence_is_normalised(self) -> None:
        result = self.triage({"summary": "s", "failing_step": "Typecheck", "confidence": "Very Sure!"})
        self.assertEqual(result["confidence"], "medium")
        result = self.triage({"summary": "s", "failing_step": "Typecheck", "confidence": "HIGH"})
        self.assertEqual(result["confidence"], "high")


if __name__ == "__main__":
    unittest.main()

"""Contracts for the fresh-store, two-pass H-MEM proof script."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class HmemTwoPassDemoTests(unittest.TestCase):
    def test_demo_script_describes_prior_triage_provenance_without_accuracy_claims(self) -> None:
        script = ROOT / "scripts" / "demo_hmem_two_pass.sh"
        self.assertTrue(script.is_file(), "missing fresh-store H-MEM demo script")

        result = subprocess.run(
            ["bash", str(script), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        text = (result.stdout + result.stderr).lower()
        self.assertIn("prior triage", text)
        self.assertIn("provenance", text)
        self.assertNotIn("validated fix", text)
        self.assertNotIn("improved accuracy", text)

    def test_presenter_copy_labels_memory_as_prior_triage_provenance(self) -> None:
        copy = (
            (ROOT / "README.md").read_text(encoding="utf-8")
            + "\n"
            + (ROOT / "docs" / "demo-script.md").read_text(encoding="utf-8")
        ).lower()

        self.assertIn("prior triage", copy)
        self.assertIn("provenance", copy)
        self.assertNotIn("past fixes reusable", copy)

    def test_runtime_proof_requires_persisted_meterless_state_between_passes(self) -> None:
        source = (ROOT / "scripts" / "hmem_two_pass_demo.py").read_text(encoding="utf-8")

        self.assertIn('"state.json"', source)
        self.assertIn('"ledger.jsonl"', source)
        self.assertIn("persisted_state_verified", source)

    def test_runtime_proof_fails_when_recall_is_linked_but_persistence_is_missing(self) -> None:
        spec = importlib.util.spec_from_file_location("hmem_two_pass_demo_under_test", ROOT / "scripts" / "hmem_two_pass_demo.py")
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        first = SimpleNamespace(memory={
            "remembered_ids": ["mem-test-1"],
            "engine_source": "vendor/hmem",
            "remember_service": "MemoryMiningService",
        })
        second = SimpleNamespace(memory={
            "recall_ids": ["mem-test-1"],
            "engine_source": "vendor/hmem",
            "recall_service": "MemoryRetrievalService",
        })
        output = io.StringIO()

        with (
            patch("memory_bridge.status", return_value={"ready": True, "engine_source": "vendor/hmem"}),
            patch("nurse.enriched_triage", side_effect=[first, second]),
            contextlib.redirect_stdout(output),
        ):
            exit_code = module.run()

        self.assertEqual(exit_code, 1)
        self.assertIn('"ok": false', output.getvalue())


if __name__ == "__main__":
    unittest.main()

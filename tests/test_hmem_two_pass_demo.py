"""Contracts for the fresh-store, two-pass H-MEM proof script."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()

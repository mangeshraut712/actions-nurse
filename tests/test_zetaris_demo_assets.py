"""Safety contracts for the opt-in local Zetaris demo-data seed."""
from __future__ import annotations

import csv
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ZetarisDemoSeedAssetTests(unittest.TestCase):
    def test_seed_wrapper_refuses_to_run_without_explicit_apply_flag(self) -> None:
        script = ROOT / "scripts" / "seed_local_zetaris_demo.sh"
        self.assertTrue(script.is_file(), "missing opt-in Zetaris demo seed wrapper")

        result = subprocess.run(
            ["bash", str(script)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--apply", result.stderr)

    def test_seed_wrapper_refuses_an_existing_csv_when_its_checksum_cannot_be_verified(self) -> None:
        script = ROOT / "scripts" / "seed_local_zetaris_demo.sh"
        self.assertTrue(script.is_file(), "missing opt-in Zetaris demo seed wrapper")
        text = script.read_text(encoding="utf-8")

        self.assertIn("Cannot verify checksum", text)
        self.assertIn("REMOTE_STATE", text)

    def test_seed_program_is_limited_to_owned_create_operations(self) -> None:
        source = ROOT / "scripts" / "ZetarisDemoSeed.java"
        self.assertTrue(source.is_file(), "missing local JDBC demo seed program")
        text = source.read_text(encoding="utf-8")

        self.assertIn("CREATE LIGHTNING DATABASE", text)
        self.assertIn("CREATE LIGHTNING FILESTORE TABLE", text)
        self.assertIn("actions_nurse_demo_20261027_f9de7301", text)
        self.assertIn('value.endsWith("." + TABLE)', text)
        self.assertIn("if (!databaseCreated)", text)
        for forbidden in ("DROP ", "DELETE ", "UPDATE ", "TRUNCATE "):
            self.assertNotIn(forbidden, text)

    def test_seed_program_verifies_the_exact_owned_corpus_before_labelling_it_synthetic(self) -> None:
        source = ROOT / "scripts" / "ZetarisDemoSeed.java"
        text = source.read_text(encoding="utf-8")

        self.assertIn("EXPECTED_COLUMNS", text)
        self.assertIn("EXPECTED_ROWS", text)
        self.assertIn("SELECT * FROM " + '" + DATABASE + "." + TABLE + " ORDER BY observed_at ASC', text)
        self.assertIn("metadata.getColumnCount()", text)
        self.assertIn("Canonical synthetic demo corpus mismatch", text)

    def test_local_live_runner_requires_an_explicit_bundle_path(self) -> None:
        script = ROOT / "scripts" / "run_local_zetaris_demo.sh"
        self.assertTrue(script.is_file(), "missing local Zetaris demo runner")
        environment = dict(os.environ)
        environment.pop("ZETARIS_PLATFORM_DIR", None)

        result = subprocess.run(
            ["bash", str(script)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ZETARIS_PLATFORM_DIR", result.stderr)

    def test_local_live_runner_refuses_inherited_noncanonical_demo_identity(self) -> None:
        script = ROOT / "scripts" / "run_local_zetaris_demo.sh"
        with tempfile.TemporaryDirectory() as temp_dir:
            platform = Path(temp_dir)
            (platform / ".env").write_text(
                "ZETARIS_ADMIN_EMAIL=demo@example.test\nZETARIS_ADMIN_PASSWORD=not-a-real-password\n",
                encoding="utf-8",
            )
            for key, value in {
                "ZETARIS_CI_EVIDENCE_TABLE": "other.ci_failure_signatures",
                "ZETARIS_EVIDENCE_PROVENANCE": "not-synthetic",
            }.items():
                with self.subTest(key=key):
                    environment = dict(os.environ)
                    environment.update({
                        "ZETARIS_PLATFORM_DIR": str(platform),
                        "PYTHON": "/usr/bin/false",
                        key: value,
                    })
                    result = subprocess.run(
                        ["bash", str(script)],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                        env=environment,
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("owned demo identity", result.stderr)

    def test_seed_csv_is_explicitly_synthetic_and_matches_expected_row_count(self) -> None:
        path = ROOT / "demo" / "zetaris" / "ci_failure_signatures.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 4)
        self.assertEqual({row["source"] for row in rows}, {"synthetic local Actions Nurse demo corpus"})
        self.assertEqual({row["failing_step"] for row in rows}, {
            "Typecheck / tsc",
            "Unit tests / pytest",
            "Runner filesystem",
            "Checkout / repository access",
        })


if __name__ == "__main__":
    unittest.main()

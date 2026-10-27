"""Contracts for the sanitized historic repository-CI case record."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "demo" / "real-ci" / "historic-docker-smoke-incident.json"
REPOSITORY = "https://github.com/mangeshraut712/actions-nurse"
FAILED_SHA = "8616b672c2b8ed186c8cb8a1f7e6d61f13eedb28"
FOLLOW_UP_SHA = "0d46c28706f5cfe0183c1c0f0db872ecf062224d"


def _strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in _strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _strings(child)]
    return [value] if isinstance(value, str) else []


class HistoricCiCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = json.loads(CASE_PATH.read_text(encoding="utf-8"))

    def test_record_pins_the_verified_immutable_ci_chain(self) -> None:
        self.assertEqual(1, self.case["schema_version"])
        self.assertEqual("historic_repository_ci_case", self.case["kind"])
        self.assertEqual(REPOSITORY, self.case["source_repository"])

        failed = self.case["failed_ci"]
        self.assertEqual(FAILED_SHA, failed["commit_sha"])
        self.assertEqual("8616b672", failed["display_sha"])
        self.assertEqual("40328653045", failed["run_id"])
        self.assertEqual("121591898621", failed["job_id"])
        self.assertEqual("failure", failed["outcome"])
        self.assertEqual("Build and smoke-test the Docker Compose deployment", failed["stage"])
        self.assertEqual("exit code 7", failed["safe_annotation"])
        self.assertEqual("curl: (7) Failed to connect", failed["safe_signature"])
        self.assertEqual(f"{REPOSITORY}/commit/{FAILED_SHA}", failed["commit_url"])
        self.assertEqual(f"{REPOSITORY}/actions/runs/40328653045", failed["run_url"])
        self.assertEqual(
            f"{REPOSITORY}/actions/runs/40328653045/job/121591898621",
            failed["job_url"],
        )

        triage = self.case["actions_nurse_triage"]
        self.assertEqual(FAILED_SHA, triage["commit_sha"])
        self.assertEqual("40328858092", triage["run_id"])
        self.assertEqual("success", triage["workflow_outcome"])
        self.assertEqual("rules", triage["engine"])
        self.assertEqual("unknown", triage["result"])
        self.assertIn("unrecognized", triage["detail"].lower())
        self.assertEqual(f"{REPOSITORY}/actions/runs/40328858092", triage["run_url"])

        follow_up = self.case["documented_follow_up"]
        self.assertEqual(FOLLOW_UP_SHA, follow_up["commit_sha"])
        self.assertEqual("0d46c28", follow_up["display_sha"])
        self.assertEqual(f"{REPOSITORY}/commit/{FOLLOW_UP_SHA}", follow_up["commit_url"])

        subsequent = self.case["subsequent_ci"]
        self.assertEqual(FOLLOW_UP_SHA, subsequent["commit_sha"])
        self.assertEqual("40331404876", subsequent["run_id"])
        self.assertEqual("success", subsequent["outcome"])
        self.assertEqual(f"{REPOSITORY}/actions/runs/40331404876", subsequent["run_url"])

    def test_record_keeps_metadata_only_and_truthful_boundaries(self) -> None:
        self.assertIn("not a live query", self.case["boundary"].lower())
        self.assertIn("not a synthetic fixture", self.case["boundary"].lower())
        self.assertIn("not production evidence", self.case["boundary"].lower())
        self.assertIn("not a successful autonomous repair", self.case["boundary"].lower())
        self.assertEqual(
            [
                "This record preserves sanitized metadata, not raw GitHub logs or artifacts.",
                "It does not establish the root cause of the failed health endpoint.",
                "It does not show production impact, a successful autonomous repair, improved accuracy, or time saved.",
            ],
            self.case["limitations"],
        )

        self.assertTrue(all("\n" not in value and len(value) <= 300 for value in _strings(self.case)))
        self.assertFalse(
            any(
                re.search(r"(?:secret|token|password|authorization|credential|raw[_-]?log)", key, re.I)
                for key in self._keys(self.case)
            )
        )

    @staticmethod
    def _keys(value: Any) -> list[str]:
        if isinstance(value, dict):
            return [key for key, child in value.items()] + [
                key for child in value.values() for key in HistoricCiCaseTests._keys(child)
            ]
        if isinstance(value, list):
            return [key for child in value for key in HistoricCiCaseTests._keys(child)]
        return []


if __name__ == "__main__":
    unittest.main()

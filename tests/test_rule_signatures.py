"""Failure signatures must not mistake tool invocations for failure evidence."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from nurse import rule_triage

ROOT = Path(__file__).resolve().parents[1]
CLI_SPEC = importlib.util.spec_from_file_location("nurse_rule_cli", ROOT / "action" / "nurse_cli.py")
assert CLI_SPEC and CLI_SPEC.loader
CLI = importlib.util.module_from_spec(CLI_SPEC)
CLI_SPEC.loader.exec_module(CLI)


class RuleSignatureTests(unittest.TestCase):
    def diagnoses(self, log: str):
        yield "app", rule_triage(log).model_dump()
        yield "action", CLI.rule_triage(log)

    def test_tool_invocations_without_failure_evidence_are_unknown(self) -> None:
        for log in (
            "Run pytest -q\n================ 12 passed in 0.2s ================",
            "Run tsc --noEmit\nTypecheck completed successfully.",
            "Run python -m pytest\nModuleNotFoundError: No module named 'plugin'",
            "Run pytest -rp\n=== short test summary info ===\nPASSED test_app.py::test_ok",
        ):
            for surface, result in self.diagnoses(log):
                with self.subTest(surface=surface, log=log):
                    self.assertEqual(result["confidence"], "low")
                    self.assertEqual(result["patterns"], [])
                    self.assertEqual(result["fix_commands"], [])

    def test_unknown_failure_reports_the_last_started_step(self) -> None:
        plain = (
            "##[group]Run actions/checkout@v4\n##[endgroup]\n"
            "##[group]Run make lint\nlint: 3 problems\n"
            "##[error]Process completed with exit code 2.\n"
        )
        gh_failed = (
            "build\tSet up job\t2026-11-10T10:00:00.1Z Current runner version: '2.320.0'\n"
            "build\tRun actions/checkout@v4\t2026-11-10T10:00:01.1Z ##[group]Run actions/checkout@v4\n"
            "build\tRun make lint\t2026-11-10T10:00:03.1Z ##[group]Run make lint\n"
            "build\tRun make lint\t2026-11-10T10:00:04.2Z ##[error]Process completed with exit code 2.\n"
        )
        for log in (plain, gh_failed):
            for surface, result in self.diagnoses(log):
                with self.subTest(surface=surface, log=log[:30]):
                    self.assertEqual(result["patterns"], [])
                    self.assertEqual(result["failing_step"], "make lint")

    def test_successful_tests_do_not_mask_later_checkout_failure(self) -> None:
        log = (
            "Run pytest -q\n12 passed in 0.2s\n"
            "Run git fetch origin\nfatal: Authentication failed for repository\n"
        )
        for surface, result in self.diagnoses(log):
            with self.subTest(surface=surface):
                self.assertEqual(result["failing_step"], "Checkout / repository access")

    def test_successful_typecheck_does_not_mask_later_install_failure(self) -> None:
        log = "Run tsc --noEmit\nRun npm ci\nnpm ERR! code ERESOLVE\n"
        for surface, result in self.diagnoses(log):
            with self.subTest(surface=surface):
                self.assertEqual(result["failing_step"], "npm install")

    def test_typecheck_invocation_does_not_mask_assertion_failure(self) -> None:
        log = "Run tsc --noEmit\nRun pytest -q\nE   AssertionError: assert 1 == 2\n"
        for surface, result in self.diagnoses(log):
            with self.subTest(surface=surface):
                self.assertEqual(result["failing_step"], "Unit tests / pytest")

    def test_real_failure_fixtures_keep_their_categories(self) -> None:
        categories = {
            "checkout-auth.txt": "Checkout / repository access",
            "disk-full.txt": "Runner filesystem",
            "npm-typecheck.txt": "Typecheck / tsc",
            "oom-killed.txt": "Build / bundler",
            "pytest-assert.txt": "Unit tests / pytest",
        }
        for filename, expected in categories.items():
            log = (ROOT / "fixtures" / filename).read_text(encoding="utf-8")
            for surface, result in self.diagnoses(log):
                with self.subTest(surface=surface, fixture=filename):
                    self.assertEqual(result["failing_step"], expected)
                    self.assertTrue(result["patterns"])

    def test_explicit_failures_do_not_require_the_tool_command(self) -> None:
        for log, expected in (
            ("src/app.ts(1,1): error TS2322: Type 'string' is not assignable", "Typecheck / tsc"),
            ("FAILED tests/test_app.py::test_regression - expected 1", "Unit tests / pytest"),
        ):
            for surface, result in self.diagnoses(log):
                with self.subTest(surface=surface, log=log):
                    self.assertEqual(result["failing_step"], expected)
                    self.assertTrue(result["patterns"])


if __name__ == "__main__":
    unittest.main()

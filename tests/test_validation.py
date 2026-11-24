"""Deterministic checks for the Gemma category validation boundary."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nurse import (
    TriageResult,
    enriched_compare,
    final_triage,
    guard_model_credential_advice as nurse_guard_credential_advice,
    health,
    enriched_triage,
    parse_model_json,
    parse_model_response as nurse_parse_response,
    rule_triage,
    validate_gemma_result,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_LOG = (ROOT / "fixtures" / "checkout-auth.txt").read_text(encoding="utf-8")
TYPECHECK_LOG = (ROOT / "fixtures" / "npm-typecheck.txt").read_text(encoding="utf-8")
CLI_SPEC = importlib.util.spec_from_file_location("actions_nurse_cli", ROOT / "action" / "nurse_cli.py")
assert CLI_SPEC and CLI_SPEC.loader
CLI = importlib.util.module_from_spec(CLI_SPEC)
CLI_SPEC.loader.exec_module(CLI)


def model_result(step: str, root_cause: str) -> TriageResult:
    return TriageResult(
        summary="Model proposal",
        failing_step=step,
        root_cause=root_cause,
        suggested_fix="Review the failing step",
        confidence="medium",
        engine="gemma",
        model="fixture-model",
    )


class GemmaValidationTests(unittest.TestCase):
    def test_fixture_comparison_attaches_sponsor_evidence_and_activity(self) -> None:
        """The comparison endpoint uses the same reviewable evidence chain."""
        with tempfile.TemporaryDirectory() as temp_dir:
            trace = Path(temp_dir) / "trace.jsonl"
            with patch("nurse.hmem_status", return_value={"ready": False, "mode": "setup_required"}), patch.dict(
                os.environ,
                {
                    "NURSE_ACTIVITY_LOG": str(trace),
                    "ZETARIS_FIXTURE_MODE": "1",
                },
                clear=False,
            ):
                result = enriched_compare(
                    TYPECHECK_LOG,
                    "fixture-model",
                    use_rules=True,
                    route="compare",
                )
            record = json.loads(trace.read_text(encoding="utf-8"))

        self.assertEqual(result.rules.engine, "rules")
        self.assertIsNone(result.gemma)
        self.assertEqual(result.zetaris["mode"], "fixture")
        self.assertEqual(result.zetaris["result"]["fixture"], "ci-failure-signatures.json")
        self.assertTrue(result.activity["id"].startswith("act-"))
        self.assertEqual(record["route"], "compare")
        self.assertNotIn(TYPECHECK_LOG, json.dumps(record))

    def test_fixture_triage_attaches_zetaris_evidence_and_appends_activity(self) -> None:
        """The offline sponsor path returns labelled evidence and preserves prior trace rows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            trace = Path(temp_dir) / "trace.jsonl"
            trace.write_text('{"event":"prior"}\n', encoding="utf-8")
            with patch("nurse.hmem_status", return_value={"ready": False, "mode": "setup_required"}), patch.dict(
                os.environ,
                {
                    "NURSE_ACTIVITY_LOG": str(trace),
                    "ZETARIS_FIXTURE_MODE": "1",
                },
                clear=False,
            ):
                result = enriched_triage(
                    TYPECHECK_LOG,
                    "fixture-model",
                    use_rules=True,
                    route="triage",
                )
            records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result.zetaris["mode"], "fixture")
        self.assertEqual(result.zetaris["source"], "recorded-demo-fixture")
        self.assertEqual(result.zetaris["result"]["fixture"], "ci-failure-signatures.json")
        self.assertEqual(result.zetaris["result"]["row_count"], 1)
        self.assertEqual(result.evidence[0]["provider"], "Zetaris Lightning SQL")
        self.assertEqual(result.evidence[0]["fixture"], "ci-failure-signatures.json")
        self.assertTrue(result.activity["id"].startswith("act-"))
        self.assertEqual(records[0], {"event": "prior"})
        self.assertEqual(records[-1]["event"], "triage")
        self.assertEqual(records[-1]["fixture"], "npm-typecheck.txt")
        self.assertEqual(records[-1]["zetaris"], {
            "fixture": "ci-failure-signatures.json",
            "mode": "fixture",
            "source": "recorded-demo-fixture",
        })
        self.assertNotIn(TYPECHECK_LOG, json.dumps(records[-1]))

    def test_unknown_log_text_is_not_written_to_activity_trace(self) -> None:
        raw_marker = "super-secret-value-987"
        with tempfile.TemporaryDirectory() as temp_dir:
            trace = Path(temp_dir) / "trace.jsonl"
            with patch("nurse.hmem_status", return_value={"ready": False, "mode": "setup_required"}), patch(
                "nurse.query_ci_evidence",
                return_value={"mode": "fixture", "source": "recorded-demo-fixture", "result": {}},
            ) as query, patch.dict(os.environ, {"NURSE_ACTIVITY_LOG": str(trace)}, clear=False):
                result = enriched_triage(
                    f"Run deploy token={raw_marker}",
                    "fixture-model",
                    use_rules=True,
                    route="triage",
                )
            record = json.loads(trace.read_text(encoding="utf-8"))

        self.assertIn(raw_marker, result.failing_step)  # User response stays useful.
        self.assertEqual(record["rules"]["failing_step"], "Unrecognized CI failure")
        self.assertEqual(record["final"]["failing_step"], "Unrecognized CI failure")
        self.assertNotIn(raw_marker, json.dumps(record))
        query.assert_called_once_with("Unrecognized CI failure", [])

    def test_known_failure_category_is_confirmed(self) -> None:
        result = validate_gemma_result(
            model_result("Checkout authentication", "Runner cannot access the repository"),
            rule_triage(CHECKOUT_LOG),
        )
        self.assertEqual(result.validation_status, "confirmed")

    def test_conflicting_category_selects_rules_result(self) -> None:
        result = final_triage(
            model_result("Typecheck", "A TypeScript export is missing"),
            rule_triage(CHECKOUT_LOG),
        )
        self.assertEqual(result.engine, "rules")
        self.assertEqual(result.validation_status, "overridden")
        self.assertEqual(result.failing_step, "Checkout / repository access")

    def test_unknown_signature_stays_unverified(self) -> None:
        result = validate_gemma_result(
            model_result("Network", "The request timed out"),
            rule_triage("Unrecognized runner failure"),
        )
        self.assertEqual(result.validation_status, "unverified")

    def test_model_response_skips_thought_part_and_parses_final_json(self) -> None:
        expected = {"summary": "Final answer", "failing_step": "Checkout"}
        response = {
            "candidates": [{
                "content": {"parts": [
                    {"thought": True, "text": '{"summary":"Internal note"}'},
                    {"text": '[{"summary":"Final answer","failing_step":"Checkout"}]'},
                ]},
            }],
        }
        self.assertEqual(nurse_parse_response(response), expected)
        self.assertEqual(CLI.parse_model_response(response), expected)

    def test_action_cli_overrides_the_same_conflict(self) -> None:
        candidate = {
            "engine": "gemma",
            "model": "fixture-model",
            "failing_step": "Typecheck",
            "root_cause": "A TypeScript export is missing",
        }
        result = CLI.final_triage(candidate, CLI.rule_triage(CHECKOUT_LOG))
        self.assertEqual(result["engine"], "rules")
        self.assertEqual(result["validation_status"], "overridden")
        self.assertEqual(result["failing_step"], "Checkout / repository access")

    def test_broad_classic_pat_advice_is_replaced_in_app_and_action(self) -> None:
        proposal = {
            "suggested_fix": "Use a Personal Access Token (PAT) with 'repo' scope to access the private dependency.",
            "fix_commands": ["echo $GITHUB_TOKEN"],
        }
        for guard in (nurse_guard_credential_advice, CLI.guard_model_credential_advice):
            with self.subTest(guard=guard.__module__):
                safe = guard(proposal)
                self.assertIn("broad token scope", safe["suggested_fix"])
                self.assertIn("read-only contents access", safe["suggested_fix"])
                self.assertNotIn("repo' scope", safe["suggested_fix"])
                self.assertEqual(safe["fix_commands"], [])


    def test_parse_model_json_ignores_later_unrelated_braces(self) -> None:
        payload = {
            "summary": "disk full",
            "failing_step": "build",
            "root_cause": "ENOSPC",
            "suggested_fix": "free space",
            "confidence": "high",
        }
        text = (
            "Here is the diagnosis:\n"
            + json.dumps(payload)
            + "\nThanks {user}."
        )
        fenced = "```json\n" + json.dumps(payload) + "\n```"
        for parse in (parse_model_json, CLI.parse_model_json):
            with self.subTest(surface=parse.__module__):
                self.assertEqual(parse(text), payload)
                self.assertEqual(parse(fenced), payload)
                self.assertIsNone(parse("no json here {not-json}"))

        response = {"candidates": [{"content": {"parts": [{"text": text}]}}]}
        for parse in (nurse_parse_response, CLI.parse_model_response):
            with self.subTest(response_surface=parse.__module__):
                self.assertEqual(parse(response), payload)

    def test_rules_only_health_does_not_expose_key_presence(self) -> None:
        with patch("nurse.RULES_ONLY", True), patch.dict(os.environ, {"GEMINI_API_KEY": "configured"}):
            status = health()
        self.assertTrue(status["rules_only"])
        self.assertFalse(status["gemma_key"])


class PytestRuleSelectorTests(unittest.TestCase):
    def both(self, log: str) -> list[list[str]]:
        return [rule_triage(log).fix_commands, CLI.rule_triage(log)["fix_commands"]]

    def test_pytest_rerun_targets_the_test_named_in_the_summary(self) -> None:
        log = (
            "build\tRun tests\t2026-11-25T00:00:00Z FAILED tests/unit/test_parse.py::test_dates[utc] - AssertionError\n"
            "build\tRun tests\t2026-11-25T00:00:00Z FAILED tests/unit/test_parse.py::test_other\n"
        )
        expected = ["pytest -q 'tests/unit/test_parse.py::test_dates[utc]'"]
        self.assertEqual(self.both(log), [expected, expected])

    def test_demo_fixture_keeps_its_selector(self) -> None:
        log = (ROOT / "fixtures" / "pytest-assert.txt").read_text(encoding="utf-8")
        expected = ["pytest -q tests/test_tools.py::test_spill_volume_last_month"]
        self.assertEqual(self.both(log), [expected, expected])

    def test_pytest_rerun_falls_back_to_the_whole_suite(self) -> None:
        logs = {
            "no summary line": "E   AssertionError: assert 1 == 2\n",
            "space in parameter id": "FAILED tests/test_parse.py::test_dates[two words] - AssertionError\n",
            "shell syntax in parameter id": "FAILED tests/test_parse.py::test_dates[a(b)] - AssertionError\n",
            "command substitution": "FAILED tests/x.py::t$(touch /tmp/pwn)\n",
            "quoted in assertion text": "E   AssertionError: FAILED tests/other.py::test_x\n",
        }
        for name, log in logs.items():
            with self.subTest(name):
                self.assertEqual(self.both(log), [["pytest -q"], ["pytest -q"]])

    def test_summary_section_wins_over_earlier_output(self) -> None:
        log = (
            "FAILED tests/old.py::test_from_captured_stdout\n"
            "=========================== short test summary info ============================\n"
            "FAILED tests/new.py::test_real\n"
        )
        expected = ["pytest -q tests/new.py::test_real"]
        self.assertEqual(self.both(log), [expected, expected])


class ActionReportWriteTests(unittest.TestCase):
    def test_report_is_written_as_utf8_into_a_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "job.log"
            log_path.write_text(CHECKOUT_LOG, encoding="utf-8")
            out_path = Path(tmp) / "reports" / "nurse.md"
            env = {
                "NURSE_LOG_PATH": str(log_path),
                "NURSE_OUTPUT": str(out_path),
                "NURSE_RULES_ONLY": "true",
                "GITHUB_OUTPUT": str(Path(tmp) / "out.txt"),
            }
            with patch.dict(os.environ, env, clear=False):
                self.assertEqual(CLI.main(), 0)
            self.assertIn("🩺", out_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

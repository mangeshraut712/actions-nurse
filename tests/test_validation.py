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
        self.assertEqual(parse_model_json(text)["summary"], "disk full")
        fenced = "```json\n" + json.dumps(payload) + "\n```"
        self.assertEqual(parse_model_json(fenced)["failing_step"], "build")
        self.assertIsNone(parse_model_json("no json here {not-json}"))

    def test_rules_only_health_does_not_expose_key_presence(self) -> None:
        with patch("nurse.RULES_ONLY", True), patch.dict(os.environ, {"GEMINI_API_KEY": "configured"}):
            status = health()
        self.assertTrue(status["rules_only"])
        self.assertFalse(status["gemma_key"])


if __name__ == "__main__":
    unittest.main()

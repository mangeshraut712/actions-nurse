"""Deterministic checks for the Gemma category validation boundary."""
from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from nurse import (
    TriageResult,
    final_triage,
    guard_model_credential_advice as nurse_guard_credential_advice,
    health,
    parse_model_response as nurse_parse_response,
    rule_triage,
    validate_gemma_result,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_LOG = (ROOT / "fixtures" / "checkout-auth.txt").read_text(encoding="utf-8")
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

    def test_rules_only_health_does_not_expose_key_presence(self) -> None:
        with patch("nurse.RULES_ONLY", True), patch.dict(os.environ, {"GEMINI_API_KEY": "configured"}):
            status = health()
        self.assertTrue(status["rules_only"])
        self.assertFalse(status["gemma_key"])


if __name__ == "__main__":
    unittest.main()

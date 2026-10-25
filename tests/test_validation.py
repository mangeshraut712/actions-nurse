"""Deterministic checks for the Gemma category validation boundary."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from nurse import TriageResult, final_triage, parse_model_response as nurse_parse_response, rule_triage, validate_gemma_result


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


if __name__ == "__main__":
    unittest.main()

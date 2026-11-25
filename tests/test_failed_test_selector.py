"""Pin the pytest re-run selector that ``action/nurse_cli.py`` derives from
the short test summary, including shell quoting and safe fallbacks."""
from __future__ import annotations

import unittest

from action.nurse_cli import rule_triage, with_failed_test_selector


PAYLOAD = {"fix_commands": ["pytest -q"]}


def selector(log: str) -> list[str]:
    return with_failed_test_selector(dict(PAYLOAD), log)["fix_commands"]


class FailedTestSelectorTests(unittest.TestCase):
    def test_plain_summary_line_becomes_the_pytest_selector(self) -> None:
        log = (
            "==================== short test summary info ====================\n"
            "FAILED tests/test_api.py::test_triage - assert 500 == 200\n"
            "1 failed, 3 passed in 0.12s\n"
        )
        self.assertEqual(selector(log), ["pytest -q tests/test_api.py::test_triage"])

    def test_gh_run_view_prefix_and_timestamp_are_tolerated(self) -> None:
        log = (
            "short test summary info\n"
            "ci\tunit\t2026-01-02T03:04:05.1234567Z FAILED tests/test_api.py::test_triage"
            " - AssertionError: boom\n"
        )
        self.assertEqual(selector(log), ["pytest -q tests/test_api.py::test_triage"])

    def test_bracketed_node_id_is_shell_quoted(self) -> None:
        log = "short test summary info\nFAILED tests/test_api.py::test_case[case-1] - assert\n"
        self.assertEqual(selector(log), ["pytest -q 'tests/test_api.py::test_case[case-1]'"])

    def test_error_summary_lines_are_skipped_in_favour_of_failed_ones(self) -> None:
        log = (
            "short test summary info\n"
            "ERROR tests/test_api.py::test_error\n"
            "FAILED tests/test_api.py::test_failed\n"
        )
        self.assertEqual(selector(log), ["pytest -q tests/test_api.py::test_failed"])

    def test_failed_lines_before_the_summary_header_are_ignored(self) -> None:
        log = (
            "FAILED tests/test_old.py::test_old\n"
            "short test summary info\n"
            "FAILED tests/test_new.py::test_new\n"
        )
        self.assertEqual(selector(log), ["pytest -q tests/test_new.py::test_new"])

    def test_missing_summary_header_falls_back_to_the_whole_log(self) -> None:
        self.assertEqual(
            selector("FAILED tests/test_api.py::test_triage\n"),
            ["pytest -q tests/test_api.py::test_triage"],
        )

    def test_indented_assertion_text_does_not_match(self) -> None:
        self.assertEqual(selector("E   FAILED tests/test_api.py::test_triage\n"), ["pytest -q"])

    def test_unsafe_node_id_falls_back_to_the_whole_suite(self) -> None:
        log = "short test summary info\nFAILED tests/test_api.py::test case name\n"
        self.assertEqual(selector(log), ["pytest -q"])

    def test_non_pytest_payload_is_returned_unchanged(self) -> None:
        payload = {"fix_commands": ["npm ci"]}
        self.assertEqual(
            with_failed_test_selector(payload, "FAILED tests/test_api.py::test_triage\n"),
            payload,
        )

    def test_rule_triage_uses_the_failed_test_selector(self) -> None:
        triage = rule_triage("FAILED tests/test_api.py::test_triage - assert 1 == 2\n")
        self.assertEqual(triage["failing_step"], "Unit tests / pytest")
        self.assertEqual(triage["fix_commands"], ["pytest -q tests/test_api.py::test_triage"])


if __name__ == "__main__":
    unittest.main()

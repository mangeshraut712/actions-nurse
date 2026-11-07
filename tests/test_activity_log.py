"""Read complete activity events even when another append is interrupted."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from activity_log import append_activity, latest_activity


class LatestActivityTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.trace = Path(temporary.name) / "trace.jsonl"
        environment = patch.dict(os.environ, {"NURSE_ACTIVITY_LOG": str(self.trace)})
        environment.start()
        self.addCleanup(environment.stop)

    def test_interrupted_append_preserves_complete_events(self) -> None:
        first = append_activity("triage", fixture="checkout-auth.txt")
        second = append_activity("triage", fixture="npm-typecheck.txt")
        with self.trace.open("ab") as stream:
            stream.write(b'{"event":"triage","id":"interrupted')
        before = self.trace.read_bytes()

        self.assertEqual(latest_activity(), [first, second])
        self.assertEqual(self.trace.read_bytes(), before)

    def test_limit_counts_valid_events_in_chronological_order(self) -> None:
        self.trace.write_text(
            '{"id":"older"}\n{"id":"middle"}\ninvalid\n\n'
            '{"id":"newest"}\n{"id":', encoding="utf-8",
        )
        self.assertEqual(latest_activity(2), [{"id": "middle"}, {"id": "newest"}])

    def test_nonobject_json_is_not_an_activity_event(self) -> None:
        self.trace.write_text(
            '{"id":"valid"}\nnull\n[]\n"text"\n42\ntrue\n', encoding="utf-8",
        )
        self.assertEqual(latest_activity(), [{"id": "valid"}])

    def test_invalid_utf8_row_does_not_hide_valid_neighbors(self) -> None:
        self.trace.write_bytes(
            b'{"id":"before"}\n{"id":"\xff"}\n{"id":"after"}\n',
        )
        self.assertEqual(latest_activity(), [{"id": "before"}, {"id": "after"}])

    def test_complete_last_event_without_newline_is_read(self) -> None:
        self.trace.write_text('{"id":"last"}', encoding="utf-8")
        self.assertEqual(latest_activity(), [{"id": "last"}])

    def test_missing_empty_and_wholly_invalid_traces_are_empty(self) -> None:
        self.assertEqual(latest_activity(), [])
        for contents in (b"", b"\n \n", b"invalid\n\xff\nnull\n"):
            with self.subTest(contents=contents):
                self.trace.write_bytes(contents)
                self.assertEqual(latest_activity(), [])

    def test_limit_is_clamped_to_supported_range(self) -> None:
        self.trace.write_text(
            "".join(json.dumps({"id": number}) + "\n" for number in range(105)),
            encoding="utf-8",
        )
        self.assertEqual(latest_activity(0), [{"id": 104}])
        self.assertEqual(latest_activity(-20), [{"id": 104}])
        self.assertEqual(len(latest_activity(1000)), 100)
        self.assertEqual(latest_activity(1000)[0], {"id": 5})
        self.assertEqual(latest_activity(1000)[-1], {"id": 104})


if __name__ == "__main__":
    unittest.main()

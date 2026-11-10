"""Long logs sent to Gemma must keep the error at the end, not only the setup noise."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import nurse

ROOT = Path(__file__).resolve().parents[1]
CLI_SPEC = importlib.util.spec_from_file_location("nurse_clip_cli", ROOT / "action" / "nurse_cli.py")
assert CLI_SPEC and CLI_SPEC.loader
CLI = importlib.util.module_from_spec(CLI_SPEC)
CLI_SPEC.loader.exec_module(CLI)


class ClipLogTests(unittest.TestCase):
    def test_long_log_keeps_head_and_failing_tail(self) -> None:
        log = "##[group]Run actions/checkout@v4\n" + ("npm http fetch GET 200 pkg\n" * 2000) + "Error: Process completed with exit code 2.\n"
        for clip in (nurse.clip_log, CLI.clip_log):
            with self.subTest(clip=clip.__module__):
                out = clip(log, 12_000)
                self.assertLessEqual(len(out), 12_000)
                self.assertTrue(out.startswith("##[group]Run actions/checkout@v4"))
                self.assertIn("exit code 2", out)
                self.assertIn("[log truncated]", out)

    def test_short_log_is_unchanged(self) -> None:
        for clip in (nurse.clip_log, CLI.clip_log):
            self.assertEqual(clip("Run x\nboom\n", 12_000), "Run x\nboom\n")


if __name__ == "__main__":
    unittest.main()

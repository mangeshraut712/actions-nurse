"""Pin the H-MEM bridge's subprocess environment boundary and stdout parsing."""
from __future__ import annotations

import json
import os
import subprocess
import unittest
from unittest.mock import patch

import memory_bridge


READY = {
    "ready": True,
    "mode": "hmem",
    "engine_source": "vendor/hmem",
    "missing": [],
}


class BridgeEnvironmentTests(unittest.TestCase):
    def test_only_runtime_essentials_reach_the_subprocess(self) -> None:
        with patch.dict(
            os.environ,
            {"PATH": "/usr/bin", "GEMINI_API_KEY": "do-not-leak", "ZETARIS_TOKEN": "do-not-leak"},
            clear=True,
        ):
            environment = memory_bridge._bridge_environment()
        self.assertEqual(environment, {"PATH": "/usr/bin", "NO_COLOR": "1"})

    def test_isolated_store_and_home_are_forwarded_when_set(self) -> None:
        with patch.dict(
            os.environ,
            {"PATH": "/usr/bin", "NURSE_HMEM_DIR": "/tmp/nurse-hmem", "HOME": "/home/nurse"},
            clear=True,
        ):
            environment = memory_bridge._bridge_environment()
        self.assertEqual(
            environment,
            {
                "PATH": "/usr/bin",
                "NO_COLOR": "1",
                "NURSE_HMEM_DIR": "/tmp/nurse-hmem",
                "HOME": "/home/nurse",
            },
        )


class InvokeTests(unittest.TestCase):
    def test_setup_required_status_never_starts_a_subprocess(self) -> None:
        not_ready = {
            "ready": False,
            "mode": "setup_required",
            "engine_source": None,
            "missing": ["npm"],
        }
        with patch.object(memory_bridge, "status", return_value=not_ready), patch(
            "memory_bridge.subprocess.run"
        ) as run:
            result = memory_bridge._invoke("ask", {"query": "why"})
        run.assert_not_called()
        self.assertEqual(result, {"ok": False, **not_ready})

    def test_last_json_line_is_parsed_and_the_environment_is_scrubbed(self) -> None:
        payload = {"ok": True, "operation": "ask", "query": "disk full"}
        stdout = "npm notice a new version of npm is available\n" + json.dumps(payload) + "\n"
        with patch.object(memory_bridge, "status", return_value=dict(READY)), patch.dict(
            os.environ,
            {"PATH": "/usr/bin", "GEMINI_API_KEY": "do-not-leak", "NURSE_HMEM_DIR": "/tmp/nurse-hmem"},
            clear=True,
        ), patch("memory_bridge.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, stdout, "")
            result = memory_bridge._invoke("ask", {"query": "disk full"})
        self.assertEqual(result, payload)
        self.assertEqual(
            run.call_args.args[0],
            ["npm", "--silent", "run", "memory", "--", "ask", "--json"],
        )
        self.assertEqual(run.call_args.kwargs["cwd"], memory_bridge.METERLESS_DIR)
        self.assertEqual(run.call_args.kwargs["input"], json.dumps({"query": "disk full"}))
        self.assertEqual(
            run.call_args.kwargs["env"],
            {"PATH": "/usr/bin", "NO_COLOR": "1", "NURSE_HMEM_DIR": "/tmp/nurse-hmem"},
        )

    def test_failure_reports_unavailable_with_redacted_stderr(self) -> None:
        with patch.object(memory_bridge, "status", return_value=dict(READY)), patch.dict(
            os.environ, {"PATH": "/usr/bin"}, clear=True
        ), patch("memory_bridge.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 1, "", "Error: token=abc123def failed")
            result = memory_bridge._invoke("ask", {"query": "disk full"})
        self.assertEqual(
            result,
            {
                "ok": False,
                "mode": "unavailable",
                "engine_source": "vendor/hmem",
                "error": "Error: [redacted] failed",
                "returncode": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()

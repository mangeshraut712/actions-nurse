"""Offline contract checks for the Zetaris evidence hook."""
from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from integrations.zetaris.client import ZetarisClient, load_environment, validate_read_only_sql


class ZetarisClientTests(unittest.TestCase):
    def test_env_local_overrides_env_while_explicit_shell_values_stay_highest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text(
                "ZETARIS_REST_URL=https://from-env/api/v1.0\nZETARIS_API_KEY=env-key\n",
                encoding="utf-8",
            )
            (root / ".env.local").write_text(
                "ZETARIS_REST_URL=https://from-local/api/v1.0\nZETARIS_API_KEY=local-key\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                local = load_environment(root)
            with patch.dict(os.environ, {"ZETARIS_API_KEY": "shell-key"}, clear=True):
                shell = load_environment(root)

        self.assertEqual(local["ZETARIS_REST_URL"], "https://from-local/api/v1.0")
        self.assertEqual(local["ZETARIS_API_KEY"], "local-key")
        self.assertEqual(shell["ZETARIS_API_KEY"], "shell-key")

    def test_incomplete_configuration_uses_recorded_preflight_fixtures(self) -> None:
        result = ZetarisClient(environment={}).preflight()

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "fixture")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["checks"][0]["result"]["fixture"], "select-1.json")
        self.assertEqual(result["checks"][1]["result"]["fixture"], "show-lightning-databases.json")

    def test_fixture_evidence_is_filtered_to_the_triaged_step(self) -> None:
        result = ZetarisClient(environment={}).query_ci_evidence("Typecheck / tsc", ["TS2305"])

        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["source"], "recorded-demo-fixture")
        self.assertEqual(result["result"]["row_count"], 1)
        self.assertEqual(result["result"]["data"][0][1], "Typecheck / tsc")

    def test_live_request_uses_the_direct_rest_contract(self) -> None:
        response = types.SimpleNamespace(status_code=200, json=lambda: {"data": [["1"]]})
        post = Mock(return_value=response)
        fake_httpx = types.SimpleNamespace(post=post, RequestError=OSError)
        client = ZetarisClient(environment={
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.run_sql("SELECT 1")

        self.assertEqual(result["mode"], "live")
        self.assertEqual(post.call_args.args[0], "https://zetaris.example/api/v1.0/sql-editor/sqls/run-query")
        self.assertEqual(post.call_args.kwargs["json"], {"sql": "SELECT 1"})
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer not-a-real-key")
        self.assertEqual(headers["X-Org-ID"], "123")
        self.assertTrue(headers["X-Request-ID"])

    def test_write_and_multiple_statement_sql_are_rejected(self) -> None:
        for sql in ("DROP TABLE ci_failure_signatures", "SELECT 1; DELETE FROM ci_failure_signatures"):
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    validate_read_only_sql(sql)


if __name__ == "__main__":
    unittest.main()

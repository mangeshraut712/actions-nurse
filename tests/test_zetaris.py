"""Offline contract checks for the Zetaris evidence hook."""
from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

from integrations.zetaris.client import ZetarisClient, load_environment, validate_read_only_sql


ROOT = Path(__file__).resolve().parents[1]


class LocalHttpx:
    """Minimal httpx double that records proxy isolation for local sessions."""

    RequestError = OSError

    def __init__(self, responses: list[object]) -> None:
        self.post = Mock(side_effect=responses)
        self.client_options: list[dict[str, object]] = []

    def Client(self, **options: object) -> "LocalHttpx":
        self.client_options.append(options)
        return self

    def __enter__(self) -> "LocalHttpx":
        return self

    def __exit__(self, *_: object) -> bool:
        return False


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

    def test_example_template_keeps_local_ui_opt_in_when_direct_rest_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                environment = load_environment(root)

        self.assertEqual(environment.get("ZETARIS_LOCAL_UI_URL"), "")
        environment.update({
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })
        self.assertEqual(ZetarisClient(environment=environment).status()["mode"], "live")

    def test_incomplete_local_session_does_not_shadow_valid_direct_rest(self) -> None:
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })

        self.assertEqual(client.status()["mode"], "live")
        self.assertEqual(client.status()["reason"], "credentials_present")

    def test_fixture_evidence_is_filtered_to_the_triaged_step(self) -> None:
        result = ZetarisClient(environment={}).query_ci_evidence("Typecheck / tsc", ["TS2305"])

        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["source"], "recorded-demo-fixture")
        self.assertEqual(result["result"]["row_count"], 1)
        self.assertEqual(result["result"]["data"][0]["failing_step"], "Typecheck / tsc")

    def test_live_request_uses_the_direct_rest_contract(self) -> None:
        response = types.SimpleNamespace(status_code=200, json=lambda: {"data": [["1"]]})
        fake_httpx = LocalHttpx([response])
        post = fake_httpx.post
        client = ZetarisClient(environment={
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.run_sql("SELECT 1")

        self.assertEqual(result["mode"], "live")
        self.assertEqual(post.call_args.args[0], "https://zetaris.example/api/v1.0/sql-editor/sqls/run")
        body = post.call_args.kwargs["json"]
        self.assertEqual(set(body), {"queryId", "sql", "source", "limit"})
        self.assertEqual(body["sql"], "SELECT 1")
        self.assertEqual(body["source"], "SqlEditor")
        self.assertEqual(body["limit"], 100)
        self.assertEqual(uuid.UUID(body["queryId"]).version, 4)
        self.assertEqual(result["data"], [["1"]])
        self.assertEqual(result["row_count"], 1)
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer not-a-real-key")
        self.assertEqual(headers["X-Org-ID"], "123")
        self.assertEqual(uuid.UUID(headers["X-Request-ID"]).version, 4)
        self.assertNotEqual(headers["X-Request-ID"], body["queryId"])
        self.assertEqual(fake_httpx.client_options, [{"trust_env": False, "follow_redirects": False}])

    def test_direct_rest_rejects_remote_plain_http_but_allows_loopback_http(self) -> None:
        remote = ZetarisClient(environment={
            "ZETARIS_REST_URL": "http://remote.example/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })
        local = ZetarisClient(environment={
            "ZETARIS_REST_URL": "http://127.0.0.1:8888/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })

        self.assertEqual(remote.status()["mode"], "fixture")
        self.assertEqual(remote.status()["reason"], "rest_url_must_be_https_or_loopback_http")
        self.assertEqual(local.status()["mode"], "live")

    def test_local_session_uses_loopback_login_then_ui_proxy_without_returning_the_token(self) -> None:
        login = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"accessToken": "session-token-not-for-output", "orgId": 42},
        )
        query = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"data": [{"one": "1"}]},
        )
        fake_httpx = LocalHttpx([login, query])
        post = fake_httpx.post
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.run_sql("SELECT 1")

        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["provider"], "local-session")
        self.assertEqual(result["data"], [{"one": "1"}])
        self.assertNotIn("session-token-not-for-output", repr(result))
        self.assertEqual(post.call_args_list[0].args[0], "http://127.0.0.1:3000/api/auth/login")
        self.assertEqual(post.call_args_list[1].args[0], "http://127.0.0.1:3000/api/proxy/query/sql/start")
        self.assertEqual(post.call_args_list[1].kwargs["json"], {"select": "SELECT 1", "pageLimit": 100})
        self.assertEqual(post.call_args_list[1].kwargs["headers"]["X-Org-ID"], "42")
        self.assertEqual(fake_httpx.client_options, [{"trust_env": False}, {"trust_env": False}])

    def test_local_session_rejects_non_loopback_ui_url(self) -> None:
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "https://outside.example",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        self.assertEqual(client.status()["mode"], "fixture")
        self.assertEqual(client.status()["reason"], "local_ui_must_be_loopback")

    def test_forced_fixture_can_report_local_configuration_without_exposing_it(self) -> None:
        client = ZetarisClient(environment={
            "ZETARIS_FIXTURE_MODE": "1",
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        status = client.status()

        self.assertEqual(status, {"mode": "fixture", "configured": True, "reason": "forced"})
        self.assertNotIn("not-a-real-password", repr(status))

    def test_local_session_accepts_the_platform_id_token_login_field(self) -> None:
        login = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"idToken": "session-token-not-for-output", "orgId": 42},
        )
        query = types.SimpleNamespace(status_code=200, json=lambda: {"data": []})
        fake_httpx = LocalHttpx([login, query])
        post = fake_httpx.post
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://localhost:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.run_sql("SELECT 1")

        self.assertEqual(result["mode"], "live")
        self.assertEqual(post.call_args_list[1].kwargs["headers"]["Authorization"], "Bearer session-token-not-for-output")

    def test_local_session_normalizes_platform_records_without_returning_query_token(self) -> None:
        login = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"idToken": "session-token-not-for-output", "orgId": 42},
        )
        query = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{"one": "1"}], "queryToken": "query-token-not-for-output"},
        )
        fake_httpx = LocalHttpx([login, query])
        post = fake_httpx.post
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.run_sql("SELECT 1")

        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["data"], [{"one": "1"}])
        self.assertNotIn("query-token-not-for-output", repr(result))

    def test_local_session_login_rejection_is_an_explicit_fixture_fallback(self) -> None:
        login = types.SimpleNamespace(status_code=401, json=lambda: {"message": "not used"})
        fake_httpx = LocalHttpx([login])
        post = fake_httpx.post
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.run_sql("SELECT 1")

        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["fallback_reason"], "local_login_auth_error")
        self.assertNotIn("not-a-real-password", repr(result))

    def test_ci_evidence_uses_a_validated_configured_table_name(self) -> None:
        client = ZetarisClient(environment={"ZETARIS_CI_EVIDENCE_TABLE": "actions_nurse_demo.ci_failure_signatures"})

        result = client.query_ci_evidence("Typecheck / tsc", ["TS2305"])

        self.assertIn("FROM actions_nurse_demo.ci_failure_signatures", result["result"]["sql"])

    def test_invalid_ci_evidence_table_name_cannot_reach_live_querying(self) -> None:
        client = ZetarisClient(environment={
            "ZETARIS_CI_EVIDENCE_TABLE": "ci_failure_signatures; DROP TABLE anything",
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })

        result = client.query_ci_evidence("Typecheck / tsc")

        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["result"]["fallback_reason"], "invalid_evidence_table")

    def test_local_evidence_marks_configured_synthetic_provenance(self) -> None:
        login = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"idToken": "session-token-not-for-output", "orgId": 42},
        )
        query = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{"failing_step": "Typecheck / tsc"}]},
        )
        fake_httpx = LocalHttpx([login, query])
        post = fake_httpx.post
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
            "ZETARIS_CI_EVIDENCE_TABLE": "actions_nurse_demo_20261027_f9de7301.ci_failure_signatures",
            "ZETARIS_EVIDENCE_PROVENANCE": "synthetic-local-demo",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.query_ci_evidence("Typecheck / tsc")

        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["source"], "zetaris-local-session")
        self.assertEqual(result["provenance"], "synthetic-local-demo")

    def test_live_evidence_redacts_secret_like_row_values_before_returning_them(self) -> None:
        login = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"idToken": "session-token-not-for-output", "orgId": 42},
        )
        query = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{
                "failing_step": "Typecheck / tsc",
                "failure_signature": "Authorization: Bearer live-row-secret",
                "latest_recommendation": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJsb2NhbCJ9.signaturepart",
                "source": "synthetic local demo",
            }]},
        )
        fake_httpx = LocalHttpx([login, query])
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
            "ZETARIS_CI_EVIDENCE_TABLE": "actions_nurse_demo_20261027_f9de7301.ci_failure_signatures",
            "ZETARIS_EVIDENCE_PROVENANCE": "synthetic-local-demo",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.query_ci_evidence("Typecheck / tsc")

        encoded = repr(result)
        self.assertEqual(result["mode"], "live")
        self.assertNotIn("live-row-secret", encoded)
        self.assertNotIn("eyJhbGciOiJIUzI1NiJ9", encoded)
        self.assertEqual(result["result"]["row_count"], 1)

    def test_live_evidence_projects_canonical_columns_and_redacts_quoted_and_github_markers(self) -> None:
        marker = "ghp_FAKEONLYabcdefghijklmnopqrstuvwx123456"
        login = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"idToken": "session-token-not-for-output", "orgId": 42},
        )
        query = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{
                "failing_step": "Typecheck / tsc",
                "failure_signature": '{"token":"' + marker + '"}',
                "occurrences": 3,
                "latest_recommendation": "Do not paste " + marker + " into CI logs.",
                "source": "synthetic local demo",
                "metadata": marker,
                "token": marker,
            }]},
        )
        fake_httpx = LocalHttpx([login, query])
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.query_ci_evidence("Typecheck / tsc")

        row = result["result"]["data"][0]
        self.assertEqual(set(row), {"failure_signature", "failing_step", "occurrences", "latest_recommendation", "source"})
        self.assertEqual(row["failure_signature"], "[redacted]")
        self.assertEqual(row["latest_recommendation"], "[redacted]")
        self.assertNotIn(marker, repr(result))

    def test_synthetic_local_demo_label_requires_the_owned_demo_table(self) -> None:
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
            "ZETARIS_CI_EVIDENCE_TABLE": "some_other_table",
            "ZETARIS_EVIDENCE_PROVENANCE": "synthetic-local-demo",
        })

        result = client.query_ci_evidence("Typecheck / tsc")

        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["result"]["fallback_reason"], "synthetic_demo_requires_owned_table")
        self.assertNotEqual(result["provenance"], "synthetic-local-demo")

    def test_synthetic_label_rejects_invalid_local_provider_before_direct_rest_can_run(self) -> None:
        response = types.SimpleNamespace(status_code=200, json=lambda: {"data": [["unexpected-live-row"]]})
        fake_httpx = LocalHttpx([response])
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "https://outside.example",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
            "ZETARIS_CI_EVIDENCE_TABLE": "actions_nurse_demo_20261027_f9de7301.ci_failure_signatures",
            "ZETARIS_EVIDENCE_PROVENANCE": "synthetic-local-demo",
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123",
            "ZETARIS_API_KEY": "not-a-real-key",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.query_ci_evidence("Typecheck / tsc")

        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["result"]["fallback_reason"], "synthetic_demo_requires_owned_table")
        self.assertNotEqual(result["provenance"], "synthetic-local-demo")
        self.assertEqual(fake_httpx.client_options, [])

    def test_failed_local_demo_query_uses_fixture_provenance(self) -> None:
        login = types.SimpleNamespace(status_code=401, json=lambda: {"message": "not used"})
        fake_httpx = LocalHttpx([login])
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
            "ZETARIS_CI_EVIDENCE_TABLE": "actions_nurse_demo_20261027_f9de7301.ci_failure_signatures",
            "ZETARIS_EVIDENCE_PROVENANCE": "synthetic-local-demo",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.query_ci_evidence("Typecheck / tsc")

        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(result["source"], "recorded-demo-fixture")
        self.assertNotEqual(result["provenance"], "synthetic-local-demo")

    def test_local_preflight_uses_select_only_probes_supported_by_the_ui_proxy(self) -> None:
        login = types.SimpleNamespace(status_code=200, json=lambda: {"idToken": "token", "orgId": 42})
        first_query = types.SimpleNamespace(status_code=200, json=lambda: {"records": [{"value": "1"}]})
        second_query = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{"query_engine_probe": "7"}]},
        )
        fake_httpx = LocalHttpx([login, first_query, login, second_query])
        post = fake_httpx.post
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.preflight()

        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["checks"][1]["name"], "local_query_engine")
        self.assertEqual(post.call_args_list[3].kwargs["json"]["select"], "SELECT 7 AS query_engine_probe")

    def test_preflight_rejects_wrong_probe_value_without_exposing_raw_rows(self) -> None:
        marker = "ghp_FAKEONLYabcdefghijklmnopqrstuvwx123456"
        login = types.SimpleNamespace(status_code=200, json=lambda: {"idToken": "token", "orgId": 42})
        wrong_probe = types.SimpleNamespace(status_code=200, json=lambda: {"records": [{"value": marker}]})
        expected_engine_probe = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{"query_engine_probe": "7"}]},
        )
        fake_httpx = LocalHttpx([login, wrong_probe, login, expected_engine_probe])
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.preflight()

        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "unavailable")
        self.assertEqual(result["checks"][0]["result"]["reason"], "unexpected_probe_value")
        self.assertNotIn(marker, repr(result))

    def test_preflight_rejects_extra_unrelated_select_one_value(self) -> None:
        login = types.SimpleNamespace(status_code=200, json=lambda: {"idToken": "token", "orgId": 42})
        ambiguous_select_one = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{"probe": "not-one", "unrelated": "1"}]},
        )
        expected_engine_probe = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{"query_engine_probe": "7"}]},
        )
        fake_httpx = LocalHttpx([login, ambiguous_select_one, login, expected_engine_probe])
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.preflight()

        self.assertFalse(result["ok"])
        self.assertEqual(result["checks"][0]["result"]["reason"], "unexpected_probe_value")

    def test_preflight_rejects_extra_unrelated_local_engine_probe_value(self) -> None:
        login = types.SimpleNamespace(status_code=200, json=lambda: {"idToken": "token", "orgId": 42})
        expected_select_one = types.SimpleNamespace(status_code=200, json=lambda: {"records": [{"value": "1"}]})
        ambiguous_engine_probe = types.SimpleNamespace(
            status_code=200,
            json=lambda: {"records": [{"query_engine_probe": "not-seven", "unrelated": "7"}]},
        )
        fake_httpx = LocalHttpx([login, expected_select_one, login, ambiguous_engine_probe])
        client = ZetarisClient(environment={
            "ZETARIS_LOCAL_UI_URL": "http://127.0.0.1:3000",
            "ZETARIS_LOCAL_ADMIN_EMAIL": "local-admin@example.test",
            "ZETARIS_LOCAL_ADMIN_PASSWORD": "not-a-real-password",
        })

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.preflight()

        self.assertFalse(result["ok"])
        self.assertEqual(result["checks"][1]["result"]["reason"], "unexpected_probe_value")

    def test_empty_database_list_is_a_valid_live_response(self) -> None:
        response = types.SimpleNamespace(status_code=200, json=lambda: {"data": []})
        client = ZetarisClient(environment={
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123", "ZETARIS_API_KEY": "not-a-real-key",
        })
        fake_httpx = LocalHttpx([response])
        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            result = client.run_sql("SHOW LIGHTNING DATABASES")
        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["data"], [])
        self.assertEqual(result["row_count"], 0)

    def test_malformed_success_body_does_not_claim_live_success(self) -> None:
        client = ZetarisClient(environment={
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "123", "ZETARIS_API_KEY": "not-a-real-key",
        })
        for body in ({"error": "query rejected"}, {"data": None}, [], {"data": "invalid"}):
            with self.subTest(body=body):
                response = types.SimpleNamespace(status_code=200, json=lambda: body)
                fake_httpx = LocalHttpx([response])
                with patch.dict(sys.modules, {"httpx": fake_httpx}):
                    result = client.run_sql("SELECT 1")
                self.assertEqual(result["mode"], "fixture")
                self.assertEqual(result["fallback_reason"], "invalid_result_shape")

    def test_organization_name_is_not_a_numeric_id(self) -> None:
        client = ZetarisClient(environment={
            "ZETARIS_REST_URL": "https://zetaris.example/api/v1.0",
            "ZETARIS_ORG_ID": "demo-org", "ZETARIS_API_KEY": "not-a-real-key",
        })
        self.assertEqual(client.status()["reason"], "org_id_must_be_numeric")
        self.assertEqual(client.run_sql("SELECT 1")["mode"], "fixture")

    def test_write_and_multiple_statement_sql_are_rejected(self) -> None:
        for sql in ("DROP TABLE ci_failure_signatures", "SELECT 1; DELETE FROM ci_failure_signatures"):
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    validate_read_only_sql(sql)


if __name__ == "__main__":
    unittest.main()


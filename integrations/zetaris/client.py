"""Small, read-only Zetaris REST client with deterministic demo fixtures.

The client deliberately accepts only one read-only Lightning SQL statement at a
time.  It is safe to call from the triage path: missing credentials, forced
fixture mode, and an unavailable or unauthorized service all return a clearly
labelled fixture response instead of interrupting a diagnosis.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
RUN_QUERY_PATH = "/sql-editor/sqls/run"
READ_ONLY_STARTERS = {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH"}
WRITE_TOKENS = re.compile(
    r"\b(?:ALTER|CALL|COPY|CREATE|DELETE|DROP|EXPORT|GRANT|INSERT|MERGE|"
    r"REVOKE|SET|TRUNCATE|UPDATE|USE|VACUUM|INTO)\b",
    re.IGNORECASE,
)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def load_environment(repo_root: Path = ROOT) -> dict[str, str]:
    """Load ``.env`` then ``.env.local`` without replacing process variables.

    ``.env.local`` takes precedence over ``.env``. Explicit process environment
    values remain highest priority, which keeps CI and shell-provided secrets
    out of files while preserving the familiar dotenv ordering for local runs.
    """
    values: dict[str, str] = {}
    try:
        from dotenv import dotenv_values
    except ImportError:
        return {key: value for key, value in os.environ.items() if value is not None}

    for path in (repo_root / ".env", repo_root / ".env.local"):
        if not path.is_file():
            continue
        for key, value in dotenv_values(path).items():
            if key and value is not None:
                values[key] = value
    values.update({key: value for key, value in os.environ.items() if value is not None})
    return values


def validate_read_only_sql(sql: str) -> str:
    """Return one normalized read-only statement or raise ``ValueError``.

    The integration is an evidence reader, never a workflow repair mechanism.
    Rejecting unsupported SQL is intentional rather than attempting to infer
    whether a complex query has side effects.
    """
    statement = str(sql or "").strip()
    if not statement:
        raise ValueError("Zetaris SQL must not be empty.")
    if statement.endswith(";"):
        statement = statement[:-1].rstrip()
    if ";" in statement:
        raise ValueError("Zetaris accepts one SQL statement per request.")

    first = re.match(r"(?:/\*.*?\*/\s*)*(?:--[^\n]*(?:\n|$)\s*)*([A-Za-z]+)", statement, re.S)
    if not first or first.group(1).upper() not in READ_ONLY_STARTERS:
        raise ValueError("Only read-only SELECT, SHOW, DESCRIBE, EXPLAIN, and WITH SQL is allowed.")
    if WRITE_TOKENS.search(statement):
        raise ValueError("Write, permission, or administration SQL is not allowed in Actions Nurse.")
    return statement


def _escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


@dataclass(frozen=True)
class ZetarisConfig:
    rest_url: str
    org_id: str
    api_key: str
    force_fixture: bool

    @property
    def credentials_ready(self) -> bool:
        return bool(self.rest_url and self.org_id and self.api_key)

    @property
    def valid_rest_url(self) -> bool:
        return self.rest_url.rstrip("/").endswith("/api/v1.0")


class ZetarisClient:
    """Direct REST client for one read-only Zetaris Lightning SQL statement."""

    def __init__(self, environment: Mapping[str, str] | None = None, *, timeout_seconds: float = 12.0) -> None:
        env = dict(load_environment() if environment is None else environment)
        self.config = ZetarisConfig(
            rest_url=env.get("ZETARIS_REST_URL", "").strip().rstrip("/"),
            org_id=env.get("ZETARIS_ORG_ID", "").strip(),
            api_key=env.get("ZETARIS_API_KEY", "").strip(),
            force_fixture=_truthy(env.get("ZETARIS_FIXTURE_MODE")),
        )
        self.timeout_seconds = timeout_seconds

    def status(self) -> dict[str, Any]:
        """Return configuration state without ever exposing credential values."""
        if self.config.force_fixture:
            return {"mode": "fixture", "configured": self.config.credentials_ready, "reason": "forced"}
        if not self.config.credentials_ready:
            return {"mode": "fixture", "configured": False, "reason": "missing_credentials"}
        if not self.config.valid_rest_url:
            return {"mode": "fixture", "configured": False, "reason": "rest_url_must_end_in_api_v1_0"}
        if not re.fullmatch(r"[0-9]+", self.config.org_id):
            return {"mode": "fixture", "configured": False, "reason": "org_id_must_be_numeric"}
        return {"mode": "live", "configured": True, "reason": "credentials_present"}

    def _fixture_name(self, sql: str) -> str:
        normalized = " ".join(sql.upper().split())
        if re.fullmatch(r"SELECT\s+1(?:\s+AS\s+[A-Z_][A-Z0-9_]*)?", normalized):
            return "select-1.json"
        if normalized == "SHOW LIGHTNING DATABASES":
            return "show-lightning-databases.json"
        return "ci-failure-signatures.json"

    def _fixture_result(self, sql: str, *, reason: str) -> dict[str, Any]:
        name = self._fixture_name(sql)
        payload = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
        rows = payload.get("data", [])

        # Make the recorded evidence behave like the query's equality predicate
        # while keeping every fixture record inspectable in version control.
        step_match = re.search(r"\bWHERE\s+failing_step\s*=\s*'((?:''|[^'])*)'", sql, re.I)
        if name == "ci-failure-signatures.json" and step_match:
            requested_step = step_match.group(1).replace("''", "'")
            rows = [row for row in rows if len(row) > 1 and row[1] == requested_step]

        return {
            "ok": True,
            "mode": "fixture",
            "sql": sql,
            "fixture": name,
            "fallback_reason": reason,
            "notice": payload.get("notice", "Recorded demo fixture; not live Zetaris data."),
            "columns": payload.get("columns", []),
            "data": rows,
            "row_count": len(rows),
        }

    def run_sql(self, sql: str) -> dict[str, Any]:
        """Run one read-only SQL statement or return a labelled fixture result.

        Direct REST uses the ``/sql-editor/sqls/run`` endpoint (not the UI proxy),
        bearer key, organization ID, and a fresh request UUID required by the
        Zetaris setup guide. Returned dictionaries contain no request headers or
        secret material and are JSON serializable for FastAPI responses.
        """
        statement = validate_read_only_sql(sql)
        state = self.status()
        if state["mode"] == "fixture":
            return self._fixture_result(statement, reason=str(state["reason"]))

        try:
            import httpx
        except ImportError:
            return self._fixture_result(statement, reason="http_client_unavailable")

        request_id = str(uuid.uuid4())
        try:
            response = httpx.post(
                f"{self.config.rest_url}{RUN_QUERY_PATH}",
                json={"queryId": str(uuid.uuid4()), "sql": statement, "source": "SqlEditor", "limit": 100},
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "X-Org-ID": self.config.org_id,
                    "X-Request-ID": request_id,
                    "Content-Type": "application/json",
                },
                timeout=self.timeout_seconds,
            )
        except httpx.RequestError:
            return self._fixture_result(statement, reason="network_error")

        if response.status_code in {401, 403}:
            return self._fixture_result(statement, reason="auth_error")
        if response.status_code < 200 or response.status_code >= 300:
            return self._fixture_result(statement, reason=f"http_{response.status_code}")
        try:
            data = response.json()
        except ValueError:
            return self._fixture_result(statement, reason="invalid_json_response")
        # The direct API returns its result rows under data. Do not turn an
        # arbitrary HTTP-200 error body into a claimed successful live query.
        if not isinstance(data, dict) or not isinstance(data.get("data"), list):
            return self._fixture_result(statement, reason="invalid_result_shape")
        rows = data["data"]
        return {
            "ok": True,
            "mode": "live",
            "sql": statement,
            "request_id": request_id,
            "data": rows,
            "row_count": len(rows),
        }

    def preflight(self) -> dict[str, Any]:
        """Run the two documented, read-only Zetaris access checks."""
        checks = [
            {"name": "select_1", "result": self.run_sql("SELECT 1")},
            {"name": "lightning_databases", "result": self.run_sql("SHOW LIGHTNING DATABASES")},
        ]
        modes = {check["result"]["mode"] for check in checks}
        return {
            "ok": all(bool(check["result"].get("ok")) for check in checks),
            "mode": "live" if modes == {"live"} else "fixture",
            "read_only": True,
            "checks": checks,
        }

    def query_ci_evidence(self, failing_step: str, patterns: list[str] | None = None) -> dict[str, Any]:
        """Ask for prior CI signatures that match the deterministic diagnosis.

        ``ci_failure_signatures`` is a deliberately small example logical table.
        Teams can point it at their own federated Zetaris evidence source; when
        it is absent or fixture mode is active, the recorded synthetic demo rows
        make that state explicit rather than pretending they are live evidence.
        """
        step = str(failing_step or "Unknown")[:200]
        sql = (
            "SELECT failure_signature, failing_step, occurrences, latest_recommendation, source "
            "FROM ci_failure_signatures "
            f"WHERE failing_step = '{_escape_sql_literal(step)}' "
            "ORDER BY observed_at DESC LIMIT 3"
        )
        result = self.run_sql(sql)
        return {
            "mode": result["mode"],
            "source": "zetaris-lightning" if result["mode"] == "live" else "recorded-demo-fixture",
            "failing_step": step,
            "patterns": [str(pattern)[:300] for pattern in (patterns or [])][:8],
            "result": result,
        }


def get_client() -> ZetarisClient:
    """Build a client from ``.env``, then ``.env.local``, then process env."""
    return ZetarisClient()


def status() -> dict[str, Any]:
    return get_client().status()


def preflight() -> dict[str, Any]:
    return get_client().preflight()


def query_ci_evidence(failing_step: str, patterns: list[str] | None = None) -> dict[str, Any]:
    return get_client().query_ci_evidence(failing_step, patterns)


if __name__ == "__main__":
    print(json.dumps(preflight(), indent=2, ensure_ascii=False))


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
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
RUN_QUERY_PATH = "/sql-editor/sqls/run"
READ_ONLY_STARTERS = {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH"}
WRITE_TOKENS = re.compile(
    r"\b(?:ALTER|CALL|COPY|CREATE|DELETE|DROP|EXPORT|GRANT|INSERT|MERGE|"
    r"REVOKE|SET|TRUNCATE|UPDATE|USE|VACUUM|INTO)\b",
    re.IGNORECASE,
)
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}\Z")
BEARER_VALUE = re.compile(r"\b(?:authorization\s*[:=]\s*)?bearer\s+\S+", re.IGNORECASE)
NAMED_SECRET_VALUE = re.compile(r"\b(?:api[_-]?key|password|token)\s*[:=]\s*\S+", re.IGNORECASE)
JWT_LIKE_VALUE = re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
QUOTED_SECRET_VALUE = re.compile(
    r"[\"']?(?:authorization|api[_-]?key|password|token|secret|access[_-]?token|refresh[_-]?token|"
    r"private[_-]?key|client[_-]?secret|credential(?:s)?)[\"']?\s*[:=]\s*(?:[\"'][^\"']*[\"']|[^\s,;}\]]+)",
    re.IGNORECASE,
)
GITHUB_TOKEN_VALUE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9_-]{8,}|github_pat_[A-Za-z0-9_]{8,})\b",
    re.IGNORECASE,
)
EVIDENCE_COLUMNS = (
    "failure_signature",
    "failing_step",
    "occurrences",
    "latest_recommendation",
    "source",
)
LOCAL_DEMO_EVIDENCE_TABLE = "actions_nurse_demo_20261027_f9de7301.ci_failure_signatures"
SYNTHETIC_LOCAL_DEMO_PROVENANCE = "synthetic-local-demo"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


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


def _safe_evidence_text(value: Any, *, limit: int = 800) -> str:
    """Bound and conservatively redact text before the triage API serializes it."""
    if isinstance(value, (Mapping, list, tuple)):
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except (TypeError, ValueError):
            text = str(value)
    else:
        text = str(value or "")
    if (
        BEARER_VALUE.search(text)
        or NAMED_SECRET_VALUE.search(text)
        or QUOTED_SECRET_VALUE.search(text)
        or JWT_LIKE_VALUE.search(text)
        or GITHUB_TOKEN_VALUE.search(text)
    ):
        return "[redacted]"
    return text[:limit]


def _canonical_evidence_column(value: Any) -> str | None:
    """Map a returned column name to the fixed, query-owned evidence schema."""
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return normalized if normalized in EVIDENCE_COLUMNS else None


def _safe_occurrences(value: Any) -> int | float | str:
    """Keep occurrence values compact without accepting arbitrary structured text."""
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    return text if re.fullmatch(r"\d{1,12}", text) else ""


def _safe_evidence_rows(rows: Any) -> list[dict[str, Any]]:
    """Project query rows onto the fixed evidence schema and redact their values."""
    if not isinstance(rows, list):
        return []
    safe_rows: list[dict[str, Any]] = []
    for row in rows[:3]:
        if isinstance(row, Mapping):
            raw_values: dict[str, Any] = {}
            for key, value in row.items():
                column = _canonical_evidence_column(key)
                if column and column not in raw_values:
                    raw_values[column] = value
        elif isinstance(row, (list, tuple)):
            raw_values = dict(zip(EVIDENCE_COLUMNS, row, strict=False))
        else:
            continue
        if not raw_values:
            continue
        safe_rows.append({
            column: _safe_occurrences(raw_values[column])
            if column == "occurrences"
            else _safe_evidence_text(raw_values[column])
            for column in EVIDENCE_COLUMNS
            if column in raw_values
        })
    return safe_rows


def _probe_value_matches(rows: Any, expected: int, *, expected_name: str | None = None) -> bool:
    """Check one unambiguous, deterministic preflight scalar without returning it."""
    if not isinstance(rows, list) or len(rows) != 1:
        return False
    row = rows[0]
    if isinstance(row, Mapping):
        if len(row) != 1:
            return False
        name, value = next(iter(row.items()))
        normalized_name = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
        if expected_name and normalized_name not in {expected_name, "value"}:
            return False
    elif isinstance(row, (list, tuple)):
        if len(row) != 1:
            return False
        value = row[0]
    else:
        value = row
    return not isinstance(value, (Mapping, list, tuple)) and str(value).strip() == str(expected)


def _safe_preflight_check(
    name: str,
    result: Mapping[str, Any],
    *,
    expected_probe: int | None = None,
    expected_probe_name: str | None = None,
) -> dict[str, Any]:
    """Return a row-free summary of one fixed, read-only preflight query."""
    raw_rows = result.get("data")
    row_count = len(raw_rows) if isinstance(raw_rows, list) else 0
    mode = str(result.get("mode") or "unavailable")
    ok = bool(result.get("ok"))
    reason = ""
    if mode == "live" and expected_probe is not None and not _probe_value_matches(
        raw_rows,
        expected_probe,
        expected_name=expected_probe_name,
    ):
        mode = "unavailable"
        ok = False
        reason = "unexpected_probe_value"

    summary: dict[str, Any] = {"ok": ok, "mode": mode, "row_count": row_count}
    if mode == "live" and result.get("provider") in {"direct-rest", "local-session"}:
        summary["provider"] = result["provider"]
    if reason:
        summary["reason"] = reason
    elif mode == "fixture":
        if result.get("fixture"):
            summary["fixture"] = _safe_evidence_text(result["fixture"], limit=120)
        if result.get("fallback_reason"):
            summary["reason"] = _safe_evidence_text(result["fallback_reason"], limit=120)
    return {"name": name, "result": summary}


@dataclass(frozen=True)
class ZetarisConfig:
    rest_url: str
    org_id: str
    api_key: str
    local_ui_url: str
    local_admin_email: str
    local_admin_password: str
    evidence_table: str
    evidence_provenance: str
    force_fixture: bool

    @property
    def credentials_ready(self) -> bool:
        return bool(self.rest_url and self.org_id and self.api_key)

    @property
    def local_session_requested(self) -> bool:
        return bool(self.local_ui_url or self.local_admin_email or self.local_admin_password)

    @property
    def local_session_ready(self) -> bool:
        return bool(self.local_ui_url and self.local_admin_email and self.local_admin_password)

    @property
    def valid_rest_url(self) -> bool:
        parsed = urlparse(self.rest_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") != "/api/v1.0"
        ):
            return False
        return parsed.scheme == "https" or parsed.hostname in LOOPBACK_HOSTS

    @property
    def valid_local_ui_url(self) -> bool:
        parsed = urlparse(self.local_ui_url)
        return (
            parsed.scheme == "http"
            and parsed.hostname in LOOPBACK_HOSTS
            and not parsed.username
            and not parsed.password
        )

    @property
    def valid_evidence_table(self) -> bool:
        return bool(IDENTIFIER.fullmatch(self.evidence_table))

    @property
    def synthetic_local_demo_requested(self) -> bool:
        return self.evidence_provenance == SYNTHETIC_LOCAL_DEMO_PROVENANCE

    @property
    def owned_synthetic_local_demo(self) -> bool:
        return (
            self.synthetic_local_demo_requested
            and self.evidence_table == LOCAL_DEMO_EVIDENCE_TABLE
            and self.local_session_ready
            and self.valid_local_ui_url
        )


class ZetarisClient:
    """Direct REST client for one read-only Zetaris Lightning SQL statement."""

    def __init__(self, environment: Mapping[str, str] | None = None, *, timeout_seconds: float = 12.0) -> None:
        env = dict(load_environment() if environment is None else environment)
        self.config = ZetarisConfig(
            rest_url=env.get("ZETARIS_REST_URL", "").strip().rstrip("/"),
            org_id=env.get("ZETARIS_ORG_ID", "").strip(),
            api_key=env.get("ZETARIS_API_KEY", "").strip(),
            local_ui_url=env.get("ZETARIS_LOCAL_UI_URL", "").strip().rstrip("/"),
            local_admin_email=env.get("ZETARIS_LOCAL_ADMIN_EMAIL", "").strip(),
            local_admin_password=env.get("ZETARIS_LOCAL_ADMIN_PASSWORD", "").strip(),
            evidence_table=env.get("ZETARIS_CI_EVIDENCE_TABLE", "ci_failure_signatures").strip(),
            evidence_provenance=env.get("ZETARIS_EVIDENCE_PROVENANCE", "").strip(),
            force_fixture=_truthy(env.get("ZETARIS_FIXTURE_MODE")),
        )
        self.timeout_seconds = timeout_seconds

    def status(self) -> dict[str, Any]:
        """Return configuration state without ever exposing credential values."""
        if self.config.force_fixture:
            return {
                "mode": "fixture",
                "configured": self.config.credentials_ready or self.config.local_session_ready,
                "reason": "forced",
            }
        if not self.config.valid_evidence_table:
            return {"mode": "fixture", "configured": False, "reason": "invalid_evidence_table"}
        if self.config.synthetic_local_demo_requested and not self.config.owned_synthetic_local_demo:
            return {"mode": "fixture", "configured": False, "reason": "synthetic_demo_requires_owned_table"}
        if self.config.local_session_ready and self.config.valid_local_ui_url:
            return {"mode": "live", "configured": True, "reason": "local_session_ready", "provider": "local-session"}
        if self.config.credentials_ready:
            if not self.config.valid_rest_url:
                return {"mode": "fixture", "configured": False, "reason": "rest_url_must_be_https_or_loopback_http"}
            if not re.fullmatch(r"[0-9]+", self.config.org_id):
                return {"mode": "fixture", "configured": False, "reason": "org_id_must_be_numeric"}
            return {"mode": "live", "configured": True, "reason": "credentials_present", "provider": "direct-rest"}
        if self.config.local_session_requested:
            if not self.config.valid_local_ui_url:
                return {"mode": "fixture", "configured": False, "reason": "local_ui_must_be_loopback"}
            return {"mode": "fixture", "configured": False, "reason": "missing_local_session_credentials"}
        return {"mode": "fixture", "configured": False, "reason": "missing_credentials"}

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
        if state.get("provider") == "local-session":
            return self._run_local_session_sql(httpx, statement, request_id)

        try:
            with httpx.Client(trust_env=False, follow_redirects=False) as session:
                response = session.post(
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
            "provider": "direct-rest",
            "sql": statement,
            "request_id": request_id,
            "data": rows,
            "row_count": len(rows),
        }

    def _run_local_session_sql(self, httpx: Any, statement: str, request_id: str) -> dict[str, Any]:
        """Run read-only SQL through a fresh, loopback-only local UI session."""
        try:
            with httpx.Client(trust_env=False) as session:
                login_response = session.post(
                    f"{self.config.local_ui_url}/api/auth/login",
                    json={
                        "username": self.config.local_admin_email,
                        "password": self.config.local_admin_password,
                    },
                    timeout=self.timeout_seconds,
                )
        except httpx.RequestError:
            return self._fixture_result(statement, reason="local_login_network_error")

        if login_response.status_code in {401, 403}:
            return self._fixture_result(statement, reason="local_login_auth_error")
        if login_response.status_code < 200 or login_response.status_code >= 300:
            return self._fixture_result(statement, reason=f"local_login_http_{login_response.status_code}")
        try:
            login = login_response.json()
        except ValueError:
            return self._fixture_result(statement, reason="local_login_invalid_json")
        if not isinstance(login, dict):
            return self._fixture_result(statement, reason="local_login_invalid_shape")
        token = login.get("idToken") or login.get("accessToken") or login.get("access_token") or login.get("token")
        org_id = login.get("orgId") or login.get("org_id")
        if not isinstance(token, str) or not token or not isinstance(org_id, (str, int)):
            return self._fixture_result(statement, reason="local_login_invalid_shape")

        try:
            with httpx.Client(trust_env=False) as session:
                response = session.post(
                    f"{self.config.local_ui_url}/api/proxy/query/sql/start",
                    json={"select": statement, "pageLimit": 100},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-Org-ID": str(org_id),
                        "X-Request-ID": request_id,
                        "Content-Type": "application/json",
                    },
                    timeout=self.timeout_seconds,
                )
        except httpx.RequestError:
            return self._fixture_result(statement, reason="local_query_network_error")

        if response.status_code in {401, 403}:
            return self._fixture_result(statement, reason="local_query_auth_error")
        if response.status_code < 200 or response.status_code >= 300:
            return self._fixture_result(statement, reason=f"local_query_http_{response.status_code}")
        try:
            data = response.json()
        except ValueError:
            return self._fixture_result(statement, reason="local_query_invalid_json")
        if not isinstance(data, dict):
            return self._fixture_result(statement, reason="local_query_invalid_result_shape")
        rows = data.get("records") if isinstance(data.get("records"), list) else data.get("data")
        if not isinstance(rows, list):
            return self._fixture_result(statement, reason="local_query_invalid_result_shape")
        return {
            "ok": True,
            "mode": "live",
            "provider": "local-session",
            "sql": statement,
            "request_id": request_id,
            "data": rows,
            "row_count": len(rows),
        }

    def preflight(self) -> dict[str, Any]:
        """Run fixed read-only checks and return summaries without upstream rows."""
        provider = self.status().get("provider")
        checks = [_safe_preflight_check("select_1", self.run_sql("SELECT 1"), expected_probe=1)]
        if provider == "local-session":
            # The local UI proxy deliberately accepts SELECT requests only. A
            # distinct SELECT confirms the same UI -> API -> driver path without
            # incorrectly reporting a rejected SHOW statement as a platform
            # outage.
            checks.append(_safe_preflight_check(
                "local_query_engine",
                self.run_sql("SELECT 7 AS query_engine_probe"),
                expected_probe=7,
                expected_probe_name="query_engine_probe",
            ))
        else:
            checks.append(_safe_preflight_check("lightning_databases", self.run_sql("SHOW LIGHTNING DATABASES")))
        modes = {check["result"]["mode"] for check in checks}
        all_ok = all(bool(check["result"].get("ok")) for check in checks)
        return {
            "ok": all_ok,
            "mode": "live" if all_ok and modes == {"live"} else "unavailable" if "unavailable" in modes else "fixture",
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
        table = self.config.evidence_table if self.config.valid_evidence_table else "ci_failure_signatures"
        sql = (
            "SELECT failure_signature, failing_step, occurrences, latest_recommendation, source "
            f"FROM {table} "
            f"WHERE failing_step = '{_escape_sql_literal(step)}' "
            "ORDER BY observed_at DESC LIMIT 3"
        )
        result = (
            self._fixture_result(sql, reason="invalid_evidence_table")
            if not self.config.valid_evidence_table
            else self.run_sql(sql)
        )
        safe_rows = _safe_evidence_rows(result.get("data"))
        result = {
            **result,
            "data": safe_rows,
            "row_count": len(safe_rows),
        }
        provenance = (
            SYNTHETIC_LOCAL_DEMO_PROVENANCE
            if (
                self.config.owned_synthetic_local_demo
                and result.get("mode") == "live"
                and result.get("provider") == "local-session"
            )
            else self.config.evidence_provenance
            if self.config.evidence_provenance != SYNTHETIC_LOCAL_DEMO_PROVENANCE
            else "unclassified"
        )
        if not provenance:
            provenance = "local-session-unclassified" if result.get("provider") == "local-session" else "unclassified"
        return {
            "mode": result["mode"],
            "source": (
                "zetaris-local-session"
                if result.get("provider") == "local-session"
                else "zetaris-lightning"
                if result["mode"] == "live"
                else "recorded-demo-fixture"
            ),
            "provenance": provenance,
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


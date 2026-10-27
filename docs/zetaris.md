# Zetaris evidence hook

Actions Nurse can attach read-only CI-history evidence after Rules and Gemma
finish a diagnosis. The hook is deliberately narrow: it runs Lightning SQL
only, never changes a workflow or a Zetaris object, and it never includes a
credential in an API response, activity log, or demo file.

## Local credential handoff

Copy the Zetaris section of [`.env.example`](../.env.example) into a local,
gitignored `.env.local` file. The client reads `.env` first, then `.env.local`;
explicit shell environment values take precedence over both.

```dotenv
ZETARIS_REST_URL=https://your-zetaris-host/api/v1.0
ZETARIS_ORG_ID=123
ZETARIS_API_KEY=replace-with-your-user-created-api-key
```

For Zetaris Cloud, use the API base supplied by the organiser or Cloud UI. It
must end in `/api/v1.0`; the browser UI address belongs in the optional
`ZETARIS_BASE_URL` and is not used by this direct REST client. Find the numeric
organisation ID under **Management → Organisation**. Create a user API token
under **Management → API Tokens** and save it locally: the token is shown only
once and must never be pasted into a prompt or committed.

The client sends one SQL statement to:

```text
POST {ZETARIS_REST_URL}/sql-editor/sqls/run
Authorization: Bearer {ZETARIS_API_KEY}
X-Org-ID: {ZETARIS_ORG_ID}
X-Request-ID: {uuid4}
Content-Type: application/json

{"queryId":"<fresh UUID>","sql":"...","source":"SqlEditor","limit":100}
```

It accepts only `SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`, or read-only `WITH`
statements. Multi-statement, write, admin, permission, and export SQL are
rejected before a network call.

## Local evaluation session (no API token)

The installed local Zetaris evaluation bundle can be queried without creating
an API token. Set these values only in a shell or an ignored local file:

```dotenv
ZETARIS_LOCAL_UI_URL=http://127.0.0.1:3000
ZETARIS_LOCAL_ADMIN_EMAIL=local-admin-email
ZETARIS_LOCAL_ADMIN_PASSWORD=local-admin-password
ZETARIS_CI_EVIDENCE_TABLE=actions_nurse_demo_20261027_f9de7301.ci_failure_signatures
ZETARIS_EVIDENCE_PROVENANCE=synthetic-local-demo
```

This mode is intentionally limited to `http://127.0.0.1`, `localhost`, or
`[::1]`; a non-loopback UI URL is rejected before a request. The client makes
a fresh login for each read-only query and uses the returned session only in
memory. It never returns the session token or the platform password. The local
UI proxy accepts `SELECT` only and returns `records`, which the client
normalizes to its ordinary `data` response shape.

Evidence responses are limited to three compact rows and redact bearer-style,
named-secret, and JWT-like text before FastAPI serializes them. The browser
applies the same defensive redaction before rendering a row, request ID, or SQL.

The local mode takes precedence when its variables are present. It is for a
local evaluation stack, not a way to reuse a browser session or cloud account.

## Verification

Direct REST preflight runs the two checks recommended by Zetaris:

```bash
python3 -m integrations.zetaris.client
```

It issues `SELECT 1` and `SHOW LIGHTNING DATABASES`. In local-session mode the
UI proxy permits `SELECT` only, so preflight uses `SELECT 1` and `SELECT 7 AS
query_engine_probe` instead. A live result reports `"mode": "live"`. Zetaris
returns values as strings, so the client keeps row values intact instead of
coercing numeric fields. A missing or malformed result list becomes an explicit
fixture fallback, not a successful live claim.

This direct REST request follows the [official runner at commit
6a2fbaa](https://github.com/zetaris/getting-started/blob/6a2fbaa47c32c9ac33f6584c64b43b146c621bed/scripts/zetaris_sql.py).
The UI-proxy path `/api/proxy/sql-editor/sqls/run-query` is a different route
on the web UI origin; it is not appended to `/api/v1.0` here. Before claiming
compatibility with a particular installed Zetaris version, compare its current
OpenAPI specification and run the two read-only checks against that instance.
Fixture success and `status()` reporting credentials present do not verify a
live connection. Confirm `SELECT 1` actually returns `1` and both preflight
checks report `mode: "live"`.

For a focused evidence query, the app calls
`query_ci_evidence(failing_step, patterns)`. Set
`ZETARIS_CI_EVIDENCE_TABLE` to a simple one-to-three-part SQL identifier; other
values are rejected before they can enter a query. Point it at a federated CI
evidence source in a normal deployment.

### Explicit synthetic local demo data

For the local hackathon demonstration only, the tracked
[`demo/zetaris/ci_failure_signatures.csv`](../demo/zetaris/ci_failure_signatures.csv)
contains four newly authored synthetic rows. It is not historic CI data. The
opt-in seed command creates only the unique
`actions_nurse_demo_20261027_f9de7301.ci_failure_signatures` object and refuses
to replace a differing CSV or table:

```bash
ZETARIS_PLATFORM_DIR=/path/to/zetaris-platform \
  bash scripts/seed_local_zetaris_demo.sh --apply
```

It uses the bundle's loopback JDBC driver, first validates the existing owned
object if present, and performs no `DROP`, delete, overwrite, or change to an
unrelated Zetaris object. Set `ZETARIS_EVIDENCE_PROVENANCE=synthetic-local-demo`
when demonstrating it. A response remains `mode: "live"` because rows came
from a real local Zetaris query, while its separate `provenance` field makes the
synthetic dataset clear.

To launch the application without copying a password into the repository:

```bash
ZETARIS_PLATFORM_DIR=/path/to/zetaris-platform \
  NURSE_RULES_ONLY=true bash scripts/run_local_zetaris_demo.sh
```

The runner reads only the two needed values from the platform `.env` into its
own process, binds Actions Nurse to `127.0.0.1:8787` by default, and never
prints or writes those values. Use `NURSE_PORT` to select another loopback port.

## Fixture mode for the hackathon demo

No credentials are needed to run the demo. Fixture mode activates when any
required direct REST value is missing, `ZETARIS_FIXTURE_MODE=1`, a network
request cannot complete, or Zetaris returns 401/403. The response always says
`"mode": "fixture"`, names the recorded JSON fixture, and includes a
`fallback_reason`; it does not present synthetic records as live evidence.

The three committed fixtures cover `SELECT 1`, `SHOW LIGHTNING DATABASES`, and
a small synthetic CI-failure-signature table. They make the presentation
repeatable while leaving a clean hook for Hackathon or Zetaris Cloud access.

## Python contract used by the app

```python
from integrations.zetaris import preflight, query_ci_evidence, status

status()  # {"mode": "fixture" | "live", "configured": bool, "reason": "..."}
preflight()  # {"ok": bool, "mode": "...", "read_only": True, "checks": [...]}
query_ci_evidence("Typecheck / tsc", ["TS2305"])
# {"mode": "...", "source": "...", "provenance": "...", "failing_step": "...", "patterns": [...], "result": {...}}
```

All returned values are JSON serializable, so the FastAPI layer can attach the
evidence unchanged. The result object never contains the API key or request
headers.

Further setup detail is available in the [official Zetaris client setup
guide](https://zetaris.github.io/getting-started/docs/connections/client-setup.html).


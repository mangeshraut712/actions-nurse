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

## Verification

The read-only preflight runs the two checks recommended by Zetaris:

```bash
python3 -m integrations.zetaris.client
```

It issues `SELECT 1` and `SHOW LIGHTNING DATABASES`. A live result reports
`"mode": "live"`. Zetaris returns values as strings, so the client keeps the
row values intact instead of coercing numeric fields. It extracts the response's
`data` list and reports `row_count`; a missing or malformed list becomes an
explicit fixture fallback, not a successful live claim. An empty list is valid
for a clean instance's database listing.

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
`query_ci_evidence(failing_step, patterns)`. Its example SQL reads a logical
`ci_failure_signatures` table. Point that table name at a federated CI evidence
source in your own Zetaris environment; no DDL is included here because this
project is read-only by design.

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
# {"mode": "...", "source": "...", "failing_step": "...", "patterns": [...], "result": {...}}
```

All returned values are JSON serializable, so the FastAPI layer can attach the
evidence unchanged. The result object never contains the API key or request
headers.

Further setup detail is available in the [official Zetaris client setup
guide](https://zetaris.github.io/getting-started/docs/connections/client-setup.html).


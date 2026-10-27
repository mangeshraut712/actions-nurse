# Judge demo · 90 seconds

The reliable route is deliberately key-free: Rules-only triage, H-MEM installed locally, and Zetaris fixture mode. If live Zetaris credentials are configured, say so and show the `live` mode; otherwise call the fixture exactly what it is.

## Before the clock starts

In one terminal:

```bash
cd meterless && npm ci && npm run setup && cd ..
ZETARIS_FIXTURE_MODE=1 NURSE_RULES_ONLY=true uvicorn nurse:app --host 127.0.0.1 --port 8787
```

In a second terminal, keep this command ready:

```bash
ZETARIS_FIXTURE_MODE=1 NURSE_RULES_ONLY=true bash scripts/smoke_agentathon.sh
```

Open <http://127.0.0.1:8787> or show the terminal output. Do not claim a Gemini or Zetaris cloud call unless the response mode says it actually happened.

## 0:00–0:12 · The promise

**Show:** the web app title or the smoke command header.

> “Actions Nurse triages failed GitHub Actions, explains likely root cause, remembers past failures. It is a first-response tool: it explains and records; it does not execute a fix.”

## 0:12–0:30 · Triage an actual red fixture

**Show:** `npm-typecheck.txt` in the browser fixture picker, then click triage; or show the smoke output for its HTTP triage request.

> “This typecheck failed because imports refer to exports that no longer exist. Rules recognizes the log signature locally, so this diagnosis is reproducible even without a model key. Gemma remains available as the optional explanatory path, with Rules checking known categories.”

Point to the failing step and the suggested local `npm run typecheck` check. Do not claim that the app executed it.

## 0:30–0:45 · Zetaris evidence, honestly labeled

**Show:** the `zetaris` field in the enriched response or `GET /api/zetaris/preflight`.

> “The Zetaris client uses read-only Lightning SQL. This machine is showing **fixture mode** [or **live mode** if returned], so the evidence source is explicit. The same call shape runs `SELECT 1`, `SHOW LIGHTNING DATABASES`, and a scoped historical CI-evidence query when credentials are present.”

## 0:45–1:05 · Meterless H-MEM recall

**Show:** a clean two-pass recall, then run:

```bash
bash scripts/demo_hmem_two_pass.sh
```

> “The first pass records a prior triage through `MemoryMiningService`; the second recalls that same ID through `MemoryRetrievalService`. The linked IDs are provenance, not proof that a repair was applied or that diagnostic accuracy increased. Its history is available from the append-only `TrustLedgerService`.”

If asked about maintenance, point to the preview-only `SleepCycleService` command instead of running a destructive operation.

## 1:05–1:20 · Trace, not hand-waving

**Show:**

```bash
tail -n 1 demo/activity/trace.jsonl
```

> “Every run appends safe metadata: a hash and size for the input, the Rules hit, whether Gemma was skipped, the Zetaris mode, H-MEM IDs or availability, and the final engine. We store no raw CI log, API key, or authorization header in the trace.”

## 1:20–1:30 · Close

**Show:** the smoke script’s final `SMOKE_AGENTATHON_OK` line, then the README sponsor section.

> “The whole fixture path is green without cloud secrets: failed log to diagnosis, evidence, prior-triage recall, and audit trace. Zetaris supplies optional federated evidence; Meterless preserves provenance for prior triages; Gemma stays at the center of the explanation path.”

## Useful backup lines

- **No Gemini key:** “Rules-only mode is intentional for this reproducible demo. The Gemma path is optional and stays bounded when configured.”
- **No Zetaris credentials:** “Fixture mode is the documented fallback, not a simulated live tenant. It proves the integration contract without inventing credentials.”
- **H-MEM missing:** “Run `cd meterless && npm install && npm run setup`; the CLI deliberately refuses to fake memory when the engine is absent.”


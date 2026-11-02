# Judge demo · 90 seconds · white UI route

The reliable route is deliberately key-free: Rules-only triage, H-MEM installed locally, and Zetaris fixture mode. The current browser experience is a white, Apple-style page: its health pill reports the runtime state, and every successful triage result includes **H-MEM recall**, **Zetaris evidence**, and an **Activity trace** row. If live Zetaris credentials are configured, say so and show the `live` mode; otherwise call the fixture exactly what it is.

## Before the clock starts

On a fresh checkout, install the Node dependencies once:

```bash
cd meterless && npm ci && cd ..
```

Then, in one terminal:

```bash
cd meterless && npm run setup && npm run memory -- seed && cd ..
DEMO_STATE_DIR="$(mktemp -d)"
export NURSE_ACTIVITY_LOG="$DEMO_STATE_DIR/trace.jsonl"
ZETARIS_FIXTURE_MODE=1 NURSE_RULES_ONLY=true uvicorn nurse:app --host 127.0.0.1 --port 8787
```

The temporary trace keeps the committed sanitized example unchanged during a
live demo. Keep this terminal open for the trace step below.

In a second terminal, keep this command ready:

```bash
ZETARIS_FIXTURE_MODE=1 NURSE_RULES_ONLY=true bash scripts/smoke_agentathon.sh
```

Open <http://127.0.0.1:8787>. The smoke command is a reliable backup, but the primary route below is the browser UI. Do not claim a Gemini or Zetaris cloud call unless the response mode says it actually happened.

## 0:00–0:12 · The promise

**Show:** the white Actions Nurse page, its sponsor chips, and the health pill.

> “Actions Nurse triages failed GitHub Actions, explains the likely root cause, and remembers past failures. The health pill makes this demo state clear: it is Rules-only, so no model request is being made. It is a first-response tool: it explains and records; it does not execute a fix.”

## 0:12–0:30 · Triage an actual red fixture

**Show:** select `npm-typecheck` under **Reproducible red-CI fixtures**, then click **Triage CI failure**. In this runtime, the status copy says Rules-only and the white result card opens below the input.

> “This typecheck failed because imports refer to exports that no longer exist. Rules recognizes the log signature locally, so this diagnosis is reproducible even without a model key. Gemma remains available as the optional explanatory path, with Rules checking known categories.”

Point to the failing step and the suggested local `npm run typecheck` check. Do not claim that the app executed it.

## 0:30–0:45 · Zetaris evidence, honestly labeled

**Show:** the **Zetaris evidence** row in that same result card. It should say **recorded reference fixture** and name `ci-failure-signatures.json` in the offline route. Optionally show `GET /api/zetaris/preflight` for the two read-only checks.

> “The Zetaris client uses read-only Lightning SQL. This machine is showing **fixture mode** [or **live mode** if returned], so the evidence source is explicit. Fixture is recorded local synthetic reference data, not a cloud claim. Direct REST preflight runs `SELECT 1` and `SHOW LIGHTNING DATABASES`; a loopback local session runs `SELECT 1` and `SELECT 7 AS query_engine_probe`. A configured source can then supply a scoped CI-evidence query.”

## 0:45–1:05 · Meterless H-MEM recall

**Show:** the **H-MEM recall** row directly above Zetaris in the result card; it identifies `vendor/hmem` and any recalled incident text. Then run a clean two-pass recall:

```bash
bash scripts/demo_hmem_two_pass.sh
```

> “The first pass records a prior triage through `MemoryMiningService`; the second recalls that same ID through `MemoryRetrievalService`. The linked IDs are provenance, not proof that a repair was applied or that diagnostic accuracy increased. Its history is available from the append-only `TrustLedgerService`.”

If asked about maintenance, point to the preview-only `SleepCycleService` command instead of running a destructive operation.

## 1:05–1:20 · Trace, not hand-waving

**Show:** the **Activity trace** row at the bottom of the same result card. It gives an `act-…` ID. Then show:

```bash
tail -n 1 "$NURSE_ACTIVITY_LOG"
```

> “Every run appends safe metadata: a hash and size for the input, the Rules hit, whether Gemma was skipped, the Zetaris mode, H-MEM IDs or availability, and the final engine. We store no raw CI log, API key, or authorization header in the trace.”

## 1:20–1:30 · Close

**Show:** the smoke script’s final `SMOKE_AGENTATHON_OK` line, then the README evidence table.

> “The whole fixture path is green without cloud secrets: failed log to diagnosis, memory recall, Zetaris evidence, and an activity trace. Zetaris supplies optional read-only evidence; Meterless preserves provenance for prior triages; Gemma remains the optional explanatory path when a key is configured.”

## Useful backup lines

- **No Gemini key:** “Rules-only mode is intentional for this reproducible demo. The Gemma path is optional and stays bounded when configured.”
- **No Zetaris credentials:** “Fixture mode is the documented fallback, not a simulated live tenant. It proves the integration contract without inventing credentials.”
- **H-MEM missing:** “Run `cd meterless && npm ci && npm run setup`; the CLI deliberately refuses to fake memory when the engine is absent.”

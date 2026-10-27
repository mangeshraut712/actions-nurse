# Actions Nurse

**Actions Nurse triages failed GitHub Actions, explains likely root cause, remembers past failures.**

This is the Open Agent Hackathon 2026 Wildcard [Tinkerer] build. It keeps the useful part of a CI assistant deliberately narrow: bring it a failed run, get a reviewable diagnosis, see the related evidence, and carry forward what the team learned from the last similar incident.

[![CI](https://github.com/mangeshraut712/actions-nurse/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mangeshraut712/actions-nurse/actions/workflows/ci.yml)
![MIT](https://img.shields.io/badge/license-MIT-0071E3)
![Gemma 4](https://img.shields.io/badge/model-Gemma%204-0071E3)

## Why

A red GitHub Actions run normally starts with a developer scrolling through thousands of lines of output. The first error is often familiar, but it is easy to miss, and the last time the team fixed the same kind of failure is usually harder to find than it should be.

Actions Nurse is a first-response tool, not an autonomous repair bot. It identifies a likely failing step, explains the evidence behind the diagnosis, suggests a human-reviewable next move, looks up relevant historic failures, and leaves an append-only trace of what it did. It never runs a proposed command or changes a repository.

## What it does

- Reads a failed Actions log, with an optional screenshot in the web UI.
- Keeps the original Gemma-first diagnosis path: Gemma 4 may propose a diagnosis; deterministic Rules independently classify known signatures and override a conflicting category.
- Works without a Gemini key. Rules-only mode is intentionally deterministic and drives the complete fixture demo.
- Uses **Meterless H-MEM** to remember completed triages and retrieve similar failures with provenance across runs.
- Uses **Zetaris Lightning SQL** as an optional, read-only evidence source. With no credentials it returns clearly labeled local fixtures, so the demo remains reproducible and never pretends it contacted a cloud account.
- Writes safe execution metadata, not raw logs or credentials, to `demo/activity/trace.jsonl`.

The supported fixture set covers checkout authentication, disk full, TypeScript typecheck, Node OOM, and pytest assertion failures.

## Architecture at a glance

```text
failed Actions log / screenshot
          |
          +--> Rules baseline ----+--> final, reviewable diagnosis
          |                       |
          +--> optional Gemma ----+    (Rules checks known categories)
          |
          +--> H-MEM recall ------+--> related prior incidents + provenance
          |
          +--> Zetaris SQL -------+--> live read-only evidence or fixtures
                                      |
                                      +--> append-only activity trace
```

Rules validate a known failure category only; they do not prove every sentence in a model explanation. The application treats pasted logs and screenshots as untrusted evidence. If Gemma is enabled, it receives at most 12,000 log characters and an optional image up to 5 MiB. Do not send secrets or private incident data to a hosted model unless that is appropriate for your environment.

## How to run

### Prerequisites

Use Python 3.12, Node.js 22 with npm, Git, and curl. Initial installation needs internet access for Python/npm dependencies and the Meterless H-MEM reference engine. The Rules + H-MEM + Zetaris-fixture demo runs without cloud API keys after setup.

## Prior work and event-specific additions

Actions Nurse was first committed on 25 October 2026 for Hack Day Pune. This Open Agent Hackathon entry reuses that earlier entry's FastAPI app, Rules/Gemma text and screenshot triage, category validator, web interface, composite GitHub Action, Docker baseline, and five CI-log fixtures. It is not an entirely new project built solely for this event.

The Open Agent Hackathon additions landed on 26 October 2026: the Zetaris read-only REST evidence client and explicitly labeled fixtures; the Meterless H-MEM bridge for mining, retrieval, provenance and preview-only maintenance; sanitized activity traces and recorded demo I/O; the sponsor smoke test; and refreshed demo documentation and interface styling. Compare the prior-entry baseline `7773b290352839110b2ac899c444da83376b56e1` with the sponsor integration commit `ffdb4c5ab91c5e43ba16d0568270b90897ddd5d3`.

The current source does not implement an NVIDIA-specific integration. Gemma is a Google model accessed through the Gemini API; it is not evidence of NVIDIA technology use. Development-tool usage, including Cursor if used, must be confirmed by the author before submission.

## Local installation

### 1. Python app

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Install the real H-MEM engine

The engine is intentionally vendored at setup time, rather than committed. This gives a fresh clone the same repeatable installation path judges use.

```bash
cd meterless
npm ci
npm run setup
npm run memory -- seed
cd ..
```

`npm run setup` vendors Meterless H-MEM under `vendor/hmem/`; it is gitignored. The memory CLI prints `engine source: vendor/hmem` (or the same value in its JSON output) when the real engine has loaded. See [the Meterless integration notes](docs/meterless.md).

### 3. Optional Zetaris credentials

The default is fixture mode. To use a real Zetaris Cloud/Hackathon organization, copy `.env.example` to the ignored `.env.local` and fill only these values:

```dotenv
ZETARIS_REST_URL=https://your-tenant/api/v1.0
ZETARIS_ORG_ID=your-org-id
ZETARIS_API_KEY=your-api-key
```

The client only issues read-only verification/evidence queries (`SELECT 1`, `SHOW LIGHTNING DATABASES`, and the configured evidence query). It falls back to labeled fixture responses if credentials are absent or an authentication request fails. Details and troubleshooting are in [docs/zetaris.md](docs/zetaris.md).

### 4. Start it

For the guaranteed offline path:

```bash
ZETARIS_FIXTURE_MODE=1 NURSE_RULES_ONLY=true uvicorn nurse:app --host 127.0.0.1 --port 8787
```

For the optional Gemma path, set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) and leave Rules-only mode off:

```bash
GEMINI_API_KEY=your-key NURSE_RULES_ONLY=false uvicorn nurse:app --host 127.0.0.1 --port 8787
```

Open <http://127.0.0.1:8787>. The browser includes the five fixtures and a bundled red-Action screenshot. The core endpoints remain `/api/health`, `/api/triage`, `/api/triage-image`, and `/api/compare`; sponsor integration endpoints expose memory, Zetaris preflight, and the latest activity trace without changing the original routes.

- `GET /api/zetaris/preflight` runs `SELECT 1` and `SHOW LIGHTNING DATABASES` only.
- `POST /api/memory/seed`, `/api/memory/ask`, and `/api/memory/remember` expose the real H-MEM bridge; `GET /api/memory/audit/{id}` returns its Trust Ledger history.
- `GET /api/activity/latest` returns the recent sanitized JSONL events.

## Run the green demo path

After the H-MEM setup, run the Agentathon smoke path from the repository root:

```bash
ZETARIS_FIXTURE_MODE=1 NURSE_RULES_ONLY=true bash scripts/smoke_agentathon.sh
```

With no argument, the script starts an isolated Rules-only server on port `8791`; pass an existing base URL as its first argument to reuse another local server. It triages `fixtures/npm-typecheck.txt` end to end, checks the real H-MEM seed/ask path, runs a Zetaris preflight (explicit fixture mode is a passing outcome), and verifies that the append-only activity trace grew. The script does not require a Gemini key or Zetaris credentials.

Committed, sanitized examples live in:

- [`demo/io/`](demo/io/) — input descriptor, enriched triage response, and memory recall.
- [`demo/activity/trace.jsonl`](demo/activity/trace.jsonl) — an append-only sample trace with hashes and modes only.

## 90-second demo

The complete presenter script is in [docs/demo-script.md](docs/demo-script.md). The short version:

1. Show the failed TypeScript fixture and run Rules-only triage.
2. Point out the likely root cause and the Zetaris evidence field; in an offline demo it is honestly labeled `fixture`.
3. Ask H-MEM for a similar failure and show its engine source and provenance IDs.
4. Open the activity trace to show the received-input hash, Rules hit, sponsor modes, and final engine.

That sequence is reliable without cloud credentials. If valid credentials are available, repeat the preflight to show `live` Zetaris mode; the application does not change its read-only contract.

## Sponsor technology

### Meterless H-MEM

This is a real H-MEM wiring, not a memory-shaped JSON stub. The `meterless/` bridge uses the named services judges expect:

- `MemoryMiningService` through `hmem.mine()` when a nurse triage is remembered;
- `MemoryRetrievalService` through `hmem.query()` before the diagnosis is returned;
- `TrustLedgerService` through `hmem.ledger.history()` for provenance/audit; and
- `SleepCycleService` through `hmem.sleep.preview()` for safe, preview-first maintenance.

H-MEM persists local state under the ignored memory directory. The running app degrades safely if the engine has not been installed, and explains that state rather than manufacturing a recall.

### Zetaris

The small Python client reads `.env` followed by `.env.local`, then sends Lightning SQL over Zetaris REST with a request ID. It never writes. `preflight()` runs `SELECT 1` and `SHOW LIGHTNING DATABASES`; triage can attach a narrowly scoped historical CI-evidence query. Fixture mode has the identical response shape and carries `mode: "fixture"` so a judge can immediately distinguish a local demo from a live tenant.

### Gemma 4 and Rules

Gemma remains the core explanatory layer when a key is configured. Rules remain the safety and reproducibility layer: they classify familiar CI signatures locally, offer bounded commands for human review, and retain the final say when a known category conflicts with the model proposal.

## GitHub Action

The reusable composite Action in [`action/action.yml`](action/action.yml) can consume a local failed-log file or retrieve failed-job output for a `workflow_run`, then write a Markdown report and GitHub job summary. It reports a diagnosis only; it does not retry workflows, execute suggested fixes, or modify a repository. Its original Rules/Gemma behavior is intentionally preserved for use in CI.

## Privacy and operational boundaries

- No Zetaris or Gemini secret belongs in git. `.env.local` is ignored.
- The activity trace records safe metadata such as hashes, timestamps, modes, and memory IDs; it does not record raw input logs, API keys, or authorization headers.
- A failed live Zetaris authentication request becomes an explicit fixture-mode result so the app stays useful offline.
- Suggested commands are display-only. Review them before running anything.

## Project map

```text
nurse.py                 FastAPI app, Rules, Gemma validation, enrichment hooks
integrations/zetaris/    read-only REST client and reproducible response fixtures
meterless/               H-MEM CLI bridge, seed data, and setup script
demo/activity/           append-only execution traces
demo/io/                 recorded fixture input/output for the demo
docs/zetaris.md          Zetaris credential and fixture-mode guide
docs/demo-script.md      90-second judge route
```

MIT licensed. Built for the Open Agent Hackathon 2026 Wildcard [Tinkerer] track.


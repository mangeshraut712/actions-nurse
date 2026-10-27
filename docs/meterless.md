# Meterless H-MEM in Actions Nurse

Actions Nurse keeps its diagnosis deterministic: Rules remain the safety net and Gemma can still propose a diagnosis. Meterless H-MEM adds the durable, inspectable history around that triage. It runs locally with no model key.

## Install the real engine

The reference engine is deliberately vendored rather than replaced with a mock. From the repository root:

```bash
cd meterless
npm ci
npm run setup
```

`npm run setup` uses `degit@3.10.1` to fetch Meterless commit `1742dec56a66e58eef9dda2d2b865823758ca8cd` into `meterless/vendor/hmem/`, then installs the engine dependencies with `npm ci` using that commit's tracked lockfile. That directory is intentionally untracked. The bridge reports `"engine_source":"vendor/hmem"` in machine output (and a matching startup line for human commands), so a demo can show the real source it loaded.

This pins the engine source and dependency lockfiles, not the entire operating environment: the installer is fetched from npm, container base images are version tags rather than digest pins, and Python's `python-dotenv` requirement remains a range. Initial setup requires network access. The engine is Meterless's deterministic reference implementation, not a production memory service.

## Demo commands

```bash
cd meterless
npm run memory -- seed
npm run memory -- ask "Have we seen an out-of-memory build failure?"
npm run memory -- sleep --preview
```

Every command goes through a named H-MEM service in `nurse-memory.ts`:

- `remember` and `seed` call `hmem.mine` — `MemoryMiningService` — then annotate the resulting H-MEM record with the fixture provenance; if its mining heuristic has no extraction, they use the engine's direct store capture path instead.
- `ask` calls `hmem.query` — `MemoryRetrievalService` — and returns memory IDs plus rank/provenance.
- `audit` calls `hmem.ledger.history` — `TrustLedgerService` — for append-only history.
- `sleep` calls `hmem.sleep.preview` — `SleepCycleService` — before it can execute maintenance.

The persistent store is `meterless/.nurse-memory/`, also untracked. Set `NURSE_HMEM_DIR` to isolate a demo or test run.

## Python bridge contract

The FastAPI app can invoke the CLI without importing Node directly. Pass `--json` and consume exactly one JSON object from stdout. For `remember` and `ask`, send a JSON object through stdin:

```bash
printf '%s' '{"failing_step":"Build / bundler","root_cause":"Node OOM","fixture":"oom-killed.txt"}' \
  | npm --silent run memory -- remember --json
printf '%s' '{"query":"what previous failure used NODE_OPTIONS?"}' \
  | npm --silent run memory -- ask --json
```

Each successful response includes `ok`, `engine_source`, `state_dir`, `service`, and provenance/memory IDs where applicable. Use `npm --silent run` in the Python bridge so npm's lifecycle banner never precedes the one JSON object. The bridge redacts common token-shaped values before writing memory.


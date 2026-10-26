# Recorded fixture I/O

These files are sanitized recordings from the green, Rules-only Agentathon
smoke path on 2026-10-26. They are deliberately small enough to inspect in a
demo, and use the tracked `npm-typecheck.txt` fixture instead of a production
CI log.

- `npm-typecheck.input.json` is the exact request body sent to `POST /api/triage`.
- `npm-typecheck.triage.json` is the enriched diagnosis: Rules, real H-MEM
  recall/mining, and labeled Zetaris fixture evidence.
- `npm-typecheck.memory-ask.json` is the response from `POST /api/memory/ask`.
- `zetaris-preflight.fixture.json` is the read-only preflight response with no
  Zetaris credentials configured.

The recordings omit only machine-specific temporary-state paths and dynamic
trace IDs where they add no diagnostic evidence. The committed
[`../activity/trace.jsonl`](../activity/trace.jsonl) is the append-only runtime
record for the same demo route; it contains input fingerprints rather than raw
logs.

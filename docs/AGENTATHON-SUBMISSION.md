# Actions Nurse — Open Agent Hackathon 2026 submission pack

> Current submission copy for the Open Agent Hackathon 2026. This is not the
> historical MLH material and does not claim that a HackOS portal submission has
> been made.

## Title

**Actions Nurse**

## One-liner

An Apple-light CI first responder that turns a failed GitHub Actions log into a
reviewable diagnosis, recalls similar incidents with Meterless H-MEM, attaches
read-only Zetaris evidence, and records a privacy-conscious activity trace.

## Detailed description

Actions Nurse makes the first minutes of a red GitHub Actions run less
expensive. Paste a failure log (optionally with a screenshot), choose a
reproducible fixture, and receive a likely failing step, root cause, and
human-reviewable next check. It never executes a proposed command or changes a
repository.

Its white, Apple-style result card keeps the relevant context together:

- deterministic Rules provide a reproducible baseline and work with no Gemini
  key;
- Gemma 4 is an optional explanatory path, whose known failure category is
  checked against Rules;
- Meterless H-MEM recalls analogous incidents before the optional model branch
  and remembers the completed diagnosis with provenance; and
- Zetaris attaches read-only Lightning SQL evidence, explicitly labeled
  `fixture` when no live credentials are configured, followed by an append-only
  activity ID.

The privacy boundary is intentional: activity records fingerprints and safe
execution metadata, not raw CI logs, prompts, API keys, or authorization
headers. The reproducible offline route uses Rules-only mode, a real local
H-MEM engine, and recorded Zetaris fixtures; it never represents a fixture as a
live Zetaris tenant.

## Repository URL

<https://github.com/mangeshraut712/actions-nurse>

## Demo steps

1. From the repository root, prepare H-MEM:

   ```bash
   cd meterless && npm run setup && npm run memory -- seed && cd ..
   ```

   On a fresh checkout, run `cd meterless && npm install && cd ..` once before
   the command above.

2. Start the white browser UI in deterministic mode:

   ```bash
   NURSE_RULES_ONLY=true uvicorn nurse:app --host 127.0.0.1 --port 8787
   ```

3. Open <http://127.0.0.1:8787>, choose `npm-typecheck`, and press **Triage
   failure**. The health pill says **Rules-only demo**; that is expected.

4. In the result card, show **H-MEM recall**, **Zetaris evidence**, and
   **Activity trace**. In the offline route Zetaris must say recorded fixture
   evidence, not live.

5. Verify the full reproducible path:

   ```bash
   NURSE_RULES_ONLY=true ./scripts/smoke_agentathon.sh
   ```

   The expected final line is `SMOKE_AGENTATHON_OK`. The script asserts
   `vendor/hmem`, labeled Zetaris fixture mode, and a growing activity trace.

For a timed walkthrough, use the [90-second demo script](demo-script.md).

## Wildcard [Tinkerer] blurb

Actions Nurse is a practical, tightly scoped agent experience for the awkward
middle of a CI incident: it turns unstructured failure output into a clear
next investigation, keeps the decision reviewable, and remembers what worked
last time. The result card makes its evidence chain visible instead of hiding
it behind a chat response: Rules baseline, H-MEM recall, Zetaris evidence, and
an activity ID. It is useful offline, does not execute fixes, and preserves a
clear handoff to the developer.

## Zetaris blurb

Zetaris is on the triage path as a read-only evidence source—not a decorative
integration. After diagnosis, Actions Nurse queries a narrowly scoped
CI-evidence contract through Lightning SQL and presents the source mode in the
result card. `SELECT 1`, `SHOW LIGHTNING DATABASES`, and the evidence query are
the only supported query shapes. Missing, rejected, or unavailable credentials
produce a clearly labeled recorded fixture response, so the demo never claims a
cloud tenant it did not contact.

## Meterless H-MEM blurb

Meterless H-MEM makes prior CI knowledge useful during the next triage.
Actions Nurse recalls similar incidents through `MemoryRetrievalService` before
the optional model branch, remembers the completed diagnosis through
`MemoryMiningService`, and exposes the append-only `TrustLedgerService` audit
path. The setup command installs the real H-MEM engine under `vendor/hmem`; the
smoke path verifies that source rather than substituting a memory-shaped stub.

## LinkedIn post

<https://www.linkedin.com/feed/update/urn:li:ugcPost:7520474269382889472/>

## Evidence links

- [Prize / track evidence table](../README.md#hackathon-prize--track-evidence)
- [Meterless bridge](../meterless/nurse-memory.ts)
- [Zetaris client and fixture contract](../integrations/zetaris/client.py)
- [End-to-end Agentathon smoke](../scripts/smoke_agentathon.sh)
- [Recorded fixture I/O](../demo/io/README.md)

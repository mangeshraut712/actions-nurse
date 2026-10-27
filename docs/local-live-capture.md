# Local live-proof capture route

This route demonstrates a real local Zetaris query while accurately labeling
the demo dataset as newly authored synthetic reference data. It never requires
showing the Zetaris portal, `.env`, Docker registry, or any credential.

## Before recording

The local Zetaris stack must already be running and healthy. From the Actions
Nurse worktree, seed (or safely re-verify) the owned demo table:

```bash
ZETARIS_PLATFORM_DIR=/path/to/zetaris-platform \
  bash scripts/seed_local_zetaris_demo.sh --apply
```

Expected safe terminal summary:

```text
demo_seed_status=created|already_seeded ... row_count=4 provenance=synthetic-local-demo
```

Start the loopback-only application:

```bash
ZETARIS_PLATFORM_DIR=/path/to/zetaris-platform \
  NURSE_RULES_ONLY=true bash scripts/run_local_zetaris_demo.sh
```

Open `http://127.0.0.1:8787`. Use `NURSE_PORT` if another local port is needed.
The runner uses a temporary activity trace unless `NURSE_ACTIVITY_LOG` is
deliberately set, so this capture route does not modify the committed sample
trace.

## 60-second route

1. **0:00–0:08 — claim boundary.** Show the local app health pill. Say: “This
   is deterministic Rules triage plus a read-only, local Zetaris evidence
   query. No repair command is executed.”
2. **0:08–0:18 — reproducible failure.** Click the `npm-typecheck` fixture,
   then **Triage CI failure**. In Rules-only mode, make clear that no Gemma
   request is being made.
3. **0:18–0:35 — live evidence.** Show `Typecheck / tsc`, then the Zetaris
   line: **live local read-only query · synthetic local demo rows · 1 matching
   row**. Expand the read-only SQL only if useful. The displayed signature and
   recommendation came from the running local Zetaris table; they are not
   historic CI records.
4. **0:35–0:47 — explain relevance.** Point out that only rows whose
   `failing_step` exactly matches the Rules diagnosis are shown. The UI shows
   at most three compact rows and redacts token-like text.
5. **0:47–0:58 — H-MEM provenance.** In a second terminal, run:

   ```bash
   bash scripts/demo_hmem_two_pass.sh
   ```

   Show that the first-pass remembered ID intersects the second-pass recall
   ID, and that `persisted_state_verified` is `true`. The script verifies the
   Meterless reference engine's temporary `state.json` and `ledger.jsonl`
   between separate bridge subprocess calls before removing that temporary
   store. Say: “These IDs prove retrieval of a prior triage record, not that a
   repair was applied or that accuracy increased.”

6. **0:58–1:00 — close.** State the held limits: synthetic local demo data,
   loopback-only services, read-only runtime queries, no cloud token, and no
   automated repair.

## Safe facts to cite

- The demo table has four synthetic rows in the owned
  `actions_nurse_demo_20261027_f9de7301` database.
- The TypeScript fixture retrieves one exact-step evidence row through a real
  local Zetaris session.
- The query result reports `mode: live`, `source: zetaris-local-session`, and
  `provenance: synthetic-local-demo`.
- The H-MEM script uses a fresh temporary store and reports only provenance
  IDs/services; it exits with `setup_required` instead of faking recall when
  the reference engine is unavailable.

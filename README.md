# 🩺 Actions Nurse

**Open-weight Gemma 4 triage for failed GitHub Actions**  
Built for [Hacktoberfest Hack Day Pune x Cloud Native Pune](https://www.mlh.com/events/hacktoberfest-hack-day-pune-x-cloud-native-pune)

> When CI fails, pair the log with the red-run screenshot → Gemma 4 proposes a diagnosis → deterministic Rules check the failure category.
> Get a reviewable first response within a bounded **20-second** model attempt; the key-free Rules path remains available, and suggestions are never executed.

[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Gemma 4](https://img.shields.io/badge/Gemma%204-multimodal-purple)](#)
[![GitHub Action](https://img.shields.io/badge/GitHub-Action-black)](action/)

---

## Why judges should care

| Prize | How Actions Nurse fits |
| --- | --- |
| **Best Use of Gemma 4** | With a local key, one click sends the `checkout-auth` log + bundled Actions screenshot to Gemma; deterministic Rules check the category, while the UI shows both results, provenance, and match/conflict/unverified outcome |
| **Best Open-Source AI** | MIT-licensed FastAPI + vanilla JS, five reproducible failures, a composite Action with scoped read permissions and report artifact, plus a key-free Rules path and CI-tested Docker Compose build |

Cloud-native angle: runs as a **composite GitHub Action** on failed workflows, or as a tiny FastAPI service / Docker container for local demos.

---

## Quick demo (local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# optional: export GEMINI_API_KEY=...   # enables live Gemma 4
NURSE_RULES_ONLY=false uvicorn nurse:app --host 127.0.0.1 --port 8788
# open http://127.0.0.1:8788 (local Gemma path; keep the key-backed server on loopback)
```

For the one-click multimodal moment, press **Run screenshot demo · 1 click**. It attaches the bundled failing Actions screenshot, loads its matching `checkout-auth` log, and opens the side-by-side comparison. With a key and `NURSE_RULES_ONLY=false`, Gemma receives both inputs; deterministic Rules check the proposal against known log signatures. A mismatch makes the Rules diagnosis final; an unknown signature stays labeled unverified. Without a key—or on the public demo—the Rules baseline remains available and the UI says Gemma was skipped.

![Bundled failing GitHub Actions screenshot](docs/fixtures-img/red-actions-permission-failure.png)

Health: `GET /api/health`  
Triage: `POST /api/triage` `{ "log": "..." }`  
Compare: `POST /api/compare` `{ "log": "..." }` → `{ rules, gemma }`  
Multimodal: `POST /api/triage-image` for one validated result, or `POST /api/compare-image` for the rules baseline beside Gemma's proposal from the log + screenshot (multipart form)

```bash
./scripts/smoke.sh                     # always rules-only and fast
NURSE_PROBE_GEMMA=1 ./scripts/smoke.sh # optional 3-second client-capped probe
```

---

## Use as a GitHub Action

```yaml
# .github/workflows/nurse.yml
name: Actions Nurse
on:
  workflow_run:
    workflows: ["CI"]          # your failing workflow name
    types: [completed]
jobs:
  nurse:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: mangeshraut712/actions-nurse/action@main
        with:
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}  # optional; rules fallback
          workflow-run-id: ${{ github.event.workflow_run.id }}
          # rules-only: true  # use this for fully offline/reproducible runs
```

Or paste a log file:

```yaml
- uses: mangeshraut712/actions-nurse/action@main
  with:
    log-path: path/to/failed.log
    gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
```

The checked-in [example workflow](.github/workflows/actions-nurse.yml) includes the required `actions: read` permission and uploads the generated markdown report. The Action writes that report and sets `summary` / `engine` outputs for job summaries.

When copying the automatic workflow, change `workflows: ["CI"]` to the exact name of the workflow you want to watch. It runs only after that workflow completes with a failure, passes its run ID to Actions Nurse, and uploads the resulting report.

---

## Docker

```bash
docker compose up --build
# http://localhost:8787
```

Compose binds to loopback. Set `GEMINI_API_KEY` to enable Gemma, or set `NURSE_RULES_ONLY=true` for an explicitly offline run.

---

## Architecture

```
failed CI log / screenshot
        │
        ▼
┌───────────────────┐  key + model available  ┌──────────────────────┐
│  FastAPI nurse.py │────────────────────────►│ Gemma 4 proposal     │
│  + web UI         │                         │ log + optional image │
└─────────┬─────────┘                         └──────────┬───────────┘
          │ no key / unavailable                         │
          ▼                                              ▼
   deterministic Rules baseline ◄──── signature check ◄─┘
                                      │ match: confirm category
                                      │ conflict: Rules final
                                      └ no known match: unverified
```

The Composite Action (`action/`) runs its self-contained CLI validator on failed-workflow logs. Both app and Action keep suggested commands reviewable and never execute them.

---

## Fixtures

Five reproducible failures live under `fixtures/`: TypeScript typecheck, pytest assertion, Node OOM, disk-full/ENOSPC, and checkout/repository auth. The separate bundled screenshot pairs with the checkout-auth fixture for the multimodal demo. Load the text fixtures from the UI chips or:

```bash
curl -s localhost:8787/api/fixtures
```

---

## Submission notes (Hack Day Pune)

- **Repo:** https://github.com/mangeshraut712/actions-nurse  
- **License:** MIT  
- **Public demo:** [temporary Cloudflare quick tunnel](https://mini-deleted-wed-week.trycloudflare.com) (ephemeral and forced to rules-only; live Gemma is not enabled publicly)
- **Gemma demo:** run `NURSE_RULES_ONLY=false uvicorn nurse:app --host 127.0.0.1 --port 8788` locally with `GEMINI_API_KEY`; Gemma receives the screenshot + log, then known signatures are checked deterministically
- Full pitch: [`docs/MLH-SUBMISSION.md`](docs/MLH-SUBMISSION.md) · win checklist: [`docs/WIN-PLAN.md`](docs/WIN-PLAN.md)

---

## License

MIT — built open so anyone can fork the nurse into their own org CI.

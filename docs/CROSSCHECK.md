# Verification record

Checked 25 October 2026 at approximately 17:23 IST. The documentation refresh is based on source tip `5e9236c`; this pass changes documentation only.

## Current checks

| Area | Result | Evidence |
|---|---|---|
| Local Rules smoke | **PASS** — `NURSE_RULES_ONLY=true ./scripts/smoke.sh` returned `SMOKE_OK`; all seven validator tests passed. The running service reported Rules-only mode and the 20-second budget. Text triage, disk-full triage, screenshot triage, text compare, and screenshot compare passed. | [`scripts/smoke.sh`](../scripts/smoke.sh), [validator tests](../tests/test_validation.py) |
| Five fixture / Action path | **PASS in CI** — the latest green run before this docs refresh exercised all five fixture files through the Action CLI. | [CI run 40189125542](https://github.com/mangeshraut712/actions-nurse/actions/runs/40189125542), [fixtures](../fixtures) |
| Remote Docker build | **PASS in CI** — the same run built and started the Compose deployment, checked health and the screenshot route, then ran the HTTP smoke script. | [CI workflow](../.github/workflows/ci.yml), [CI run 40189125542](https://github.com/mangeshraut712/actions-nurse/actions/runs/40189125542) |
| Local Docker Compose | **UNAVAILABLE** — `docker compose build` returned `docker: unknown command: docker compose`. No local image was built. | Command result from this workstation |
| Screenshot asset | **PASS** — the PNG is bundled in the Docker image and was checked at `/demo-assets/red-actions-permission-failure.png` in CI. Rules-only screenshot triage and compare also passed locally. | [asset](fixtures-img/red-actions-permission-failure.png), [Dockerfile](../Dockerfile) |
| Key-backed local runtime | **AVAILABLE** — at ~17:23 IST, `http://127.0.0.1:8788/api/health` reported `rules_only: false`, `gemma_key: true`, and a 20-second budget. Health confirms configuration only. The previous recorded live multimodal check at 17:00 IST used the bundled screenshot plus `checkout-auth.txt` and received a category-confirmed Gemma result. | [`nurse.py`](../nurse.py), [submission readiness notes](WIN-PLAN.md) |
| Public demo | **RESPONDING, EPHEMERAL, RULES-ONLY** — at ~17:23 IST, the temporary Cloudflare URL's health endpoint reported `rules_only: true` and `gemma_key: false`. No Gemma request is made by this public runtime. | [Open temporary demo](https://mini-deleted-wed-week.trycloudflare.com) |

## What the validator proves

The category check compares Gemma's reported failure step with the category implied by a known Rules signature. A category match is marked `confirmed`, a mismatch `overridden`, and a log without a known signature `unverified`. This is a category-level check; it does not verify the model's complete explanation or fix. Single-result triage selects Rules on a known conflict; comparison routes retain both views.

## Runtime facts checked in source

- Default model: `gemma-4-26b-a4b-it`; fallback attempted: `gemma-4-31b-it`.
- Model request budget: 20 seconds. Gemini receives up to 12,000 log characters and an optional image up to 5 MiB.
- Global `NURSE_RULES_ONLY=true` disables model calls; request-level `rules_only: true` is available on text and image triage/compare routes.
- The composite Action grants only the example workflow's `actions: read` and `contents: read`; suggestions are never executed.

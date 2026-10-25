# Actions Nurse — MLH Submission Pack
Event: Hacktoberfest Hack Day Pune x Cloud Native Pune (Oct 25, 2026)
Deadline: show-and-tell / submit by ~5:00 PM IST

## Project title
Actions Nurse

## Tagline / short pitch
Actions Nurse is a Gemma 4-first incident room for failed GitHub Actions: paste the log or attach the red screenshot, get a structured diagnosis plus reviewable fix commands, and still get a deterministic answer when the network is unavailable.

## Detailed description
Cloud-native engineers waste time scrolling thousands of lines of GitHub Actions noise. Actions Nurse is a lightweight FastAPI + vanilla JS triage room powered by open-weight **Gemma 4** (`gemma-4-26b-a4b-it`) via the Gemini API. The model is always attempted first, including for the bundled red Actions screenshot plus its matching `checkout-auth` log, with a hard 12-second end-to-end budget. If there is no key, no network, an unsupported alias, or an invalid model response, the deterministic rules engine returns a transparent fallback instead of leaving the engineer waiting.

Paste a raw log or upload a red Actions screenshot → get Summary, Failing Step, Root Cause, Suggested Fix, Confidence, engine provenance, and copyable commands. The compare view makes the open AI contribution legible to judges by showing the rules baseline beside Gemma's contextual diagnosis. Commands are displayed, never executed.

It ships as a Docker-ready FastAPI demo and a production-shaped composite GitHub Action. The included `.github/workflows/actions-nurse.yml` listens for failed workflow runs, uses scoped read permissions, pulls failed-step logs with `gh run view --log-failed`, writes a job summary, and uploads a markdown report. Five reproducible fixtures cover TypeScript exports, pytest assertions, Node OOM, runner disk exhaustion, and checkout/repository authentication denial. The UI pairs the bundled red Actions screenshot with the auth fixture for a repeatable screenshot + log multimodal demo.

Built for Hacktoberfest Hack Day Pune x Cloud Native Pune / Best Use of Gemma 4 and Best Open-Source AI.

## Links
- Repo: https://github.com/mangeshraut712/actions-nurse
- Demo: [temporary Cloudflare quick tunnel](https://mini-deleted-wed-week.trycloudflare.com) (ephemeral; public instance is intentionally forced to rules-only mode). For Gemma 4, run locally with `NURSE_RULES_ONLY=false uvicorn nurse:app --host 127.0.0.1 --port 8787`, configure `GEMINI_API_KEY`, then use **Load red screenshot demo**.
- Demo script: docs/demo-script.md

## Challenge categories to enter
- Best Use of Gemma 4
- Best Open-Source AI

## Paste-ready category entries

### Best Use of Gemma 4
Actions Nurse makes Gemma 4 useful at the exact moment a CI run turns red. The presenter clicks **Load red screenshot demo**, which loads a bundled GitHub Actions failure screenshot and its matching sanitized `checkout-auth` log; `/api/triage-image` sends both parts to `gemma-4-26b-a4b-it` for a structured diagnosis. The UI shows failing step, root cause, suggested fix, confidence, and copyable—but never executed—commands. A visible 12-second end-to-end model budget and a side-by-side Rules vs Gemma view make the model contribution, response time, and provenance easy to judge. If the key or network is unavailable, a visibly labeled deterministic fallback still returns a safe diagnosis without falsely claiming a model response.

### Best Open-Source AI
Actions Nurse is an MIT-licensed, practical developer tool: FastAPI, vanilla JavaScript, Docker configuration, a composite GitHub Action, and five reproducible red-CI fixtures are all in the repository. It uses an open-weight Gemma 4 model as the preferred reasoning engine while retaining a local deterministic rules path for key-free, reproducible operation. The Action consumes failed workflow logs, emits a markdown report and job summary, and keeps all suggested commands reviewable rather than executing them. Developers can run the rules-backed app locally without a hosted service; adding a Gemini API key enables Gemma requests.

## Judging proof points
- **Gemma 4 use:** text and image parts are sent together to the requested Gemma 4 model; structured JSON constrains the output to a diagnosis and non-destructive suggested commands.
- **Reliability:** the 12-second model budget is end-to-end across Gemma aliases; rules mode is deterministic and visibly labeled.
- **Open source:** MIT-licensed Python, FastAPI, vanilla JavaScript, Docker, fixtures, smoke test, composite Action, and no proprietary front-end framework.
- **Reproducibility:** `./scripts/smoke.sh` forces rules-only requests for fast, key-free health, triage, and compare checks; `NURSE_PROBE_GEMMA=1` adds an optional client-capped live probe. The Action example preserves a markdown report as an artifact.

## Tech
Python 3.11+, FastAPI, Gemma 4 via Gemini API, deterministic rules fallback, vanilla JavaScript, Docker, composite GitHub Action, MIT license

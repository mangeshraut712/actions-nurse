# Actions Nurse — MLH Submission Pack
Event: Hacktoberfest Hack Day Pune x Cloud Native Pune (Oct 25, 2026)
Deadline: show-and-tell / submit by ~5:00 PM IST

## Project title
Actions Nurse

## Tagline / short pitch
Actions Nurse is a Gemma 4-first incident room for failed GitHub Actions: paste the log or attach the red screenshot, get a structured diagnosis plus reviewable fix commands, and still get a deterministic answer when the network is unavailable.

## Detailed description
Cloud-native engineers waste time scrolling thousands of lines of GitHub Actions noise. Actions Nurse is a lightweight FastAPI + vanilla JS triage room powered by open-weight **Gemma 4** (`gemma-4-26b-a4b-it`) via the Gemini API. The model is always attempted first, including for screenshot + log input, with a hard 12-second end-to-end budget. If there is no key, no network, an unsupported alias, or an invalid model response, the deterministic rules engine returns a transparent fallback instead of leaving the engineer waiting.

Paste a raw log or upload a red Actions screenshot → get Summary, Failing Step, Root Cause, Suggested Fix, Confidence, engine provenance, and copyable commands. The compare view makes the open AI contribution legible to judges by showing the rules baseline beside Gemma's contextual diagnosis. Commands are displayed, never executed.

It ships as a Docker-ready FastAPI demo and a production-shaped composite GitHub Action. The included `.github/workflows/actions-nurse.yml` listens for failed workflow runs, uses scoped read permissions, pulls failed-step logs with `gh run view --log-failed`, writes a job summary, and uploads a markdown report. Five reproducible fixtures cover TypeScript exports, pytest assertions, Node OOM, npm resolution, and runner disk exhaustion.

Built for Hacktoberfest Hack Day Pune x Cloud Native Pune / Best Use of Gemma 4 and Best Open-Source AI.

## Links
- Repo: https://github.com/mangeshraut712/actions-nurse
- Demo: run locally with the documented `uvicorn nurse:app --port 8787` command (no hosted demo URL is claimed)
- Demo script: docs/demo-script.md

## Challenge categories to enter
- Best Use of Gemma 4
- Best Open-Source AI Project (if listed)

## Judging proof points
- **Gemma 4 use:** text and image parts are sent together to the requested Gemma 4 model; structured JSON constrains the output to a diagnosis and non-destructive suggested commands.
- **Reliability:** the 12-second model budget is end-to-end across Gemma aliases; rules mode is deterministic and visibly labeled.
- **Open source:** MIT-licensed Python, FastAPI, vanilla JavaScript, Docker, fixtures, smoke test, composite Action, and no proprietary front-end framework.
- **Reproducibility:** `./scripts/smoke.sh` exercises health, triage, and compare with no model key; the Action example preserves a markdown report as an artifact.

## Tech
Python 3.11+, FastAPI, Gemma 4 via Gemini API, deterministic rules fallback, vanilla JavaScript, Docker, composite GitHub Action, MIT license

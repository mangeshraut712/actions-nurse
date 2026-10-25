# Actions Nurse — MLH Submission Pack
Event: Hacktoberfest Hack Day Pune x Cloud Native Pune (Oct 25, 2026)
Deadline: show-and-tell / submit by ~5:00 PM IST

## Project title
Actions Nurse

## Tagline / short pitch
Actions Nurse turns failed GitHub Actions logs into structured, reviewable diagnoses. With a Gemini API key configured, Gemma 4 proposes a diagnosis from the log and optional screenshot; deterministic rules then check its failure category against known log signatures. A conflict returns the rules diagnosis, while an unknown signature stays labeled as an unverified model hypothesis. Key-free and offline runs still get the deterministic baseline.

## Detailed description
Cloud-native engineers waste time scrolling through thousands of lines of GitHub Actions noise. Actions Nurse is a lightweight FastAPI + vanilla JS triage room powered by open-weight **Gemma 4** (`gemma-4-26b-a4b-it`) via the Gemini API. When enabled, Gemma is attempted first with a bounded 12-second model budget, including for the bundled red Actions screenshot and matching `checkout-auth` log. A deterministic signature check confirms a known failure category or overrides a conflicting proposal; unsupported signatures remain explicitly unverified. With no key, network, compatible model response, or in forced rules-only mode, the app returns the deterministic baseline.

One click loads the bundled screenshot and matching auth fixture, then opens the comparison. The model receives both screenshot and log; the Rules baseline reads the log, and the validator displays whether a known signature confirmed or overrode Gemma's category. Paste a raw log or attach another screenshot to get Summary, Failing Step, Root Cause, Suggested Fix, Confidence, provenance, and copyable commands. Commands are displayed, never executed.

It ships as a Docker-ready FastAPI demo and a production-shaped composite GitHub Action. The included `.github/workflows/actions-nurse.yml` listens for failed workflow runs, uses scoped read permissions, pulls failed-step logs with `gh run view --log-failed`, writes a job summary, and uploads a markdown report. Five reproducible fixtures cover TypeScript exports, pytest assertions, Node OOM, runner disk exhaustion, and checkout/repository authentication denial. The UI pairs the bundled red Actions screenshot with the auth fixture for a repeatable screenshot + log multimodal demo.

Built for Hacktoberfest Hack Day Pune x Cloud Native Pune / Best Use of Gemma 4 and Best Open-Source AI.

## Links
- Repo: https://github.com/mangeshraut712/actions-nurse
- Public demo: [temporary Cloudflare quick tunnel](https://mini-deleted-wed-week.trycloudflare.com) (ephemeral; public instance is intentionally forced to rules-only mode).
- Gemma demo: run locally with `GEMINI_API_KEY` and `NURSE_RULES_ONLY=false`, then click **Run screenshot demo · 1 click**. The local server sends the screenshot + log to Gemma and shows the signature check beside the deterministic baseline.
- Demo script: docs/demo-script.md

## Challenge categories to enter
- Best Use of Gemma 4
- Best Open-Source AI

## Paste-ready category entries

### Best Use of Gemma 4
Actions Nurse applies Gemma 4 to a concrete CI incident, with the evidence visible. One click loads the bundled GitHub Actions failure screenshot and matching sanitized `checkout-auth` log, then sends both to `gemma-4-26b-a4b-it` through `/api/compare-image`. Gemma proposes a structured diagnosis; deterministic rules independently check the failure category against the log. The comparison shows the Rules baseline, Gemma's proposal, input provenance, and whether the known signature confirmed or overrode the proposal. Single-result triage returns the deterministic diagnosis on a known-signature conflict and labels unknown signatures as unverified. The model has a bounded 12-second budget. Suggested commands are copyable but never executed. The public tunnel is rules-only; a local key-enabled run demonstrates live Gemma multimodality.

### Best Open-Source AI
Actions Nurse is an MIT-licensed developer tool built with FastAPI and vanilla JavaScript. The repository includes Docker configuration, a composite GitHub Action, and five reproducible red-CI fixtures. It uses open-weight Gemma 4 for model-assisted diagnosis while keeping a deterministic rules baseline for reproducible, key-free operation. On failed workflow runs, the Action reads failed-step logs with scoped permissions, writes a markdown report and job summary, and uploads the report artifact. The app and Action both check Gemma's failure category against known signatures; neither executes suggested commands. Developers can run rules-only locally without a hosted service, or configure a Gemini API key for Gemma requests.

## Judging proof points
- **Gemma 4 use:** the web demo sends text and image parts together to Gemma; structured JSON constrains the proposal to a diagnosis and suggested commands.
- **Deterministic check:** known failure signatures confirm the proposal's category or select the rules result; no-match proposals are marked unverified.
- **Reliability:** Gemma attempts are bounded by a 12-second budget; rules-only mode is deterministic and visibly labeled.
- **Open source:** MIT-licensed Python, FastAPI, vanilla JavaScript, Docker, fixtures, smoke test, composite Action, and no proprietary front-end framework.
- **Reproducibility:** `./scripts/smoke.sh` forces rules-only requests for fast, key-free health, triage, and compare checks; `NURSE_PROBE_GEMMA=1` adds an optional client-capped live probe. The Action example preserves a markdown report as an artifact.

## Tech
Python 3.11+, FastAPI, Gemma 4 via Gemini API, deterministic rules fallback, vanilla JavaScript, Docker, composite GitHub Action, MIT license

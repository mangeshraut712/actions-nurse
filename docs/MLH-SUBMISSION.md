# Actions Nurse — MLH Submission Pack

Event: Hacktoberfest Hack Day Pune x Cloud Native Pune
Submission window: Oct 25, 2026

## Project title

Actions Nurse

## One-line pitch

When GitHub Actions fails, Actions Nurse turns the noisy log and failing-run screenshot into a reviewable diagnosis: Gemma 4 proposes the cause, and deterministic Rules check whether its failure category matches a known log signature.

## Project description

A red CI run can bury the useful error in thousands of log lines, while a screenshot shows which workflow step failed. Actions Nurse pairs both pieces of evidence in one click. Gemma 4 receives the log and screenshot and returns a structured diagnosis. The Rules baseline reads the log independently; a category check confirms a known match, chooses the Rules result on a conflict, or leaves an unfamiliar model proposal marked unverified. The comparison shows both results and exactly what Gemma received.

This is a focused first-response tool for the moment after CI fails. It does not retry jobs, change repositories, or execute suggested commands. A model attempt is bounded to 20 seconds; when a key, network, or usable response is missing, the deterministic path remains available.

The project includes five sanitized CI fixtures, a FastAPI app with a light Hacktoberfest-themed web UI, and an MIT-licensed composite GitHub Action. On a failed workflow run, the Action reads failed-step logs with read-scoped permissions, writes a Markdown report and job summary, and uploads the report artifact. GitHub Actions CI tests the Rules and Action paths, builds the Docker Compose image, starts the service, and checks health, the bundled screenshot route, and HTTP smoke behavior.

## Demo and links

- Repository: https://github.com/mangeshraut712/actions-nurse
- Public demo: [temporary Cloudflare quick tunnel](https://mini-deleted-wed-week.trycloudflare.com). It is ephemeral and intentionally rules-only; no Gemma key is exposed through that demo.
- Live Gemma demo: with `GEMINI_API_KEY` configured locally, run `NURSE_RULES_ONLY=false uvicorn nurse:app --host 127.0.0.1 --port 8788`, then click **Run screenshot demo · 1 click**. This sends the bundled screenshot and matching `checkout-auth` fixture to Gemma.
- Walkthrough: [docs/demo-script.md](demo-script.md)

## Paste-ready entry — Best Use of Gemma 4

Actions Nurse uses Gemma 4 for a concrete CI incident, not a generic chat. One click loads a sanitized GitHub Actions checkout failure log and its red-run screenshot, then sends both to `gemma-4-26b-a4b-it` through `/api/compare-image`. Gemma proposes the failing step, cause, and fix; the Rules baseline independently reads the log. The UI puts both results side by side and shows the model, evidence provenance, and category-check outcome. A known category match is confirmed, a conflict selects the deterministic Rules diagnosis for single-result triage, and an unknown signature stays explicitly unverified. The live multimodal path has been exercised end to end. Model calls are bounded to 20 seconds, the public demo is rules-only, and suggested commands are never executed.

## Paste-ready entry — Best Open-Source AI

Actions Nurse is an MIT-licensed CI diagnostic that teams can inspect, run locally, and adapt. The repository contains a FastAPI app, a lightweight vanilla JavaScript UI, five reproducible failure fixtures, and a composite GitHub Action that reads failed-job logs with scoped permissions and publishes a Markdown report as a workflow artifact. Gemma 4 is optional; deterministic Rules keep the web and Action paths usable without a key or hosted model. Both paths check a model proposal against known failure categories, expose unverified cases, and leave suggested commands for human review. The public GitHub Actions workflow builds and smoke-tests the Docker Compose deployment, including the screenshot asset used by the one-click demo.

## Judging proof points

- **Multimodal use:** the live demo sends text and screenshot together; Rules provide a separate log-only baseline.
- **Trust boundary:** known category matches are confirmed, conflicts select Rules for the final diagnosis, and unknown signatures remain unverified.
- **Fast fallback:** the model attempt is capped at 20 seconds; key-free Rules mode stays reproducible.
- **Open-source integration:** MIT license, self-contained composite Action, five fixtures, and a Docker Compose deployment checked in CI.
- **Safe output:** credential advice is constrained to least-privilege access; commands are suggestions and never run automatically.

## Technical stack

Python, FastAPI, Gemma 4 through the Gemini API, deterministic Python Rules, vanilla JavaScript, Docker Compose, GitHub Actions composite Action, MIT license.

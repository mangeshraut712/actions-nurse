# Actions Nurse — MLH Submission Pack
Event: Hacktoberfest Hack Day Pune x Cloud Native Pune (Oct 25, 2026)
Deadline: show-and-tell / submit by ~5:00 PM IST

## Project title
Actions Nurse

## Tagline / short pitch
Gemma 4 triage for failed GitHub Actions — paste a red CI log (or screenshot) and get failing step, root cause, and a concrete fix in seconds. Offline rules keep the demo alive without a key.

## Detailed description
Cloud-native engineers waste time scrolling thousands of lines of GitHub Actions noise. Actions Nurse is a lightweight FastAPI + vanilla JS triage room powered by open-weight **Gemma 4** (`gemma-4-26b-a4b-it`) via the Gemini API, with a deterministic regex fallback so demos never die on venue Wi‑Fi.

Paste a raw log or upload a red Actions screenshot → get Summary, Failing Step, Root Cause, Suggested Fix, Confidence, and which engine answered (gemma vs rules). Ships with three realistic fixtures (TypeScript TS2305, Node OOM/exit 134, pytest assert) and a 2–3 minute show-and-tell script.

Built today for Hacktoberfest Hack Day Pune x Cloud Native Pune / Best Use of Gemma 4.

## Links
- Repo: https://github.com/mangeshraut712/actions-nurse
- Local demo: http://127.0.0.1:8787
- Demo script: docs/demo-script.md

## Challenge categories to enter
- Best Use of Gemma 4
- Best Open-Source AI Project (if listed)

## Tech
Python 3.11, FastAPI, Gemma 4 (Gemini API), dual-engine rules fallback, MIT license

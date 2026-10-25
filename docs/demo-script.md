# Judge demo · 2:30

## Before presenting

For the Gemma path, start a local server with `GEMINI_API_KEY` available and `NURSE_RULES_ONLY=false`. The public [Cloudflare quick tunnel](https://mini-deleted-wed-week.trycloudflare.com) is temporary and currently forced to Rules-only mode. It is useful for the interface and key-free fallback, but it cannot demonstrate a live model call. Keep the key-backed server on loopback.

To reproduce locally after installing [`requirements.txt`](../requirements.txt):

```bash
GEMINI_API_KEY=your-key NURSE_RULES_ONLY=false uvicorn nurse:app --host 127.0.0.1 --port 8787
```

Open `http://127.0.0.1:8787`. If no key is available, use the public Rules-only demo and say so directly.

## 0:00–0:20 · Problem and evidence

**Show:** Actions Nurse’s light Hacktoberfest interface and its runtime status.

> “When a GitHub Actions run fails, a developer has to find the useful signal in the log. Actions Nurse turns that first look into a reviewable diagnosis. This local run has Gemma enabled; the public tunnel is Rules-only.”

## 0:20–0:55 · One-click screenshot fixture

**Action:** Click **Run screenshot demo · 1 click**. It loads `checkout-auth.txt` and `red-actions-permission-failure.png`, then runs the comparison.

> “The app pairs one known permission failure log with its screenshot. In this Gemma-enabled run, Gemma sees both. The deterministic Rules baseline sees the log.”

If the model is unavailable, use this line:

> “Gemma did not return within the request budget, so this run shows the Rules baseline. The interface labels the skipped proposal explicitly.”

## 0:55–1:30 · Compare the result

**Show:** The Rules baseline, Gemma card, input provenance, and category-check banner.

> “Rules checks the failure category against known log signatures. A match confirms only that category; a mismatch selects Rules for single-result triage; and an unknown signature leaves Gemma’s proposal unverified. This check does not prove the full explanation or fix. Suggested commands are for review and are never run.”

## 1:30–2:05 · GitHub Action

**Show:** [`actions-nurse.yml`](../.github/workflows/actions-nurse.yml) and the report artifact step.

> “For automation, the composite Action listens for a failed workflow completion, reads failed job logs with Actions read permission, adds a Markdown report to the job summary, and uploads that report. The example also grants contents read. It does not retry the job or modify the repository.”

## 2:05–2:30 · Close

**Show:** The MIT license, five fixture names, and the repository’s CI workflow.

> “The model path uses open-weight Gemma 4 through the Gemini API; the repository does not bundle model weights. The deterministic Rules path is available without a key. CI checks the Action fixtures and builds and smoke-tests the container. That is Actions Nurse: a bounded, inspectable first response to failed CI.”

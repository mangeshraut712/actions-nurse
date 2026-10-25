# Actions Nurse — 2:30 Judge Demo

**Audience:** Hacktoberfest Hack Day Pune x Cloud Native Pune judges
**Prize targets:** Best Use of Gemma 4 · Best Open-Source AI

## Before the demo

For the live multimodal Gemma path, start locally with `GEMINI_API_KEY` configured and `NURSE_RULES_ONLY=false`:

```bash
NURSE_RULES_ONLY=false uvicorn nurse:app --host 127.0.0.1 --port 8787
```

The public quick tunnel is intentionally rules-only. Use it to show the UI and reproducible baseline; do not claim it ran Gemma.

## 0:00–0:25 — Problem and pitch

> “A red GitHub Actions run can hide the useful error in thousands of lines. Actions Nurse turns that failure into a structured diagnosis and a reviewable next step. Its key design is Gemma’s contextual proposal checked against deterministic log signatures.”

## 0:25–1:20 — One-click multimodal path

**Action:** Open `http://127.0.0.1:8787` and click **Run screenshot demo · 1 click**.

> “One click loads this red Actions screenshot and its matching sanitized `checkout-auth` log, then runs the comparison. The Rules baseline reads the log. Gemma receives the same log plus the screenshot as image input.”

**Action:** Point to the two cards and the Rules check banner.

> “Gemma proposes the failure category and fix. Rules independently look for a known signature in the log. A matching category is confirmed; a conflict makes single-result triage use the Rules diagnosis; a log with no known signature stays labeled unverified. The comparison keeps both views visible so you can judge the model’s contribution.”

> “The UI also shows exactly what Gemma received and which engine returned the diagnosis. Suggested commands can be copied, but Actions Nurse never runs them.”

If the model is unavailable, say:

> “This runtime skipped Gemma, so the screen shows the deterministic baseline. The public tunnel is deliberately rules-only; the multimodal Gemma call runs locally when a key is configured.”

## 1:20–1:55 — Gemma with a safety boundary

> “For a known failure, Gemma adds context to the same text and screenshot evidence, while the deterministic check limits which category can be accepted as the final single-result diagnosis. For an unfamiliar failure, it does not pretend the rules verified the model; it labels the proposal unverified. If the key, network, or model response is unavailable, the rules path remains usable under a bounded 12-second model budget.”

## 1:55–2:30 — Open source and prize fit

**Action:** Show `.github/workflows/actions-nurse.yml` and the report artifact setup.

> “The MIT-licensed repository includes five red-CI fixtures and a composite GitHub Action. On a failed workflow, it reads failed-step logs with scoped permissions, writes a job summary and Markdown report, and uploads the report. The Action also runs the deterministic category check; it never executes suggested commands.”

> “That is the Gemma 4 use case: multimodal CI triage with an explicit evidence check. The open-source contribution is a reproducible, key-free rules path plus an Action teams can adapt to their own failed workflows.”

> “Repo: `mangeshraut712/actions-nurse`. Thank you.”

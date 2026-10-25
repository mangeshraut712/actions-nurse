# Win plan — Best Use of Gemma 4 + Best Open-Source AI

Deadline: Oct 25 2026 5:00 PM IST. Show-and-tell 2–3 min. Polish window through 4:30 PM IST.

## Prize criteria (MLH)
1. **Best Use of Gemma 4**: multimodal (text+images), focused AI tool, rapid Gemini API prototype.
2. **Best Open-Source AI Project**: open-weight AI is core; MIT; original.

## Must-ship before submit
- [x] Gemma 4 log triage via Gemini API + rules fallback (12s hard budget)
- [x] Screenshot multimodal endpoint (`POST /api/triage-image`)
- [x] GitHub Action on failed workflow_run (`.github/workflows/actions-nurse.yml` + `action/`)
- [x] Compare endpoint + UI: rules vs Gemma side-by-side
- [x] Dockerfile + docker-compose
- [x] Judge-first README + MLH-SUBMISSION.md + demo-script.md
- [x] Fixtures: typecheck, pytest, OOM, npm/disk/ENOSPC, checkout-auth
- [ ] Public demo URL (tunnel) — nice-to-have; local demo is documented honestly
- [x] Screenshot fixture image under `docs/fixtures-img/` for multimodal live demo
- [ ] MLH submit both categories (~5:00 PM IST)

## Demo story (2–3 min)
1. Paste TS2305 fixture → structured fix + copy commands
2. **Compare Rules vs Gemma** → show open-AI value
3. Composite Action + Docker as cloud-native OSS path
4. Optional: attach red Actions screenshot for multimodal

## Crosscheck (2026-10-25 ~3:55 PM IST)
- Repo cwd: `/Users/mangeshraut/codex-work/actions-nurse` only
- Latest pushed: see `git log -1`
- Rules path verified for all fixtures + HTTP triage/compare without API key

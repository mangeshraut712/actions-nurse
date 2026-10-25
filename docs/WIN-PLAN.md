# Win plan — Best Use of Gemma 4 + Best Open-Source AI

Deadline: Oct 25 2026 5:00 PM IST. Show-and-tell 2–3 min. Polish window through 4:30 PM IST.

## Prize criteria (MLH)
1. **Best Use of Gemma 4**: multimodal (text+images), focused AI tool, rapid Gemini API prototype.
2. **Best Open-Source AI**: open-weight AI is core; MIT; original.

## Must-ship before submit
- [x] Gemma 4 log triage via Gemini API + rules fallback (12s hard budget)
- [x] Screenshot multimodal endpoint (`POST /api/triage-image`)
- [x] GitHub Action on failed workflow_run (`.github/workflows/actions-nurse.yml` + `action/`)
- [x] Compare endpoint + UI: rules vs Gemma side-by-side
- [x] Dockerfile + docker-compose
- [x] Judge-first README + MLH-SUBMISSION.md + demo-script.md
- [x] Fixtures: typecheck, pytest, OOM, npm/disk/ENOSPC, checkout-auth
- [x] Public demo tunnel smoke-tested — temporary Cloudflare quick tunnel; local demo remains the durable judge path
- [x] Screenshot fixture image under `docs/fixtures-img/` for multimodal live demo
- [ ] MLH submit both categories (~5:00 PM IST)

## Demo story (2–3 min)
1. **Load red screenshot demo** → matching `checkout-auth` log + screenshot enter the multimodal path
2. Show structured diagnosis and visibly labeled Gemma/rules provenance
3. **Compare Rules vs Gemma** → make the model contribution legible
4. Show composite Action + Docker configuration as the cloud-native OSS path

## Crosscheck (2026-10-25 ~3:55 PM IST)
- Repo cwd: `/Users/mangeshraut/codex-work/actions-nurse` only
- Latest pushed: see `git log -1`
- Rules path verified for all fixtures + HTTP triage/compare without API key

## Crosscheck (2026-10-25 ~4:05 PM IST)
- Full evidence: [`CROSSCHECK.md`](CROSSCHECK.md)
- Public quick tunnel reached local health successfully, but is intentionally not used as a permanent submission link.
- Docker client is installed; build verification is blocked because the local Docker daemon is not running. Do not claim a successful image build.

## Deep pass (2026-10-25 ~4:21 PM IST)
- Image-aware comparison route and UI provenance are implemented; text fixture selection clears the prior screenshot attachment.
- Public quick tunnel rechecked: app page, health endpoint, screenshot asset, and image-aware comparison all responded successfully. Current instance is forced to rules-only mode.
- `docker compose build` rechecked; Compose plugin is unavailable, and the Docker daemon is not reachable. See [`CROSSCHECK.md`](CROSSCHECK.md).
- Browser interaction confirmed screenshot-to-compare and fixture-switch behavior; header status badge sizing was corrected.
- Replaced the dark blue app surface with a warm light Hacktoberfest palette and verified it in the browser.

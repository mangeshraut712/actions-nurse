# Win plan — Best Use of Gemma 4 + Best Open-Source AI

Deadline: Oct 25 2026 5:15 PM IST (extended). Freeze ready by 5:10 PM IST. Show-and-tell 2–3 min.

## Prize criteria (MLH)
1. **Best Use of Gemma 4**: multimodal (text+images), focused AI tool, rapid Gemini API prototype.
2. **Best Open-Source AI**: open-weight AI is core; MIT; original.

## Must-ship before submit
- [x] Gemma 4 log triage via Gemini API + rules fallback (20s bounded model budget)
- [x] Screenshot multimodal endpoint (`POST /api/triage-image`)
- [x] GitHub Action on failed workflow_run (`.github/workflows/actions-nurse.yml` + `action/`)
- [x] Compare endpoint + UI: rules vs Gemma side-by-side
- [x] Dockerfile + docker-compose
- [x] Judge-first README + MLH-SUBMISSION.md + demo-script.md
- [x] Fixtures: typecheck, pytest, OOM, npm/disk/ENOSPC, checkout-auth
- [x] Public demo tunnel smoke-tested — temporary Cloudflare quick tunnel; local demo remains the durable judge path
- [x] Screenshot fixture image under `docs/fixtures-img/` for multimodal live demo
- [ ] MLH submit both categories (~5:15 PM IST)

## Demo story (2–3 min)
1. **Run screenshot demo · 1 click** → attach the bundled red screenshot and matching `checkout-auth` log, then open the compare view
2. Gemma proposes from text + image; deterministic rules check the reported failure category, confirm a known category, override a conflict, or mark an unknown proposal unverified
3. Show the Rules baseline, Gemma input provenance, and transparent skipped-model state when running the public rules-only demo
4. Show the composite Action + report artifact as the cloud-native OSS path

## Judge positioning note

The Temporal/Gemma example [Quorum](https://dev.to/arqamwd/we-should-go-out-this-weekend-i-built-a-discord-member-that-holds-the-clock-until-were-outside-10ek) leads with durable group planning: votes, scheduled checks, retries, and restart recovery. Actions Nurse solves a different, immediate problem: after CI fails, turn a log and screenshot into a diagnosis a developer can inspect. Lead with the one-click multimodal evidence, the independent Rules category check, and the key-free fallback. Do not imply that Actions Nurse provides Temporal-style orchestration or durable retries.

**Live Gemma endpoint for judges:** `http://127.0.0.1:8788` with `GEMINI_API_KEY` configured. The public tunnel at `https://mini-deleted-wed-week.trycloudflare.com` remains rules-only on port 8787.

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

## Judge polish follow-up (2026-10-25 ~4:30 PM IST)
- Added Gemma failure-category checking to the web triage, compare routes, and Action CLI. Known conflicts select the deterministic diagnosis; unknown signatures remain explicitly unverified.
- Reworked the compare hero to explain evidence → proposal → rules check, with dynamic copy for forced rules-only mode.
- **Run screenshot demo · 1 click** now loads the screenshot + `checkout-auth` fixture and executes the multimodal comparison in one action.
- Tightened README prize mapping, both paste-ready MLH entries, and the timed demo script. The public tunnel is still temporary and rules-only; no live Gemma call was claimed.
- Verification: `NURSE_RULES_ONLY=true ./scripts/smoke.sh` passed; all five Action fixtures and mocked category-check scenarios passed; compile, JavaScript syntax, and diff whitespace checks passed. See [`CROSSCHECK.md`](CROSSCHECK.md).
- `docker compose build` remains blocked because this host has no `docker compose` subcommand; no image was produced.

## SDLC readiness pass (2026-10-25 ~4:45 PM IST)
- **Gemma end-to-end works:** loopback-only port 8788 returned a multimodal `gemma-4-26b-a4b-it` diagnosis from the bundled screenshot + auth fixture; the Rules validator confirmed the checkout category. The compare UI also displayed this live result. Public port 8787 stays rules-only.
- **Parser hardened:** Gemma can return thought parts and a JSON array. The app and Action CLI now use the final non-thought result, and a regression test covers that format. The default model attempt budget is 20 seconds to avoid needless fallback on variable provider latency.
- **CI passed remotely on `be8823c`:** [Run 40188367576](https://github.com/mangeshraut712/actions-nurse/actions/runs/40188367576) built the Compose image and passed container health, screenshot asset, HTTP smoke, Python/JavaScript checks, unit tests, and all five Action fixtures using Node 24 action majors. Its only annotation was the moving `ubuntu-latest` image notice; the release gate now pins `ubuntu-24.04`.
- **Packaging/security fixes:** Docker context retains the screenshot required at runtime; Compose binds only to localhost and accepts `NURSE_RULES_ONLY`; the Action avoids shell interpolation of its path inputs; prompts treat log/image content as untrusted.
- **Local verification:** rules smoke `SMOKE_OK`, five unit tests passed, five Action fixtures passed, YAML parsing, Python compile, `node --check`, `bash -n`, and `git diff --check` passed. Local Docker build remains blocked by the missing Compose plugin; remote CI built and smoke-tested the image successfully.

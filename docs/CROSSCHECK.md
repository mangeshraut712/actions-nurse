# Crosscheck — 2026-10-25

Scope: `/Users/mangeshraut/codex-work/actions-nurse` only. These are the submission-readiness checks verified against the local service on 2026-10-25.

- **Rules HTTP path — PASS.** `./scripts/smoke.sh` passed against `http://127.0.0.1:8787`: health, rules-only TypeScript triage, rules-only disk-full triage, and rules-only compare. The health response reported `rules_only: true` and a 12-second Gemma budget.
- **Five fixtures — PASS.** Rules-only HTTP triage and the composite Action CLI (`action/nurse_cli.py`, `NURSE_RULES_ONLY=true`) each produced a rules diagnosis for `checkout-auth`, `disk-full`, `npm-typecheck`, `oom-killed`, and `pytest-assert`.
- **Action/compile path — PASS.** The Action CLI completed for all five fixtures, and `python3 -m compileall -q nurse.py action/nurse_cli.py` passed.
- **Multimodal demo asset — PASS.** [`red-actions-permission-failure.png`](fixtures-img/red-actions-permission-failure.png) is bundled and the local app's **Load red screenshot demo** pairs it with `fixtures/checkout-auth.txt` before calling `POST /api/triage-image`.
- **Public demo tunnel — PASS, temporary.** A Cloudflare quick tunnel served `/api/health` successfully at `https://mini-deleted-wed-week.trycloudflare.com` during this check. Quick-tunnel URLs are ephemeral; use the local-demo instructions as the durable judge path and do not paste this URL into a permanent submission.
- **Docker build — BLOCKED BY LOCAL DAEMON.** `docker` is installed (`29.9.2`), but `docker compose build` is unavailable on this installation. The available legacy `docker-compose build` reached the client, then failed because no Docker daemon is listening at `/var/run/docker.sock`. No Docker image-build success is claimed.

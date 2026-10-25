# Submission readiness

Updated 25 October 2026. This file tracks the evidence and presentation for the two target categories; it does not record an award or confirm portal submission.

## Prize mapping

| Category | Lead with | Proof |
|---|---|---|
| Best Use of Gemma 4 | One-click CI log + screenshot input, Gemma proposal through the Gemini API, and an explicit deterministic category check. | [`/api/compare-image`](../nurse.py), [screenshot demo UI](../web/app.js), [paste-ready copy](MLH-SUBMISSION.md#best-use-of-gemma-4) |
| Best Open-Source AI | MIT license, composite Action and report artifact workflow, five reproducible fixtures, and key-free Rules fallback. | [MIT license](../LICENSE), [Action](../action/action.yml), [automation workflow](../.github/workflows/actions-nurse.yml), [fixtures](../fixtures), [paste-ready copy](MLH-SUBMISSION.md#best-open-source-ai) |

## Judge path

1. Use the local Gemma-enabled server for the one-click `checkout-auth` screenshot + log comparison. Explain that Gemma sees both inputs and Rules sees the text log.
2. Read the outcome precisely: a known category match confirms the category only; a conflict selects Rules for the single-result route; an unknown signature leaves the proposal unverified.
3. Show the failed-run composite Action, read-only permissions, Markdown report, and artifact upload.
4. Close with the MIT license, five fixtures, key-free Rules mode, and the green CI evidence.

The [public quick tunnel](https://mini-deleted-wed-week.trycloudflare.com) is **ephemeral and Rules-only**. Its health check reports model calls disabled. It can show the interface and fallback, but it cannot serve as proof of live Gemma inference. Keep the key-backed demonstration on loopback.

## Verified evidence and limits

- Latest pre-documentation [CI run](https://github.com/mangeshraut712/actions-nurse/actions/runs/40189125542) passed on source commit `5e9236c`; it includes compile/syntax checks, seven validator tests, all five Action CLI fixtures, Docker Compose build, container health, screenshot route, and HTTP smoke.
- The local Docker client on the documentation workstation does not provide `docker compose`; no local image build is claimed. The remote CI build is the Docker proof.
- A previous local Gemma-enabled multimodal pass used the bundled screenshot and checkout-auth fixture and returned a category-confirmed result. The current public tunnel remains Rules-only; see [the verification record](CROSSCHECK.md) for timestamps and this pass’s checks.
- The category validator checks the reported failure step against known deterministic signatures. It does not establish that all model prose is correct.

## Submission materials

- [README and quickstart](../README.md)
- [Paste-ready entries for both prize categories](MLH-SUBMISSION.md)
- [Timed 2:30 demo script](demo-script.md)
- [Current verification record](CROSSCHECK.md)

No additional feature is needed to explain the current entry. Keep the presentation focused on the multimodal comparison, its narrow validation claim, and the reusable open-source Action.

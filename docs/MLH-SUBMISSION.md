# Historical: MLH Hack Day Pune submission copy

> This file is retained as prior-event material. It is **not** the Open Agent
> Hackathon 2026 submission or current demo guide; start with the
> [Agentathon README](../README.md) and [90-second demo script](demo-script.md).

The entries below are ready to paste into the two prize categories. They describe the implementation and its current limits; no award or portal-submission status is claimed here.

## Best Use of Gemma 4

**Actions Nurse** helps developers investigate a failed GitHub Actions run. In the Gemma-enabled demo, one click loads a bundled checkout-permission screenshot and its matching CI log. Open-weight Gemma 4 (`gemma-4-26b-a4b-it`) receives the log and image through the Gemini API and proposes a failure category and next steps. A separate deterministic Rules path reads the log and checks that category against known failure signatures: a matching category is marked confirmed, a conflict selects the Rules diagnosis as the single result, and an unknown signature leaves the proposal unverified. The comparison view shows both outputs and what evidence Gemma received. Model calls have a 20-second budget; if Gemma is unavailable, the key-free Rules path remains usable. Suggested commands are never executed. The public demo link is an ephemeral, Rules-only tunnel; use a local key-backed run to demonstrate multimodal Gemma inference.

## Best Open-Source AI

Actions Nurse is an MIT-licensed FastAPI app and composite GitHub Action for first-response CI triage. The repository includes five failure-log fixtures, a deterministic key-free Rules path, and a Gemma 4 integration through the Gemini API; model weights are not bundled or run locally. On a failed workflow, the Action can read failed job logs with `actions: read`, write a Markdown report and job summary, and upload that report as an artifact. The example grants `actions: read` and `contents: read`. CI checks the Python and browser code, runs seven validator tests and the five Action CLI fixtures, then builds and smoke-tests the Docker Compose deployment. The Rules path continues to work when no model key is configured or when Rules-only mode is selected. The app reports suggested fixes for human review and does not execute commands, retry jobs, or change repositories.

## Evidence links

- [Source and quickstart](../README.md)
- [Gemma request, bounds, and validator](../nurse.py)
- [Composite Action](../action/action.yml)
- [Failed-workflow automation](../.github/workflows/actions-nurse.yml)
- [CI checks and Docker Compose smoke](../.github/workflows/ci.yml)
- [Current verification and demo status](CROSSCHECK.md)
- [MIT license](../LICENSE)

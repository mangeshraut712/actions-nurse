# Historic repository CI case study

This is an inspectable summary of one real, public Actions Nurse repository CI
history record. Its canonical source is the sanitized
[metadata record](../demo/real-ci/historic-docker-smoke-incident.json).

## Evidence boundary

The record is historic repository CI metadata, not a live query, not synthetic
Zetaris data, and not production evidence. It preserves identifiers, timestamps,
safe annotations, and immutable GitHub links; it does not retain raw logs or
artifacts.

The timeline does not establish the root cause of the failed health endpoint.
It also does not show an automatic remedy, a diagnostic-quality measurement, or
an efficiency metric. The reproducible interactive route remains the separately
labeled fixture or local Zetaris synthetic-reference-row demo.

## Recorded timeline

1. [CI run 40328653045](https://github.com/mangeshraut712/actions-nurse/actions/runs/40328653045)
   at [commit 8616b672](https://github.com/mangeshraut712/actions-nurse/commit/8616b672c2b8ed186c8cb8a1f7e6d61f13eedb28)
   failed the “Build and smoke-test the Docker Compose deployment” stage. Its
   [job 121591898621](https://github.com/mangeshraut712/actions-nurse/actions/runs/40328653045/job/121591898621)
   recorded the safe annotation `exit code 7` and signature
   `curl: (7) Failed to connect`.
2. The same commit triggered [Actions Nurse triage run
   40328858092](https://github.com/mangeshraut712/actions-nurse/actions/runs/40328858092).
   The workflow completed its report path, but the Rules engine returned
   `unknown`: an unrecognized failure signature. It produced no diagnosis or
   repair claim.
3. [Follow-up commit 0d46c28](https://github.com/mangeshraut712/actions-nurse/commit/0d46c28706f5cfe0183c1c0f0db872ecf062224d)
   documents CI image-import and startup-health-diagnostic updates. The
   [subsequent CI run 40331404876](https://github.com/mangeshraut712/actions-nurse/actions/runs/40331404876)
   completed successfully at that commit.

The final step is a recorded sequence, not proof that the failed job isolated a
specific cause or that Actions Nurse made a change. It is useful precisely
because it shows both an authentic CI failure and an honest Rules abstention.

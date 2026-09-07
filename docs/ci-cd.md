# CI/CD and DevOps Implementation

## 1. Pipeline overview

```
   Developer pushes / opens a PR
              |
   ┌──────────▼──────────────────────────────────────────────┐
   │                    CI  (.github/workflows/ci.yml)        │
   │                                                          │
   │  quality ──────────────┐                                 │
   │  (ruff, black, bandit) │                                 │
   │                        ├──> docker-build                 │
   │  unit-tests ───┐       │    (build + run + /healthz)     │
   │                ├──> coverage (85% gate)                  │
   │  integration ──┘       │                                 │
   │  (PostgreSQL 16)       │                                 │
   │                        │                                 │
   │              quality-gate  <── required status check     │
   └──────────────┬───────────────────────────────────────────┘
                  │ passed, on main
   ┌──────────────▼──────────────────────────────────────────┐
   │                    CD  (.github/workflows/cd.yml)        │
   │                                                          │
   │  verify CI conclusion == success                         │
   │        -> flyctl deploy --strategy rolling               │
   │        -> poll https://.../healthz until healthy         │
   │        -> smoke-test the sign-in page                    │
   │        -> record the deployment in the job summary       │
   │        -> on failure: report releases for rollback       │
   └──────────────────────────────────────────────────────────┘
```

## 2. Continuous Integration

**Triggers:** push to `main` or `develop`, any pull request into them, and
manual dispatch.

**Concurrency:** runs are grouped by ref with `cancel-in-progress`, so a new
push supersedes the previous run rather than queueing behind it.

### Job 1 — `quality`

| Step | Command | Fails when |
| --- | --- | --- |
| Lint | `ruff check . --output-format=github` | Any lint error (annotated inline on the PR) |
| Format | `black --check --diff .` | Any file is not formatted |
| Security | `bandit -c pyproject.toml -r app -ll` | Any medium or high severity finding |

It runs first because it is fast: a formatting mistake should not wait behind a
seventy-second test run.

### Job 2 — `unit-tests`

`pytest tests/unit -m unit -v --no-cov --junitxml=reports/junit-unit.xml`

Coverage is off here so unit feedback is as fast as possible; the `coverage`
job measures it once, properly.

### Job 3 — `integration-tests`

Runs a **PostgreSQL 16 service container** and points the suite at it via
`TEST_DATABASE_URL`.

This is a deliberate choice. The unit tests use in-memory SQLite for speed, but
SQLite silently permits things PostgreSQL rejects. Running the integration
suite against the production engine means a constraint violation is caught in
CI rather than on the live system.

### Job 4 — `coverage`

Runs the full suite with coverage and the `--cov-fail-under=85` gate, publishes
the percentage to the GitHub job summary, and uploads the HTML and XML reports
as artefacts.

### Job 5 — `docker-build`

Builds the image with Buildx and GitHub Actions layer caching, then **runs it**:

1. Start the container with an ephemeral secret key and a SQLite database.
2. Poll `/healthz` for up to 60 seconds.
3. Fetch `/login` and assert the page renders.
4. Dump container logs (always) and remove the container.

An image that builds but will not start is not a passing build, so the smoke
test is part of the gate rather than a separate manual check.

### Job 6 — `quality-gate`

Depends on all five jobs with `if: always()`, and fails if any of them failed or
was cancelled. This is the **single required status check** for branch
protection — one check covering the whole pipeline, so adding a job later does
not require editing the protection rules.

## 3. Automated verification of requirements

The assignment asks how requirements are automatically verified. Concretely:

| Mechanism | Where | Effect |
| --- | --- | --- |
| Test cases | `tests/` — 264 tests | Each "Must" requirement has at least one test (`docs/requirements-traceability.md`) |
| Validation rules | `app/utils/validators.py`, re-applied in services | Invalid data cannot be written, even bypassing the form |
| Database constraints | Unique, check, foreign key constraints | The final backstop below the application |
| Coverage gate | `--cov-fail-under=85` | Untested new code fails the build |
| Lint gate | `ruff check` | Style and defect patterns block the merge |
| Format gate | `black --check` | One consistent style, no diff noise in reviews |
| Security gate | `bandit -ll` | Medium/high findings block the merge |
| Container health gate | `docker-build` job | A non-starting image blocks the merge |
| Deployment health gate | CD `/healthz` poll | A broken release fails its deployment |

The important property: these are **blocking**, not advisory. A pull request
that fails any of them cannot be merged under the branch protection rules in
`docs/git-workflow.md`.

## 4. Continuous Delivery

**Trigger:** `workflow_run` — CD starts only when the *CI* workflow completes on
`main`.

**The gate:**

```yaml
if: >-
  github.event_name == 'workflow_dispatch' ||
  github.event.workflow_run.conclusion == 'success'
```

`workflow_run` fires for failed runs too, so the conclusion is checked
explicitly. Without that line, a failing CI run would trigger a deployment —
this is the single most important line in the CD workflow.

**Concurrency:** `group: deploy-production` with `cancel-in-progress: false`, so
two deployments can never race onto the same app, and a running deployment is
never killed half-way.

**Steps:** set up flyctl → `flyctl deploy --remote-only --strategy rolling` →
poll `/healthz` for up to 150 seconds → smoke-test `/login` → write a deployment
record to the job summary.

**Rollback:** a `rollback-on-failure` job runs on failure and lists recent
releases with the `flyctl releases rollback` command. Rolling back is left as a
deliberate human action rather than automated — an automatic rollback can mask a
data-layer problem that the next deployment will simply hit again.

**Secrets:** `FLY_API_TOKEN` is a GitHub Actions secret. Application secrets are
Fly secrets. Nothing sensitive is in the workflow files.

## 5. Rolling deployment and health checks

`fly.toml` declares an HTTP check on `/healthz` every 30 seconds with a
15-second grace period, and `--strategy rolling` replaces machines one at a
time. A new machine takes traffic only after passing its check, so a release
that cannot start does not take the service down with it.

`/healthz` returns **503, not 200**, when the database is unreachable. A health
check that only proves the web process is alive would report a healthy service
that cannot verify a single credential.

## 6. Pipeline evidence

Every run uploads artefacts, retained for 30 days:

| Artefact | Contents |
| --- | --- |
| `bandit-report` | `bandit-report.json` |
| `junit-unit` | Unit test results (JUnit XML) |
| `junit-integration` | Integration test results (JUnit XML) |
| `coverage-report` | HTML coverage site, `coverage.xml`, full-suite JUnit XML |

Coverage percentage is also written to the job summary on the run page.

`docs/evidence-checklist.md` lists the screenshots the team must capture,
including a **failing** pipeline — evidence that the gate actually blocks bad
code is more convincing than a wall of green ticks.

## 7. Running the same gates locally

The pipeline is reproducible on a laptop, so failures are found before pushing:

```bash
ruff check .
black --check .
bandit -c pyproject.toml -r app -ll
pytest
docker build -t qvs:local .
docker run --rm -p 8080:8080 \
  -e SECRET_KEY=local-only-not-a-real-secret \
  -e DATABASE_URL=sqlite:////tmp/qvs.db \
  -e SESSION_COOKIE_SECURE=false qvs:local
curl -fsS http://localhost:8080/healthz
```

## 8. DevOps practices demonstrated

| Practice | How |
| --- | --- |
| Version control | Git, protected branches, PR-based flow |
| Automated build | Docker multi-stage build in CI |
| Continuous integration | Every push and PR runs the full gate |
| Automated testing | 264 tests across unit and integration |
| Test against production-like infrastructure | Integration suite on PostgreSQL 16 |
| Static analysis | Ruff, Black, Bandit |
| Quality gates | Blocking checks, single required status check |
| Continuous delivery | Automatic deployment of `main` after CI passes |
| Infrastructure as code | `Dockerfile`, `docker-compose.yml`, `fly.toml`, workflow YAML |
| Immutable artefacts | The container image is built once and deployed as built |
| Health checks | Container `HEALTHCHECK`, Fly service check, post-deployment verification |
| Observability | Structured stdout logs, `/healthz`, `/metrics`, live dashboard counters |
| Secret management | Environment variables, GitHub secrets, Fly secrets, start-up guards |
| Rollback | Documented, with the command surfaced automatically on failure |

## 8.1 Pipeline verification

Both workflows have run against the real repository and application:

- **CI** - six jobs green on `main` and `develop` (264 tests, 92.69% coverage,
  Docker image built and smoke-tested on the runner).
- **CD** - failed correctly when `FLY_API_TOKEN` was absent, then deployed
  releases v3 and v4. Release v4 was fully automatic: push to `main` triggered
  CI, the quality gate passed, and CD deployed and health-checked with no human
  step.

Evidence: `reports/deployment-verification.md` section 8.

## 9. Known limitations

- **No staging environment.** `develop` is integrated and tested but not
  deployed anywhere; `main` goes straight to production. A staging Fly app is
  the obvious next step.
- **No automated dependency-vulnerability scanning.** Bandit analyses our code,
  not our dependencies. Adding `pip-audit` to the `quality` job is a task in the
  collaboration plan.
- **No database migration step in CD.** The entrypoint calls `db.create_all()`,
  which creates missing tables but does not alter existing ones. The first real
  schema change must add `flask db upgrade` to the deployment.
- **Single region.** `primary_region = "jnb"` with one machine minimum; there is
  no multi-region redundancy.

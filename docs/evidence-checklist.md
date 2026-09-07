# Evidence Collection Checklist

Everything the team must capture for submission. **Capture it from the real
system as you do the work.** Nothing on this list may be mocked up, staged or
recreated afterwards — the markers can check the repository, the Actions history
and the live site against what you submit.

Store files as `evidence/<section>/<NN>-<description>.png`.

---

## A. Git repository

| # | Evidence | Where to capture it | Done |
| --- | --- | --- | :---: |
| A1 | Repository home page showing the file tree and README | GitHub repo root | ☐ |
| A2 | Branch list showing `main`, `develop` and feature branches | Insights → Network, or the branches page | ☐ |
| A3 | Commit history with meaningful messages | Commits tab | ☐ |
| A4 | Commit history per author (all four members visible) | Insights → Contributors | ☐ |
| A5 | A single commit's diff, showing a real change | Any commit page | ☐ |
| A6 | Open and closed issues | Issues tab, filter `is:issue` | ☐ |
| A7 | One issue in full, with acceptance criteria | Any task issue | ☐ |
| A8 | Issue linked to the PR that closed it | Issue page, "closed by" reference | ☐ |
| A9 | Pull request list showing merged PRs from all four members | Pull requests → Closed | ☐ |
| A10 | A pull request in full: description, commits, checks, review | Any merged PR | ☐ |
| A11 | A code review with actual comments on lines | PR → Files changed | ☐ |
| A12 | A review that requested changes, and the follow-up commits | PR conversation | ☐ |
| A13 | An approval | PR → Reviewers | ☐ |
| A14 | Branch protection settings | Settings → Branches | ☐ |
| A15 | CODEOWNERS automatically requesting a reviewer | PR → Reviewers | ☐ |

## B. Merge conflict

Follow the exercise in `docs/collaboration-plan.md`.

| # | Evidence | Where | Done |
| --- | --- | --- | :---: |
| B1 | The terminal output reporting the conflict | `git merge origin/develop` | ☐ |
| B2 | `git status` showing the unmerged path | Terminal | ☐ |
| B3 | The conflict markers in the editor | VS Code / editor | ☐ |
| B4 | The resolved file | Editor | ☐ |
| B5 | Grep proving no markers remain | `grep -rn '<<<<<<<' app/` | ☐ |
| B6 | Tests passing after resolution | `pytest` output | ☐ |
| B7 | The merge commit in the history | `git log --graph --oneline` | ☐ |
| B8 | CI green on the updated pull request | Actions | ☐ |

## C. CI/CD pipeline

| # | Evidence | Where | Done |
| --- | --- | --- | :---: |
| C1 | Workflow list showing CI and CD | Actions tab | ☐ |
| C2 | A **successful** CI run, all jobs green | Actions → a CI run | ☐ |
| C3 | A **failed** CI run, with the failing step expanded | Actions → a failed run | ☐ |
| C4 | The commit that fixed it, with CI passing | Actions | ☐ |
| C5 | The `quality` job output: ruff, black, bandit | Job log | ☐ |
| C6 | The `unit-tests` job output showing tests passing | Job log | ☐ |
| C7 | The `integration-tests` job with the PostgreSQL service container | Job log | ☐ |
| C8 | The `coverage` job showing the percentage against the 85% gate | Job log / summary | ☐ |
| C9 | The `docker-build` job: image built, container healthy | Job log | ☐ |
| C10 | The `quality-gate` job passing | Job log | ☐ |
| C11 | A pull request blocked by a failing required check | PR page | ☐ |
| C12 | Build artefacts available for download | Actions run → Artifacts | ☐ |
| C13 | The HTML coverage report open in a browser | `reports/coverage/index.html` | ☐ |
| C14 | The CD workflow running after CI succeeded on main | Actions | ☐ |
| C15 | The CD deployment summary with the live URL | CD run → Summary | ☐ |

> **C3 matters more than C2.** Evidence that the gate actually blocks bad code
> is stronger than a wall of green ticks. Push a deliberate lint error or a
> failing test on a throwaway branch, screenshot the red pipeline, then fix it.

## D. Testing and quality

| # | Evidence | Where | Done |
| --- | --- | --- | :---: |
| D1 | Full `pytest` run: 255+ passed, coverage percentage | Terminal | ☐ |
| D2 | `pytest -m unit` output | Terminal | ☐ |
| D3 | `pytest -m integration` output | Terminal | ☐ |
| D4 | `pytest -m security` output | Terminal | ☐ |
| D5 | Coverage report showing per-module percentages | Terminal or HTML | ☐ |
| D6 | A deliberately failing test, proving the gate works | Terminal | ☐ |
| D7 | `ruff check .` passing | Terminal | ☐ |
| D8 | `black --check .` passing | Terminal | ☐ |
| D9 | `bandit -c pyproject.toml -r app -ll` with no findings | Terminal | ☐ |

## E. The application

Capture from the **live system** at https://qvs-mim736.fly.dev.

| # | Evidence | Page | Done |
| --- | --- | --- | :---: |
| E1 | Sign-in page | `/login` | ☐ |
| E2 | Sign-in failure message | `/login` after a wrong password | ☐ |
| E3 | Administrator dashboard with live counters | `/dashboard` | ☐ |
| E4 | Issuer dashboard (different content) | `/dashboard` as issuer | ☐ |
| E5 | Verifier dashboard (fewer options) | `/dashboard` as verifier | ☐ |
| E6 | Qualification registration form | `/qualifications/new` | ☐ |
| E7 | Validation errors on the registration form | Submit it with a future award date | ☐ |
| E8 | Registration success showing the generated credential ID | After registering | ☐ |
| E9 | Duplicate credential ID rejected | Register the same ID twice | ☐ |
| E10 | Search results | `/qualifications/?q=...` | ☐ |
| E11 | Filtered search (status = revoked) | `/qualifications/?status=revoked` | ☐ |
| E12 | Qualification detail page | `/qualifications/<id>` | ☐ |
| E13 | The review assistant panel with signals | Detail page of the revoked credential | ☐ |
| E14 | Verification form | `/verify/` | ☐ |
| E15 | **VALID** result | Verify `QVS-2023-DEMO01` | ☐ |
| E16 | **INVALID** result | Verify `QVS-2024-ZZZZZZ` | ☐ |
| E17 | **REVOKED** result | Verify `QVS-2021-DEMO03` | ☐ |
| E18 | **EXPIRED** result | Verify `QVS-2022-DEMO02` | ☐ |
| E19 | Verification receipt page | `/verify/result/<reference>` | ☐ |
| E20 | Verification history | `/verify/history` | ☐ |
| E21 | Verifier seeing only their own history | `/verify/history` as verifier | ☐ |
| E22 | Revocation panel with the reason field | Detail page → Revoke | ☐ |
| E23 | The same credential verifying as REVOKED afterwards | `/verify/` | ☐ |
| E24 | Audit trail | `/admin/audit` | ☐ |
| E25 | Audit trail filtered by action | `/admin/audit?action=verification.performed` | ☐ |
| E26 | User management | `/admin/users` | ☐ |
| E27 | Institution management | `/admin/institutions` | ☐ |
| E28 | Profile page | `/profile` | ☐ |
| E29 | 403 page (sign in as verifier, open `/admin/users`) | `/admin/users` | ☐ |
| E30 | 404 page | Any bad URL | ☐ |
| E31 | The interface on a phone-width screen | Any page, narrow window | ☐ |

## F. Docker

| # | Evidence | Command | Done |
| --- | --- | --- | :---: |
| F1 | `docker build` completing | `docker build -t qvs:local .` | ☐ |
| F2 | The built image and its size | `docker images qvs` | ☐ |
| F3 | The container running | `docker run ...` then `docker ps` | ☐ |
| F4 | The health check reporting healthy | `docker ps` STATUS column | ☐ |
| F5 | `/healthz` responding from the container | `curl localhost:8080/healthz` | ☐ |
| F6 | The application served from the container | Browser on `localhost:8080` | ☐ |
| F7 | `docker compose up` with app and PostgreSQL | `docker compose up --build` | ☐ |

> **If Docker will not run on your machine**, the `docker-build` CI job builds
> and smoke-tests the image on every push — screenshot that job instead, and say
> in your report that this is where the Docker evidence comes from. That is
> honest and still demonstrates the capability. Do not pretend you ran it
> locally.

## G. Deployment

| # | Evidence | Where | Done |
| --- | --- | --- | :---: |
| G1 | The live application in a browser, URL bar visible | https://qvs-mim736.fly.dev | ☐ |
| G2 | HTTPS padlock and certificate details | Browser | ☐ |
| G3 | Fly.io dashboard showing the app | fly.io/apps/qvs-mim736 | ☐ |
| G4 | `flyctl status` output | Terminal | ☐ |
| G5 | Machine list showing it running | `flyctl machine list` | ☐ |
| G6 | Fly health checks passing | Fly dashboard → Monitoring | ☐ |
| G7 | Live logs | `flyctl logs` | ☐ |
| G8 | Release history | `flyctl releases` | ☐ |
| G9 | Volume list | `flyctl volumes list` | ☐ |
| G10 | Secrets list (names and digests only — **never values**) | `flyctl secrets list` | ☐ |
| G11 | The live `/healthz` response | `curl https://qvs-mim736.fly.dev/healthz` | ☐ |
| G12 | Security headers on the live site | `curl -I` or browser dev tools | ☐ |
| G13 | A full verification performed on the live system | Browser | ☐ |

## H. Individual contributions

Each member captures for themselves:

| # | Evidence | Where | Done |
| --- | --- | --- | :---: |
| H1 | Your commits, filtered to you | `git log --author="Your Name"` or GitHub | ☐ |
| H2 | Your contribution graph | Insights → Contributors | ☐ |
| H3 | Your branches | Branches page | ☐ |
| H4 | Your pull requests | PRs filtered by author | ☐ |
| H5 | A review **you gave** someone else | PR → Files changed | ☐ |
| H6 | A review **you received** and addressed | Your PR | ☐ |
| H7 | Issues you opened and closed | Issues, filtered by author | ☐ |
| H8 | Tests you wrote, passing | Terminal | ☐ |

---

## Rules

1. **Capture as you go.** Recreating evidence later produces artefacts with
   suspicious timestamps and no supporting history.
2. **Never fabricate.** No edited screenshots, no invented PR numbers, no
   pretend deployment URLs. It is checkable, and a genuine partial result marks
   better than a fake complete one.
3. **Include the context.** The URL bar, the timestamp, the branch name and the
   commit SHA are what make a screenshot evidence rather than a picture.
4. **Redact secrets.** Never capture a secret value, a token or a real password.
   `flyctl secrets list` shows names and digests only — that is the safe one.
5. **Name files consistently.** `evidence/C/03-failed-ci-run.png`.
6. **A failure is evidence too.** The failing pipeline, the requested changes,
   the conflict — these demonstrate the process working, which is what is being
   assessed.

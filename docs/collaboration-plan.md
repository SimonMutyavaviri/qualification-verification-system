# Post-Baseline Collaboration Plan

The baseline system is complete, tested and deployed. This plan gives each of
the four team members **genuine improvements to make to a working system** —
not busy-work to generate commits.

Every task below fixes a real, named gap. Each is small enough to complete in a
few sittings, and each leaves the system better than it found it.

---

## How to read a task

Each task specifies: the issue to raise, the branch name, acceptance criteria,
the files you will touch, the tests you must add, and the evidence to capture.

**Do not skip the issue.** The assignment is assessed on issue tracking as well
as commits, and an issue written before the code is what keeps the work honest.

## The cycle every task follows

```
1. Open the issue (use .github/ISSUE_TEMPLATE/task.md)
2. git checkout develop && git pull origin develop
3. git checkout -b <branch>
4. Work in small commits (Conventional Commits format)
5. git push -u origin <branch>
6. Open a pull request; link the issue with "Closes #N"
7. Wait for CI. A red pipeline is not ready for review.
8. Request a review from the teammate named in your task
9. Address the feedback with follow-up commits
10. Squash and merge once approved; delete the branch
```

**Every member must both request and give at least one review.** Review pairing:

| Author | Reviewed by |
| --- | --- |
| Student 1 | Student 3 |
| Student 2 | Student 4 |
| Student 3 | Student 1 |
| Student 4 | Student 2 |

---

# Student 1 — Authentication, backend hardening and user management

**Area of ownership:** `app/services/user_service.py`, `app/utils/security.py`,
`app/auth/`, `app/routes/auth_routes.py`

## Task 1.1 — Lock an account after repeated failed sign-ins

**The real gap.** `docs/security.md` §7 records this openly: the system counts
failed sign-ins and rate-limits them at 10 per minute, but never locks an
account. An attacker with a list of common passwords can keep guessing
indefinitely at 10 attempts a minute.

**Issue title:** `[Task] Lock an account after repeated failed sign-in attempts`

**Branch:** `feature/auth-account-lockout`

**Acceptance criteria**

- [ ] After 5 consecutive failed attempts, the account is locked
- [ ] A locked account is refused sign-in even with the correct password
- [ ] The lock expires automatically after a configurable period (default 15 minutes)
- [ ] A successful sign-in clears the counter and the lock
- [ ] The lockout message does not reveal whether the account exists
- [ ] Locking and automatic unlocking are written to the audit trail
- [ ] An administrator can clear a lock from the user management page
- [ ] The threshold and duration are configurable in `app/config.py`

**Files you will change**

```
app/models/user.py                 add locked_until (nullable datetime)
app/config.py                      LOCKOUT_THRESHOLD, LOCKOUT_MINUTES
app/services/user_service.py       lock in authenticate(); add clear_lock()
app/models/enums.py                new AuditAction values
app/routes/admin_routes.py         route to clear a lock
app/templates/admin/users.html     lock status and the clear button
tests/unit/test_auth_and_audit.py  tests
docs/security.md                   move this out of the gaps table
migrations/versions/               a migration for the new column
```

**Tests you must add** — at least six: lock after the threshold; correct
password refused while locked; automatic expiry after the window; counter reset
on success; lockout audited; administrator can clear a lock.

**Watch out for.** Do not let the lockout message differ from the ordinary
failure message in a way that lets an attacker discover which accounts exist.
Think about what an attacker learns from each possible response.

## Task 1.2 — Prevent password reuse

**The real gap.** `change_password` rejects reusing the *current* password, but
a user can alternate between two passwords forever.

**Issue title:** `[Task] Prevent reuse of recent passwords`
**Branch:** `feature/auth-password-history`

**Acceptance criteria**

- [ ] The last 5 password hashes are retained per user
- [ ] Changing to any of those 5 is refused with a clear message
- [ ] History is stored as hashes only — never plaintext
- [ ] The history is capped at 5 and old entries are discarded
- [ ] Password changes remain audited

**Files:** `app/models/user.py` (or a new `PasswordHistory` model),
`app/services/user_service.py`, tests, a migration.

**Watch out for.** Storing history on the user row as a list is tempting, but a
separate table with a foreign key is the right shape — and think about what
happens to it when the user is deleted.

---

# Student 2 — Qualification management

**Area of ownership:** `app/services/qualification_service.py`,
`app/routes/qualification_routes.py`, `app/templates/qualifications/`

## Task 2.1 — Bulk registration from CSV

**The real gap.** `docs/requirements.md` §6 lists bulk import as out of scope
for the baseline, but a registry adding a graduating cohort of 400 students one
form at a time is the obvious real-world need.

**Issue title:** `[Task] Register qualifications in bulk from a CSV upload`
**Branch:** `feature/qualifications-bulk-import`

**Acceptance criteria**

- [ ] An issuer can upload a CSV of qualifications
- [ ] A downloadable template CSV documents the expected columns
- [ ] Every row is validated with the **existing** validators — no second set of rules
- [ ] A preview shows what will be imported and what will be rejected, before committing
- [ ] Valid rows import; invalid rows are reported with the row number and the reason
- [ ] The whole import is one transaction — a failure imports nothing
- [ ] The import is audited as a single event recording the row count
- [ ] Upload size is capped and only `.csv` is accepted

**Files:** `app/services/qualification_service.py` (a `bulk_register` method),
`app/forms.py`, `app/routes/qualification_routes.py`, a new template,
`tests/unit/test_qualification_service.py`, `tests/integration/test_workflows.py`.

**Tests:** a valid import; a file with some invalid rows; duplicate credential
IDs inside the file itself; a duplicate against the existing register; an empty
file; a malformed file; a non-CSV upload; and a verifier being refused.

**Watch out for.** File upload is an attack surface. Cap the size, check the
content type, and never trust the filename. Also: two rows in the *same file*
carrying the same credential ID must be caught — the database constraint will
catch it, but the error message should be helpful rather than a 500.

## Task 2.2 — Sortable columns and a saved result count

**The real gap.** The register lists newest-first only. A registrar looking for
"everything awarded by MSU in 2023" cannot order by award date.

**Issue title:** `[Task] Allow the qualification register to be sorted`
**Branch:** `feature/qualifications-sortable-columns`

**Acceptance criteria**

- [ ] Credential ID, holder name, award date and status are sortable
- [ ] Selecting a column header toggles ascending/descending
- [ ] The current sort is shown in the header and survives pagination
- [ ] Sorting composes with the existing filters
- [ ] The sort field is validated against an allow-list — never interpolated into SQL
- [ ] Page size is selectable (10 / 25 / 50)

**Watch out for.** An unvalidated sort parameter that reaches `order_by` is a
genuine injection risk. Map the request value through a dictionary of permitted
columns; never pass the raw string.

---

# Student 3 — Verification and audit

**Area of ownership:** `app/services/verification_service.py`,
`app/services/audit_service.py`, `app/routes/verification_routes.py`,
`app/templates/verification/`

## Task 3.1 — Export the audit trail and add date filtering

**The real gap.** The audit trail can only be browsed by action type, page by
page. An auditor asking "show me everything that happened between 1 and 31
March" cannot be answered, and there is no way to hand the evidence over.

**Issue title:** `[Task] Add date-range filtering and CSV export to the audit trail`
**Branch:** `feature/audit-export-and-date-filter`

**Acceptance criteria**

- [ ] The audit page accepts a start and end date
- [ ] Filters compose with the existing action filter
- [ ] An invalid or reversed date range is rejected with a clear message
- [ ] An administrator can export the filtered result as CSV
- [ ] The export respects the filters currently applied
- [ ] The export itself is audited — exporting the audit trail is an auditable act
- [ ] The export streams rather than loading everything into memory
- [ ] Only administrators can export

**Files:** `app/repositories/audit_repository.py`, `app/services/audit_service.py`,
`app/routes/admin_routes.py`, `app/templates/admin/audit.html`, tests.

**Watch out for.** Streaming a large export inside a request context is the
subtle part — read how Flask's `stream_with_context` interacts with the database
session before you start. Also: timezone. Timestamps are stored in UTC; a date
filter typed by a user is in their local day.

## Task 3.2 — A verification result the holder can share

**The real gap.** A verification receipt is only visible to signed-in users. A
graduate who wants to give an employer proof cannot, and the employer would need
an account.

**Issue title:** `[Task] Add a shareable, expiring public verification receipt`
**Branch:** `feature/verification-shareable-receipt`

**Acceptance criteria**

- [ ] A signed-in user can generate a shareable link for a verification they performed
- [ ] The link is viewable without signing in
- [ ] The link expires after a configurable period (default 7 days)
- [ ] An expired link shows a clear message, not an error
- [ ] The public page shows only holder, title, institution, award date and result
- [ ] The public page shows **no** internal identifiers, no verifier identity, no IP
- [ ] The token is unguessable and is not the verification's own reference
- [ ] Public views are rate-limited and audited
- [ ] Links can be revoked by their creator

**Watch out for.** This deliberately weakens the "verification requires
authentication" property described in `docs/requirements.md` §6, so the
compensating controls matter: expiry, an unguessable token, minimal disclosure,
rate limiting and revocability. Update `docs/security.md` to describe the new
surface honestly.

---

# Student 4 — DevOps, QA, Docker and deployment

**Area of ownership:** `.github/`, `Dockerfile`, `docker-compose.yml`,
`fly.toml`, `pyproject.toml`

## Task 4.1 — Scan dependencies for known vulnerabilities

**The real gap.** `docs/security.md` §7 and `docs/ci-cd.md` §9 both record it:
Bandit analyses **our** code but never looks at our dependencies. A published
CVE in Flask or SQLAlchemy would pass every current check.

**Issue title:** `[Task] Add dependency vulnerability scanning to CI`
**Branch:** `chore/ci-dependency-scanning`

**Acceptance criteria**

- [ ] `pip-audit` runs in the `quality` job on every push and pull request
- [ ] A known vulnerability fails the build
- [ ] The report is uploaded as a build artefact
- [ ] Any accepted exception is listed with a written justification, not silently ignored
- [ ] `requirements-dev.txt` pins the tool version
- [ ] A scheduled weekly run catches CVEs published after a merge
- [ ] `docs/ci-cd.md` and `docs/security.md` are updated to remove this gap

**Watch out for.** A scheduled scan that fails on a newly published CVE will
wake the team up at an inconvenient moment. Decide deliberately whether the
scheduled run should fail the build or open an issue, and write down why.

## Task 4.2 — Add a staging environment

**The real gap.** `docs/ci-cd.md` §9 states it plainly: `develop` is tested but
deployed nowhere, and `main` goes straight to production. Nobody ever sees a
change running before real users do.

**Issue title:** `[Task] Deploy the develop branch to a staging environment`
**Branch:** `chore/cd-staging-environment`

**Acceptance criteria**

- [ ] A second Fly app (`qvs-mim736-staging`) exists with its own volume and secrets
- [ ] Merging to `develop` deploys to staging automatically after CI passes
- [ ] Staging is clearly marked as such in the interface
- [ ] Staging uses its own secrets — never production's
- [ ] The staging deployment is health-checked exactly as production is
- [ ] Production deployment still happens only from `main`
- [ ] `docs/flyio-deployment.md` documents both environments

**Watch out for.** The single most important thing is that staging cannot reach
production data or secrets. Check that twice.

## Task 4.3 — Close the remaining test gaps

**The real gap.** `docs/testing-strategy.md` §11 lists them honestly: rate
limiting is disabled in tests, the `/healthz` database-outage branch is not
automatically tested, and there are no browser-level tests.

**Issue title:** `[Task] Test the rate limiter and the health-check failure path`
**Branch:** `test/close-known-coverage-gaps`

**Acceptance criteria**

- [ ] A test proves the sign-in rate limit returns 429 after the threshold
- [ ] A test proves the verification rate limit behaves the same
- [ ] Rate-limit tests are isolated so they do not affect other tests
- [ ] A test proves `/healthz` returns 503 when the database is unreachable
- [ ] Coverage rises, and the gate in `pyproject.toml` is raised to match
- [ ] `docs/testing-strategy.md` §11 is updated to reflect what is now covered

**Watch out for.** Rate-limit state leaks between tests — the limiter's storage
must be reset per test or the suite becomes order-dependent, which is exactly
the property the current suite is careful to keep. Ensure the 503 test does not
leave the session broken for the tests that follow.

---

# Merge conflict exercise

The assignment requires evidence of genuine merge conflict management. This
produces a **real** conflict from two legitimate changes, not an artificial one.

## The setup

`app/models/enums.py` contains the `AuditAction` enumeration. Two tasks in this
plan both need to add members to it:

- **Student 1** (Task 1.1) adds `USER_LOCKED` and `USER_UNLOCKED`
- **Student 3** (Task 3.1) adds `AUDIT_EXPORTED`

If both branch from the same commit and add their members at the end of the
same enum, Git cannot know which order the lines belong in, and the merge
conflicts. This is exactly how conflicts arise in real work: two people
extending the same list for unrelated, equally valid reasons.

## Running the exercise

**1. Both students branch from the same point.**

```bash
git checkout develop && git pull origin develop
git rev-parse HEAD        # both must record the same SHA
```

**2. Each adds their members at the end of `AuditAction`,** commits and pushes.

**3. Student 1 merges first.** Normal review, normal merge into `develop`.

**4. Student 3 now updates their branch and hits the conflict.**

```bash
git checkout feature/audit-export-and-date-filter
git fetch origin
git merge origin/develop
# CONFLICT (content): Merge conflict in app/models/enums.py
```

```
<<<<<<< HEAD
    AUDIT_EXPORTED = "audit.exported"
=======
    USER_LOCKED = "user.locked"
    USER_UNLOCKED = "user.unlocked"
>>>>>>> origin/develop
```

**5. Resolve by keeping both.** This is the point of the exercise: the
resolution is not one side or the other. Both members are needed, and deleting
either would silently remove a colleague's feature.

```python
    USER_LOCKED = "user.locked"
    USER_UNLOCKED = "user.unlocked"
    AUDIT_EXPORTED = "audit.exported"
```

**6. Verify the resolution.**

```bash
grep -rn '<<<<<<<\|=======\|>>>>>>>' app/     # must return nothing
pytest                                        # must pass
ruff check . && black --check .
```

**7. Commit and push.**

```bash
git add app/models/enums.py
git commit          # keep the merge message; add a line on how you resolved it
git push
```

## What to document

Student 3 records in their individual report, and the team in the technical
report:

1. **What caused it** — two branches adding members to the same enum, both valid.
2. **How it was found** — `git merge origin/develop` reported the conflict;
   `git status` listed the file.
3. **How it was resolved** — both sets of members kept, in a sensible order,
   because each supports a feature the other did not know about.
4. **How the resolution was tested** — marker grep, full `pytest` run, lint and
   format checks, and CI passing on the updated pull request.
5. **How the PR completed** — re-review after the merge commit, approval, merge.

**Capture:** `[INSERT SCREENSHOT: the conflict in the editor]`,
`[INSERT SCREENSHOT: git status showing the unmerged path]`,
`[INSERT SCREENSHOT: the resolved file]`,
`[INSERT SCREENSHOT: CI green on the updated PR]`.

> **Do not fabricate this.** A conflict that was actually resolved looks
> different from an invented one, and the commit graph shows which happened.

---

# Definition of done

A task is finished when **all** of these are true:

- [ ] The issue is closed by the merged pull request
- [ ] Acceptance criteria are all met
- [ ] Tests are added and the full suite passes
- [ ] Coverage is at or above the gate
- [ ] `ruff`, `black` and `bandit` pass
- [ ] The pull request was reviewed and approved by the assigned reviewer
- [ ] Review feedback was addressed with follow-up commits
- [ ] CI is green on the final commit
- [ ] Documentation is updated where behaviour changed
- [ ] Evidence is captured per `docs/evidence-checklist.md`
- [ ] The individual contribution report is updated with real commit SHAs and PR numbers

# Suggested sequence

| Phase | Student 1 | Student 2 | Student 3 | Student 4 |
| --- | --- | --- | --- | --- |
| 1 | Task 1.1 | Task 2.1 | Task 3.1 | Task 4.1 |
| 2 | *(conflict exercise with S3)* | Task 2.2 | *(conflict exercise with S1)* | Task 4.2 |
| 3 | Task 1.2 | Review + evidence | Task 3.2 | Task 4.3 |
| 4 | Individual report | Individual report | Individual report | Individual report |

Student 4's Task 4.1 is worth doing first: once dependency scanning is in CI,
everyone else's pull requests benefit from it.

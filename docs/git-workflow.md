# Git and Collaboration Workflow

## 1. Branching strategy

A trimmed **GitHub Flow with a develop integration branch** — enough structure
for a four-person team on a fixed-length project, without the ceremony of full
Git Flow (release and hotfix branches solve problems this project does not
have).

```
main ─────●───────────────●───────────────●──────>   protected, always deployable
           \             /               /
develop ────●───●───●───●───●───●───●───●────────>   integration branch
             \     /     \     /     \ /
              ●───●       ●───●       ●             short-lived work branches
```

| Branch | Purpose | Protected | Deploys to |
| --- | --- | --- | --- |
| `main` | Release-ready. Every commit has passed the full quality gate. | Yes | Fly.io production |
| `develop` | Integration. Where completed work lands before release. | Yes | — |
| `feature/*` | New functionality | No | — |
| `fix/*` | Bug fixes | No | — |
| `docs/*` | Documentation only | No | — |
| `chore/*` | Tooling, CI, dependencies | No | — |
| `test/*` | Test-only additions | No | — |

### Branch naming

```
<type>/<short-kebab-case-description>

feature/auth-account-lockout
fix/expiry-boundary-off-by-one
chore/ci-add-pip-audit
docs/update-deployment-guide
```

Keep it under about 50 characters and name the *change*, not the person.

## 2. The contribution cycle

```
Issue  ->  Branch  ->  Commit(s)  ->  Push  ->  Pull Request
                                                     |
                                              CI quality gate
                                                     |
                                              Code review
                                                     |
                                        Changes requested? --> fix, push again
                                                     |
                                                 Approved
                                                     |
                                              Squash and merge
                                                     |
                                             Delete the branch
```

### Step by step

**1. Open an issue.** Every change starts with one, using a template from
`.github/ISSUE_TEMPLATE/`. Acceptance criteria must be objectively checkable
before any code is written.

**2. Branch from `develop`.**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/auth-account-lockout
```

**3. Commit as you work.** Small, focused commits — not one enormous commit at
the end. A reviewer reads the commits, and so does the marker.

**4. Push and open a pull request.**

```bash
git push -u origin feature/auth-account-lockout
```

Fill in the template. Link the issue with `Closes #12`.

**5. CI runs automatically.** Lint, format, security scan, unit tests,
integration tests against PostgreSQL, coverage gate, Docker build and smoke
test. A red pipeline is not ready for review.

**6. Review.** At least one approval from another team member. CODEOWNERS
requests the owner of the touched area automatically.

**7. Address feedback.** Push follow-up commits to the same branch; the pull
request and CI update themselves. Do not force-push during review — it destroys
the reviewer's place in the diff.

**8. Merge.** Squash and merge into `develop`, then delete the branch.

## 3. Commit message convention

Conventional Commits:

```
<type>(<scope>): <subject in the imperative>

<body: why, not what>

<footer: issue references>
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `style`.

Good:

```
feat(auth): lock an account after five consecutive failed sign-ins

The rate limit slows online guessing but does not stop it. Locking after
five failures within the window bounds the attempt count per account,
while the existing audit entries still record every attempt.

Closes #12
```

```
fix(verification): treat a credential expiring today as still valid

is_expired() used `<=`, so a credential reported EXPIRED on its own expiry
date. The certificate is valid through the whole of that day.

Closes #23
```

Poor: `update`, `fixed stuff`, `changes`, `asdf`, `final version`, `final
version 2`.

Rules: imperative mood ("add", not "added"), subject under 72 characters, no
trailing full stop in the subject, body explains *why*.

## 4. Code review standards

A reviewer checks:

- [ ] Does it do what the issue asked, and nothing unrelated?
- [ ] Are there tests, and do they test behaviour rather than implementation?
- [ ] Are negative and edge cases covered?
- [ ] Does it hold the layering (routes → services → repositories)?
- [ ] Are authorisation checks present where they need to be?
- [ ] Is anything auditable actually audited?
- [ ] Are error paths handled, without leaking internals?
- [ ] Any secrets, credentials or debug output left behind?
- [ ] Do the names and comments explain the non-obvious?
- [ ] Is the documentation updated if behaviour changed?

Review etiquette: comment on the code, not the author; distinguish blocking
concerns from suggestions ("nit:" for the optional); explain *why*; and approve
once it is better than what is on `develop` — not once it is perfect.

## 5. Merge conflict management

Conflicts are normal on a shared codebase. Resolve them like this:

```bash
# Bring your branch up to date with develop
git checkout feature/my-work
git fetch origin
git merge origin/develop
# ... CONFLICT (content): Merge conflict in app/services/qualification_service.py
```

Open the file and find the markers:

```
<<<<<<< HEAD
    your change
=======
    the change already on develop
>>>>>>> origin/develop
```

Then:

1. **Understand both sides.** `git log --oneline origin/develop -5` and
   `git blame` tell you what the other change was trying to do.
2. **Keep both intentions.** The resolution is usually not one side or the
   other, but code that satisfies both. Deleting a colleague's change to make
   the conflict go away is the failure mode to avoid.
3. **Remove every marker.** `grep -rn '<<<<<<<' app/` before committing.
4. **Run the tests.** `pytest` — a syntactically clean resolution can still be
   semantically wrong.
5. **Commit and push.**

```bash
git add app/services/qualification_service.py
git commit          # keep the generated merge message; add a note on the resolution
git push
```

A planned, genuine conflict exercise is described in
`docs/collaboration-plan.md` (section "Merge conflict exercise").

## 6. Branch protection settings

Configure on GitHub for `main` and `develop`
(**Settings → Branches → Add rule**):

- [x] Require a pull request before merging
- [x] Require 1 approval
- [x] Dismiss stale approvals when new commits are pushed
- [x] Require review from Code Owners
- [x] Require status checks to pass — select **Quality gate**
- [x] Require branches to be up to date before merging
- [x] Require conversation resolution before merging
- [x] Do not allow bypassing the above settings

`Quality gate` is a single job that depends on every other CI job, so one
required check covers the whole pipeline.

## 7. Everyday commands

```bash
# Start work
git checkout develop && git pull origin develop
git checkout -b feature/my-change

# See what you have changed
git status
git diff

# Stage and commit
git add app/services/verification_service.py tests/unit/test_verification_service.py
git commit

# Keep up to date with develop
git fetch origin && git merge origin/develop

# Push
git push -u origin feature/my-change

# Review history
git log --oneline --graph --decorate --all
git log --author="Your Name" --oneline

# Undo safely
git restore app/file.py             # discard unstaged changes to a file
git restore --staged app/file.py    # unstage, keep the changes
git revert <sha>                    # undo a pushed commit with a new commit
```

Never `git push --force` to a shared branch. Use `git revert` to undo published
history.

## 8. What must never be committed

- `.env` or any real secret, token or key
- `*.db`, `*.sqlite3` — local databases
- `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
- `reports/coverage/`, `.coverage`
- IDE directories

All are covered by `.gitignore`. If a secret is committed by accident: rotate
it immediately — removing it from history does not un-leak it.

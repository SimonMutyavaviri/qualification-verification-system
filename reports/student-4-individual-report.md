# Individual Contribution Report

## Student 4

---

## 1. Student information

| | |
| --- | --- |
| **Full name** | `[INSERT YOUR FULL NAME]` |
| **Student number** | `[INSERT YOUR STUDENT NUMBER]` |
| **Course** | MIM736 |
| **Assignment** | Practical Assignment - Qualification Verification System |
| **GitHub username** | `[INSERT YOUR GITHUB USERNAME]` |
| **Repository** | `[INSERT REPOSITORY URL]` |
| **Submission date** | `[INSERT DATE]` |

---

## 2. Assigned role

**DevOps, QA, Docker and Deployment**

I was responsible for the following areas of the codebase, as recorded in
`.github/CODEOWNERS`:

- `.github/workflows/ci.yml` - the continuous integration pipeline
- `.github/workflows/cd.yml` - continuous delivery to Fly.io
- `Dockerfile`, `docker-compose.yml` - containerisation
- `fly.toml`, `pyproject.toml` - deployment and tooling configuration

My work is defined in `docs/collaboration-plan.md` under "Student 4".

---

## 3. Summary of contributions

> Complete this after your Git work. Every figure must come from the repository.

| Metric | Value |
| --- | --- |
| Issues opened | `[INSERT NUMBER]` |
| Branches created | `[INSERT NUMBER]` |
| Commits authored | `[INSERT NUMBER]` |
| Pull requests opened | `[INSERT NUMBER]` |
| Pull requests merged | `[INSERT NUMBER]` |
| Code reviews given | `[INSERT NUMBER]` |
| Tests added | `[INSERT NUMBER]` |
| Files changed | `[INSERT NUMBER]` |

Obtain these with:

```bash
git log --author="YOUR NAME" --oneline | wc -l
git log --author="YOUR NAME" --stat
```

and from **Insights - Contributors** on GitHub.

`[INSERT SCREENSHOT: your contribution graph]`

---

## 4. Tasks completed

### Task 4.1 - Dependency vulnerability scanning in CI

**Branch:** `chore/ci-dependency-scanning`
**Issue:** `[INSERT ISSUE NUMBER]`
**Pull request:** `[INSERT PR NUMBER]`

**The gap this addressed.** Bandit analysed our own code but never our dependencies, so a published CVE in Flask or SQLAlchemy would have passed every check. This gap was documented in `docs/security.md` section 7 and `docs/ci-cd.md` section 9.

**Acceptance criteria met:** see `docs/collaboration-plan.md`, Task 4.1.

**What I changed:**

`[INSERT: the files you touched and what you did to each]`

**Tests I added:**

`[INSERT: name each test and say what it proves]`

**Evidence:**

- `[INSERT SCREENSHOT: the CI run passing on this PR]`
- `[INSERT SCREENSHOT: the feature working in the application]`
- `[INSERT SCREENSHOT: the merged pull request]`


### Task 4.2 - A staging environment

**Branch:** `chore/cd-staging-environment`
**Issue:** `[INSERT ISSUE NUMBER]`
**Pull request:** `[INSERT PR NUMBER]`

**The gap this addressed.** `develop` was tested but deployed nowhere and `main` went straight to production, so no change was ever seen running before real users saw it. Documented in `docs/ci-cd.md` section 9.

**Acceptance criteria met:** see `docs/collaboration-plan.md`, Task 4.2.

**What I changed:**

`[INSERT: the files you touched and what you did to each]`

**Tests I added:**

`[INSERT: name each test and say what it proves]`

**Evidence:**

- `[INSERT SCREENSHOT: the CI run passing on this PR]`
- `[INSERT SCREENSHOT: the feature working in the application]`
- `[INSERT SCREENSHOT: the merged pull request]`


### Task 4.3 - Close the known test gaps

**Branch:** `test/close-known-coverage-gaps`
**Issue:** `[INSERT ISSUE NUMBER]`
**Pull request:** `[INSERT PR NUMBER]`

**The gap this addressed.** Rate limiting was disabled in the test suite and the `/healthz` database-outage branch was only manually verified. Both were listed honestly in `docs/testing-strategy.md` section 11.

**Acceptance criteria met:** see `docs/collaboration-plan.md`, Task 4.3.

**What I changed:**

`[INSERT: the files you touched and what you did to each]`

**Tests I added:**

`[INSERT: name each test and say what it proves]`

**Evidence:**

- `[INSERT SCREENSHOT: the CI run passing on this PR]`
- `[INSERT SCREENSHOT: the feature working in the application]`
- `[INSERT SCREENSHOT: the merged pull request]`


---

## 5. Git branches

| Branch | Purpose | Commits | Merged | PR |
| --- | --- | ---: | --- | --- |
| `chore/ci-dependency-scanning` | Dependency vulnerability scanning in CI | `[N]` | `[DATE]` | `[#N]` |
| `chore/cd-staging-environment` | A staging environment | `[N]` | `[DATE]` | `[#N]` |
| `test/close-known-coverage-gaps` | Close the known test gaps | `[N]` | `[DATE]` | `[#N]` |

`[INSERT SCREENSHOT: the branches page filtered to your branches]`

---

## 6. Commits

List your most significant commits. Use real SHAs from `git log`.

| SHA | Message | Files changed | Why it mattered |
| --- | --- | ---: | --- |
| `[INSERT SHA]` | `[INSERT COMMIT MESSAGE]` | `[N]` | `[INSERT]` |
| `[INSERT SHA]` | `[INSERT COMMIT MESSAGE]` | `[N]` | `[INSERT]` |
| `[INSERT SHA]` | `[INSERT COMMIT MESSAGE]` | `[N]` | `[INSERT]` |
| `[INSERT SHA]` | `[INSERT COMMIT MESSAGE]` | `[N]` | `[INSERT]` |
| `[INSERT SHA]` | `[INSERT COMMIT MESSAGE]` | `[N]` | `[INSERT]` |

```bash
git log --author="YOUR NAME" --pretty=format:"%h %s" --shortstat
```

`[INSERT SCREENSHOT: your commit history]`

---

## 7. Issues

| # | Title | Opened | Closed by | Status |
| --- | --- | --- | --- | --- |
| `[#N]` | `[INSERT TITLE]` | `[DATE]` | `[PR #N]` | Closed |
| `[#N]` | `[INSERT TITLE]` | `[DATE]` | `[PR #N]` | Closed |

`[INSERT SCREENSHOT: an issue you opened, showing its acceptance criteria]`

---

## 8. Pull requests

| # | Title | Reviewer | Changes requested? | Merged |
| --- | --- | --- | --- | --- |
| `[#N]` | `[INSERT TITLE]` | `[REVIEWER]` | `[Yes/No]` | `[DATE]` |
| `[#N]` | `[INSERT TITLE]` | `[REVIEWER]` | `[Yes/No]` | `[DATE]` |

`[INSERT SCREENSHOT: one of your pull requests in full - description, commits,
checks, review]`

---

## 9. Code reviews I gave

I reviewed **Student 2**'s work.

| PR | Author | Comments made | Outcome |
| --- | --- | ---: | --- |
| `[#N]` | `[AUTHOR]` | `[N]` | `[Approved / Changes requested then approved]` |

**A substantive review comment I made:**

> `[INSERT YOUR ACTUAL COMMENT]`

**Why I raised it:** `[INSERT: what problem would this have caused if merged?]`

**How the author responded:** `[INSERT]`

`[INSERT SCREENSHOT: your review comments on the Files-changed tab]`

---

## 10. Code review I received

| PR | Reviewer | Changes requested | How I responded |
| --- | --- | --- | --- |
| `[#N]` | `[REVIEWER]` | `[INSERT]` | `[INSERT]` |

**The most useful feedback I received:**

> `[INSERT THE ACTUAL COMMENT]`

**What I changed as a result:** `[INSERT]`

**What I learned from it:** `[INSERT - be specific. "I learned to write better
code" says nothing.]`

---

## 11. Technical contribution

### 11.1 What I built

`[INSERT: describe your implementation. Explain the design decisions you took
and why, not just what the feature does. Reference specific functions and
files.]`

### 11.2 A decision I had to make

`[INSERT: describe a genuine choice you faced - two ways of doing something -
what you chose, and why. Include what the alternative would have cost.]`

### 11.3 How my work fits the architecture

`[INSERT: explain how your change respects the routes - services - repositories
layering, where you put authorisation checks, and what you audited.]`

---

## 12. Testing contribution

| Test file | Tests added | What they cover |
| --- | ---: | --- |
| `[INSERT FILE]` | `[N]` | `[INSERT]` |
| `[INSERT FILE]` | `[N]` | `[INSERT]` |

**Coverage before my work:** `[INSERT]`%
**Coverage after:** `[INSERT]`%

**A negative test case I am pleased with:**

```python
[INSERT THE ACTUAL TEST]
```

`[INSERT: why this case mattered - what bug would it catch?]`

`[INSERT SCREENSHOT: your tests passing]`

---

## 13. Challenges encountered

> Describe **real** difficulties. An invented challenge is obvious to a marker,
> and a genuine one - even a small one - reads far better than a polished
> fiction. "I could not work out why the test passed locally and failed in CI"
> is a good challenge.

### Challenge 1

**What happened:** `[INSERT]`

**Why it was difficult:** `[INSERT]`

**What I tried that did not work:** `[INSERT]`

**How I eventually solved it:** `[INSERT]`

**What I would do differently next time:** `[INSERT]`

### Challenge 2

**What happened:** `[INSERT]`

**How I solved it:** `[INSERT]`



---

## 14. Solutions and problem-solving approach

`[INSERT: describe how you approach a problem you cannot immediately solve.
Which resources did you use - documentation, teammates, error messages, the
existing tests? What worked?]`

---

## 15. Lessons learnt

> Be specific. Vague reflection scores poorly.

**Technical:**

`[INSERT: something concrete you did not know before. For example: why a test
that passes on SQLite can fail on PostgreSQL, or why authorisation belongs in
the service layer as well as the route.]`

**About collaboration:**

`[INSERT: something about working on a shared codebase - reviewing, being
reviewed, resolving a conflict, or coordinating a change that touched someone
else's area.]`

**About process:**

`[INSERT: something about issues, CI, or quality gates. Did the pipeline catch
something you would have missed?]`

---

## 16. Personal reflection

`[INSERT - 250 to 400 words in your own voice.]`

Consider addressing:

- What are you most satisfied with in your contribution?
- What are you least satisfied with, and why?
- How did working on an already-working system differ from starting from scratch?
- What did the automated quality gates change about how you worked?
- Which part of the team's process would you change?
- What will you take into your next project?

---

## 17. Declaration

I confirm that this report is an accurate account of my own contribution to the
project, that the Git evidence cited is genuine and verifiable in the
repository, and that I have not misrepresented the work of others as my own.

**Signature:** `[INSERT]`
**Date:** `[INSERT]`

---

### Before you submit - checklist

- [ ] Every `[INSERT]` placeholder replaced
- [ ] Every commit SHA is real and appears in `git log`
- [ ] Every PR and issue number is real
- [ ] Screenshots attached and legible, with URL bars visible
- [ ] Challenges are genuine experiences, not invented ones
- [ ] The reflection is in your own voice
- [ ] Nothing here contradicts what the repository actually shows

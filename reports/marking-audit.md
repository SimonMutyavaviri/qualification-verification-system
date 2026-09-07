# MIM736 Marking Audit

A deliberately harsh self-assessment against the assignment's marking criteria,
carried out as if by the lecturer. Its purpose is to find what is missing while
there is still time to fix it — so it credits nothing that is not actually
present in the repository.

**Audited:** 7 September 2026
**Baseline commit:** `985df54`
**Live system:** https://qvs-mim736.fly.dev

---

## The single most important thing to understand

The baseline is complete, but **the collaboration evidence is not yet earned**.
Roughly **35 of the 100 marks** depend on things only the four students can
produce: real commits from four people, real pull requests, real code reviews, a
real merge conflict, and individual reports citing real SHAs.

An excellent baseline with no collaboration history is a mid-range submission.
The work remaining is not optional polish.

---

## 1. Git Repository — 20%

| Criterion | Present now | Marks at risk | Evidence |
| --- | --- | ---: | --- |
| Git version control | Yes — repository initialised, baseline committed, `main` and `develop` branches | — | `git log`, `git branch` |
| Branching strategy | Yes — documented and configured | — | `docs/git-workflow.md` |
| Pull requests | **No** — none exist yet | ~4 | — |
| Code reviews | **No** — none exist yet | ~4 | — |
| Issue tracking | **No** — templates ready, no issues raised | ~3 | `.github/ISSUE_TEMPLATE/` |
| Meaningful commit history | **Partial** — one honest baseline commit; no multi-author history | ~4 | `git log` |
| Merge conflict management | **No** — the exercise is designed but not performed | ~3 | `docs/collaboration-plan.md` |
| Documentation | Yes — 14 documents | — | `docs/` |
| CI/CD configuration | Yes — `ci.yml`, `cd.yml` | — | `.github/workflows/` |

**Estimated now: 8–10 / 20**
**Achievable after the collaboration phase: 18–19 / 20**

**Required action.** Push to GitHub, enable branch protection, and complete the
four task sets in `docs/collaboration-plan.md`. Every member needs several real
commits, at least one merged PR, and at least one review given and received.

> A single baseline commit is honest and correct — fabricating a history would be
> far worse. But it earns few marks on its own, and only real collaboration
> fixes that.

## 2. Working Software System — 25%

| Criterion | Assessment | Evidence |
| --- | --- | --- |
| Functional completeness | **Strong.** All four required capabilities implemented, plus revocation, reinstatement, administration and a bonus feature. 62 of 64 functional requirements automatically verified. | `docs/requirements-traceability.md` |
| Usability | **Good.** Responsive, role-aware navigation, unambiguous result states, inline validation errors, empty states. Not formally usability-tested. | `docs/user-manual.md`, MT-01 to MT-04 |
| Reliability | **Strong.** 264 tests, health checks, transactional integrity, graceful error handling, live deployment verified across 15 checks. | `reports/deployment-verification.md` |
| Maintainability | **Strong.** Strict layering, one query location, pure decision function, enforced style, documented decisions. | `docs/architecture.md` |

**Estimated: 22–24 / 25**

**Weakness.** No browser-level tests, so nothing automatically proves the
interface renders correctly. Capture MT-01 to MT-04 manually with screenshots.

## 3. Technical Report — 25%

| Criterion | Assessment |
| --- | --- |
| Problem analysis | **Strong** — analyses why the problem is hard, not just what it is |
| Requirements | **Strong** — 79 requirements, each written to be verifiable |
| System architecture | **Strong** — layering explained with the microservices alternative rejected on stated grounds |
| Design decisions | **Strong** — ten decisions, each with its trade-off and cost |
| DevOps workflow | **Strong** — pipeline design with the reasoning for each gate |
| Testing strategy | **Strong** — includes what is *not* tested |
| Verification strategy | **Strong** — the requirement → test → CI → merge-block chain |
| Critical evaluation | **Strong** — including the design we did not build and why |

**Estimated: 22–24 / 25**

**Required action.** Fill in the placeholders: team names and numbers, the
repository URL, the word count, and the evidence appendix. Confirm the word
count is inside 3,000–4,000 excluding tables, code and references. Adjust the
reference list to your department's citation style and **remove any source you
did not actually consult**.

## 4. Demonstration and Viva — 15%

| Criterion | Ready | Notes |
| --- | --- | --- |
| System functionality | Yes | Script covers all four verification results |
| Git workflow | **Depends on the collaboration phase** | The script assumes PRs and reviews exist |
| CI/CD pipeline | **Partly** | Needs a real pipeline run, including a failed one |
| Automated testing | Yes | |
| Verification process | Yes | |

**Estimated after the collaboration phase: 12–14 / 15**

**Required action.** Record the video. Rehearse to 12 minutes. Make sure all
four members speak. Capture a **failing** CI run before recording — the script
depends on it, and it is the most persuasive single piece of evidence.

## 5. Individual Contribution Report — 15%

| Criterion | Present |
| --- | --- |
| Contributions described | Templates ready, real content required |
| Git activity evidence | **Must be produced by each student** |
| Reflection on lessons learnt | Prompts ready, real content required |
| Challenges encountered | Prompts ready — **must be genuine** |

**Estimated now: 0 / 15** (nothing to assess yet)
**Achievable: 12–14 / 15**

**Required action.** Each member completes their template with real SHAs, PR
numbers and screenshots after doing their tasks.

> Invented challenges are transparent to a marker. "My test passed locally and
> failed in CI and it took me an hour to work out why" scores better than a
> polished fiction.

## Bonus — up to 10 marks

| Feature | Status |
| --- | --- |
| Agentic AI | **Partial** — the review assistant is rule-based by deliberate design (explainability). Argue this as a decision, not a shortfall. |
| Advanced security | **Yes** — 30 controls, each with a verifying test |
| Real-time monitoring | **Yes** — `/metrics` endpoint with live dashboard counters |
| Infrastructure as Code | **Yes** — `Dockerfile`, `docker-compose.yml`, `fly.toml`, workflow YAML |
| Blockchain verification | No — not attempted |

**Estimated bonus: 5–7 / 10**

---

## Overall estimate

| Component | Weight | Now | After collaboration |
| --- | ---: | ---: | ---: |
| Git repository | 20 | 9 | 18 |
| Working software | 25 | 23 | 24 |
| Technical report | 25 | 23 | 24 |
| Demonstration and viva | 15 | 6 | 13 |
| Individual contributions | 15 | 0 | 13 |
| **Subtotal** | **100** | **61** | **92** |
| Bonus | +10 | 6 | 6 |

**The 31-mark gap is entirely collaboration evidence.**

---

## Missing evidence

Ordered by marks at stake:

1. **All Git collaboration** — issues, branches, commits from four people, PRs,
   reviews, the merge conflict *(≈14 marks)*
2. **All four individual reports** *(15 marks)*
3. **The demonstration video** *(15 marks)*
4. **Pipeline screenshots**, including a failing run *(several marks across
   sections 1 and 4)*
5. **Application screenshots** for the report and manual test cases
6. **Team names and student numbers** throughout — currently `[INSERT]`
7. **The repository URL** — currently `[INSERT]`

## Weak areas

| Area | Weakness | Fix |
| --- | --- | --- |
| Browser testing | No automated evidence the UI renders | Execute MT-01 to MT-04 manually with screenshots |
| Rate limiting | Configuration-verified, not behaviour-verified | Student 4 Task 4.3, or MT-08/MT-09 manually |
| Health-check failure path | Not automatically tested | MT-07 manually, or Task 4.3 |
| CSP | `'unsafe-inline'` present | Compile Tailwind, or defend the decision in the viva |
| Account lockout | Absent | Student 1 Task 1.1 |
| Dependency scanning | Absent | Student 4 Task 4.1 |
| Staging environment | Absent | Student 4 Task 4.2 |
| Live database | SQLite, not PostgreSQL | Defend the decision, or switch (two commands) |

## Technical defects

**None outstanding.** Two were found and fixed during the build:

1. **Missing HSTS on the live deployment.** TLS terminates at Fly's edge, so
   `request.is_secure` was always False. Fixed with `ProxyFix` behind a
   `TRUST_PROXY_HEADERS` setting that is off by default; four regression tests
   added. *This is worth raising unprompted in the viva — it demonstrates
   verifying reality rather than trusting the pipeline.*
2. **`ACCESS_DENIED` audit entries were never committed.** They were added to
   the session, but the request aborted with 403 before any commit, so the
   session was discarded at teardown. Fixed by committing immediately.

## Documentation gaps

- [ ] Team names and student numbers (README, technical report, individual reports)
- [ ] Repository URL (README, technical report)
- [ ] Screenshots throughout — every `[INSERT SCREENSHOT]` marker
- [ ] Word count in the technical report
- [ ] `CODEOWNERS` still uses placeholder handles (`@student-one` etc.)
- [ ] Reference list trimmed to sources actually consulted

## Viva risks

| Question | Risk | Preparation |
| --- | --- | --- |
| "Show me your pull requests." | **High** — none exist yet | Complete the collaboration phase |
| "Which parts did *you* write?" | **High** if a member cannot answer for their own area | Everyone must know their own code |
| "Why SQLite in production?" | Medium | Prepared answer, viva Q36 |
| "Did you build the Docker image?" | Medium | Answer honestly — viva Q35 |
| "Explain `evaluate_status`." | Low | Everyone should be able to walk through it |
| "Is your AI feature really AI?" | Medium | Argue explainability as a design choice, viva Q47 |

## Required fixes, in priority order

**Before anything else**

1. Push to GitHub; configure branch protection per `docs/git-workflow.md` §6
2. Replace the placeholder handles in `.github/CODEOWNERS`
3. Add `FLY_API_TOKEN` to Actions secrets so CD can run
4. Raise the issues for all four task sets

**The collaboration phase — the largest block of marks**

5. Each member completes their tasks with real commits, PRs and reviews
6. Perform the merge conflict exercise (Students 1 and 3)
7. Deliberately break the build once, screenshot the red pipeline, then fix it

**Evidence**

8. Work through `docs/evidence-checklist.md` — 100+ items
9. Execute the manual test cases MT-01 to MT-12
10. Capture application screenshots from the **live** system

**Documents**

11. Complete the four individual reports with real evidence
12. Fill every placeholder in the technical report; check the word count
13. Build the slide deck from `reports/presentation.md`
14. Record the 10–15 minute demonstration

**Optional, if time allows**

15. Compile Tailwind and remove `'unsafe-inline'` from the CSP
16. Switch the live deployment to managed PostgreSQL

---

## One honest word of advice

The strongest thing about this submission is that it **does not claim more than
it can prove**. The security document lists seven gaps. The testing strategy
lists five limitations. The deployment record states plainly what was not done.
The technical report describes a better design that was not built.

Do not undo that in the viva by overstating. When asked about something the
system does not do, say so and explain why. An examiner who catches an
overstatement will discount everything else; one who sees accurate
self-assessment will trust the rest of the work.

# Demonstration Script

**Target length: 13 minutes** (assignment allows 10–15). Timings are cumulative.

## Before you record

- [ ] Live system open and signed out: https://qvs-mim736.fly.dev
- [ ] Second tab: the GitHub repository
- [ ] Third tab: GitHub Actions, with a successful CI run open
- [ ] Fourth tab: the Fly.io dashboard for `qvs-mim736`
- [ ] A terminal, in the project directory, font size increased
- [ ] Credentials to hand (from `deployment-credentials.local.md`)
- [ ] Browser zoom at 110–125% so text is readable in the recording
- [ ] Notifications silenced; unrelated tabs and bookmarks hidden
- [ ] Do a full dry run — the first attempt always overruns

> **Speak to what is on screen.** If a step fails during recording, say what
> happened and move on. A recovered mistake looks competent; a re-cut that hides
> it looks rehearsed.

---

## 0:00 — Introduction (45 seconds)

> "Good morning. We are `[NAMES]`, and this is our MIM736 practical assignment:
> a DevOps-enabled Qualification Verification System.
>
> The problem we set out to solve is this. When an employer receives a CV
> claiming a degree, verifying it means telephoning a registry and waiting days
> for an answer that is itself unverifiable. Meanwhile credential fraud is a
> real and well-documented market.
>
> Our system lets an institution register credentials, lets an authorised
> verifier check one in seconds, and keeps an audit trail that nobody — not even
> an administrator — can rewrite.
>
> It is live right now at qvs-mim736.fly.dev, and everything I show you is the
> deployed system, not a local copy."

*Show the live URL in the address bar.*

---

## 0:45 — Sign in and the dashboard (1 minute)

*Navigate to the live URL.*

> "This is the sign-in page. There is no self-registration — accounts are created
> by an administrator, because a verification system is only as trustworthy as
> its access control."

*Sign in as `admin`.*

> "This is the administrator dashboard. The counters at the top are live — they
> refresh from a metrics endpoint every fifteen seconds, so you will see them
> move later in this demonstration.
>
> Below we have recent verifications, recently registered credentials, and the
> most recent audit activity. The navigation is role-aware: a verifier signing
> in here sees fewer options, because the interface only offers what the role
> actually permits."

---

## 1:45 — Registering a qualification (1 minute 30)

*Go to **Register**.*

> "Let me register a new qualification, as a registry officer would.
>
> Note the credential ID field — I am leaving it blank. The system generates a
> unique reference automatically, and it deliberately avoids the letter O, zero,
> the letter I and the digit one, because those get confused when someone reads
> a reference off a printed certificate over the telephone."

*Fill in: title `MSc Cyber Security`, type `Degree`, holder `[a name]`,
institution `Midlands State University`, award date `[a past date]`.*

> "First, let me show you the validation. I will set the award date to next
> month."

*Set a future award date and submit.*

> "Rejected — an award date cannot be in the future. This rule lives in the
> service layer, not just the form, so a script posting directly to the endpoint
> is refused too."

*Correct the date and submit.*

> "Registered. And there is the generated credential ID — `[READ IT OUT]`. That
> is what the graduate would quote to an employer."

---

## 3:15 — Verification: the four results (3 minutes)

*Go to **Verify**.*

> "This is the core of the system. One reference in, one unambiguous result out.
> There are four possible results, and I will show you all of them."

**VALID** — *verify `QVS-2023-DEMO01`.*

> "VALID, in green. Registered, not revoked, not expired. It shows the holder,
> the qualification, the institution and the award date — exactly the facts
> already printed on the certificate the employer is holding. Nothing more,
> because verification should confirm what they have, not disclose new
> information about the person.
>
> Note the verification reference at the bottom. Every check produces a permanent
> receipt."

**EXPIRED** — *verify `QVS-2022-DEMO02`.*

> "EXPIRED, in amber, and the wording matters: 'validly issued but has passed its
> expiry date'. This was a genuine award. The employer's next step is to ask
> about renewal, not to suspect fraud — which is why we do not lump this in with
> 'invalid'."

**REVOKED** — *verify `QVS-2021-DEMO03`.*

> "REVOKED, in red. The institution has withdrawn this credential. This is a
> completely different signal from expired, and conflating them would be a
> serious design error.
>
> One design decision worth mentioning: if a credential is both revoked *and*
> expired, we report REVOKED. Revocation is the more serious fact, and the
> verifier needs to see it."

**INVALID** — *verify `QVS-2024-ZZZZZZ`.*

> "INVALID. No such credential. And notice what is *not* on the screen — no
> holder name, no partial match, no hint that a similar reference exists. An
> invalid result discloses nothing at all about our register."

*Now verify the credential you registered at 1:45.*

> "And the one I registered two minutes ago verifies as VALID. That is a complete
> write-then-read cycle against the live database."

---

## 6:15 — Revocation changing the answer (1 minute)

*Open the credential you registered, from the register.*

> "Here is the full record. This panel on the right is our bonus feature: a
> rule-based review assistant. It scores a record for signals worth a human
> look — an implausible date, an unusually short validity window, repeated
> failed lookups.
>
> We deliberately made it rules, not machine learning. An assistant that
> influences whether someone's degree is believed has to be able to explain
> itself, and every signal here points at a specific field and gives a reason."

*Select **Revoke**, enter a reason, confirm.*

> "Now let me revoke it — a reason is mandatory and is permanently recorded."

*Go to **Verify** and re-verify the same reference.*

> "And immediately, the same reference now returns REVOKED. That change
> propagated instantly, and it is attributed to me in the audit trail."

---

## 7:15 — Access control and the audit trail (1 minute 30)

*Sign out. Sign in as `verifier`.*

> "Now I am signed in as a verifier. Notice the navigation — no Register option,
> no Users, no Audit."

*Manually type `/admin/users` in the address bar.*

> "But the interface hiding a button is not access control. If I type the
> administrator URL directly — 403, access denied. And that denial was itself
> written to the audit trail.
>
> Authorisation is enforced twice: on the route and again in the service layer,
> so a future developer who adds a route and forgets the decorator still cannot
> bypass it."

*Sign out; sign back in as `admin`; go to **Audit**.*

> "Here is the complete audit trail: every sign-in, every failed sign-in, every
> registration, every revocation, every verification, and that denied access
> attempt from a moment ago. Each entry has the action, the actor, a timestamp,
> the entity and the source IP.
>
> These records cannot be edited or deleted through the application by anyone,
> including administrators. That is not a policy — it is enforced by database
> listeners that raise an exception, and two tests prove it."

---

## 8:45 — Git workflow (1 minute 15)

*Switch to the GitHub repository tab.*

> "Turning to how we built it."

*Show the branch list.*

> "We use GitHub Flow with a develop integration branch — main is always
> deployable, develop integrates, and short-lived feature branches carry
> individual changes."

*Show the issues list, then one issue.*

> "Every change starts with an issue carrying checkable acceptance criteria,
> written before any code."

*Show a merged pull request, then its Files-changed tab with review comments.*

> "Each pull request needs a passing pipeline and one approval. CODEOWNERS
> requests the right reviewer automatically. Here is a review where changes were
> requested `[POINT AT IT]`, and here are the follow-up commits that addressed
> them."

*Show the commit history.*

> "Commits follow Conventional Commits, and the body explains why rather than
> what."

*`[IF DONE]` Show the merge conflict evidence.*

> "We also handled a genuine merge conflict: two branches both added members to
> the same audit-action enumeration, for unrelated but equally valid reasons. We
> resolved it by keeping both — the resolution is never simply picking a side."

---

## 10:00 — CI/CD pipeline (1 minute 30)

*Switch to the Actions tab; open a successful CI run.*

> "Every push and every pull request runs this pipeline. Six jobs.
>
> Quality runs Ruff, Black and Bandit. Unit tests run the business-logic suite.
> Integration tests run against a real PostgreSQL 16 container — not SQLite —
> because SQLite silently allows things Postgres rejects, and we would rather
> find that here than in production.
>
> Coverage enforces an eighty-five percent gate. We are at ninety-two point
> seven.
>
> The Docker job builds the image and then actually *runs* it, polling the health
> endpoint. An image that builds but will not start is not a passing build.
>
> And the quality gate aggregates all of it into the single required status check
> our branch protection depends on."

*`[IMPORTANT]` Open a failed run.*

> "Here is a run that failed `[EXPLAIN WHAT FAILED]`, and here is the pull request
> blocked from merging because of it. That is the part that matters — the gate
> actually stops bad code, rather than just reporting on it."

*Show the CD workflow file, highlighting the conclusion check.*

> "Delivery is gated on that. This single line — `if workflow_run.conclusion ==
> 'success'` — is the most important line in our CD workflow, because the trigger
> also fires for failed runs. Without it, a broken build would deploy itself."

---

## 11:30 — Deployment (1 minute)

*Switch to the Fly.io dashboard.*

> "The system is deployed on Fly.io, in the Johannesburg region, running a
> multi-stage Docker image of about 78 megabytes. The application runs as an
> unprivileged user inside the container, and health checks are passing."

*In the terminal:*

```bash
curl -sS https://qvs-mim736.fly.dev/healthz
```

> "The health endpoint reports the application *and* the database. It returns 503,
> not 200, if the database is unreachable — a health check that only proves the
> web process is alive would report a healthy system that cannot verify a single
> credential."

```bash
curl -sSI https://qvs-mim736.fly.dev/login | grep -iE "strict-transport|x-frame|content-security"
```

> "And the security headers on the live site, including HSTS.
>
> That header is worth a sentence. It did *not* work on our first deployment.
> Fly terminates TLS at the edge, so Flask saw plain HTTP and never sent it. It
> passed every test, a clean lint and a clean security scan — and `curl` against
> the real deployment found it in seconds. We fixed it with proxy-aware
> middleware and added four regression tests."

---

## 12:30 — Closing (30 seconds)

> "To summarise: a working, deployed qualification verification system, with 264
> automated tests at ninety-two percent coverage, a CI pipeline with blocking
> quality gates, gated continuous delivery, and a live deployment we verified
> against reality rather than trusting the pipeline.
>
> The things we are least satisfied with are documented rather than hidden — no
> account lockout yet, no staging environment, and a CSP compromise we took to
> avoid a build step. Each is assigned as a task in our collaboration plan.
>
> Thank you. We are happy to take questions."

---

## Timing summary

| Segment | Start | Duration |
| --- | --- | --- |
| Introduction | 0:00 | 0:45 |
| Sign in and dashboard | 0:45 | 1:00 |
| Registration and validation | 1:45 | 1:30 |
| Verification — four results | 3:15 | 3:00 |
| Revocation and review assistant | 6:15 | 1:00 |
| Access control and audit | 7:15 | 1:30 |
| Git workflow | 8:45 | 1:15 |
| CI/CD | 10:00 | 1:30 |
| Deployment | 11:30 | 1:00 |
| Closing | 12:30 | 0:30 |
| **Total** | | **13:00** |

## If you are running short of time

Cut in this order — these lose the least:
1. The review assistant commentary at 6:15 (30s)
2. The commit-history detail at 8:45 (20s)
3. The registration validation failure at 1:45 (30s)

**Never cut:** the four verification results, the 403 access-control
demonstration, the audit trail, or the failed CI run. Those are the segments
carrying the most marks.

## Division of speaking

Suggested, so all four members are heard:

| Member | Segments |
| --- | --- |
| Student 1 | Introduction, sign-in, access control |
| Student 2 | Registration, validation, search |
| Student 3 | Verification, revocation, audit trail |
| Student 4 | Git workflow, CI/CD, deployment, closing |

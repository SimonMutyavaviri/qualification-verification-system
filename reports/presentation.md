# Presentation — Qualification Verification System

16 slides for a 10–15 minute presentation. Speaker notes are in italics beneath
each slide. Keep the slides sparse; the detail belongs in what you say.

---

## Slide 1 — Title

# Qualification Verification System
### A DevOps-Enabled Credential Verification Platform

**MIM736 Practical Assignment**

`[NAME]` · `[NAME]` · `[NAME]` · `[NAME]`

**Live:** qvs-mim736.fly.dev

*Speaker notes: Introduce the team and state up front that the system is live
and everything shown is the deployed system.*

---

## Slide 2 — The problem

**Verifying a qualification today**

- Telephone or email a registry → wait days
- The answer arrives by email — itself unverifiable
- No record either party can later inspect
- Credential fraud is a documented, active market

> A forged certificate is easy. Checking one is hard.

*Speaker notes: The asymmetry is the point — forgery is cheap, verification is
expensive, which is exactly why the fraud market exists.*

---

## Slide 3 — What makes it hard

1. **Trust must be transferable** — the verifier must be able to rely on, and
   later prove, the answer
2. **The answer changes over time** — "was awarded" is the wrong question;
   "can be relied on now" is the right one
3. **The audit trail is part of the product** — not logging, a requirement

*Speaker notes: Point 3 is what shaped the architecture. Say so.*

---

## Slide 4 — Objectives

| | |
| --- | --- |
| Register | Credentials, validated, with guaranteed-unique references |
| Retrieve | Search and filter the register |
| Verify | One reference in, one unambiguous result out |
| Audit | An append-only record nobody can rewrite |

Plus: role-based access, revocation, and full DevOps automation.

---

## Slide 5 — The solution

**Three roles**

- **Verifier** — check credentials, see their own history
- **Issuer** — register, edit, revoke
- **Administrator** — users, institutions, the audit trail

**Four verification results**

`VALID` · `INVALID` · `REVOKED` · `EXPIRED`

*Speaker notes: Four results, not two — this is a design decision worth
defending, and slide 7 explains why.*

---

## Slide 6 — Architecture

```
        Routes          thin controllers
           ↓
        Services        rules · authorisation · transactions · audit
           ↓
        Repositories    every query in the system
           ↓
        Models          entities · constraints · indexes
           ↓
        Database
```

**A layered monolith — deliberately not microservices.**

*Speaker notes: The audit entry must commit in the same transaction as the
change it describes. Distributed transactions would introduce exactly the
failure the system exists to prevent.*

---

## Slide 7 — The verification engine

```
credential ID → validate → look up → evaluate status
     → result → verification record → audit record
                    (one transaction)
```

**Revocation outranks expiry.**
**Failed attempts are recorded too.**
**INVALID discloses nothing.**

*Speaker notes: Three decisions, each defensible. Revoked-and-expired reports
REVOKED because it is the more serious fact. Failed attempts are the fraud
signal. INVALID showing nothing protects the register and the holder.*

---

## Slide 8 — Security

**30 implemented controls, each with a verifying test**

- PBKDF2 hashing · 12-char policy · enumeration resistance
- RBAC enforced at **two** layers — route *and* service
- CSRF · parameterised queries · security headers · HSTS
- Append-only audit trail — enforced, not documented
- Production refuses to start without real secrets

**7 documented gaps** — named, not hidden

*Speaker notes: Mention that gaps are documented. Examiners trust a report that
admits weaknesses far more than one that claims perfection.*

---

## Slide 9 — Git collaboration

```
Issue → Branch → Commits → PR → CI → Review → Merge
```

- GitHub Flow with a `develop` integration branch
- Branch protection: 1 approval + code owners + quality gate
- Conventional Commits
- A genuine merge conflict, resolved by keeping **both** changes

*Speaker notes: If you have done the conflict exercise, show it. The resolution
is never "pick a side".*

---

## Slide 10 — CI pipeline

| Job | Gate |
| --- | --- |
| `quality` | Ruff · Black · Bandit |
| `unit-tests` | 177 tests |
| `integration-tests` | 87 tests, **on PostgreSQL 16** |
| `coverage` | **85% minimum** |
| `docker-build` | Build **and run** the container |
| `quality-gate` | The single required check |

*Speaker notes: Integration on Postgres, not SQLite — SQLite silently allows
what Postgres rejects. And the Docker job runs the image, because one that
builds but won't start is not a passing build.*

---

## Slide 11 — Testing

# 264 tests · 92.69% coverage

- **Unit (177)** — validation, the decision table, business rules, audit
  immutability
- **Integration (87)** — full workflows, access control, security properties
- Negative cases carry equal weight
- Coverage is a **gate**, not a target

*Speaker notes: Not written to inflate the number — cli.py is excluded
deliberately. Testing the negative is what matters: proving a verifier gets 403.*

---

## Slide 12 — Continuous Delivery

```
main → CI passes → Docker build → Fly.io deploy
     → health check → smoke test → live
```

```yaml
if: workflow_run.conclusion == 'success'
```

**The most important line in the workflow.**

*Speaker notes: `workflow_run` fires for failed runs too. Without that
condition, a broken build deploys itself.*

---

## Slide 13 — Deployment

**Live: qvs-mim736.fly.dev**

- Multi-stage Docker image, 78 MB
- Runs as unprivileged uid 10001
- Fly.io · Johannesburg · TLS at the edge
- Health checks passing · encrypted volume with snapshots
- **15 of 15 live functional checks passed**

*Speaker notes: Checks included registering a new credential live and verifying
it — a complete write-then-read cycle, not just serving seeded data.*

---

## Slide 14 — What deployment taught us

**HSTS was not working on the live site.**

- Fly terminates TLS at the edge → Flask saw plain HTTP
- Passed 255 tests, clean lint, clean security scan
- Found by `curl` in seconds
- Fixed with `ProxyFix` + 4 regression tests

> A pipeline gives confidence about the artefact it built —
> not the environment it runs in.

*Speaker notes: This is the strongest slide in the deck. It shows genuine
engineering judgement rather than a feature tour.*

---

## Slide 15 — Critical evaluation

**Worked well**
Layering · the pure verification function · enforcing invariants in code ·
deploying early

**Would do differently**
Traceability matrix first · compile Tailwind (drop the CSP compromise) ·
test controls against the real topology sooner

**Known limitations**
No browser or load testing · no staging · no account lockout yet · SQLite in the
live deployment

*Speaker notes: Do not rush this slide. The critical evaluation carries real
marks, and the willingness to name weaknesses is what distinguishes it.*

---

## Slide 16 — Conclusion

**Delivered**

- A working, deployed verification system
- 264 tests · 92.69% coverage · blocking quality gates
- Gated continuous delivery to a live environment
- Verified against reality, not just the pipeline

**What mattered most:** the invariants — a verification cannot be recorded
without being audited, and audit history cannot be rewritten.

### Questions?

**qvs-mim736.fly.dev**

---

## Building the slide deck

These are the contents, not the design. When you build the deck:

- **One idea per slide.** If a slide needs a paragraph, it needs two slides.
- **Do not read the slides aloud.** They are the audience's anchor; your words
  are the content.
- **Use real screenshots**, not stock imagery — the live system, a green
  pipeline, the audit trail.
- **Keep code to at most three lines**, at a size readable from the back of a
  room. Slide 12's single line is the right amount.
- **Rehearse to 12 minutes** so questions and overrun fit inside 15.

### Suggested speaker allocation

| Member | Slides |
| --- | --- |
| Student 1 | 1–4 (problem, objectives) |
| Student 2 | 5–7 (solution, architecture, verification) |
| Student 3 | 8–9 (security, Git) |
| Student 4 | 10–14 (CI/CD, deployment, the defect) |
| All | 15–16 (evaluation, conclusion, questions) |

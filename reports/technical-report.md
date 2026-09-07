# A DevOps-Enabled Qualification Verification System

### Technical Report — MIM736 Practical Assignment

**Team members**

| Name | Student number | Area of responsibility |
| --- | --- | --- |
| `[INSERT NAME]` | `[INSERT NUMBER]` | Authentication, backend hardening, user management |
| `[INSERT NAME]` | `[INSERT NUMBER]` | Qualification management |
| `[INSERT NAME]` | `[INSERT NUMBER]` | Verification and audit |
| `[INSERT NAME]` | `[INSERT NUMBER]` | DevOps, QA, Docker and deployment |

**Repository:** `[INSERT REPOSITORY URL]`
**Live system:** https://qvs-mim736.fly.dev
**Date:** `[INSERT SUBMISSION DATE]`

---

## Table of contents

1. Introduction
2. Problem Analysis
3. Requirements Analysis
4. System Architecture
5. Design and Technology Decisions
6. Git and Collaboration Workflow
7. DevOps and CI/CD Implementation
8. Testing Strategy
9. Automated Requirement Verification
10. Security
11. Deployment
12. Critical Evaluation
13. Conclusion
14. References
15. Appendices

---

## 1. Introduction

This report describes the design, implementation, testing and deployment of a
Qualification Verification System (QVS): a web application that allows
authorised users to register academic and professional qualifications, verify
their authenticity, and maintain an auditable history of every verification
performed.

The system is implemented in Python using the Flask framework, is covered by 264
automated tests at 92.69% line coverage, is built and verified by a
six-job continuous integration pipeline, and is deployed and running at
https://qvs-mim736.fly.dev.

The report is organised around the decisions taken rather than a tour of the
features. Where a decision involved a trade-off, the alternative and the cost of
the choice are stated. Where something is incomplete or weaker than it should
be, it is named rather than omitted — section 12 is deliberately the most
critical part of this document.

---

## 2. Problem Analysis

### 2.1 The problem

Employers, admitting institutions and professional bodies regularly need to
establish three things about a claimed qualification: that it was actually
awarded, that it was awarded by the institution named on the certificate, and
that it has not since been withdrawn.

The conventional process is manual. A prospective employer telephones or emails
a university registry, waits days or weeks for a response, and receives an
answer that is itself unverifiable — an email can be spoofed as easily as a
certificate. The process is slow, expensive in staff time, inconsistent between
institutions, and leaves no record that anyone can later inspect.

The consequences are not hypothetical. Credential fraud is well documented:
fabricated degrees, altered classifications, and certificates from institutions
that never existed. The market in counterfeit qualifications exists precisely
because verification is hard enough that many employers skip it.

### 2.2 What makes it hard

Three properties make this more than a database lookup.

**Trust must be transferable.** A verification result is only useful if a third
party can rely on it. This means the answer must come from an authority the
verifier trusts, and the fact that the check was performed must itself be
recordable.

**The answer changes over time.** A qualification that was valid last year may
have expired, or may have been revoked following an academic misconduct finding.
A system that answers "this was awarded" is answering the wrong question. The
question is "can this be relied upon *now*".

**The audit trail is part of the product.** If a verification is later disputed
— an employer says they checked, a candidate says the result was wrong — there
must be a record neither party can alter. This makes the audit trail a primary
requirement rather than a logging afterthought, and it shapes the architecture.

### 2.3 Stakeholders

| Stakeholder | What they need |
| --- | --- |
| Awarding institution | Its credentials verifiable; forgeries detectable; the ability to withdraw a credential and have that take effect immediately |
| Registry officer (issuer) | To register credentials quickly and accurately, and to correct or withdraw them |
| Verifier (employer, admissions) | A fast, unambiguous, trustworthy answer, and proof they asked |
| Administrator | Control over who has access, and oversight of what has happened |
| Credential holder | Their genuine award confirmed promptly, without disclosing more about them than the certificate already states |

The last row deserves emphasis. A verification system is a system that discloses
information about people. The holder is a stakeholder with an interest that can
conflict with the verifier's, and section 10.5 describes how that conflict was
resolved.

### 2.4 Scope

**In scope:** credential registration with validation and duplicate prevention;
search and retrieval; verification returning a four-state result; revocation and
reinstatement; an append-only audit trail; role-based access control; and a
rule-based assistant that flags records warranting human review.

**Out of scope, deliberately:** bulk import of legacy records; a self-service
portal for holders; storage of scanned certificate images; and cryptographic
signing of credentials. Bulk import is assigned as a post-baseline task
(`docs/collaboration-plan.md`). Cryptographic signing — issuing each credential
as a digitally signed object verifiable without contacting the register — is a
genuinely better design for the trust problem, and section 12.4 explains why it
was not attempted here.

---

## 3. Requirements Analysis

### 3.1 Method

Requirements were derived from the assignment specification and from the problem
analysis above, then written in a form that could be **objectively verified**.
This was a deliberate constraint: a requirement that cannot be checked by a test
is a statement of intent, not a requirement.

Each was given an identifier (`FR-VER-05`, `NFR-SEC-03`) used consistently
across `docs/requirements.md`, the traceability matrix, the test-case document
and the test suite itself. This is what makes section 9 possible.

### 3.2 Functional requirements

Sixty-four functional requirements were specified across seven areas:
authentication and access control (9), qualification management (13),
verification (12), audit (9), validation (10), administration (5), operations
(4), plus two for the bonus feature. They are listed in full in
`docs/requirements.md`; the ones that shaped the design most are these:

- **FR-VER-01** — verification returns exactly one of `VALID`, `INVALID`,
  `REVOKED`, `EXPIRED`. Four states rather than a boolean, because "not valid"
  conflates three situations that call for entirely different responses from the
  verifier. A revoked credential is a fraud signal; an expired one usually is
  not.
- **FR-VER-05** — revocation takes precedence over expiry. Discussed in 5.3.
- **FR-VER-07** — an `INVALID` result discloses nothing. Discussed in 10.5.
- **FR-VER-08** — *every* verification attempt is recorded, including failures.
  Discussed in 5.4.
- **FR-AUD-07/08** — audit entries cannot be modified or deleted. Discussed in
  5.5.
- **FR-QUAL-10** — credential ID, award date, institution and issuer are
  immutable after registration. Discussed in 5.6.

### 3.3 Non-functional requirements

Fifteen were specified, covering security (8), quality (3), usability (2),
maintainability (1) and operations (2). Notably, three of the quality
requirements are enforced mechanically rather than by review:

| ID | Requirement | Enforcement |
| --- | --- | --- |
| NFR-QUA-01 | Coverage ≥ 85% | `--cov-fail-under=85` fails the build |
| NFR-QUA-02 | Consistent style | `black --check` and `ruff check` fail the build |
| NFR-QUA-03 | No medium/high security findings | `bandit -ll` fails the build |

A quality requirement that depends on someone remembering to check it will
eventually be violated. Making it a build failure removes the dependency on
diligence.

### 3.4 Roles

Three roles were specified — Verifier, Qualification Issuer, Administrator —
with Administrator modelled as a **superset** of the others rather than a
parallel role. This was a deliberate simplification: it means privilege is
decided in exactly one place (`User.has_role`), and there is no possibility of
an administrator being unable to perform an action an issuer can. The cost is
that the model cannot express "an administrator who may manage users but not
issue credentials". For an organisation of this size that separation would be
theatre rather than security.

---

## 4. System Architecture

### 4.1 Style

The system is a **layered monolith** using the Flask application-factory
pattern. Four layers, each permitted to call only the one beneath it:

```
Routes  (app/routes/)         thin controllers: parse, call one service, render
   ↓
Services (app/services/)      business rules, authorisation, transactions, audit
   ↓
Repositories (app/repositories/)  every SQLAlchemy query in the system
   ↓
Models (app/models/)          entities, constraints, indexes
   ↓
Database                      PostgreSQL (supported) / SQLite (dev, tests, live)
```

Cross-cutting concerns sit beside the stack: `app/utils/validators.py` (pure
validation functions), `app/utils/security.py` (authorisation decorators and
response headers), `app/utils/audit_guard.py` (append-only enforcement) and
`app/errors.py` (central error handling).

### 4.2 Why a monolith

Microservices were considered and rejected. The domain is small and tightly
coupled in a specific way that matters: a verification is meaningless without
the register, and the audit entry for a verification must be transactionally
consistent with the verification record itself. Splitting these across services
would replace a single database transaction with a distributed one — introducing
the possibility of a verification that was performed but not audited, which is
precisely the failure the system exists to prevent.

The layering delivers the separation of concerns that maintainability requires
without paying that cost. If the register later needed to scale independently of
verification, the repository layer is the seam at which to split it.

### 4.3 Request lifecycle

A verification request, end to end:

1. `POST /verify/` reaches `verification_routes.verify`.
2. `@login_required` and `@roles_required(...)` establish identity and
   permission. A denial writes an `access.denied` audit entry and aborts 403.
3. `@limiter.limit` applies the endpoint's rate limit.
4. `VerificationForm` validates CSRF and field presence.
5. `VerificationService.verify` normalises the reference, looks up the
   credential, evaluates status, and creates **both** a `Verification` row and
   an `AuditLog` row, committing them in **one transaction**.
6. The route renders the outcome; `apply_security_headers` decorates the
   response.

Step 5 is the architecturally significant one. The single commit means a
verification cannot be recorded without being audited, or audited without being
recorded. This is enforced by structure rather than by discipline.

---

## 5. Design and Technology Decisions

### 5.1 Flask rather than Django

Django offers authentication, an admin interface and an ORM out of the box, and
would have reduced the amount of code written. It was rejected because the
majority of what it provides would not be used — the domain needs a register, a
verification check and an audit trail, not a content-management system — and
because Django's conventions would have obscured the layering.

The relevant consideration was not development speed but **comprehensibility**:
this codebase must be understood and extended by four contributors, and then
explained in a viva. Flask's explicitness makes the flow from route to service
to repository visible in the code rather than implied by framework convention.

The cost is real: authentication, user administration and the forms were built
rather than inherited, which is several hundred lines that Django would have
supplied. It is a cost we would pay again for a system of this size, and would
not for a substantially larger one.

### 5.2 The verification decision is a pure function

`VerificationService.evaluate_status(qualification, on_date)` takes a model (or
`None`) and returns a result. It touches no database, no request context and no
clock it was not given.

This makes the entire decision table directly unit testable — missing, revoked,
expired, revoked-and-expired, expiring-today — without constructing an HTTP
request. The impure work (lookup, recording, auditing) is a thin shell around
it. Seven unit tests cover the function exhaustively; testing the same cases
through the web layer would have required four times the setup and told us less.

### 5.3 Revocation outranks expiry

A credential that is both revoked and past its expiry date reports `REVOKED`.

The ordering matters. Expiry is an administrative fact — the credential was
genuine and lapsed. Revocation is a statement that the credential should never
be relied upon, often following misconduct. Reporting `EXPIRED` for a revoked
credential would understate the situation to exactly the person who most needs
to know. The rule is one branch of an ordered `if` chain, and one test
(`test_revocation_outranks_expiry`) pins it.

### 5.4 Failed verifications are recorded

`Verification.qualification_id` is nullable on purpose, so that an attempt
against an unregistered reference still produces a row.

The reasoning: "someone attempted to verify a credential that does not exist,
from this address, at this time" is exactly the signal a fraud investigation
needs. A system that records only successful lookups is blind to the pattern
that matters most — repeated attempts with near-miss references. The attempted
reference is stored as text alongside the nullable foreign key, so it survives
even when it matched nothing.

Malformed references are treated as `INVALID` rather than as errors, for the
same reason: the attempt is real and auditable, and returning a distinct error
for a badly formed reference would tell an attacker which references are even
well-formed.

### 5.5 The audit trail is enforced append-only

`app/utils/audit_guard.py` registers SQLAlchemy `before_update` and
`before_delete` listeners on `AuditLog` that raise `ImmutableRecordError`.

Documenting the intention would not have prevented a future contributor from
writing `entry.detail = ...`. The listener does, and it fails loudly at commit
time rather than silently rewriting history. Four tests assert it, including one
that confirms the entry survives a blocked deletion attempt.

The scope of the guarantee is stated honestly in `docs/database-design.md`: this
prevents modification *through the application*. A database superuser can still
alter rows. Closing that would require database-level permissions or write-once
storage, and is recorded as a limitation rather than claimed as solved.

A related decision: `AuditLog.actor_label` denormalises the username alongside
the nullable `actor_id` foreign key. This is deliberate denormalisation — if an
account is later removed, the trail must still record who performed the action.
Normalising it would let account deletion erase history.

### 5.6 Immutable credential fields

Credential ID, award date, institution and issuer cannot be edited after
registration; `QualificationService.update` accepts no parameters for them.

A third party may already have verified the credential and recorded the result.
Silently changing what that reference means would make their receipt untrue —
and the receipt is the artefact the system asks people to trust. If those
details are wrong, the correct action is to revoke the record and register a
corrected one, which leaves both facts in the audit trail.

### 5.7 Credential IDs avoid ambiguous characters

Generated IDs use the alphabet `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` — no `O`, `0`,
`I` or `1`.

Credential references are read off printed certificates and dictated over the
telephone, where those characters are routinely confused. Excluding them
eliminates a class of `INVALID` results that are transcription errors rather
than verification failures — and an `INVALID` result carries an implicit
accusation, so reducing false ones has a human cost as well as an operational
one. A test asserts the exclusion.

### 5.8 Validation is applied twice, deliberately

WTForms validates at the boundary so users get inline field errors; the service
layer then re-applies the authoritative rules from `app/utils/validators.py`.

The duplication is intentional. The form gives good user experience; the service
check is what a request that bypasses the form — a script, a future API, a new
route written by a contributor who forgot — still cannot get past. The unit
tests call the services directly, precisely to prove the rules hold without the
form.

The same reasoning applies to authorisation: `@roles_required` on the route and
`_assert_can_issue` in the service. The decorator is what a reader sees; the
service check is what a future route cannot forget.

### 5.9 Expiry is derived, not stored

`Qualification.status` holds the administrative state (`active` / `revoked`);
whether a credential has expired is computed at read time by
`effective_status`.

A stored expiry flag would be wrong the day after it was written unless a
scheduled job kept it current — and a system whose correctness depends on a cron
job running is a system that will one day be quietly wrong. Computing it from
the date is always correct, at the cost of a trivial comparison per read.

### 5.10 The bonus feature is rule-based, not model-based

The Qualification Review Assistant (`app/services/risk_service.py`) scores a
record against six explicit rules — implausible award date, very short validity
window, missing holder contact, unusual credential volume for one holder,
repeated failed lookups, and revocation — producing a score, a level and a
plain-English reason for each triggered signal.

A machine-learning model was considered and rejected on principle. An assistant
that influences whether a person's qualification is trusted must be
**explainable and reproducible**. A reviewer must be able to see why a record
was flagged, and the same record must produce the same assessment tomorrow.
Every rule here points at a specific field and states its reason. The thresholds
are declared as data (`THRESHOLDS`) so they can be reviewed without reading the
code.

The honest limitation: it cannot detect a pattern nobody has written a rule for.
That is a real weakness relative to an anomaly-detection model, and it is the
price of explainability in a context where a false accusation is costly.

---

## 6. Git and Collaboration Workflow

### 6.1 Branching model

A trimmed **GitHub Flow with a `develop` integration branch**: `main` is always
deployable, `develop` integrates completed work, and short-lived
`feature/`, `fix/`, `docs/`, `chore/` and `test/` branches carry individual
changes.

Full Git Flow was rejected: release and hotfix branches solve problems — parallel
supported versions, emergency patches to production while a release is in
progress — that a single-deployment student project does not have. Trunk-based
development with no integration branch was also rejected, because it depends on
feature flags and a maturity of test coverage the team is still building.

### 6.2 The contribution cycle

```
Issue → Branch → Commits → Push → Pull Request → CI → Review → Merge
```

Every change starts with an issue carrying objectively checkable acceptance
criteria, written before any code. Pull requests use a template requiring the
linked issue, a description of testing performed, and a quality checklist.

Commits follow Conventional Commits (`feat(auth): lock accounts after five
failed sign-ins`), with the body explaining *why*. The convention was adopted
not for tooling but because the message format prompts the author to state
intent — and a reviewer reading a well-described commit series understands a
change far faster than one reading a single squashed diff.

### 6.3 Code review

Every pull request requires one approval. `CODEOWNERS` maps each area of the
codebase to its owner so the right reviewer is requested automatically.
Reviewers work through the checklist in `docs/git-workflow.md` §4: correctness,
test coverage of negative cases, respect for the layering, authorisation checks,
audit coverage, error handling, and absence of secrets.

Review pairing is fixed and reciprocal (1↔3, 2↔4) so that every member both
gives and receives review, which the individual-contribution mark requires.

### 6.4 Branch protection

`main` and `develop` require a pull request, one approval, review from code
owners, conversation resolution, an up-to-date branch, and the **Quality gate**
status check. `Quality gate` is a single CI job depending on all the others, so
one required check covers the entire pipeline and adding a job later does not
require editing the protection rules.

### 6.5 Merge conflict management

A genuine conflict exercise is planned rather than manufactured. Two independent
tasks in the collaboration plan both need to add members to the `AuditAction`
enumeration — Student 1 adds `USER_LOCKED`/`USER_UNLOCKED` for account lockout,
Student 3 adds `AUDIT_EXPORTED` for audit export. Branching from the same commit
and appending to the same list produces a real conflict from two legitimate,
unrelated changes.

The resolution is instructive precisely because it is **not** "take one side":
both sets of members are needed, and discarding either would silently remove a
colleague's feature. The full procedure, the verification steps (marker grep,
full test run, lint, CI) and the documentation requirements are in
`docs/collaboration-plan.md`.

`[INSERT: evidence of the conflict, resolution and merged PR — see docs/evidence-checklist.md §B]`

---

## 7. DevOps and CI/CD Implementation

### 7.1 Continuous Integration

`.github/workflows/ci.yml` runs on every push to `main`/`develop` and every pull
request, in six jobs:

| Job | Purpose | Fails when |
| --- | --- | --- |
| `quality` | Ruff, Black, Bandit | Lint error, unformatted file, or medium/high security finding |
| `unit-tests` | Unit suite | Any unit test fails |
| `integration-tests` | Integration suite **on PostgreSQL 16** | Any integration test fails |
| `coverage` | Full suite with the gate | Coverage below 85% |
| `docker-build` | Build the image, run it, poll `/healthz` | Image fails to build **or fails to start** |
| `quality-gate` | Aggregate | Any of the above failed |

Two choices here are worth defending.

**The integration suite runs on PostgreSQL, not SQLite.** The unit tests use
in-memory SQLite for speed, but SQLite silently permits things PostgreSQL
rejects — constraint semantics differ. A suite that only ever saw SQLite could
pass on code that breaks in production. Running the integration tests against
the production engine catches that in CI.

**The Docker job runs the container, not just builds it.** An image that builds
but will not start is not a passing build. The job starts the container, polls
`/healthz` for up to 60 seconds, and fetches `/login` to confirm the application
serves. This caught nothing during development — but it is the check that would
catch a broken entrypoint or a missing runtime dependency.

### 7.2 Continuous Delivery

`.github/workflows/cd.yml` is triggered by `workflow_run` on CI completion for
`main`, and gated by:

```yaml
if: github.event.workflow_run.conclusion == 'success'
```

`workflow_run` fires for *failed* runs too. Without that condition, a failing CI
run would trigger a deployment — it is the single most important line in the
workflow. The pipeline then deploys with `--strategy rolling`, polls the live
`/healthz` for up to 150 seconds, smoke-tests the sign-in page, and writes a
deployment record to the job summary.

Rollback is deliberately **not** automated. A `rollback-on-failure` job lists
recent releases and prints the exact `flyctl releases rollback` command, but
executing it is a human decision — an automatic rollback can mask a data-layer
fault that the next deployment will simply hit again.

### 7.3 Observability

Structured logs to stdout (captured by Fly), a `/healthz` endpoint returning
**503 rather than 200** when the database is unreachable, an authenticated
`/metrics` endpoint, and dashboard counters that refresh from it every fifteen
seconds.

The 503 matters: a health check that only proves the web process is alive would
report a healthy service that cannot verify a single credential.

---

## 8. Testing Strategy

### 8.1 Shape and scale

**264 tests, 92.69% line coverage** — 177 unit and 87 integration.

More unit than integration tests, because the business rules are where the risk
lies. The verification decision table has more meaningful cases than the route
that calls it. The integration tests then prove those units are correctly wired
together.

### 8.2 Principles

**One behaviour per test.** `test_revocation_outranks_expiry` fails for exactly
one reason, so a failure names the defect rather than starting an investigation.

**Negative cases carry equal weight.** For every "registers a valid
qualification" there is a duplicate, a future award date, an expiry before the
award, a blank title, an unknown institution, an inactive institution and an
unauthorised actor.

**Tests state intent.** `test_invalid_result_discloses_no_qualification` records
a privacy requirement. If someone later "fixes" the code by returning the
qualification anyway, the failure explains why that is wrong — the test is
documentation that cannot go stale.

**Fixtures build the world; tests exercise it.** Every test gets a fresh
in-memory database, so no test depends on another's state or on ordering.

### 8.3 Security testing

`tests/integration/test_security.py` (marked `security`) asserts the controls
claimed in `docs/security.md`: authentication requirements across ten routes,
role-based access control including direct POSTs that bypass the interface,
response headers, information disclosure, SQL injection, CSRF, open redirects,
proxy awareness and production configuration guards.

Testing the *negative* is the part that matters. A test proving an administrator
can reach the audit trail says nothing about whether a verifier can too.

### 8.4 Coverage as a gate, not a target

`--cov-fail-under=85` makes coverage a build failure rather than a metric in a
report. The suite was not written to inflate it: `app/cli.py` is excluded
because it is exercised by running `flask seed-demo`, and writing tests purely to
cover it would be the coverage-chasing this strategy avoids. The uncovered ~7%
is chiefly defensive branches — the `IntegrityError` fallback for a registration
race, the database-unreachable path in `/healthz` — that require a genuinely
broken process to reach.

---

## 9. Automated Requirement Verification

The assignment asks how requirements are automatically verified. The answer is a
chain, and every link is mechanical:

```
Requirement (FR-VER-05)
      ↓  named in
Test (test_revocation_outranks_expiry)
      ↓  executed by
CI job (unit-tests)
      ↓  aggregated by
Quality gate (required status check)
      ↓  enforced by
Branch protection — the merge is blocked
```

`docs/requirements-traceability.md` maps all 79 requirements to their
implementation, their test, and the CI job that runs it. The summary:

| Category | Total | Automated | Manual | Not done |
| --- | ---: | ---: | ---: | ---: |
| Functional | 64 | 62 | 2 | 0 |
| Non-functional | 15 | 11 | 4 | 0 |
| **Total** | **79** | **73** | **6** | **0** |

**Every "Must" requirement is verified by an automated test that runs in CI.**

The six manual items are named rather than glossed: the live dashboard counters,
the `/healthz` database-outage branch, rate-limiting behaviour, and three
usability/accessibility properties. Each is listed as manually verified in the
traceability matrix, with a manual test case in `docs/test-cases.md` (MT-01 to
MT-12). Closing three of them is assigned as Student 4's Task 4.3.

Beyond tests, requirements are enforced at four levels of defence:

1. **Form validation** — immediate user feedback
2. **Service-layer validation** — cannot be bypassed by skipping the form
3. **Database constraints** — unique, check and foreign-key constraints as the
   final backstop
4. **CI quality gates** — blocking, not advisory

---

## 10. Security

`docs/security.md` records thirty implemented controls with the test that
verifies each. This section covers the ones that involved a judgement.

### 10.1 Authentication

Passwords are stored as PBKDF2-SHA256 hashes with per-password salts (Werkzeug).
Sign-in accepts a username or an email address through one code path, so timing
and messaging do not differ.

A failed sign-in returns the single message *"Invalid username or password."*
whether the account exists or not, and follows the same code path. The failure
counter is incremented only for a real account, but this is not observable from
the response. Account enumeration is a real attack — knowing which addresses
have accounts is the first step in a credential-stuffing campaign.

### 10.2 Authorisation in two layers

`@roles_required` at the route and an explicit assertion in the service. The
duplication is defence in depth against the specific failure mode of a future
contributor adding a route and forgetting the decorator.

### 10.3 The CSP compromise, stated plainly

The Content Security Policy includes `'unsafe-inline'` in `script-src`, because
Tailwind's play CDN generates styles at runtime. This is a **genuine weakening**
of XSS protection, accepted to avoid a build toolchain.

It is honest to state the consequence: the CSP does not protect against injected
inline script. The mitigation is that Jinja2 autoescapes all output by default
and the application renders no user-supplied HTML. Removing the compromise means
compiling Tailwind at build time, and is recorded as a task rather than quietly
left as a claimed control.

### 10.4 Secrets

No secret is committed. `ProductionConfig` **raises at start-up** if `SECRET_KEY`
is missing, empty or still the development placeholder, and if `DATABASE_URL` is
missing. Five tests assert this. A misconfigured production deployment fails
loudly rather than running on a default signing key — the failure mode where a
system appears to work while being trivially compromisable.

Demo passwords are generated randomly at seed time and printed once;
`flask create-admin` prompts rather than accepting a command-line argument, so
passwords never enter shell history.

### 10.5 Minimal disclosure

An `INVALID` result returns nothing at all — not even a hint that a similar
reference exists. `VALID`, `EXPIRED` and `REVOKED` return only holder name,
title, institution and award date: the facts already printed on the certificate
the verifier is holding. Holder email and issuing officer are never released to
a verifier.

This is where the holder's interest and the verifier's conflict, and the
resolution is that verification confirms what the verifier already has rather
than disclosing anything new.

### 10.6 A defect the deployment revealed

The first live check showed **no HSTS header**, despite the code setting it for
secure requests. Fly.io terminates TLS at its edge and forwards over plain HTTP,
so Flask's `request.is_secure` was `False` for every request. The same fault
meant audit entries would have recorded the proxy's address rather than the
client's.

Fixed with `ProxyFix`, enabled by a `TRUST_PROXY_HEADERS` setting that is **off
by default** — trusting `X-Forwarded-*` without a trusted proxy in front lets any
client forge its own scheme and address. Four regression tests were added.

It is worth stating what this means: the defect passed 255 tests, a clean lint,
a clean security scan and a local smoke test. Only a real deployment, checked
against reality, revealed it. That is an argument for deploying early and for
verifying the deployed artefact rather than trusting the pipeline.

### 10.7 Known gaps

Named rather than omitted (`docs/security.md` §7): no account lockout (rate
limiting only); in-memory rate limiting, so limits are per-process; the CSP
compromise above; no multi-factor authentication; application-level rather than
database-level audit immutability; no dependency-vulnerability scanning; no
password reset flow.

The first and sixth are assigned as post-baseline tasks. The others are
documented accepted risks with the reasoning recorded.

---

## 11. Deployment

### 11.1 Container

A multi-stage Docker build: a builder stage compiles wheels, and the runtime
stage installs from them, so no compiler toolchain ships in the final 78 MB
image. The application runs as an unprivileged user (uid 10001), and a
`HEALTHCHECK` polls `/healthz`.

The entrypoint starts as root only long enough to take ownership of the mounted
volume — a Fly volume attaches root-owned, so the unprivileged user could not
otherwise write the database — then drops privileges with `gosu` before exec'ing
gunicorn. The window in which the process is privileged contains one `chown` and
nothing else.

### 11.2 Platform and current state

Deployed on **Fly.io** at https://qvs-mim736.fly.dev — `shared-cpu-1x`, 512 MB,
region `jnb` (Johannesburg, closest to the users), TLS terminated at the edge
with HTTP redirected to HTTPS, and a 1 GB encrypted volume with scheduled
snapshots.

Fifteen functional checks were executed against the live system and all passed,
including registering a new credential and verifying it — proving a complete
write-then-read cycle against the persistent volume, not merely that seeded data
is served. Full record: `reports/deployment-verification.md`.

### 11.3 Two honest qualifications

**The image was not built locally.** Docker Desktop requires WSL2, and WSL2
reported that hardware virtualisation is disabled in the machine's firmware.
`flyctl deploy --remote-only` builds on Fly's builders, so the deployment is
genuine and the `Dockerfile` is genuinely exercised — but local `docker build`
evidence must come from the CI job or another machine.

**The live database is SQLite on a volume, not PostgreSQL.** The architecture
specifies PostgreSQL, the application supports it unchanged, and CI runs the
integration suite against PostgreSQL 16 — but the deployed instance uses SQLite
to avoid provisioning a billed database cluster for a demonstration. The
trade-off is real: a volume attaches to one machine, so the app cannot scale
horizontally in this configuration. The switch is two commands
(`docs/flyio-deployment.md` §11).

### 11.4 An operational problem encountered

The first deployment failed to allocate public IP addresses
(`org_slug is only supported with private_v6 type` — a Fly API error). The
machine launched correctly; the addresses were allocated manually with
`flyctl ips allocate-v4/-v6`. Documented so the next person does not lose time to
it.

---

## 12. Critical Evaluation

### 12.1 What worked

**Layering paid for itself.** Because every query lives in a repository and
every rule in a service, adding the review assistant touched one new service file
and one template. Nothing had to be untangled.

**The pure verification function was the best single decision.** Making
`evaluate_status` free of database and request context turned the most important
logic in the system into something testable in microseconds and exhaustively
coverable. The seven tests over it give more confidence than any number of
end-to-end checks.

**Enforcing invariants in code rather than documenting them.** The audit
immutability guard is the clearest case: a comment saying "do not modify audit
entries" would have been ignored eventually; a listener that raises cannot be.

**Deploying before the report was written.** It found the HSTS defect that
nothing else did.

### 12.2 What we would do differently

**Discover the proxy problem earlier.** HSTS was written, tested and documented
as a control, and it did not work in the only environment where it matters. The
test asserted the code path, not the deployed behaviour. The lesson is that a
test of a security control that never runs against the real deployment topology
is weaker evidence than it appears.

**Write the traceability matrix first.** It was written after the tests and
revealed two requirements (`FR-OPS-02`, `FR-OPS-04`) with no automated cover.
Written first, it would have driven those tests rather than auditing their
absence.

**Reconsider the Tailwind CDN.** It saved a build step and cost a real CSP
weakening. Given the system's security posture, that was probably the wrong
trade — the build step is half an hour of work.

**Test rate limiting.** Disabling it in the suite for determinism was
reasonable, but it means the control is configuration-verified rather than
behaviour-verified.

### 12.3 Honest limitations

- No browser-level tests; a CSS regression hiding the result banner would not
  fail the suite
- No load or performance testing whatsoever
- Accessibility checked by inspection, not audited
- Single region, single machine — no redundancy
- No staging environment; `main` deploys straight to production
- Schema managed by `create_all()`; the first real migration is still ahead
- The review assistant cannot detect patterns nobody wrote a rule for

### 12.4 The design we did not build

The strongest solution to the trust problem is not a central register at all. It
is **cryptographically signed credentials**: each qualification issued as a
signed object that a verifier can validate offline against the institution's
public key, with the register consulted only for revocation.

That design removes the register as a single point of trust and failure, works
when the system is offline, and does not require the verifier to have an
account. It is how modern verifiable-credential standards (W3C Verifiable
Credentials) approach the problem.

It was not attempted here because key management — issuance, rotation,
revocation, and the institutional processes around them — is a substantially
larger problem than the application itself, and doing it badly would be worse
than not doing it. But it is the honest answer to "how would you build this
properly", and the current architecture does not preclude it: signing would
attach to the qualification model, and the existing verification workflow would
become the revocation check.

### 12.5 Against the assignment criteria

| Criterion | Assessment |
| --- | --- |
| Git repository | Branching model, protection rules, templates, CODEOWNERS and workflows are in place. The collaboration history is the part the team must now produce. |
| Working software | Complete, deployed, and verified live across 15 functional checks. |
| Technical report | This document, argued from decisions rather than features. |
| Demonstration | Script and viva preparation in `reports/`. |
| Individual contributions | Four genuine task sets defined; templates ready for real evidence. |

---

## 13. Conclusion

This project delivered a working, tested, deployed qualification verification
system, together with the DevOps machinery that keeps it correct: 264 automated
tests at 92.69% coverage, a six-job CI pipeline with blocking quality gates, a
gated delivery pipeline, and a live deployment verified against reality.

The technical work that mattered most was not the feature set — a register and a
lookup are not difficult — but the invariants: that a verification cannot be
recorded without being audited, that audit history cannot be rewritten, that a
credential's meaning cannot change after someone has relied on it, and that a
failed verification is as carefully recorded as a successful one. Each of these
is enforced by structure and pinned by a test, rather than described in a
document and hoped for.

The most instructive moment was the HSTS defect. It survived a full test suite, a
clean lint, a clean security scan and a local smoke test, and was found in
minutes by checking the deployed system with `curl`. The general lesson is that
a pipeline gives confidence about the artefact it built, not about the
environment it runs in, and that the gap between those two is where production
defects live.

The system is not finished, and section 12 says where it falls short rather than
claiming otherwise. The four post-baseline task sets in
`docs/collaboration-plan.md` address the most significant gaps — account
lockout, dependency scanning, a staging environment, and the untested paths —
and each is a real improvement to a working system rather than an exercise.

---

## 14. References

Anthropic (2026) *Flask-Limiter documentation*. Available at: https://flask-limiter.readthedocs.io/

Beck, K. (2003) *Test-Driven Development: By Example*. Boston: Addison-Wesley.

Chacon, S. and Straub, B. (2014) *Pro Git*. 2nd edn. New York: Apress. Available at: https://git-scm.com/book

Docker Inc. (2026) *Best practices for writing Dockerfiles*. Available at: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/

Evans, E. (2003) *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Boston: Addison-Wesley.

Fly.io (2026) *Fly Launch documentation*. Available at: https://fly.io/docs/

Forsgren, N., Humble, J. and Kim, G. (2018) *Accelerate: The Science of Lean Software and DevOps*. Portland: IT Revolution Press.

Fowler, M. (2018) *Refactoring: Improving the Design of Existing Code*. 2nd edn. Boston: Addison-Wesley.

GitHub (2026) *GitHub Actions documentation*. Available at: https://docs.github.com/actions

Grinberg, M. (2018) *Flask Web Development: Developing Web Applications with Python*. 2nd edn. Sebastopol: O'Reilly Media.

Humble, J. and Farley, D. (2010) *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Boston: Addison-Wesley.

Kim, G., Debois, P., Willis, J. and Humble, J. (2016) *The DevOps Handbook*. Portland: IT Revolution Press.

Meszaros, G. (2007) *xUnit Test Patterns: Refactoring Test Code*. Boston: Addison-Wesley.

OWASP Foundation (2021) *OWASP Top Ten Web Application Security Risks*. Available at: https://owasp.org/www-project-top-ten/

OWASP Foundation (2026) *Authentication Cheat Sheet*. Available at: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

Pallets Projects (2026) *Flask documentation*. Available at: https://flask.palletsprojects.com/

SQLAlchemy (2026) *SQLAlchemy 2.0 Documentation*. Available at: https://docs.sqlalchemy.org/

W3C (2022) *Verifiable Credentials Data Model v1.1*. Available at: https://www.w3.org/TR/vc-data-model/

> `[Adjust the reference list to the citation style your department requires, and
> remove any source you did not actually consult.]`

---

## 15. Appendices

### Appendix A — Repository structure

See `README.md` §"Project structure".

### Appendix B — Requirements traceability matrix

`docs/requirements-traceability.md` — all 79 requirements mapped to
implementation, test and CI check.

### Appendix C — Test case document

`docs/test-cases.md` — 126 automated cases and 12 manual cases.

### Appendix D — Deployment verification record

`reports/deployment-verification.md` — the live verification, with commands and
results.

### Appendix E — Security control register

`docs/security.md` — thirty implemented controls with their verifying tests, and
seven documented gaps.

### Appendix F — Evidence

`[INSERT: screenshots per docs/evidence-checklist.md]`

### Appendix G — Word count

`[INSERT WORD COUNT]` — target 3,000–4,000 words excluding tables, code, the
reference list and appendices.

# Viva Preparation

Thirty-six likely questions with answers grounded in **what was actually built**.

> **Rule for the viva:** if you do not know, say so and say where you would look.
> An examiner can tell the difference between a confident answer and an invented
> one, and the invented one costs far more than the admission. Several answers
> below are deliberately "we did not do that, and here is why" — those are good
> answers, not weak ones.

---

## System and domain

**1. What problem does this system solve?**

Verifying a claimed qualification currently means telephoning a registry and
waiting days for an answer that is itself unverifiable. Our system gives an
authorised verifier an immediate, authoritative answer, and keeps an auditable
record of the check so it can be relied on later if disputed.

**2. Why four verification results rather than valid/invalid?**

Because "not valid" conflates three situations that call for entirely different
responses. `EXPIRED` means the award was genuine and has lapsed — the employer
asks about renewal. `REVOKED` means the institution withdrew it, often after
misconduct — that is a serious signal. `INVALID` means no such credential exists
— possibly a typing error, possibly a forgery. Collapsing these would destroy
the information the verifier most needs.

**3. What happens if a credential is both revoked and expired?**

It reports `REVOKED`. Revocation is the more serious fact and the one the
verifier must act on. It is an ordered branch in `evaluate_status`, and
`test_revocation_outranks_expiry` pins it.

**4. Why record failed verification attempts?**

Because "someone tried to verify a credential that does not exist, from this
address, at this time" is exactly the signal a fraud investigation needs.
Repeated near-miss references are a pattern worth seeing. `qualification_id` is
nullable specifically so a failed attempt still produces a row, and the attempted
reference is stored as text alongside it.

**5. Who can use the system, and why is it not public?**

Three roles: Verifier, Issuer, Administrator. Verification requires
authentication deliberately — an anonymous check would be recorded but not
attributable, which would gut the value of the audit trail. The trade-off is
that a third party holding only a reference cannot self-serve; a shareable,
expiring public receipt is assigned as a post-baseline task.

**6. What is out of scope, and why?**

Bulk import, a holder self-service portal, certificate image storage, and
cryptographic credential signing. The first is a student task. The last is
discussed in question 36.

---

## Architecture

**7. Describe your architecture.**

A layered monolith: routes → services → repositories → models. Routes are thin
controllers; services hold business rules, authorisation and transactions;
repositories hold every SQLAlchemy query; models hold entities and constraints.
Each layer may only call the one beneath it.

**8. Why not microservices?**

The domain is small and tightly coupled in a way that matters: the audit entry
for a verification must be transactionally consistent with the verification
record. Splitting them across services would replace one database transaction
with a distributed one, introducing the possibility of a verification that was
performed but not audited — the exact failure the system exists to prevent.

**9. What would you split first if you had to scale?**

The repository layer is the seam. The register (read-heavy, cacheable) could be
separated from verification recording (write-heavy). But we would first exhaust
vertical scaling and read replicas, because the distributed-transaction cost is
real.

**10. Why is `evaluate_status` a separate pure function?**

Because it is the most important logic in the system and it should be testable
without a database or an HTTP request. Making it take a model and a date and
return a result means all seven cases in the decision table are unit tested
directly, in microseconds. The impure work is a thin shell around it.

**11. How do routes, services and repositories differ in responsibility?**

A route parses input, calls exactly one service, and chooses a template or
redirect — no queries, no rules. A service enforces authorisation, validates,
mutates, writes the audit entry, and owns the transaction boundary. A repository
holds queries and returns models — no rules. If you find `db` imported into a
route, the logic is in the wrong place.

**12. Where are transaction boundaries?**

In the service layer. Each service command does its work and calls
`db.session.commit()` exactly once, so the domain change and its audit entry
commit together or not at all.

---

## Database

**13. Walk me through your schema.**

Five tables: `institutions`, `users`, `qualifications`, `verifications`,
`audit_logs`. An institution has users and awards qualifications; a user issues
qualifications and performs verifications; a qualification is checked by many
verifications; audit logs reference an actor.

**14. Why is `qualification_id` nullable in `verifications`?**

So a verification attempt against an unregistered reference still creates a row.
See question 4.

**15. Why is expiry computed rather than stored?**

A stored expiry flag would be wrong the day after it was written unless a
scheduled job maintained it — and a system whose correctness depends on a cron
job running is a system that will one day be quietly wrong. `effective_status`
computes it from the date, which is always correct.

**16. Explain your delete behaviours.**

`RESTRICT` on a qualification's institution and issuer — you cannot delete an
institution or user out from under credentials they are responsible for.
`SET NULL` on user references in verifications and audit logs — history survives
account deletion. `CASCADE` only from qualification to verification, because
verification records for a deleted credential describe nothing.

**17. Why does `audit_logs` store `actor_label` as well as `actor_id`?**

Deliberate denormalisation. If the account is later removed, `actor_id` becomes
null but the trail must still record who acted. Normalising it would let account
deletion erase history.

**18. Which indexes did you add and why?**

`credential_id` (unique) for the verification lookup — the hottest query;
`holder_name` and `title` for search; `status` for filters and dashboard counts;
a composite `(credential_id, created_at)` on verifications so the per-credential
history is ordered without a sort; and `(action, created_at)` for audit
filtering.

**19. Why non-native enums?**

`native_enum=False` stores them as strings with a check constraint, so the same
schema works on both PostgreSQL and SQLite and adding a value does not require a
PostgreSQL `ALTER TYPE`.

---

## Git and GitHub

**20. Describe your branching strategy and why.**

GitHub Flow with a `develop` integration branch. Full Git Flow was rejected —
release and hotfix branches solve problems (parallel supported versions,
emergency patches during a release) that a single-deployment project does not
have. Pure trunk-based was rejected because it depends on feature flags and a
test maturity we are still building.

**21. How do you prevent bad code reaching main?**

Branch protection: a pull request, one approval, code-owner review, conversation
resolution, an up-to-date branch, and the `Quality gate` status check. That gate
is one job depending on all the others, so a single required check covers the
whole pipeline.

**22. Tell me about a merge conflict you resolved.**

`[ANSWER FROM YOUR ACTUAL EXPERIENCE — the enum conflict in docs/collaboration-plan.md]`
Two branches added members to the same `AuditAction` enumeration for unrelated
but equally valid reasons. Git could not know the ordering. We resolved it by
keeping **both** sets — the resolution is never simply picking a side, because
discarding either would silently delete a colleague's feature. We then grepped
for leftover markers, ran the full suite, and let CI confirm before merging.

**23. What makes a good commit message here?**

Conventional Commits format, imperative subject under 72 characters, and a body
explaining *why*. `feat(auth): lock accounts after five failed sign-ins` followed
by the reasoning beats `fixed login`. The reviewer and the marker both read the
history.

**24. What is CODEOWNERS for?**

It maps areas of the codebase to their owner so the right reviewer is requested
automatically, rather than depending on the author choosing correctly.

---

## Testing

**25. How many tests, and what do they cover?**

264 tests at 92.69% line coverage — 177 unit, 87 integration. Unit tests cover
validation rules, the verification decision table, service business rules, audit
immutability and the review assistant. Integration tests cover full HTTP
workflows, access control and security properties.

**26. Why more unit tests than integration tests?**

The business rules are where the risk is. The verification decision table has
more meaningful cases than the route that calls it. Integration tests then prove
those units are correctly wired together.

**27. How do you test that audit logs cannot be modified?**

`test_updating_an_entry_raises` fetches a persisted entry, changes its `detail`,
commits, and asserts `ImmutableRecordError`. `test_deleting_an_entry_raises`
does the same for deletion, and `test_entry_survives_a_blocked_deletion`
confirms the row is still there afterwards.

**28. Why do integration tests run on PostgreSQL rather than SQLite?**

SQLite silently permits things PostgreSQL rejects — constraint semantics differ.
A suite that only ever saw SQLite could pass on code that breaks in production.
CI runs a PostgreSQL 16 service container for the integration job.

**29. What is not tested, and does that worry you?**

Named honestly: no browser-level tests, so a CSS regression hiding the result
banner would not fail the suite; no load or performance testing; rate limiting is
disabled in tests for determinism, so it is configuration-verified rather than
behaviour-verified; and the `/healthz` database-outage branch is manually
verified. The browser and load gaps are the ones that would worry us in a real
production system. Three of the four are assigned as Student 4's Task 4.3.

**30. Your coverage is 92%. Why not 100%?**

Because the remaining 8% is defensive code — the `IntegrityError` fallback for a
registration race, the database-unreachable path — that requires a genuinely
broken process to reach, and writing tests purely to cover it would test the
mocks rather than the behaviour. We deliberately excluded `app/cli.py` for the
same reason: it is exercised by running `flask seed-demo`, not by unit tests.

---

## CI/CD, Docker and deployment

**31. Walk me through your pipeline.**

Six jobs. `quality` runs Ruff, Black and Bandit. `unit-tests` and
`integration-tests` run their suites, the latter against PostgreSQL. `coverage`
runs everything with an 85% gate. `docker-build` builds the image and then runs
it, polling `/healthz`. `quality-gate` aggregates all of them into the single
required status check.

**32. What stops a failing build from deploying?**

CD is triggered by `workflow_run` on CI completion, and gated on
`github.event.workflow_run.conclusion == 'success'`. That trigger also fires for
*failed* runs, so without that condition a broken build would deploy itself. It
is the single most important line in the CD workflow.

**33. Why does the Docker job run the container rather than just build it?**

Because an image that builds but will not start is not a passing build. A broken
entrypoint or a missing runtime dependency produces a successful build and a
useless artefact.

**34. Your Dockerfile starts as root. Isn't that a security problem?**

The container starts as root only to `chown` the mounted volume — a Fly volume
attaches root-owned, so the unprivileged user could not otherwise write the
database — then drops to uid 10001 with `gosu` before exec'ing gunicorn. The
privileged window contains one `chown` and nothing else. The application never
runs as root.

**35. Did you build the image locally?**

No, and this is worth being straight about. Docker Desktop needs WSL2, and WSL2
reported that hardware virtualisation is disabled in the machine's firmware. We
deployed with `flyctl deploy --remote-only`, which builds on Fly's builders, and
the `docker-build` CI job builds and smoke-tests the image on GitHub's runners.
The Dockerfile is genuinely exercised — just not on that laptop.

**36. Your live database is SQLite, but your architecture says PostgreSQL. Explain.**

The application supports both — `DATABASE_URL` is the only difference — and CI
runs the integration suite against PostgreSQL 16. The live deployment uses SQLite
on a persistent volume to avoid provisioning a billed database cluster for a
demonstration. The cost is real and we state it: a volume attaches to one
machine, so the app cannot scale horizontally in this configuration. Switching
is two `flyctl` commands.

---

## Security

**37. What security controls did you implement?**

Thirty, listed in `docs/security.md` with the test that verifies each. The main
ones: PBKDF2 password hashing, a 12-character policy with character classes,
account-enumeration resistance, role-based access enforced at two layers, CSRF
protection, parameterised queries throughout, security headers including a CSP
and HSTS, rate limiting, open-redirect protection, an append-only audit trail,
and production start-up guards on secrets.

**38. How do you prevent SQL injection?**

Every query goes through SQLAlchemy expressions; there is no string-built SQL
anywhere in the codebase. Four tests fire injection payloads at the search and
verification fields and assert they are treated as literal text and that the
register survives.

**39. Tell me about a security bug you found.**

HSTS was not being sent on the live site. Fly terminates TLS at its edge and
forwards over plain HTTP, so `request.is_secure` was `False` for every request
and the header was never set. The same fault meant audit entries would have
logged the proxy's address rather than the client's. We fixed it with `ProxyFix`,
gated behind a `TRUST_PROXY_HEADERS` setting that is **off by default** —
trusting `X-Forwarded-*` without a proxy in front lets a client forge its own
scheme and address — and added four regression tests.

The lesson: it passed 255 tests, a clean lint and a clean security scan. Only
`curl` against the real deployment found it.

**40. Your CSP includes `'unsafe-inline'`. Isn't that defeating the point?**

Partly, and we say so. Tailwind's play CDN generates styles at runtime, so the
CSP does not protect against injected inline script. The mitigations are that
Jinja2 autoescapes all output and we render no user-supplied HTML anywhere. The
proper fix is compiling Tailwind at build time and dropping the directive — about
half an hour of work, and on reflection we should have done it.

**41. Why no account lockout?**

We have rate limiting at ten sign-in attempts per minute and we count and audit
failures, but we do not lock. That is a genuine gap, documented in
`docs/security.md` §7, and it is Student 1's first post-baseline task. The
subtlety in implementing it is making sure the lockout message does not become
an account-enumeration oracle.

**42. How are secrets managed?**

Nothing is committed. `SECRET_KEY` and `DATABASE_URL` are Fly secrets;
`FLY_API_TOKEN` is a GitHub Actions secret. `ProductionConfig` raises at start-up
if the secret key is missing, empty or still the development placeholder — five
tests assert this, because the dangerous failure mode is a system that appears to
work while being trivially compromisable.

**43. Why does an INVALID result show nothing at all?**

Because any detail — even confirming a similar reference exists — helps someone
probing the register. And there is a privacy dimension: verification should
confirm what the verifier already holds, not disclose new information about the
credential holder.

---

## Team and process

**44. How did you divide the work?**

By area of ownership, reflected in CODEOWNERS: authentication and user
management; qualification management; verification and audit; DevOps and QA.
Review pairing is reciprocal so every member both gives and receives review.

**45. What was the hardest technical problem?**

`[ANSWER FROM YOUR ACTUAL EXPERIENCE. Candidates: the proxy/HSTS defect; making
the audit entry commit in the same transaction as the change it describes;
resolving the enum merge conflict without losing either feature.]`

**46. What would you do differently?**

Four things. Write the traceability matrix first — writing it afterwards revealed
two requirements with no automated cover, and writing it first would have driven
those tests. Compile Tailwind rather than taking the CSP compromise. Test the
security controls against the real deployment topology earlier. And test rate
limiting behaviourally rather than only by configuration.

---

## Design judgement

**47. If you rebuilt this from scratch, what would you do differently
architecturally?**

The strongest answer to the trust problem is not a central register at all — it
is cryptographically signed credentials. Each qualification issued as a signed
object that a verifier validates offline against the institution's public key,
with the register consulted only for revocation. That removes the register as a
single point of trust and failure, works offline, and does not require the
verifier to have an account. It is roughly how W3C Verifiable Credentials
approach it.

We did not attempt it because key management — issuance, rotation, revocation and
the institutional processes around them — is a bigger problem than the
application itself, and doing it badly would be worse than not doing it. Our
architecture does not preclude it: signing would attach to the qualification
model, and our existing verification workflow would become the revocation check.

**48. What is the weakest part of your system?**

The absence of browser-level and load testing. Everything we assert about
correctness is asserted at the HTTP layer or below; we have no automated evidence
that the interface actually works in a browser, and no evidence at all about
behaviour under concurrent load. For a system whose whole value is that people
trust its answer, "we never measured what happens when many people ask at once"
is the gap that would concern us most in real deployment.

---

## How to prepare

- [ ] Every member can explain the **whole** architecture, not only their area
- [ ] Everyone can open `evaluate_status` and walk through the decision table
- [ ] Everyone can locate any file the examiner names
- [ ] Everyone knows their own commits, PRs and reviews by number
- [ ] Rehearse questions 22, 39, 45 and 46 — they need *your* real experiences,
      and inventing them is transparent
- [ ] Run `pytest` once before the viva so you can quote the current numbers
- [ ] Have the live system, the repository and a CI run open in tabs

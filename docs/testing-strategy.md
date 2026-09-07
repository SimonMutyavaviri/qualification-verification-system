# Testing Strategy

## 1. Objectives

The test suite exists to do three things:

1. Prove that every "Must" requirement in `docs/requirements.md` is implemented.
2. Prevent a regression from reaching `main`.
3. Give the four contributors a safety net so they can refactor confidently.

It is deliberately **not** written to inflate a coverage number. Coverage is a
by-product of testing behaviour that matters.

## 2. The test pyramid as applied here

```
        /\        Integration (87 tests)
       /  \       Full HTTP request -> response through the real stack.
      /----\      Workflows, access control, security properties.
     /      \
    /        \    Unit (177 tests)
   /          \   Validation rules, the verification decision table, service
  /____________\  business rules, audit immutability, the review assistant.
```

**264 tests, 92.69% line coverage** at the time of writing.

More unit tests than integration tests, because the business rules are where
the risk is: the verification decision table has more meaningful cases than the
route that calls it. The integration tests then prove those units are wired
together correctly.

## 3. What is tested at each level

### 3.1 Unit tests (`tests/unit/`)

| File | What it covers |
| --- | --- |
| `test_validators.py` | Every validation rule, positive and negative: credential ID format, required fields, qualification type, email, username, the password policy, award/expiry date rules |
| `test_qualification_service.py` | Registration, duplicate prevention, credential ID generation, update rules, immutable fields, revocation, reinstatement, search and filtering, statistics |
| `test_verification_service.py` | The full status decision table, the verify workflow, record creation, audit creation, history filtering, statistics |
| `test_auth_and_audit.py` | Password hashing, authentication, the role model, user and institution administration, password change, **audit immutability** |
| `test_risk_service.py` | Every review-assistant rule and the score/level boundaries |

### 3.2 Integration tests (`tests/integration/`)

`test_workflows.py` exercises the workflow the assignment specifies, as HTTP:

```
sign in -> register a qualification -> retrieve it by search -> open its
detail page -> verify it -> assert the verification record -> assert the
audit records
```

plus revocation changing a verification result, expired and invalid outcomes,
duplicate rejection, editing, search and filtering, verification history
visibility by role, administration workflows, the profile page, the health and
metrics endpoints, and error handling.

`test_security.py` asserts the security properties claimed in
`docs/security.md`. See section 6.

## 4. Test design principles

**Each test asserts one behaviour.** A test named
`test_revocation_outranks_expiry` fails for exactly one reason, so a failure
names the defect.

**Fixtures build the world, tests exercise it.** `tests/conftest.py` provides a
fresh in-memory database, an institution, one user per role, and active,
expired and revoked qualifications. No test depends on another test's state or
on execution order.

**Negative cases carry equal weight.** For every "it registers a valid
qualification" there is a duplicate, a future award date, an expiry before the
award, a blank title, an unknown institution, an inactive institution and an
unauthorised actor.

**Pure logic is tested purely.** `evaluate_status` takes a model and a date and
returns a result, so the decision table is tested directly rather than through
four HTTP round trips.

**Tests state intent, not mechanics.** `test_invalid_result_discloses_no_qualification`
records a privacy requirement; if someone "fixes" the code by returning the
qualification anyway, the failure explains why that is wrong.

## 5. Fixtures

| Fixture | Provides |
| --- | --- |
| `app` | A Flask app in testing config with a fresh in-memory SQLite database, dropped afterwards |
| `db` | The SQLAlchemy session inside the app context |
| `client` | Flask test client |
| `institution` | One active institution |
| `admin_user`, `issuer_user`, `verifier_user` | One user per role |
| `qualification` | Active, non-expiring |
| `expired_qualification` | Award date in the past, expiry ten days ago |
| `revoked_qualification` | Revoked with a reason |
| `auth` | Sign-in/sign-out helper for the test client |
| `logged_in_admin` / `_issuer` / `_verifier` | Pre-authenticated sessions |

Test passwords are module constants in `conftest.py`. They exist only inside
the test process and grant access to nothing.

## 6. Security testing

`tests/integration/test_security.py` carries the `security` marker:

```bash
pytest -m security -v
```

| Class | Property asserted |
| --- | --- |
| `TestAuthenticationRequired` | All ten protected routes redirect anonymous users |
| `TestRoleBasedAccessControl` | Each role is confined to its permissions, including by direct POST |
| `TestSecurityHeaders` | Hardening headers present, including on error responses |
| `TestSessionCookies` | `HttpOnly` and `SameSite` are configured |
| `TestInformationDisclosure` | No register data on INVALID; no user enumeration; no stack traces |
| `TestSqlInjectionResistance` | Three injection payloads treated as literal text; the register survives |
| `TestCsrfProtection` | CSRF enabled outside testing; state-changing routes reject GET |
| `TestOpenRedirectProtection` | An external `next` is ignored; a relative one is honoured |
| `TestProductionConfigurationGuards` | Production refuses a missing/placeholder secret key or missing database URL |

Testing the *negative* — that a verifier receives 403 rather than a page — is
the part that matters. A test proving an administrator can reach the audit trail
says nothing about whether a verifier can too.

## 7. Coverage and the quality gate

Configured in `pyproject.toml`:

```toml
addopts = [
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html:reports/coverage",
    "--cov-report=xml:reports/coverage.xml",
    "--cov-fail-under=85",
]
```

`--cov-fail-under=85` is the gate: below it, `pytest` exits non-zero and the CI
job fails. Current coverage is **92.69%**.

`app/cli.py` is omitted from coverage. It is exercised by running `flask
seed-demo` (which CI and the demonstration both do) rather than by unit tests,
and writing tests purely to cover it would be exactly the coverage-chasing this
strategy avoids.

The uncovered ~7% is chiefly defensive branches: the `IntegrityError` fallback
for a registration race, the database-unreachable path in `/healthz`, and
error-handler branches for conditions that need a genuinely broken process to
reach.

## 8. Running the tests

```bash
pytest                          # everything, with coverage and the gate
pytest -m unit                  # unit tests only
pytest -m integration           # integration tests only
pytest -m security              # security tests only
pytest --no-cov -q              # fast feedback while developing
pytest tests/unit/test_verification_service.py -v
pytest -k "revoke" -v           # every test about revocation
```

The HTML coverage report is written to `reports/coverage/index.html`.

## 9. Continuous integration

Every push and pull request runs the whole suite (`.github/workflows/ci.yml`):

| Job | Purpose |
| --- | --- |
| `quality` | Ruff, Black, Bandit |
| `unit-tests` | `pytest tests/unit -m unit` |
| `integration-tests` | `pytest tests/integration -m integration` **against PostgreSQL 16** |
| `coverage` | The full suite with the 85% gate |
| `docker-build` | Build the image, run it, require `/healthz` to pass |
| `quality-gate` | Fails if any of the above failed |

The integration job runs against PostgreSQL rather than SQLite on purpose: the
production engine enforces constraints SQLite does not, so a test suite that
only ever saw SQLite could pass on code that breaks in production.

JUnit XML and coverage reports are uploaded as artefacts on every run, which is
the pipeline evidence the assignment asks for.

## 10. Manual test evidence

Automated tests cannot check that the interface is *usable*. `docs/test-cases.md`
records the manual test cases — responsive layout, keyboard navigation, flash
message clarity, the verification result being unmistakable at a glance — with
places to attach screenshots.

## 11. Limitations of the current suite

Stated honestly:

- **No browser-level tests.** Templates are asserted by substring matching on
  the rendered HTML, not by driving a real browser. A CSS regression that made
  the result banner invisible would not fail the suite.
- **No load or performance testing.** Behaviour under concurrent verification
  load is unmeasured.
- **Rate limiting is disabled in tests** (`RATELIMIT_ENABLED = False`) so the
  suite is deterministic; the limits themselves are therefore configuration-tested,
  not behaviour-tested.
- **HSTS is not asserted**, because the test client does not make TLS requests.
- **Accessibility is manually checked**, not automatically audited.

Each is a candidate for the collaboration phase rather than a claim quietly left
unexamined.

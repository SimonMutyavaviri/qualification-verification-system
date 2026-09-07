# Developer Guide

Everything you need to work on this codebase.

---

## 1. Architecture in one minute

A layered Flask monolith. **Each layer may only call the one beneath it:**

```
Routes  (app/routes/)        thin controllers: parse, call a service, render
   ↓
Services (app/services/)     business rules, authorisation, transactions, audit
   ↓
Repositories (app/repositories/)  every SQLAlchemy query in the system
   ↓
Models (app/models/)         entities, constraints, indexes
```

**The rule that matters:** never write a query in a route, and never write a
business rule in a repository. If you find yourself importing `db` into a route
file, the logic belongs in a service.

Full detail: `docs/architecture.md`.

## 2. Project structure

```
qualification-verification-system/
├── app/
│   ├── __init__.py          application factory
│   ├── config.py            per-environment config; production secret guards
│   ├── extensions.py        unbound extension singletons
│   ├── forms.py             WTForms definitions
│   ├── errors.py            central error handlers (400/401/403/404/405/429/500)
│   ├── cli.py               init-db, create-admin, seed-demo
│   ├── models/              User, Institution, Qualification, Verification, AuditLog
│   ├── repositories/        all queries
│   ├── services/            business rules
│   ├── routes/              blueprints: main, auth, qualifications, verification, admin
│   ├── auth/                Flask-Login wiring
│   ├── utils/               validators, errors, security, audit_guard
│   ├── templates/           Jinja2; _macros.html holds shared components
│   └── static/              app.css, app.js
├── tests/
│   ├── conftest.py          fixtures
│   ├── unit/                155 tests
│   └── integration/         100 tests
├── docs/                    this documentation set
├── reports/                 academic deliverables and generated coverage
├── migrations/              Alembic (Flask-Migrate)
├── .github/workflows/       ci.yml, cd.yml
├── Dockerfile               multi-stage; runs as uid 10001
├── docker-compose.yml       local app + PostgreSQL
├── fly.toml                 deployment configuration
├── pyproject.toml           ruff, black, pytest, coverage, bandit config
├── requirements.txt         runtime dependencies
├── requirements-dev.txt     runtime + test and quality tooling
├── run.py                   local development entry point
└── wsgi.py                  production entry point (gunicorn)
```

## 3. Environment setup

**Requires Python 3.11+.** The project is developed on 3.14 and deployed on 3.12.

```bash
git clone <repository-url>
cd qualification-verification-system

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements-dev.txt

cp .env.example .env               # then edit SECRET_KEY
```

### Known dependency notes

- **`psycopg[binary]` (psycopg 3), not `psycopg2`.** psycopg2 has no wheel for
  recent Python versions and needs a C toolchain to build. psycopg 3 is the
  supported SQLAlchemy 2 driver; the URL scheme is `postgresql+psycopg://`,
  which `BaseConfig.normalise_database_url` produces automatically.
- **Bandit 1.9.4 or later** on Python 3.13+. Earlier versions use
  `ast.Constant.s`, which was removed, and crash on every file.
- **Email validation does not check deliverability.** `EMAIL_FORMAT` in
  `app/forms.py` sets `check_deliverability=False`, so form validation does not
  make a DNS lookup — that would fail offline and in CI. Note that
  `email_validator` still rejects special-use TLDs (`.test`, `.local`,
  `.invalid`), which is why test data uses `example.com`.

## 4. Running locally

```bash
export FLASK_APP=run.py            # Windows: set FLASK_APP=run.py
flask seed-demo                    # creates the database and demo data
python run.py                      # http://127.0.0.1:5000
```

`seed-demo` prints generated passwords once. To choose your own:

```bash
SEED_ADMIN_PASSWORD='YourDevPassword123' flask seed-demo
```

Demo credentials in the register: `QVS-2023-DEMO01` (valid),
`QVS-2022-DEMO02` (expired), `QVS-2021-DEMO03` (revoked).

### Other CLI commands

```bash
flask init-db                      # create tables only
flask create-admin --username x --email x@example.com --full-name "X Y"
                                   # password is prompted, never in shell history
```

## 5. Running against PostgreSQL locally

```bash
docker compose up -d db
export DATABASE_URL=postgresql://qvs:qvs-local-dev@localhost:5432/qvs
flask seed-demo && python run.py
```

Or the whole stack as deployed:

```bash
echo "SECRET_KEY=$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" > .env
docker compose up --build          # http://localhost:8080
```

## 6. Testing

```bash
pytest                             # everything, with coverage and the 85% gate
pytest --no-cov -q                 # fast feedback loop
pytest -m unit                     # unit only
pytest -m integration              # integration only
pytest -m security                 # security properties only
pytest tests/unit/test_verification_service.py -v
pytest -k "revoke" -v              # everything about revocation
pytest --lf                        # re-run only last failures
```

Coverage HTML: `reports/coverage/index.html`.

### Writing a test

Use the fixtures in `tests/conftest.py` — they give you an app, an in-memory
database, an institution, a user per role, and active/expired/revoked
qualifications.

```python
def test_revoked_credential_verifies_as_revoked(db, revoked_qualification, verifier_user):
    outcome = VerificationService.verify(
        credential_id=revoked_qualification.credential_id, actor=verifier_user
    )
    assert outcome.result == VerificationResult.REVOKED
```

Conventions: one behaviour per test; a name that states the rule; a negative
case for every positive one; mark it `unit`, `integration` or `security`.

## 7. Code quality

```bash
ruff check .                       # lint
ruff check --fix .                 # auto-fix what is safe
black .                            # format
black --check .                    # verify without changing
bandit -c pyproject.toml -r app -ll # security scan (medium+ severity)
```

All four run in CI and **block the merge** on failure. Run them before pushing.

Standards: Black formatting at 100 columns; Ruff rule set `E,F,W,I,B,C4,UP,SIM,ARG,RET,N`;
type hints on public functions; docstrings that explain *why*, not *what*.

## 8. How to add a feature

Worked example — adding a "suspend" state alongside revoke:

1. **Model** — add the value to `QualificationStatus` in `app/models/enums.py`.
2. **Validation** — extend the rules in `app/utils/validators.py` if new input
   is involved.
3. **Repository** — add the query if you need one (`app/repositories/`).
4. **Service** — put the rule in `QualificationService`: check authorisation,
   validate, mutate, `AuditService.record(...)`, then **one** `db.session.commit()`.
5. **Verification** — decide how the new state maps to a result in
   `VerificationService.evaluate_status`, and unit test every branch.
6. **Route** — a thin view in `app/routes/` with the right `@roles_required`.
7. **Form** — add it to `app/forms.py` if it takes input.
8. **Template** — render it; reuse the macros in `_macros.html`.
9. **Tests** — unit tests for the rule, integration test for the workflow, a
   security test if it touches permissions.
10. **Docs** — update `docs/requirements.md` and
    `docs/requirements-traceability.md`.

### Non-negotiables

- **Audit anything auditable.** Every state change calls `AuditService.record`,
  and the audit row commits in the *same transaction* as the change it describes.
- **Check authorisation in the service, not only the route.** The decorator is
  what a reader sees; the service check is what a future route cannot forget.
- **Validate in the service, not only the form.** A request that bypasses the
  form must still not be able to write invalid data.
- **Never build SQL by string concatenation.** SQLAlchemy expressions only.

## 9. Database changes

The baseline schema comes from `db.create_all()`. From the first schema change
onwards, use migrations so deployed data survives:

```bash
flask db init                      # once, if migrations/versions/ does not exist
flask db migrate -m "Add suspended status to qualifications"
flask db upgrade
```

Review the generated revision before committing — Alembic's autogenerate is a
draft, not an answer. Commit `migrations/versions/*.py`.

## 10. Contribution workflow

Summarised from `docs/git-workflow.md`:

```
issue → branch from develop → commits → push → PR → CI → review → merge
```

- Branch names: `feature/…`, `fix/…`, `docs/…`, `chore/…`, `test/…`
- Commits: Conventional Commits (`feat(scope): imperative subject`)
- Every PR needs a green pipeline and one approval
- Never force-push a shared branch

## 11. Deployment

```bash
flyctl deploy --remote-only --app qvs-mim736
flyctl logs --app qvs-mim736
flyctl status --app qvs-mim736
```

`--remote-only` builds on Fly's builders, so local Docker is not needed. Full
detail in `docs/flyio-deployment.md`.

## 12. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `RuntimeError: Working outside of application context` | Touching `db` or `current_user` outside a request/app context | Wrap in `with app.app_context():` |
| `sqlalchemy.exc.InvalidRequestError` about the session | A previous exception left the session dirty | `db.session.rollback()`; the global error handler does this |
| `ImmutableRecordError` on commit | You modified or deleted an `AuditLog` row | That is the guard working as designed — do not edit audit history |
| Tests pass locally, fail in CI | CI runs integration tests on PostgreSQL | Reproduce with `docker compose up -d db` and `TEST_DATABASE_URL=...` |
| `Invalid email address` for a plausible address | `email_validator` rejects `.test` / `.local` / `.invalid` TLDs | Use `example.com` in test data |
| Bandit crashes on every file | Bandit older than 1.9 on Python 3.13+ | `pip install --upgrade bandit` |
| psycopg2 wheel build fails | No wheel for your Python; needs a compiler | The project uses `psycopg[binary]` — check you installed from `requirements.txt` |
| CSRF token missing in a test | Testing config disables CSRF; production does not | `WTF_CSRF_ENABLED = False` is set in `TestingConfig` only |
| `flask` command not found | Virtual environment not activated | Activate `.venv` |
| Docker fails to start on Windows | Hardware virtualisation disabled in BIOS | Use `flyctl deploy --remote-only`, or enable virtualisation |

# Qualification Verification System

A DevOps-enabled system for registering academic and professional
qualifications, verifying their authenticity, and maintaining an auditable
history of every verification performed.

**Live system:** https://qvs-mim736.fly.dev
**Health:** https://qvs-mim736.fly.dev/healthz

Built for the **MIM736 Practical Assignment**.

---

## Status

| | |
| --- | --- |
| Tests | **264 passing** |
| Coverage | **92.69%** (gate: 85%) |
| Lint (Ruff) | Clean |
| Format (Black) | Clean |
| Security (Bandit) | 0 findings |
| Deployment | Live on Fly.io (`jnb`) |

---

## What it does

Employers and admitting institutions need to know whether a claimed
qualification is genuine, was awarded by the body named on it, and has not since
been withdrawn. This system holds a register of issued credentials, verifies a
credential against that register, and records every check.

### Features

- **Register credentials** — issuers record qualifications with full validation;
  unique credential IDs are generated automatically
- **Search and retrieve** — search by credential ID, holder or title; filter by
  status, type and institution; paginated results
- **Verify authenticity** — one reference in, one unambiguous result out:
  `VALID`, `INVALID`, `REVOKED` or `EXPIRED`
- **Verification receipts** — every check gets a permanent, shareable record
- **Auditable history** — an append-only trail of every verification, sign-in,
  registration, revocation and administrative change, which the application
  cannot modify or delete
- **Role-based access** — Administrator, Qualification Issuer, Verifier
- **Revocation** — withdraw a credential with a recorded reason; verifiers see
  the change immediately
- **Review assistant** *(bonus)* — a rule-based check that flags records
  warranting a human look, with a plain-English reason for every signal
- **Live monitoring** *(bonus)* — dashboard counters refreshed from a metrics
  endpoint

---

## Architecture

A layered monolith. Each layer may only call the one beneath it:

```
Routes → Services → Repositories → Models → Database
```

- **Routes** (`app/routes/`) — thin controllers: parse, call one service, render
- **Services** (`app/services/`) — business rules, authorisation, transactions,
  audit writes
- **Repositories** (`app/repositories/`) — every SQLAlchemy query in the system
- **Models** (`app/models/`) — entities, constraints, indexes, relationships

The verification decision itself is a **pure function**
(`VerificationService.evaluate_status`), so the whole decision table is unit
tested directly rather than through HTTP round trips.

Full detail and the reasoning behind the trade-offs: [`docs/architecture.md`](docs/architecture.md).

---

## Technology stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.12 (developed on 3.14) |
| Framework | Flask 3.1 |
| ORM | SQLAlchemy 2.0 / Flask-SQLAlchemy |
| Auth | Flask-Login, Werkzeug PBKDF2-SHA256 |
| Forms & CSRF | Flask-WTF, WTForms |
| Rate limiting | Flask-Limiter |
| Migrations | Flask-Migrate (Alembic) |
| Database | PostgreSQL (supported) · SQLite (dev, tests, current deployment) |
| Frontend | HTML5, Tailwind CSS, vanilla JavaScript |
| Testing | pytest, pytest-cov |
| Quality | Ruff, Black, Bandit |
| CI/CD | GitHub Actions |
| Container | Docker (multi-stage, non-root) |
| Hosting | Fly.io |

---

## Quick start

```bash
git clone <repository-url>
cd qualification-verification-system

python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env                # edit SECRET_KEY

export FLASK_APP=run.py             # Windows: set FLASK_APP=run.py
flask seed-demo                     # creates the database and demo data
python run.py                       # http://127.0.0.1:5000
```

`flask seed-demo` prints generated sign-in passwords **once**. To choose your
own, set `SEED_ADMIN_PASSWORD`, `SEED_ISSUER_PASSWORD` and
`SEED_VERIFIER_PASSWORD` before running it.

### Demonstration credentials in the register

| Credential ID | Result |
| --- | --- |
| `QVS-2023-DEMO01` | VALID |
| `QVS-2022-DEMO02` | EXPIRED |
| `QVS-2021-DEMO03` | REVOKED |
| anything unregistered | INVALID |

---

## Environment variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | **Yes in production** | dev placeholder | Session signing. Production refuses to start without a real value. |
| `DATABASE_URL` | **Yes in production** | `sqlite:///qvs-dev.db` | Database connection. `postgres://` is normalised automatically. |
| `FLASK_ENV` | No | `development` | `development` / `testing` / `production` |
| `SESSION_COOKIE_SECURE` | No | `false` | Forced `true` in production |
| `SESSION_LIFETIME_MINUTES` | No | `30` | Session inactivity timeout |
| `PASSWORD_MIN_LENGTH` | No | `12` | Minimum password length |
| `ITEMS_PER_PAGE` | No | `10` | Pagination size |
| `RATELIMIT_ENABLED` | No | `true` | Master switch for rate limiting |
| `RATELIMIT_LOGIN` | No | `10 per minute` | Sign-in rate limit |
| `RATELIMIT_VERIFY` | No | `30 per minute` | Verification rate limit |
| `LOG_TO_FILE` | No | `false` | Also log to `logs/qvs.log` |

Never commit a real `.env`. See [`.env.example`](.env.example).

---

## Database setup

```bash
flask init-db      # create tables
flask seed-demo    # tables + demo data (idempotent)
flask create-admin --username admin --email admin@example.com --full-name "A B"
                   # password is prompted, so it never reaches shell history
```

From the first schema change onward, use migrations — see
[`migrations/README.md`](migrations/README.md).

---

## Running the tests

```bash
pytest                     # everything, with coverage and the 85% gate
pytest --no-cov -q         # fast feedback
pytest -m unit             # unit tests only
pytest -m integration      # integration tests only
pytest -m security         # security properties only
pytest -k "revoke" -v      # everything about revocation
```

Coverage HTML report: `reports/coverage/index.html`.

## Code quality

```bash
ruff check .                          # lint
black --check .                       # formatting
bandit -c pyproject.toml -r app -ll   # security scan
```

All three run in CI and block the merge on failure.

---

## Docker

```bash
docker build -t qvs:local .

docker run --rm -p 8080:8080 \
  -e SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" \
  -e DATABASE_URL=sqlite:////data/qvs.db \
  -e SESSION_COOKIE_SECURE=false \
  qvs:local

curl http://localhost:8080/healthz
```

Or the full stack with PostgreSQL:

```bash
echo "SECRET_KEY=$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" > .env
docker compose up --build            # http://localhost:8080
```

The image is multi-stage (≈78 MB), runs the application as an unprivileged user
(uid 10001), and carries a `HEALTHCHECK`.

---

## CI/CD

**CI** (`.github/workflows/ci.yml`) runs on every push and pull request:

| Job | What it does |
| --- | --- |
| `quality` | Ruff, Black, Bandit |
| `unit-tests` | The unit suite |
| `integration-tests` | The integration suite **against PostgreSQL 16** |
| `coverage` | Full suite with the 85% gate |
| `docker-build` | Builds the image, runs it, requires `/healthz` to pass |
| `quality-gate` | Fails if any of the above failed — the single required check |

**CD** (`.github/workflows/cd.yml`) deploys to Fly.io **only** when CI concluded
successfully on `main`, then polls `/healthz` and smoke-tests the sign-in page.

Full detail: [`docs/ci-cd.md`](docs/ci-cd.md).

---

## Deployment

```bash
flyctl deploy --remote-only --app qvs-mim736
```

`--remote-only` builds on Fly's builders, so local Docker is not required.
Complete guide, including the switch to managed PostgreSQL:
[`docs/flyio-deployment.md`](docs/flyio-deployment.md).

---

## User roles

| Capability | Verifier | Issuer | Admin |
| --- | :---: | :---: | :---: |
| Verify a credential | ✓ | ✓ | ✓ |
| Search the register | ✓ | ✓ | ✓ |
| View own verification history | ✓ | ✓ | ✓ |
| View all verification history | — | ✓ | ✓ |
| Register a qualification | — | ✓ | ✓ |
| Edit a qualification | — | ✓ | ✓ |
| Revoke a qualification | — | ✓ | ✓ |
| Reinstate a revoked qualification | — | — | ✓ |
| Manage users and institutions | — | — | ✓ |
| View the audit trail | — | — | ✓ |

---

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/requirements.md`](docs/requirements.md) | Functional and non-functional requirements |
| [`docs/architecture.md`](docs/architecture.md) | Architecture, design decisions, trade-offs |
| [`docs/database-design.md`](docs/database-design.md) | ER model, constraints, indexes |
| [`docs/security.md`](docs/security.md) | Implemented controls **and known gaps** |
| [`docs/testing-strategy.md`](docs/testing-strategy.md) | Test design, coverage, limitations |
| [`docs/requirements-traceability.md`](docs/requirements-traceability.md) | Requirement → code → test → CI check |
| [`docs/ci-cd.md`](docs/ci-cd.md) | Pipeline design and quality gates |
| [`docs/git-workflow.md`](docs/git-workflow.md) | Branching, commits, reviews, conflicts |
| [`docs/flyio-deployment.md`](docs/flyio-deployment.md) | Deployment and operations |
| [`docs/user-manual.md`](docs/user-manual.md) | End-user guide |
| [`docs/developer-guide.md`](docs/developer-guide.md) | Setup, conventions, troubleshooting |
| [`docs/test-cases.md`](docs/test-cases.md) | Formal test cases including manual ones |
| [`docs/collaboration-plan.md`](docs/collaboration-plan.md) | The four post-baseline task sets |
| [`docs/evidence-checklist.md`](docs/evidence-checklist.md) | What to capture for submission |

---

## Project structure

```
├── app/
│   ├── models/          User, Institution, Qualification, Verification, AuditLog
│   ├── repositories/    all database queries
│   ├── services/        business rules, authorisation, audit
│   ├── routes/          HTTP blueprints
│   ├── auth/            Flask-Login wiring
│   ├── utils/           validators, errors, security, audit guard
│   ├── templates/       Jinja2
│   └── static/          CSS and JavaScript
├── tests/
│   ├── unit/            177 tests
│   └── integration/     87 tests
├── docs/                documentation set
├── reports/             academic deliverables, coverage output
├── migrations/          Alembic
├── .github/workflows/   ci.yml, cd.yml
├── Dockerfile
├── docker-compose.yml
├── fly.toml
└── pyproject.toml
```

---

## Screenshots

> `[INSERT SCREENSHOT: sign-in page]`
> `[INSERT SCREENSHOT: dashboard]`
> `[INSERT SCREENSHOT: verification result — VALID]`
> `[INSERT SCREENSHOT: verification result — REVOKED]`
> `[INSERT SCREENSHOT: qualification register]`
> `[INSERT SCREENSHOT: audit trail]`

See [`docs/evidence-checklist.md`](docs/evidence-checklist.md) for the full list.

---

## Team

| Member | Area of responsibility |
| --- | --- |
| `[INSERT NAME]` `[INSERT STUDENT NUMBER]` | Authentication, backend hardening, user management |
| `[INSERT NAME]` `[INSERT STUDENT NUMBER]` | Qualification management |
| `[INSERT NAME]` `[INSERT STUDENT NUMBER]` | Verification and audit |
| `[INSERT NAME]` `[INSERT STUDENT NUMBER]` | DevOps, QA, Docker and deployment |

---

## Known limitations

Stated openly rather than omitted — see `docs/security.md` §7,
`docs/testing-strategy.md` §11 and `docs/ci-cd.md` §9 for the full accounting:

- No account lockout (rate limiting only) — Student 1's task
- Rate limiting is in-memory, so limits are per-process
- The CSP includes `'unsafe-inline'` because Tailwind is loaded from a CDN
- Audit immutability is enforced at the application layer, not the database
- No dependency vulnerability scanning yet — Student 4's task
- No staging environment — Student 4's task
- The current deployment uses SQLite on a volume rather than PostgreSQL; the
  application supports both, and switching is one command

---

## Licence

MIT — see [`LICENSE`](LICENSE).

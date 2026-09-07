# System Architecture

## 1. Architectural style

The system is a **layered monolith** built with the Flask application-factory
pattern. Each layer may only call the layer beneath it:

```
        HTTP request
             |
     +-------v--------+   Blueprints. Parse input, call one service, choose a
     |     Routes     |   template or a redirect. No business rules, no SQL.
     +-------+--------+
             |
     +-------v--------+   Business rules, authorisation checks, audit writing
     |    Services    |   and transaction boundaries. Framework-independent
     +-------+--------+   apart from the audit helper.
             |
     +-------v--------+   Every SQLAlchemy query in the system lives here.
     |  Repositories  |   Returns models or pagination objects.
     +-------+--------+
             |
     +-------v--------+   SQLAlchemy declarative models, constraints, indexes
     |     Models     |   and small pure helpers (e.g. effective_status).
     +-------+--------+
             |
     +-------v--------+
     |   PostgreSQL   |   SQLite for local development and unit tests.
     +----------------+
```

Cross-cutting concerns sit beside the stack rather than inside it:
`app/utils/validators.py` (pure validation rules), `app/utils/security.py`
(authorisation decorators and response headers), `app/utils/audit_guard.py`
(append-only enforcement) and `app/errors.py` (central error handling).

### Why a layered monolith rather than microservices

The domain is small and highly cohesive: a verification is meaningless without
the register, and the audit trail must be transactionally consistent with both.
Splitting these into services would introduce network calls and distributed
transactions to solve a problem this system does not have, while making the
audit guarantee harder to keep. The layering gives the separation of concerns
that maintainability requires without paying the distributed-systems cost. If
the register later needed to scale independently of verification, the
repository layer is the natural seam at which to split.

## 2. Component responsibilities

| Component | Responsibility |
| --- | --- |
| `app/__init__.py` | Application factory: config, extensions, blueprints, filters |
| `app/config.py` | Environment-specific configuration; production secret guards |
| `app/extensions.py` | Unbound extension singletons (db, login, csrf, limiter, migrate) |
| `app/models/` | Entities, constraints, indexes, relationships, enums |
| `app/repositories/` | All queries: lookup, search, pagination, counts |
| `app/services/` | Business rules, authorisation, transactions, audit writes |
| `app/routes/` | HTTP blueprints; thin controllers |
| `app/forms.py` | WTForms definitions, CSRF, presentation-level validation |
| `app/auth/` | Flask-Login wiring: user loader, unauthenticated handler |
| `app/utils/` | Validation, domain errors, security helpers, audit guard |
| `app/errors.py` | Content-negotiating error handlers for 400/401/403/404/405/429/500 |
| `app/cli.py` | `init-db`, `create-admin`, `seed-demo` |
| `app/templates/` | Jinja2 templates; `_macros.html` holds shared components |

## 3. Request lifecycle

A verification request, end to end:

1. `POST /verify/` reaches `verification_routes.verify`.
2. `@login_required` and `@roles_required(...)` establish identity and
   permission; a denial writes an `access.denied` audit entry and aborts 403.
3. `@limiter.limit` applies the rate limit for the endpoint.
4. `VerificationForm` validates CSRF and field presence.
5. `VerificationService.verify` normalises and validates the reference, looks
   the credential up, evaluates status, builds a `Verification` row and an
   `AuditLog` row, and commits **both in one transaction**.
6. The route renders the outcome; `apply_security_headers` decorates the
   response.

The single commit in step 5 is the important part: a verification that is
recorded but not audited, or audited but not recorded, would undermine exactly
the guarantee the system exists to make.

## 4. Key design decisions

### 4.1 The verification decision is a pure function

`VerificationService.evaluate_status(qualification, on_date)` takes a model (or
`None`) and returns a result. It touches no database and no request context,
so the whole decision table — missing, revoked, expired, revoked-and-expired,
expiring-today — is unit tested directly and exhaustively. The impure work
(lookup, recording, auditing) is a thin shell around it.

### 4.2 Revocation outranks expiry

A credential that is both revoked and past its expiry date reports REVOKED.
Expiry is an administrative fact; revocation is a statement that the credential
should never be relied upon. Reporting the weaker signal would understate the
problem to the verifier.

### 4.3 Failed verifications are recorded

`Verification.qualification_id` is nullable so that an attempt against an
unknown reference still produces a row. "Someone tried to verify a credential
that does not exist, from this address, at this time" is precisely the signal a
fraud investigation needs, and discarding it would leave a blind spot.

### 4.4 The audit trail is enforced append-only

`app/utils/audit_guard.py` registers SQLAlchemy `before_update` and
`before_delete` listeners on `AuditLog` that raise `ImmutableRecordError`.
Documenting the intention would not have prevented a future contributor from
writing `entry.detail = ...`; the listener does, and two tests assert it.

### 4.5 Validation is applied twice, deliberately

WTForms validates at the boundary so users get inline field errors. The service
layer re-applies the authoritative rules from `app/utils/validators.py`. The
duplication is intentional: a request that bypasses the form — a script, a
future API, a mistake in a new route — still cannot write an invalid record.

### 4.6 Credential IDs avoid ambiguous characters

The generator alphabet excludes `O`, `0`, `I` and `1`. Credential references are
read off printed certificates and dictated over the telephone, where those
characters are routinely confused; excluding them removes a class of
"verification failed" incidents that are not actually verification failures.

### 4.7 Immutable credential fields

Credential ID, award date, institution and issuer cannot be edited after
registration. A third party may already have verified the credential and
recorded the result; silently changing what that reference means would make
past verification receipts untrue.

## 5. Data flow: registration

```
Issuer submits form
        |
   CSRF + field validation (QualificationForm)
        |
   QualificationService.register
        |-- authorisation: actor.has_role(ISSUER)
        |-- validate title, type, holder, email, dates
        |-- resolve and check the institution is active
        |-- credential ID: validate supplied, or generate unused
        |-- duplicate check (+ IntegrityError fallback for the race)
        |-- INSERT qualification
        |-- INSERT audit entry
        +-- COMMIT (one transaction)
        |
   Redirect to the detail page
```

## 6. Deployment architecture

```
        Browser (HTTPS)
             |
   Fly.io edge: TLS termination, force_https
             |
   Health check GET /healthz  --> unhealthy machines receive no traffic
             |
   Machine: Docker container (non-root user 10001)
        gunicorn, 2 workers x 4 threads
             |
        Flask application
             |
   PostgreSQL (Fly Postgres) via DATABASE_URL secret
```

Configuration reaches the container as environment variables. `SECRET_KEY` and
`DATABASE_URL` are Fly secrets, never present in the repository or the image.

## 7. Technology choices and their trade-offs

| Choice | Why | Trade-off accepted |
| --- | --- | --- |
| Flask over Django | The domain needs a register, a verification check and an audit trail; Django's admin, ORM conventions and app machinery would add surface area the project would not use. Flask keeps the layering explicit and readable, which suits a codebase that must be understood and extended by four contributors. | Authentication, forms and admin screens are built rather than inherited. |
| Server-rendered Jinja over a SPA | The interface is forms and tables. Server rendering removes an entire build toolchain and API surface, and works without JavaScript. | No offline use; each interaction is a round trip. |
| PostgreSQL in production | Real constraint enforcement, concurrent access, and the engine the integration tests run against in CI. | Requires a managed database rather than a file. |
| SQLite for tests | An in-memory database per test makes the suite fast and order-independent. | Engine differences; mitigated by running the integration suite against PostgreSQL in CI. |
| Tailwind via CDN | No build step; the whole UI ships as templates and one stylesheet. | A CDN dependency, and `'unsafe-inline'` in the CSP for its runtime styles. Documented in `docs/security.md`. |
| Rule-based review assistant | An assistant that influences whether a credential is trusted must be explainable; every signal points at a field and states its reason. | Cannot detect patterns nobody has written a rule for. |

## 8. Known limitations

- Rate limiting uses in-memory storage, so limits are per-process. A multi-machine
  deployment would need a shared Redis backend.
- The schema is created with `db.create_all()` at container start. Flask-Migrate
  is wired in, and the first schema change onwards should use migrations.
- The review assistant is advisory: it never blocks a registration, and a
  reviewer must act on it.
- Verification is authenticated only; there is no public verification endpoint
  for a third party holding just a reference number.

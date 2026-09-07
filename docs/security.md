# Security

This document records **what is actually implemented**, where it lives, and how
it is verified. Controls that were considered but not built are listed in
section 7 as gaps rather than being quietly omitted.

---

## 1. Implemented controls

| # | Control | Implementation | Verified by |
| --- | --- | --- | --- |
| 1 | Password hashing | `User.set_password` uses Werkzeug `generate_password_hash` (PBKDF2-SHA256, per-password salt) | `test_auth_and_audit.py::TestPasswordHashing` |
| 2 | Constant-time password comparison | `check_password_hash` | `TestPasswordHashing` |
| 3 | Password policy | `validate_password`: ≥12 chars, upper + lower + digit | `test_validators.py::TestPasswordPolicy` |
| 4 | Account enumeration resistance | Identical message and code path for unknown user and wrong password | `TestInformationDisclosure::test_login_failure_does_not_reveal_whether_the_user_exists` |
| 5 | Account deactivation | `is_active=False` refuses sign-in | `TestAuthentication::test_rejects_a_deactivated_account` |
| 6 | Session management | Flask-Login, `session_protection="strong"`, 30-minute lifetime | `TestSessionCookies` |
| 7 | Secure cookies | `HttpOnly`, `SameSite=Lax` always; `Secure` in production | `TestSessionCookies::test_cookie_configuration_is_hardened` |
| 8 | Role-based access control | `roles_required` / `admin_required` / `issuer_required` decorators; service layer re-checks | `test_security.py::TestRoleBasedAccessControl` (9 tests) |
| 9 | Authorisation enforced in the service layer | `_assert_can_issue`, `_assert_admin` — a new route cannot forget the check | `test_qualification_service.py`, `test_auth_and_audit.py` |
| 10 | CSRF protection | Flask-WTF `CSRFProtect` on every state-changing form | `TestCsrfProtection` |
| 11 | SQL injection resistance | SQLAlchemy parameterised queries only; no string-built SQL anywhere | `TestSqlInjectionResistance` (4 tests) |
| 12 | Input validation | `app/utils/validators.py`, applied at the form **and** the service | `test_validators.py` (40 tests) |
| 13 | Security response headers | `apply_security_headers` as an `after_request` hook | `TestSecurityHeaders` |
| 14 | Content Security Policy | `default-src 'self'`, `frame-ancestors 'none'`, `form-action 'self'` | `TestSecurityHeaders::test_content_security_policy_is_set` |
| 15 | HSTS | Set on HTTPS responses (`max-age=31536000; includeSubDomains`) | `TestProxyAwareness::test_hsts_is_sent_for_an_https_request`; confirmed live |
| 16 | Rate limiting | Flask-Limiter: 10/min on sign-in, 30/min on verification | Configured in `app/config.py`; disabled in tests |
| 17 | Open redirect protection | `_safe_next` rejects absolute URLs and non-`/` paths | `TestOpenRedirectProtection` |
| 18 | No stack traces to clients | Central handlers in `app/errors.py`; traces go to the log | `TestInformationDisclosure::test_error_pages_do_not_leak_stack_traces` |
| 19 | Minimal disclosure on failed verification | An INVALID result carries no register data | `TestInformationDisclosure`, `test_verification_service.py` |
| 20 | Secrets from the environment only | `app/config.py`; production raises on a missing or placeholder `SECRET_KEY` | `TestProductionConfigurationGuards` (5 tests) |
| 21 | Production database required | Production raises without `DATABASE_URL` | `TestProductionConfigurationGuards` |
| 22 | Debug disabled in production | `ProductionConfig.DEBUG = False` | `TestProductionConfigurationGuards` |
| 23 | Append-only audit trail | SQLAlchemy `before_update` / `before_delete` guards raise `ImmutableRecordError` | `TestAuditImmutability` (4 tests) |
| 24 | Access denials audited | `access.denied` entries written and committed on 403 | `TestRoleBasedAccessControl::test_denied_access_is_audited` |
| 25 | Sign-in attempts audited | Success and failure both recorded with source IP | `TestAuthentication` |
| 26 | Non-root container | Dockerfile runs as UID 10001 | Dockerfile; CI container smoke test |
| 27 | No secrets in the image or repository | `.gitignore`, `.dockerignore`, Fly secrets | Reviewed; see section 4 |
| 28 | Automated dependency security scanning | Bandit at `-ll` in CI, failing the build | `.github/workflows/ci.yml` |
| 29 | Self-lockout prevention | An admin cannot demote or deactivate themselves | `TestUserAdministration` |
| 30 | Unpredictable receipt URLs | Verification receipts keyed by UUID4, not a sequential id | `app/models/verification.py` |
| 31 | Proxy-aware request scheme | `ProxyFix`, gated on `TRUST_PROXY_HEADERS` (off by default, on in production) | `TestProxyAwareness` (4 tests) |
| 32 | Strict CSRF Referer checking | Flask-WTF, active over HTTPS once the scheme is correct (see 5.1) | Verified live -- `reports/deployment-verification.md` |

## 2. Authentication and session design

Sign-in accepts a username or an email address. Both lookups are
case-insensitive and go through one code path, so timing and messaging are the
same either way.

On failure the system: writes a `login.failure` audit entry with the attempted
identifier and source IP, increments `failed_login_count` when the account
exists, and returns the single message *"Invalid username or password."* The
increment happens only for a real account, but this is not observable from the
response — the message and status are identical, and no timing branch is
introduced before the response.

On success it resets the failure counter, stamps `last_login_at`, and writes a
`login.success` entry.

Sessions use Flask-Login's `strong` protection, which invalidates a session
whose client identity changes, limiting the value of a stolen cookie.

## 3. Authorisation model

Authorisation is checked **twice, at two layers**:

1. **Route layer** — `@roles_required(...)` returns 403 before the view runs.
2. **Service layer** — `QualificationService._assert_can_issue`,
   `UserService._assert_admin` and the explicit admin check in `reinstate`.

The duplication is deliberate. The decorator is what a reader sees, but a new
route that forgets it, or a service called from the CLI, still cannot perform a
privileged action. `test_security.py` asserts the route layer; the service unit
tests assert the service layer independently.

`Role.ADMIN` satisfies every role check via `User.has_role`, so privilege is
decided in exactly one place.

## 4. Secret management

- No secret is committed. `.gitignore` excludes `.env`, `*.pem`, `*.key` and
  local databases; `.dockerignore` keeps them out of the image.
- `.env.example` documents every variable with placeholder values only.
- `ProductionConfig` **raises at start-up** if `SECRET_KEY` is missing, empty or
  still the development placeholder, and if `DATABASE_URL` is missing. A
  misconfigured production deployment fails loudly instead of running insecurely.
- Fly.io secrets (`flyctl secrets set`) are encrypted at rest and injected as
  environment variables; they never enter the repository or the image layers.
- `FLY_API_TOKEN` lives in GitHub Actions secrets.
- `flask create-admin` takes the password from an interactive prompt, so it
  never appears in shell history.
- `flask seed-demo` reads passwords from the environment or generates strong
  random ones and prints them once. No demo password is hard-coded.

## 5. The Content Security Policy and its one compromise

```
default-src 'self';
script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
font-src 'self' data:;
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

`'unsafe-inline'` is present because Tailwind's play CDN generates styles at
runtime. This is a **real weakening** of the XSS protection a strict CSP would
give, accepted to avoid a build toolchain in a project of this size. It is
honest to state the consequence: the CSP does not protect against injected
inline script.

The mitigation is that Jinja2 autoescapes all template output by default and
the application renders no user-supplied HTML anywhere. Removing this compromise
means compiling Tailwind at build time and dropping `'unsafe-inline'` — this is
recorded as a task in the collaboration plan.

### 5.1 A control that was silently inactive in production

Flask-WTF applies a strict `Referer` check to CSRF-protected POSTs **only when
the request is secure**. Because TLS terminates at Fly's edge, the application
considered every request to be plain HTTP, so this check had never been active
in the deployed system. Applying `ProxyFix` (control 31) turned it on — the same
defect that suppressed HSTS was also disabling a CSRF control.

The lesson generalises: a control whose behaviour depends on the request scheme
cannot be assumed to work in production merely because its unit test passes
locally. See `reports/deployment-verification.md` §4 for how this was found.

## 6. Verification and privacy

The verification response is deliberately minimal:

- **INVALID** returns no register data at all — not even a hint that a similar
  reference exists. `VerificationService.verify` sets
  `qualification=None` for this result before rendering.
- **VALID / EXPIRED / REVOKED** return only holder name, title, institution and
  award date: the facts printed on the certificate the verifier is already
  holding. Holder email, issuing officer and internal identifiers are not
  released to a verifier.
- A malformed reference is treated as INVALID rather than as an error, so the
  response does not tell an attacker which references are even well-formed.

## 7. Known gaps and accepted risks

These are stated plainly rather than omitted:

| Gap | Risk | Why it stands / how to close it |
| --- | --- | --- |
| No account lockout | Online password guessing is slowed only by the 10/min rate limit | Failures are counted and audited; adding a lockout threshold is a task in the collaboration plan |
| Rate limiting is in-memory | Limits are per-process, so a multi-machine deployment weakens them | Acceptable at `min_machines_running = 1`; needs a Redis storage backend to scale |
| `'unsafe-inline'` in the CSP | Weakens XSS defence | See section 5 |
| No multi-factor authentication | A stolen password is sufficient to sign in | Out of scope for this delivery |
| Audit immutability is application-level | A database superuser can still alter rows | Closing this needs database-level permissions or append-only storage |
| No automated dependency-vulnerability scanning | A known-vulnerable dependency could go unnoticed | Bandit scans our code, not our dependencies; adding `pip-audit` to CI is a task in the collaboration plan |
| No password reset flow | A locked-out user needs an administrator | Deliberate: an email-based reset would add an unauthenticated attack surface |
| Verification requires authentication | A third party holding only a reference cannot self-serve | Deliberate: anonymous checks would make the audit trail unattributable |

## 8. Testing the controls

Security is not asserted only in prose. `tests/integration/test_security.py`
carries the `security` marker and covers authentication requirements,
role-based access control, response headers, information disclosure, SQL
injection, CSRF, open redirects and production configuration guards.

```bash
pytest -m security -v
```

Every one of these runs in CI on every push and pull request, so a change that
weakens a control fails the build rather than reaching main.

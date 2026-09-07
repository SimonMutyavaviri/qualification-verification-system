# Requirements Specification

Qualification Verification System (QVS) — MIM736 Practical Assignment

---

## 1. Problem context

Employers, professional bodies and admitting institutions routinely need to
establish that a qualification a candidate claims is genuine, was awarded by
the body named on it, and has not since been withdrawn. The manual process —
telephoning a registry, emailing a transcript request — is slow, hard to audit,
and easy to defeat with a convincing forgery.

The system addresses this by holding a register of issued credentials, exposing
a verification check against that register, and keeping an auditable record of
every check performed.

## 2. Stakeholders

| Stakeholder | Interest |
| --- | --- |
| Awarding institution | Wants its credentials verifiable and forgeries detectable |
| Qualification issuer (registry officer) | Registers and maintains credential records |
| Verifier (employer, admissions officer) | Needs a fast, trustworthy yes/no answer |
| Administrator | Operates the system, manages access, oversees the audit trail |
| Credential holder | Wants their genuine award confirmed quickly and not over-disclosed |

## 3. User roles and permissions

| Capability | Verifier | Issuer | Administrator |
| --- | :---: | :---: | :---: |
| Sign in / out | Yes | Yes | Yes |
| Change own password | Yes | Yes | Yes |
| Verify a credential | Yes | Yes | Yes |
| View own verification history | Yes | Yes | Yes |
| View all verification history | No | Yes | Yes |
| Search the register | Yes | Yes | Yes |
| View qualification detail | Yes | Yes | Yes |
| Register a qualification | No | Yes | Yes |
| Edit a qualification | No | Yes | Yes |
| Revoke a qualification | No | Yes | Yes |
| Reinstate a revoked qualification | No | No | Yes |
| Manage users | No | No | Yes |
| Manage institutions | No | No | Yes |
| View the audit trail | No | No | Yes |
| View the review assistant | No | Yes | Yes |

Administrators satisfy every role check: the role model treats `ADMIN` as a
superset rather than a parallel role, so there is one place where privilege is
decided (`User.has_role`).

## 4. Functional requirements

Each requirement has an ID used throughout the traceability matrix
(`docs/requirements-traceability.md`) and the test-case document.

### 4.1 Authentication and access control

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-AUTH-01 | A user shall sign in with a username or email address and a password | Must |
| FR-AUTH-02 | Passwords shall be stored only as salted one-way hashes | Must |
| FR-AUTH-03 | A failed sign-in shall not reveal whether the account exists | Must |
| FR-AUTH-04 | A deactivated account shall be refused sign-in | Must |
| FR-AUTH-05 | Every page except sign-in and the health probe shall require authentication | Must |
| FR-AUTH-06 | Access shall be restricted by role as specified in section 3 | Must |
| FR-AUTH-07 | A user shall be able to change their own password | Should |
| FR-AUTH-08 | A new password shall meet the password policy (FR-VAL-07) | Must |
| FR-AUTH-09 | A user shall be able to sign out, ending the session | Must |

### 4.2 Qualification management

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-QUAL-01 | An issuer shall register a qualification with title, type, holder, institution and award date | Must |
| FR-QUAL-02 | Each qualification shall carry a unique credential ID | Must |
| FR-QUAL-03 | The system shall generate a credential ID when one is not supplied | Should |
| FR-QUAL-04 | Registering a credential ID that already exists shall be refused | Must |
| FR-QUAL-05 | A qualification shall record an optional expiry date | Must |
| FR-QUAL-06 | The register shall be searchable by credential ID, holder name and title | Must |
| FR-QUAL-07 | The register shall be filterable by status, type and institution | Should |
| FR-QUAL-08 | Search results shall be paginated | Should |
| FR-QUAL-09 | An issuer shall edit the mutable fields of a qualification | Must |
| FR-QUAL-10 | Credential ID, award date, institution and issuer shall be immutable after registration | Must |
| FR-QUAL-11 | An issuer shall revoke a qualification, recording a mandatory reason | Must |
| FR-QUAL-12 | A revoked qualification shall not be editable | Should |
| FR-QUAL-13 | An administrator shall reinstate a revoked qualification with a reason | Could |

### 4.3 Verification

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-VER-01 | The system shall verify a credential by its reference and return VALID, INVALID, REVOKED or EXPIRED | Must |
| FR-VER-02 | An unregistered reference shall return INVALID | Must |
| FR-VER-03 | A revoked credential shall return REVOKED | Must |
| FR-VER-04 | A credential past its expiry date shall return EXPIRED | Must |
| FR-VER-05 | Revocation shall take precedence over expiry | Must |
| FR-VER-06 | The result shall be communicated unambiguously in the interface | Must |
| FR-VER-07 | An INVALID result shall disclose no register data | Must |
| FR-VER-08 | Every verification attempt shall create a persistent verification record | Must |
| FR-VER-09 | Each verification shall have a unique reference usable as a receipt | Should |
| FR-VER-10 | Verification history shall be viewable and filterable | Must |
| FR-VER-11 | A verifier shall see only their own verification history | Should |
| FR-VER-12 | Credential lookup shall be case-insensitive | Should |

### 4.4 Audit

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-AUD-01 | Every verification attempt shall create an audit entry | Must |
| FR-AUD-02 | Sign-in success, sign-in failure and sign-out shall be audited | Must |
| FR-AUD-03 | Qualification creation, update, revocation and reinstatement shall be audited | Must |
| FR-AUD-04 | User and institution administration shall be audited | Must |
| FR-AUD-05 | A denied access attempt shall be audited | Should |
| FR-AUD-06 | Each entry shall record action, actor, timestamp, entity and source IP | Must |
| FR-AUD-07 | Audit entries shall not be modifiable through the application | Must |
| FR-AUD-08 | Audit entries shall not be deletable through the application | Must |
| FR-AUD-09 | An administrator shall browse and filter the audit trail | Must |

### 4.5 Validation

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-VAL-01 | Required fields shall be enforced | Must |
| FR-VAL-02 | Credential IDs shall match `PREFIX-YYYY-XXXXXX` | Must |
| FR-VAL-03 | Duplicate credential IDs shall be rejected | Must |
| FR-VAL-04 | An award date shall not be in the future or before 1900 | Must |
| FR-VAL-05 | An expiry date shall not precede its award date | Must |
| FR-VAL-06 | Email addresses shall be format-checked | Must |
| FR-VAL-07 | Passwords shall be at least 12 characters with upper case, lower case and a digit | Must |
| FR-VAL-08 | Qualification type shall be one of the supported values | Must |
| FR-VAL-09 | Institution references shall exist and be active | Must |
| FR-VAL-10 | Validation shall be enforced in the service layer, not only in the form | Must |

### 4.6 Administration

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-ADM-01 | An administrator shall create user accounts with a role | Must |
| FR-ADM-02 | An administrator shall change a user's role | Must |
| FR-ADM-03 | An administrator shall deactivate and reactivate accounts | Must |
| FR-ADM-04 | An administrator shall not remove their own admin role or deactivate themselves | Should |
| FR-ADM-05 | An administrator shall create institutions and set them active or inactive | Must |

### 4.7 Operations

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-OPS-01 | A health endpoint shall report application and database status | Must |
| FR-OPS-02 | The health endpoint shall return 503 when the database is unreachable | Must |
| FR-OPS-03 | An authenticated metrics endpoint shall expose system counters | Should |
| FR-OPS-04 | The dashboard shall display live counters | Could |

### 4.8 Bonus

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-BON-01 | A rule-based review assistant shall score a qualification for signals warranting human review | Could |
| FR-BON-02 | Each signal shall state, in plain language, why it triggered | Could |

## 5. Non-functional requirements

| ID | Requirement | How it is met |
| --- | --- | --- |
| NFR-SEC-01 | Passwords never stored in plaintext | PBKDF2-SHA256 via Werkzeug |
| NFR-SEC-02 | Protection against CSRF | Flask-WTF on every state-changing form |
| NFR-SEC-03 | Protection against SQL injection | SQLAlchemy parameterised queries throughout |
| NFR-SEC-04 | Security response headers | `apply_security_headers` on every response |
| NFR-SEC-05 | Rate limiting on sign-in and verification | Flask-Limiter |
| NFR-SEC-06 | Secrets only from the environment | `app/config.py`; production refuses to start without them |
| NFR-SEC-07 | No stack traces in production responses | Central error handlers; `DEBUG=False` |
| NFR-SEC-08 | No open redirect on sign-in | `_safe_next` rejects absolute URLs |
| NFR-QUA-01 | Test coverage at or above 85% | `--cov-fail-under=85`, enforced in CI |
| NFR-QUA-02 | Consistent code style | Black and Ruff, enforced in CI |
| NFR-QUA-03 | No medium or high severity security findings | Bandit `-ll`, enforced in CI |
| NFR-USE-01 | Usable on a phone as well as a desktop | Responsive Tailwind layout |
| NFR-USE-02 | Accessible markup | Semantic HTML, form labels, ARIA landmarks, `prefers-reduced-motion` |
| NFR-MNT-01 | Separation of concerns | Routes → services → repositories → models |
| NFR-OPS-01 | Reproducible deployment | Docker image built and smoke-tested in CI |
| NFR-OPS-02 | Zero-downtime releases | Fly.io rolling strategy with health checks |

## 6. Assumptions and constraints

- **Assumption.** Institutions are trusted to register accurate data; the system
  verifies that a credential *was issued and is still valid*, not that the
  underlying academic work was performed.
- **Assumption.** Verifiers are authenticated users, not the anonymous public.
  This is what makes the audit trail meaningful — an anonymous check would be
  recorded but not attributable.
- **Constraint.** Python and Flask, per the assignment's stack.
- **Constraint.** A single deployed instance; horizontal scale-out is possible
  but not part of this delivery.
- **Out of scope.** Bulk import of legacy records, holder self-service portal,
  document/certificate image storage, cryptographic credential signing.

## 7. Requirement verification approach

Every "Must" requirement is verified by at least one automated test, and every
test runs in CI on every push and pull request. The mapping from requirement to
test to CI check is in `docs/requirements-traceability.md`. A requirement whose
test fails blocks the merge, which is what makes the verification automatic
rather than aspirational.

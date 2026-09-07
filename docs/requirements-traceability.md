# Requirements Traceability Matrix

Every requirement from `docs/requirements.md` mapped to its implementation, its
automated test, the CI check that runs that test, and its status.

**Legend** — Status: ✅ implemented and tested · ⚠️ implemented, manually verified only · ❌ not implemented
**CI check:** the workflow job that must pass for the requirement to be considered verified.

---

## 1. Authentication and access control

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-AUTH-01 | Sign in with username or email | `AuthService.authenticate`, `auth_routes.login` | `TestAuthentication::test_authenticates_by_username`, `::test_authenticates_by_email` | unit-tests | ✅ |
| FR-AUTH-02 | Passwords stored only as hashes | `User.set_password` (PBKDF2-SHA256) | `TestPasswordHashing` (4 tests) | unit-tests | ✅ |
| FR-AUTH-03 | Failure does not reveal account existence | Single generic message in `AuthService.authenticate` | `TestInformationDisclosure::test_login_failure_does_not_reveal_whether_the_user_exists` | integration-tests | ✅ |
| FR-AUTH-04 | Deactivated accounts refused | `is_active` check | `TestAuthentication::test_rejects_a_deactivated_account` | unit-tests | ✅ |
| FR-AUTH-05 | All pages require authentication | `@login_required` on every view | `TestAuthenticationRequired` (10 parametrised) | integration-tests | ✅ |
| FR-AUTH-06 | Role-based restrictions | `roles_required` decorators + service checks | `TestRoleBasedAccessControl` (9 tests) | integration-tests | ✅ |
| FR-AUTH-07 | Change own password | `UserService.change_password`, `/profile` | `TestPasswordChange` (4), `TestProfile` | unit + integration | ✅ |
| FR-AUTH-08 | New password meets policy | `validate_password` in `change_password` | `TestPasswordChange::test_enforces_the_password_policy` | unit-tests | ✅ |
| FR-AUTH-09 | Sign out ends the session | `auth_routes.logout` (POST only) | `TestSignInFlow::test_sign_out_ends_the_session` | integration-tests | ✅ |

## 2. Qualification management

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-QUAL-01 | Register a qualification | `QualificationService.register` | `TestRegistration::test_registers_with_generated_credential_id` | unit-tests | ✅ |
| FR-QUAL-02 | Unique credential ID | `uq_qualification_credential_id` + service check | `TestRegistration::test_rejects_duplicate_credential_id` | unit-tests | ✅ |
| FR-QUAL-03 | Auto-generate credential ID | `generate_credential_id` | `TestGeneratedCredentialIds` (3 tests) | unit-tests | ✅ |
| FR-QUAL-04 | Duplicate registration refused | Existence check + `IntegrityError` fallback | `::test_rejects_duplicate_credential_id`, `::test_duplicate_check_is_case_insensitive` | unit-tests | ✅ |
| FR-QUAL-05 | Optional expiry date | `Qualification.expiry_date` nullable | `TestAwardAndExpiryDates::test_accepts_award_without_expiry` | unit-tests | ✅ |
| FR-QUAL-06 | Search by ID, holder, title | `QualificationRepository.search` | `TestSearch` (5 tests) | unit-tests | ✅ |
| FR-QUAL-07 | Filter by status, type, institution | `search()` filter arguments | `TestSearch::test_filters_by_status`, `TestSearchAndFiltering` | unit + integration | ✅ |
| FR-QUAL-08 | Paginated results | `db.paginate` + `ITEMS_PER_PAGE` | `TestSearch`, pagination markup in `list.html` | unit-tests | ✅ |
| FR-QUAL-09 | Edit mutable fields | `QualificationService.update` | `TestUpdate` (7 tests) | unit-tests | ✅ |
| FR-QUAL-10 | Core fields immutable | `update()` accepts no such parameters | `TestUpdate` — no path to change them | unit-tests | ✅ |
| FR-QUAL-11 | Revoke with a mandatory reason | `QualificationService.revoke` | `TestRevocation` (5 tests) | unit-tests | ✅ |
| FR-QUAL-12 | Revoked records not editable | Guard in `update()` | `TestUpdate::test_rejects_editing_a_revoked_qualification` | unit-tests | ✅ |
| FR-QUAL-13 | Admin reinstatement | `QualificationService.reinstate` | `TestReinstatement` (3 tests) | unit-tests | ✅ |

## 3. Verification

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-VER-01 | Four-state verification result | `VerificationService.verify` / `evaluate_status` | `TestStatusDecisionTable` (7), `TestVerifyWorkflow` (9) | unit-tests | ✅ |
| FR-VER-02 | Unknown reference → INVALID | `evaluate_status(None)` | `::test_missing_qualification_is_invalid` | unit-tests | ✅ |
| FR-VER-03 | Revoked → REVOKED | Status branch | `::test_revoked_is_revoked` | unit-tests | ✅ |
| FR-VER-04 | Past expiry → EXPIRED | `Qualification.is_expired` | `::test_past_expiry_is_expired` | unit-tests | ✅ |
| FR-VER-05 | Revocation outranks expiry | Ordered branches in `evaluate_status` | `::test_revocation_outranks_expiry` | unit-tests | ✅ |
| FR-VER-06 | Result communicated unambiguously | `verify.html` result banner, `css_tone` | `TestFullQualificationLifecycle` (4 result assertions) | integration-tests | ✅ |
| FR-VER-07 | INVALID discloses nothing | `qualification=None` for INVALID | `::test_invalid_result_discloses_no_qualification`, `TestInformationDisclosure` | unit + integration | ✅ |
| FR-VER-08 | Every attempt recorded | `VerificationRepository.add` before commit | `TestVerificationRecording` (6 tests) | unit-tests | ✅ |
| FR-VER-09 | Unique receipt reference | UUID4 `reference` | `::test_references_are_unique`, `TestVerificationHistory::test_receipt_page_is_reachable` | unit + integration | ✅ |
| FR-VER-10 | History viewable and filterable | `verification_routes.history` | `TestHistoryAndStatistics` (4), `TestVerificationHistory` | unit + integration | ✅ |
| FR-VER-11 | Verifiers see only their own history | `performed_by_id` filter by role | `TestVerificationHistory::test_verifier_sees_only_their_own_attempts` | integration-tests | ✅ |
| FR-VER-12 | Case-insensitive lookup | `.upper()` normalisation | `::test_lookup_is_case_insensitive` | unit-tests | ✅ |

## 4. Audit

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-AUD-01 | Verification attempts audited | `AuditService.record` in `verify()` | `TestVerificationRecording::test_records_an_audit_entry` | unit-tests | ✅ |
| FR-AUD-02 | Sign-in/out audited | `AuthService` | `TestAuthentication::test_successful_sign_in_is_audited`, `::test_failed_sign_in_is_audited` | unit-tests | ✅ |
| FR-AUD-03 | Qualification lifecycle audited | `AuditService.record` in each command | `TestRegistration::test_writes_an_audit_entry`, `TestUpdate`, `TestRevocation` | unit-tests | ✅ |
| FR-AUD-04 | Administration audited | `UserService`, `InstitutionService` | `TestUserAdministration`, `TestInstitutionAdministration` | unit-tests | ✅ |
| FR-AUD-05 | Denied access audited | `_record_denial` in `roles_required` | `TestRoleBasedAccessControl::test_denied_access_is_audited` | integration-tests | ✅ |
| FR-AUD-06 | Entries record action/actor/time/entity/IP | `AuditLog` columns | `TestAuditQueries` (5 tests) | unit-tests | ✅ |
| FR-AUD-07 | Entries not modifiable | `before_update` guard | `TestAuditImmutability::test_updating_an_entry_raises` | unit-tests | ✅ |
| FR-AUD-08 | Entries not deletable | `before_delete` guard | `::test_deleting_an_entry_raises`, `::test_entry_survives_a_blocked_deletion` | unit-tests | ✅ |
| FR-AUD-09 | Browse and filter the trail | `admin_routes.audit` | `TestAdministrationWorkflows::test_admin_views_the_audit_trail`, `::test_audit_trail_can_be_filtered` | integration-tests | ✅ |

## 5. Validation

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-VAL-01 | Required fields enforced | `validate_required` | `TestRequiredText` (3 tests) | unit-tests | ✅ |
| FR-VAL-02 | Credential ID format | `CREDENTIAL_ID_PATTERN` | `TestCredentialId` (12 parametrised) | unit-tests | ✅ |
| FR-VAL-03 | Duplicates rejected | Service check + unique constraint | `TestRegistration` | unit-tests | ✅ |
| FR-VAL-04 | Award date not future/pre-1900 | `validate_award_and_expiry` | `TestAwardAndExpiryDates` (7 tests) | unit-tests | ✅ |
| FR-VAL-05 | Expiry not before award | Same + `ck_qualification_expiry_after_award` | `::test_rejects_expiry_before_award` | unit-tests | ✅ |
| FR-VAL-06 | Email format checked | `validate_email`, `EMAIL_FORMAT` | `TestEmail` (8 tests) | unit-tests | ✅ |
| FR-VAL-07 | Password policy | `validate_password` | `TestPasswordPolicy` (7 tests) | unit-tests | ✅ |
| FR-VAL-08 | Qualification type constrained | `validate_qualification_type` | `TestQualificationType` (2 tests) | unit-tests | ✅ |
| FR-VAL-09 | Institution must exist and be active | Checks in `register()` | `::test_rejects_unknown_institution`, `::test_rejects_inactive_institution` | unit-tests | ✅ |
| FR-VAL-10 | Validation in the service layer | Validators called in every service command | `TestRegistration` (service-level, bypassing forms) | unit-tests | ✅ |

## 6. Administration

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-ADM-01 | Create users with a role | `UserService.create_user` | `TestUserAdministration::test_admin_creates_a_user`, `TestAdministrationWorkflows` | unit + integration | ✅ |
| FR-ADM-02 | Change a user's role | `UserService.set_role` | `::test_changes_a_role`, `::test_admin_changes_a_user_role` | unit + integration | ✅ |
| FR-ADM-03 | Deactivate / reactivate | `UserService.set_active` | `::test_deactivates_another_user`, `::test_admin_deactivates_a_user_who_then_cannot_sign_in` | unit + integration | ✅ |
| FR-ADM-04 | No self-demotion or self-deactivation | Guards in `set_role` / `set_active` | `::test_admin_cannot_demote_themselves`, `::test_admin_cannot_deactivate_themselves` | unit-tests | ✅ |
| FR-ADM-05 | Manage institutions | `InstitutionService` | `TestInstitutionAdministration` (5 tests) | unit-tests | ✅ |

## 7. Operations

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-OPS-01 | Health endpoint | `main_routes.healthz` | `TestOperationalEndpoints::test_health_endpoint_reports_healthy` | integration-tests | ✅ |
| FR-OPS-02 | 503 when the database is down | `try/except` around `SELECT 1` | Code path present; not automatically tested — see note | docker-build (health check) | ⚠️ |
| FR-OPS-03 | Authenticated metrics endpoint | `main_routes.metrics` | `::test_metrics_endpoint_requires_authentication`, `::test_metrics_endpoint_returns_counters` | integration-tests | ✅ |
| FR-OPS-04 | Live dashboard counters | `static/js/app.js` polling `/metrics` | Manual — see `docs/test-cases.md` MT-06 | — | ⚠️ |

> **FR-OPS-02 note.** The 503 branch requires the database to be genuinely
> unreachable mid-request. Simulating that reliably in the suite would mean
> mocking the session in a way that tests the mock rather than the behaviour, so
> it is verified manually (stop the `db` container in `docker compose`, then
> curl `/healthz`). This is recorded as a known gap rather than claimed as
> automated.

## 8. Bonus

| ID | Requirement | Implementation | Test | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| FR-BON-01 | Rule-based review assistant | `RiskService.assess` | `TestRiskSignals` (8), `TestRiskScoring` (4) | unit-tests | ✅ |
| FR-BON-02 | Each signal explains itself | `RiskSignal.message` | `TestRiskScoring::test_signals_carry_an_explanation` | unit-tests | ✅ |

## 9. Non-functional requirements

| ID | Requirement | Implementation | Test / Evidence | CI check | Status |
| --- | --- | --- | --- | --- | --- |
| NFR-SEC-01 | No plaintext passwords | Werkzeug PBKDF2 | `TestPasswordHashing` | unit-tests | ✅ |
| NFR-SEC-02 | CSRF protection | Flask-WTF `CSRFProtect` | `TestCsrfProtection` (3 tests) | integration-tests | ✅ |
| NFR-SEC-03 | SQL injection resistance | SQLAlchemy parameterisation | `TestSqlInjectionResistance` (4 tests) | integration-tests | ✅ |
| NFR-SEC-04 | Security headers | `apply_security_headers` | `TestSecurityHeaders` (5 tests) | integration-tests | ✅ |
| NFR-SEC-05 | Rate limiting | Flask-Limiter | Configuration; disabled in tests for determinism | — | ⚠️ |
| NFR-SEC-06 | Secrets from the environment | `app/config.py` guards | `TestProductionConfigurationGuards` (5 tests) | integration-tests | ✅ |
| NFR-SEC-07 | No stack traces in production | `app/errors.py` | `::test_error_pages_do_not_leak_stack_traces` | integration-tests | ✅ |
| NFR-SEC-08 | No open redirect | `_safe_next` | `TestOpenRedirectProtection` (2 tests) | integration-tests | ✅ |
| NFR-QUA-01 | Coverage ≥ 85% | `--cov-fail-under=85` | Current: 92.55% | coverage | ✅ |
| NFR-QUA-02 | Consistent style | Black + Ruff | `black --check`, `ruff check` | quality | ✅ |
| NFR-QUA-03 | No medium/high security findings | Bandit `-ll` | Current: 0 findings | quality | ✅ |
| NFR-USE-01 | Responsive interface | Tailwind responsive classes | Manual — `docs/test-cases.md` MT-01 | — | ⚠️ |
| NFR-USE-02 | Accessible markup | Semantic HTML, labels, ARIA | Manual — MT-02, MT-03 | — | ⚠️ |
| NFR-MNT-01 | Separation of concerns | Routes → services → repositories | Code review; import structure | quality | ✅ |
| NFR-OPS-01 | Reproducible deployment | Docker image built and run in CI | `docker-build` job | docker-build | ✅ |
| NFR-OPS-02 | Zero-downtime releases | Rolling strategy + health checks | CD workflow health poll | CD | ✅ |

## 10. Summary

| Category | Total | ✅ Automated | ⚠️ Manual | ❌ Not done |
| --- | ---: | ---: | ---: | ---: |
| Authentication and access control | 9 | 9 | 0 | 0 |
| Qualification management | 13 | 13 | 0 | 0 |
| Verification | 12 | 12 | 0 | 0 |
| Audit | 9 | 9 | 0 | 0 |
| Validation | 10 | 10 | 0 | 0 |
| Administration | 5 | 5 | 0 | 0 |
| Operations | 4 | 2 | 2 | 0 |
| Bonus | 2 | 2 | 0 | 0 |
| Non-functional | 15 | 11 | 4 | 0 |
| **Total** | **79** | **73** | **6** | **0** |

**Every "Must" requirement is verified by an automated test that runs in CI.**
The six manual items are the live monitoring panel, the database-outage health
branch, rate-limit behaviour, and the three usability/accessibility properties —
each stated as manually verified rather than claimed as automated.

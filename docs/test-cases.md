# Test Case Document

Formal test cases for the Qualification Verification System.

- **Automated cases (AT-*)** are executed by `pytest` on every CI run. "Actual
  result" records the outcome of the run of 7 September 2026: **255 passed,
  92.55% coverage**.
- **Manual cases (MT-*)** cover properties automation cannot check — usability,
  layout, accessibility and the database-outage path.
- **Security cases (ST-*)** carry the `security` marker.

Evidence placeholders mark where the team attaches screenshots.

---

## 1. Authentication

| ID | Requirement | Preconditions | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AT-01 | FR-AUTH-01 | An active user exists | Authenticate with the correct username and password | The user object is returned | As expected | Pass | `test_authenticates_by_username` |
| AT-02 | FR-AUTH-01 | As above | Authenticate with the email address instead | The user object is returned | As expected | Pass | `test_authenticates_by_email` |
| AT-03 | FR-AUTH-01 | As above | Authenticate with the username in upper case | The user object is returned | As expected | Pass | `test_username_match_is_case_insensitive` |
| AT-04 | FR-AUTH-02 | A user has been created | Inspect `password_hash` | The plaintext password does not appear in the hash | As expected | Pass | `test_password_is_not_stored_in_plaintext` |
| AT-05 | FR-AUTH-02 | As above | Set the same password twice and compare the hashes | The hashes differ (salted) | As expected | Pass | `test_the_same_password_hashes_differently_each_time` |
| AT-06 | FR-AUTH-03 | A user exists | Authenticate with a wrong password | `ValidationError`, "Invalid username or password." | As expected | Pass | `test_rejects_a_wrong_password` |
| AT-07 | FR-AUTH-03 | — | Authenticate as a non-existent user | The **identical** message and code path | As expected | Pass | `test_unknown_user_gets_the_same_message_as_a_wrong_password` |
| AT-08 | FR-AUTH-04 | A user with `is_active=False` | Authenticate with the correct password | Refused, "This account has been deactivated." | As expected | Pass | `test_rejects_a_deactivated_account` |
| AT-09 | FR-AUD-02 | A user exists | Sign in successfully | A `login.success` audit entry is written | As expected | Pass | `test_successful_sign_in_is_audited` |
| AT-10 | FR-AUD-02 | A user exists | Sign in with a wrong password | A `login.failure` audit entry is written | As expected | Pass | `test_failed_sign_in_is_audited` |
| AT-11 | FR-AUTH-01 | A user exists | Fail three times in a row | `failed_login_count == 3` | As expected | Pass | `test_failed_attempts_are_counted` |
| AT-12 | FR-AUTH-01 | Following AT-11 | Sign in successfully | The counter resets to 0 | As expected | Pass | `test_successful_sign_in_resets_the_failure_counter` |
| AT-13 | FR-AUTH-09 | Signed in | POST `/logout` | Session ends; `/dashboard` redirects to sign-in | As expected | Pass | `test_sign_out_ends_the_session` |
| AT-14 | FR-AUTH-07 | Signed in | Change password with the correct current password | The new password authenticates | As expected | Pass | `test_changes_the_password` |
| AT-15 | FR-AUTH-07 | Signed in | Change password with the wrong current password | Refused, "Your current password is incorrect." | As expected | Pass | `test_rejects_a_wrong_current_password` |
| AT-16 | FR-AUTH-08 | Signed in | Change to the same password | Refused, "must differ" | As expected | Pass | `test_rejects_reusing_the_current_password` |

## 2. Validation

| ID | Requirement | Input | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| AT-17 | FR-VAL-02 | `QVS-2024-A1B2C3` | Accepted, normalised | As expected | Pass | `TestCredentialId` |
| AT-18 | FR-VAL-02 | `qvs-2024-a1b2c3` | Accepted, upper-cased | As expected | Pass | `TestCredentialId` |
| AT-19 | FR-VAL-02 | `QVS2024A1B2C3` (no separators) | `ValidationError` | As expected | Pass | `TestCredentialId` |
| AT-20 | FR-VAL-02 | `QVS-24-A1B2C3` (short year) | `ValidationError` | As expected | Pass | `TestCredentialId` |
| AT-21 | FR-VAL-02 | `QVS-2024-A1B2` (short suffix) | `ValidationError` | As expected | Pass | `TestCredentialId` |
| AT-22 | FR-VAL-02 | `QVS-2024-A1B2C!` (bad character) | `ValidationError` | As expected | Pass | `TestCredentialId` |
| AT-23 | FR-VAL-02 | Empty / whitespace / `None` | `ValidationError` | As expected | Pass | `TestCredentialId` |
| AT-24 | FR-VAL-01 | A blank title | "Title is required." | As expected | Pass | `TestRequiredText` |
| AT-25 | FR-VAL-01 | A title over the length limit | "must be N characters or fewer" | As expected | Pass | `TestRequiredText` |
| AT-26 | FR-VAL-08 | Type `Honorary Doctorate` | "must be one of…" | As expected | Pass | `TestQualificationType` |
| AT-27 | FR-VAL-06 | `not-an-email`, `@example.com`, `a b@c.com` | `ValidationError` | As expected | Pass | `TestEmail` |
| AT-28 | FR-VAL-06 | `Person@Example.COM` | Accepted, lower-cased | As expected | Pass | `TestEmail` |
| AT-29 | FR-VAL-07 | `Short1a` (7 chars) | "at least 12 characters" | As expected | Pass | `TestPasswordPolicy` |
| AT-30 | FR-VAL-07 | `alllowercase123` | "uppercase letter" | As expected | Pass | `TestPasswordPolicy` |
| AT-31 | FR-VAL-07 | `ALLUPPERCASE123` | "lowercase letter" | As expected | Pass | `TestPasswordPolicy` |
| AT-32 | FR-VAL-07 | `NoDigitsInHere` | "one digit" | As expected | Pass | `TestPasswordPolicy` |
| AT-33 | FR-VAL-04 | Award date tomorrow | "cannot be in the future" | As expected | Pass | `TestAwardAndExpiryDates` |
| AT-34 | FR-VAL-04 | Award date 1899-12-31 | "earlier than 1900" | As expected | Pass | `TestAwardAndExpiryDates` |
| AT-35 | FR-VAL-05 | Expiry before award | "on or after the award date" | As expected | Pass | `TestAwardAndExpiryDates` |
| AT-36 | FR-VAL-05 | Expiry equal to award | Accepted (boundary) | As expected | Pass | `TestAwardAndExpiryDates` |

## 3. Qualification management

| ID | Requirement | Preconditions | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AT-37 | FR-QUAL-01 | Signed in as issuer | Register with valid data, ID blank | Created, `ACTIVE`, ID generated | As expected | Pass | `test_registers_with_generated_credential_id` |
| AT-38 | FR-QUAL-03 | — | Generate 50 credential IDs | All 50 unique | As expected | Pass | `test_ids_are_unique_across_many_calls` |
| AT-39 | FR-QUAL-03 | — | Inspect a generated ID | Contains no `O`, `0`, `I` or `1` | As expected | Pass | `test_id_avoids_ambiguous_characters` |
| AT-40 | FR-QUAL-04 | A credential exists | Register the same ID again | `DuplicateCredentialError` | As expected | Pass | `test_rejects_duplicate_credential_id` |
| AT-41 | FR-QUAL-04 | As above | Register it in lower case | `DuplicateCredentialError` | As expected | Pass | `test_duplicate_check_is_case_insensitive` |
| AT-42 | FR-AUTH-06 | Signed in as verifier | Attempt to register | `PermissionDeniedError` | As expected | Pass | `test_rejects_verifier` |
| AT-43 | FR-VAL-09 | — | Register against institution id 9999 | "does not exist" | As expected | Pass | `test_rejects_unknown_institution` |
| AT-44 | FR-VAL-09 | Institution deactivated | Register against it | "not active" | As expected | Pass | `test_rejects_inactive_institution` |
| AT-45 | FR-AUD-03 | Issuer signed in | Register a qualification | `qualification.created` audit entry | As expected | Pass | `test_writes_an_audit_entry` |
| AT-46 | FR-QUAL-09 | A qualification exists | Edit the title and holder | Fields updated | As expected | Pass | `test_updates_mutable_fields` |
| AT-47 | FR-AUD-03 | As above | Edit it | Audit detail names the old and new values | As expected | Pass | `test_records_an_audit_entry_describing_the_change` |
| AT-48 | FR-QUAL-09 | As above | "Edit" with unchanged values | No audit entry written | As expected | Pass | `test_no_change_writes_no_audit_entry` |
| AT-49 | FR-QUAL-12 | A revoked qualification | Attempt to edit | "A revoked qualification cannot be edited." | As expected | Pass | `test_rejects_editing_a_revoked_qualification` |
| AT-50 | FR-QUAL-11 | An active qualification | Revoke with a reason | Status `REVOKED`, reason stored | As expected | Pass | `test_revokes_with_a_reason` |
| AT-51 | FR-QUAL-11 | As above | Revoke with a blank reason | "reason is required" | As expected | Pass | `test_requires_a_reason` |
| AT-52 | FR-QUAL-11 | Already revoked | Revoke again | "already revoked" | As expected | Pass | `test_rejects_double_revocation` |
| AT-53 | FR-QUAL-13 | Revoked; signed in as admin | Reinstate with a reason | Status `ACTIVE`, reason cleared | As expected | Pass | `test_admin_can_reinstate` |
| AT-54 | FR-QUAL-13 | Revoked; signed in as issuer | Attempt to reinstate | `PermissionDeniedError` | As expected | Pass | `test_issuer_cannot_reinstate` |
| AT-55 | FR-QUAL-06 | A qualification exists | Search a partial holder name | The record is returned | As expected | Pass | `test_finds_by_partial_holder_name` |
| AT-56 | FR-QUAL-07 | Active and revoked exist | Filter by status = revoked | Only the revoked record | As expected | Pass | `test_filters_by_status` |
| AT-57 | FR-QUAL-06 | Records exist | Search an unmatched term | Zero results, empty state shown | As expected | Pass | `test_returns_nothing_for_an_unmatched_query` |

## 4. Verification

| ID | Requirement | Preconditions | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AT-58 | FR-VER-01 | An active credential | Verify it | `VALID`, details returned | As expected | Pass | `test_valid_credential_returns_valid_with_details` |
| AT-59 | FR-VER-02 | — | Verify an unregistered reference | `INVALID` | As expected | Pass | `test_unknown_credential_returns_invalid` |
| AT-60 | FR-VER-03 | A revoked credential | Verify it | `REVOKED` | As expected | Pass | `test_revoked_credential_returns_revoked` |
| AT-61 | FR-VER-04 | An expired credential | Verify it | `EXPIRED` | As expected | Pass | `test_expired_credential_returns_expired` |
| AT-62 | FR-VER-05 | Revoked **and** expired | Verify it | `REVOKED` (revocation wins) | As expected | Pass | `test_revocation_outranks_expiry` |
| AT-63 | FR-VER-04 | Expiry date is today | Verify it | `VALID` (boundary) | As expected | Pass | `test_expiry_on_the_expiry_date_itself_is_still_valid` |
| AT-64 | FR-VER-12 | An active credential | Verify with the reference in lower case | `VALID` | As expected | Pass | `test_lookup_is_case_insensitive` |
| AT-65 | FR-VER-07 | An active credential exists | Verify an unregistered reference | No qualification returned | As expected | Pass | `test_invalid_result_discloses_no_qualification` |
| AT-66 | FR-VER-01 | — | Verify `not a credential` | `INVALID`, noted as malformed | As expected | Pass | `test_malformed_reference_is_invalid_and_noted` |
| AT-67 | FR-VER-01 | — | Verify a blank reference | `INVALID`, no crash | As expected | Pass | `test_blank_reference_is_handled` |
| AT-68 | FR-VER-08 | An active credential | Verify it | A verification row is created | As expected | Pass | `test_creates_a_verification_record` |
| AT-69 | FR-VER-08 | — | Verify an unregistered reference | A row is **still** created | As expected | Pass | `test_failed_attempt_is_still_recorded` |
| AT-70 | FR-AUD-01 | An active credential | Verify it | A `verification.performed` audit entry | As expected | Pass | `test_records_an_audit_entry` |
| AT-71 | FR-VER-09 | An active credential | Verify five times | Five distinct references | As expected | Pass | `test_references_are_unique` |
| AT-72 | FR-VER-10 | Two verifications performed | List the history | Newest first | As expected | Pass | `test_history_returns_newest_first` |
| AT-73 | FR-VER-10 | Mixed results exist | Filter by `INVALID` | Only invalid attempts | As expected | Pass | `test_history_filters_by_result` |
| AT-74 | FR-VER-11 | Two users have verified | Sign in as verifier, open history | Only that verifier's attempts | As expected | Pass | `test_verifier_sees_only_their_own_attempts` |
| AT-75 | FR-VER-11 | As above | Sign in as issuer, open history | All attempts | As expected | Pass | `test_issuer_sees_all_attempts` |
| AT-76 | FR-VER-09 | A verification exists | Open its receipt URL | The receipt renders | As expected | Pass | `test_receipt_page_is_reachable` |

## 5. Audit

| ID | Requirement | Preconditions | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AT-77 | FR-AUD-07 | An audit entry exists | Modify its `detail` and commit | `ImmutableRecordError` raised | As expected | Pass | `test_updating_an_entry_raises` |
| AT-78 | FR-AUD-08 | An audit entry exists | Delete it and commit | `ImmutableRecordError` raised | As expected | Pass | `test_deleting_an_entry_raises` |
| AT-79 | FR-AUD-08 | Following AT-78 | Count the entries | The entry is still present | As expected | Pass | `test_entry_survives_a_blocked_deletion` |
| AT-80 | FR-AUD-06 | — | Record an entry with a 2000-character detail | Truncated to 1000 | As expected | Pass | `test_detail_is_truncated_to_the_column_width` |
| AT-81 | FR-AUD-06 | No request context | Record an entry | Attributed to `system` | As expected | Pass | `test_entry_is_attributed_to_system_outside_a_request` |
| AT-82 | FR-AUD-06 | Unauthenticated request | Record an entry | Attributed to `anonymous` | As expected | Pass | `test_entry_is_attributed_to_anonymous_for_a_signed_out_request` |
| AT-83 | FR-AUD-09 | Entries exist | Filter by action | Only matching entries | As expected | Pass | `test_filters_by_action` |
| AT-84 | FR-AUD-05 | Signed in as verifier | Request `/admin/users` | 403 **and** an `access.denied` entry | As expected | Pass | `test_denied_access_is_audited` |

## 6. Security (ST-*)

| ID | Requirement | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| ST-01 | FR-AUTH-05 | Request each of 10 protected routes anonymously | 302 to `/login` | As expected | Pass | `TestAuthenticationRequired` |
| ST-02 | FR-AUTH-06 | As issuer, request `/admin/users`, `/admin/institutions`, `/admin/audit` | 403 each | As expected | Pass | `test_issuer_cannot_reach_admin_pages` |
| ST-03 | FR-AUTH-06 | As verifier, request `/admin/users`, `/admin/audit`, `/qualifications/new` | 403 each | As expected | Pass | `test_verifier_cannot_reach_privileged_pages` |
| ST-04 | FR-AUTH-06 | As verifier, **POST** a registration directly | 403; nothing created | As expected | Pass | `test_verifier_cannot_register_a_qualification_by_posting` |
| ST-05 | FR-AUTH-06 | As verifier, POST a revocation | 403; the credential is unchanged | As expected | Pass | `test_verifier_cannot_revoke` |
| ST-06 | NFR-SEC-04 | Inspect response headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` present | As expected | Pass | `TestSecurityHeaders` |
| ST-07 | NFR-SEC-04 | Inspect the CSP | `default-src 'self'`, `frame-ancestors 'none'` | As expected | Pass | `test_content_security_policy_is_set` |
| ST-08 | NFR-SEC-04 | Inspect headers on a 403 | Headers still present | As expected | Pass | `test_headers_are_present_on_error_responses` |
| ST-09 | NFR-SEC-03 | Search `'; DROP TABLE qualifications; --` | Treated as literal text; the table survives | As expected | Pass | `TestSqlInjectionResistance` |
| ST-10 | NFR-SEC-03 | Search `' OR '1'='1` | Zero results (not every row) | As expected | Pass | `TestSqlInjectionResistance` |
| ST-11 | NFR-SEC-03 | Verify `' OR '1'='1` | `INVALID` | As expected | Pass | `test_injection_in_the_verification_field_is_handled` |
| ST-12 | NFR-SEC-02 | GET a state-changing route | 405 Method Not Allowed | As expected | Pass | `test_state_changing_routes_reject_get` |
| ST-13 | NFR-SEC-08 | Sign in with `?next=https://evil.example.com` | Redirect stays on this host | As expected | Pass | `test_external_next_parameter_is_ignored` |
| ST-14 | NFR-SEC-08 | Sign in with `?next=/admin/audit` | Redirected to `/admin/audit` | As expected | Pass | `test_relative_next_parameter_is_honoured` |
| ST-15 | NFR-SEC-07 | Trigger a 404 | No `Traceback` in the response | As expected | Pass | `test_error_pages_do_not_leak_stack_traces` |
| ST-16 | FR-VER-07 | Verify an unknown reference while a record exists | The existing holder's name does not appear | As expected | Pass | `test_invalid_result_reveals_nothing_about_the_register` |
| ST-17 | NFR-SEC-06 | Instantiate `ProductionConfig` with no `SECRET_KEY` | `RuntimeError` | As expected | Pass | `test_production_refuses_a_missing_secret_key` |
| ST-18 | NFR-SEC-06 | Instantiate it with the dev placeholder key | `RuntimeError` | As expected | Pass | `test_production_refuses_the_development_placeholder_key` |
| ST-19 | NFR-SEC-06 | Instantiate it with no `DATABASE_URL` | `RuntimeError` | As expected | Pass | `test_production_requires_a_database_url` |
| ST-20 | NFR-SEC-06 | Instantiate it with `postgres://…` | Normalised to `postgresql+psycopg://` | As expected | Pass | `test_production_normalises_the_postgres_url_scheme` |
| ST-21 | NFR-SEC-07 | Inspect production config | `DEBUG` False, `SESSION_COOKIE_SECURE` True | As expected | Pass | `test_production_disables_debug_and_forces_secure_cookies` |

## 7. Error handling

| ID | Requirement | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| AT-85 | Error handling | Request an unknown URL as a browser | 404 page, "Page not found" | As expected | Pass | `test_404_renders_the_html_page_for_a_browser` |
| AT-86 | Error handling | Request it with `Accept: */*` | HTML page, not JSON | As expected | Pass | `test_wildcard_accept_still_gets_html` |
| AT-87 | Error handling | Request it with `Accept: application/json` | JSON body with `status: 404` | As expected | Pass | `test_404_returns_json_when_json_is_requested` |
| AT-88 | Error handling | GET `/logout` | 405, "Method not allowed" | As expected | Pass | `test_405_is_handled` |
| AT-89 | Error handling | As verifier, GET `/admin/users` | 403, "Access denied" | As expected | Pass | `test_403_renders_the_access_denied_page` |
| AT-90 | NFR-SEC-07 | Inspect a 404 body | The secret key does not appear | As expected | Pass | `test_error_pages_never_expose_the_secret_key` |

## 8. Operations

| ID | Requirement | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| AT-91 | FR-OPS-01 | GET `/healthz` | 200, `status: healthy`, `database: ok` | As expected | Pass | `test_health_endpoint_reports_healthy` |
| AT-92 | FR-OPS-01 | GET `/healthz` anonymously | 200 — no authentication needed | As expected | Pass | `test_health_endpoint_needs_no_authentication` |
| AT-93 | FR-OPS-03 | GET `/metrics` anonymously | 302 to sign-in | As expected | Pass | `test_metrics_endpoint_requires_authentication` |
| AT-94 | FR-OPS-03 | GET `/metrics` signed in | JSON counters | As expected | Pass | `test_metrics_endpoint_returns_counters` |

## 9. Review assistant (bonus)

| ID | Requirement | Preconditions | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| AT-95 | FR-BON-01 | A clean record | Level `low`, no review required | As expected | Pass | `test_clean_record_scores_low` |
| AT-96 | FR-BON-01 | No holder email | `incomplete_holder_contact` flagged | As expected | Pass | `test_missing_holder_email_is_flagged` |
| AT-97 | FR-BON-01 | Award date 70 years ago | `implausible_award_date` flagged | As expected | Pass | `test_implausibly_old_award_date_is_flagged` |
| AT-98 | FR-BON-01 | Expires 5 days after award | `short_validity_window` flagged | As expected | Pass | `test_very_short_validity_window_is_flagged` |
| AT-99 | FR-BON-01 | Expires a year after award | **Not** flagged | As expected | Pass | `test_normal_validity_window_is_not_flagged` |
| AT-100 | FR-BON-01 | Revoked | `revoked_credential` flagged; review required | As expected | Pass | `test_revoked_credential_is_flagged` |
| AT-101 | FR-BON-01 | 6 credentials under one holder name | `high_holder_volume` flagged | As expected | Pass | `test_many_credentials_for_one_holder_are_flagged` |
| AT-102 | FR-BON-01 | 5 non-VALID attempts on one reference | `repeated_failed_lookups` flagged | As expected | Pass | `test_repeated_failed_lookups_are_flagged` |
| AT-103 | FR-BON-01 | 7 VALID attempts | **Not** flagged | As expected | Pass | `test_successful_lookups_do_not_trigger_the_failure_rule` |
| AT-104 | FR-BON-01 | Every rule triggered | Score capped at 100 | As expected | Pass | `test_score_is_capped_at_100` |
| AT-105 | FR-BON-02 | Any triggered signal | Carries a message and a positive weight | As expected | Pass | `test_signals_carry_an_explanation` |

## 10. Manual test cases (MT-*)

To be executed against the live system and recorded by the team.

| ID | Requirement | Steps | Expected result | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| MT-01 | NFR-USE-01 | Open every page at 375 px, 768 px and 1440 px width | No horizontal scrolling; navigation collapses; tables scroll within their container | `[INSERT]` | ☐ | `[INSERT SCREENSHOTS]` |
| MT-02 | NFR-USE-02 | Navigate the sign-in and verification forms using only Tab and Enter | Every control reachable; focus visible; forms submit | `[INSERT]` | ☐ | `[INSERT]` |
| MT-03 | NFR-USE-02 | Inspect form markup | Every input has an associated `<label>`; errors use `role="alert"` | `[INSERT]` | ☐ | `[INSERT]` |
| MT-04 | FR-VER-06 | Show a VALID and an INVALID result to someone unfamiliar with the system | They identify the outcome correctly without reading the body text | `[INSERT]` | ☐ | `[INSERT]` |
| MT-05 | FR-QUAL-01 | Register a qualification on the live system | Success message shows the generated credential ID | `[INSERT]` | ☐ | `[INSERT]` |
| MT-06 | FR-OPS-04 | Watch the dashboard for 30 seconds while verifying in another tab | The counters increase without a page reload | `[INSERT]` | ☐ | `[INSERT]` |
| MT-07 | **FR-OPS-02** | `docker compose up`, then `docker compose stop db`, then `curl /healthz` | **503** with `database: error` | `[INSERT]` | ☐ | `[INSERT]` |
| MT-08 | NFR-SEC-05 | Submit the sign-in form 11 times in a minute | The 11th returns 429 | `[INSERT]` | ☐ | `[INSERT]` |
| MT-09 | NFR-SEC-05 | Submit 31 verifications in a minute | The 31st returns 429 | `[INSERT]` | ☐ | `[INSERT]` |
| MT-10 | NFR-OPS-01 | `docker build`, then run the image and curl `/healthz` | Image builds; container reports healthy | `[INSERT]` | ☐ | `[INSERT]` |
| MT-11 | Deployment | Open the live URL | HTTPS padlock; valid certificate; the application loads | Verified 7 Sep 2026 | Pass | `reports/deployment-verification.md` |
| MT-12 | NFR-SEC-04 | `curl -I` the live site | Security headers present on the live deployment | `[INSERT]` | ☐ | `[INSERT]` |

> MT-07 through MT-10 are the cases automation currently cannot cover — see
> `docs/testing-strategy.md` §11. Executing them manually is how those gaps are
> honestly closed for this submission.

---

## Summary

| Category | Cases | Passed | Manual / outstanding |
| --- | ---: | ---: | ---: |
| Authentication | 16 | 16 | 0 |
| Validation | 20 | 20 | 0 |
| Qualification management | 21 | 21 | 0 |
| Verification | 19 | 19 | 0 |
| Audit | 8 | 8 | 0 |
| Security | 21 | 21 | 0 |
| Error handling | 6 | 6 | 0 |
| Operations | 4 | 4 | 0 |
| Review assistant | 11 | 11 | 0 |
| **Automated total** | **126** | **126** | **0** |
| Manual | 12 | 1 | 11 |

The 126 documented automated cases are executed by 255 individual pytest tests
(several cases are parametrised across many inputs).

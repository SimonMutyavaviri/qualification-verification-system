# User Manual

Qualification Verification System — https://qvs-mim736.fly.dev

---

## 1. Getting started

### Signing in

1. Open the system in a browser.
2. Enter your **username or email address** and your password.
3. Tick **Keep me signed in** if you are on your own device.
4. Select **Sign in**.

> `[INSERT SCREENSHOT: sign-in page]`

Accounts are created by an administrator; there is no self-registration. If you
cannot sign in, contact your administrator — repeated failures are recorded.

If the message *"This account has been deactivated"* appears, your access has
been withdrawn and only an administrator can restore it.

### Signing out

Select **Sign out** in the top-right corner. Do this on any shared computer:
your session also expires automatically after 30 minutes of inactivity.

### Your role

The bar under your name shows your role, and the navigation only shows what you
may use:

| Role | What you can do |
| --- | --- |
| **Verifier** | Verify credentials, search the register, view your own verification history |
| **Qualification Issuer** | Everything a verifier can, plus register, edit and revoke qualifications, and see all verification history |
| **Administrator** | Everything, plus manage users and institutions, view the audit trail, and reinstate revoked qualifications |

---

## 2. The dashboard

The dashboard opens after sign-in and shows live counters — total credentials,
active credentials, verifications performed, valid results and revoked
credentials. They refresh every 15 seconds without reloading the page.

Below the counters:

- **Recent verifications** — the last five checks and their results
- **Recently registered** (issuers and administrators)
- **Recent system activity** (administrators only) — the newest audit entries

> `[INSERT SCREENSHOT: dashboard]`

---

## 3. Verifying a credential

This is the system's main purpose and is available to every role.

1. Select **Verify** in the navigation.
2. Type the credential reference exactly as it appears on the certificate,
   for example `QVS-2023-DEMO01`. Case does not matter.
3. Select **Verify credential**.

> `[INSERT SCREENSHOT: verification form]`

### Reading the result

| Result | Colour | Meaning | What to do |
| --- | --- | --- | --- |
| **VALID** | Green ✓ | Registered, not revoked, not expired | The credential can be relied upon |
| **EXPIRED** | Amber ⚠ | Genuinely awarded, but past its expiry date | Genuine award; ask the holder about renewal |
| **REVOKED** | Red ✗ | Withdrawn by the issuing institution | Do not rely on it; contact the institution |
| **INVALID** | Red ✗ | No credential with that reference exists | Re-check the reference for typing errors; if it is correct, the document may be fraudulent |

> `[INSERT SCREENSHOT: VALID result]`
> `[INSERT SCREENSHOT: INVALID result]`
> `[INSERT SCREENSHOT: REVOKED result]`

For VALID, EXPIRED and REVOKED, the result also shows the holder name,
qualification title, institution and award date — the same facts printed on the
certificate. For INVALID **nothing** is shown, because there is nothing to show.

### The verification receipt

Every check produces a unique **verification reference** (a long identifier such
as `3f7a…`). Select **Open receipt** for a permanent page recording what was
checked, the result, who checked it and when. The link can be shared as evidence
that the check was performed.

> `[INSERT SCREENSHOT: verification receipt]`

### Common problems

| Problem | Likely cause |
| --- | --- |
| INVALID for a certificate you believe is genuine | A typing error — `0` vs `O`, `1` vs `I`. The system never issues references containing those characters, so if you typed one, it is wrong. |
| "Too many requests" | The rate limit (30 verifications a minute) has been reached. Wait a moment. |
| The reference looks wrong | The expected form is `PREFIX-YEAR-SIXCHARS`, e.g. `QVS-2024-A1B2C3`. |

---

## 4. Searching the register

1. Select **Qualifications**.
2. Search by credential ID, holder name or qualification title — partial words
   work.
3. Narrow with the **Status**, **Type** and **Institution** filters.
4. Select **Search**. Use **Clear filters** to start again.

Results are paginated; **Previous** and **Next** keep your filters.

Select a credential ID to open its full record.

> `[INSERT SCREENSHOT: search results]`

---

## 5. Registering a qualification

*Issuers and administrators only.*

1. Select **Register**.
2. Complete the form:

| Field | Required | Notes |
| --- | --- | --- |
| Credential ID | No | **Leave blank** and the system generates a unique reference. Only supply one when transferring an existing reference. |
| Qualification title | Yes | As printed on the certificate |
| Qualification type | Yes | Degree, Diploma, Certificate, Professional Certification, Short Course or Licence |
| Institution | Yes | Only active institutions appear |
| Holder full name | Yes | As printed on the certificate |
| Holder email | No | Recommended — without it the review assistant flags the record |
| Award date | Yes | Cannot be in the future, or before 1900 |
| Expiry date | No | Leave blank for a credential that does not expire |

3. Select **Save qualification**.

The confirmation shows the credential ID. **Give this to the holder** — it is
what a verifier will need.

> `[INSERT SCREENSHOT: registration form]`
> `[INSERT SCREENSHOT: registration confirmation showing the credential ID]`

If something is wrong, the field turns red and explains why. Nothing is saved
until every field is valid.

---

## 6. The qualification record

The detail page shows the full record, its status, and — for issuers and
administrators — the **Review assistant** panel and the credential's own
verification history.

### The review assistant

An advisory, rule-based check that flags records worth a second look: an
implausible award date, a credential that expires almost immediately, a missing
holder email, an unusual number of credentials under one holder name, repeated
failed lookups, or a revoked credential.

It shows a level (LOW / MEDIUM / HIGH), a score out of 100, and **a plain-English
reason for every signal**. It never blocks anything and never makes a decision —
it only draws attention. A HIGH score is a prompt to check with the institution,
not a finding of fraud.

> `[INSERT SCREENSHOT: qualification detail with the review assistant]`

### Editing

*Issuers and administrators.* Select **Edit** to change the title, type, holder
name, holder email or expiry date.

The credential ID, award date, institution and issuer **cannot be changed**.
Someone may already have verified this credential and recorded the result;
changing what the reference means would make their record untrue. If those
details are wrong, revoke the record and register a corrected one.

A revoked qualification cannot be edited.

### Revoking

*Issuers and administrators.*

1. Select **Revoke** on the detail page.
2. Enter a reason — this is **required** and permanently recorded.
3. Select **Revoke qualification** and confirm.

The credential immediately returns REVOKED to every verifier. Revocation is
recorded in the audit trail against your name.

> `[INSERT SCREENSHOT: revocation panel]`

### Reinstating

*Administrators only.* Select **Reinstate** on a revoked record and give a
reason. The credential returns to active and verifies as VALID again.

---

## 7. Verification history

Select **History**.

- **Verifiers** see their own checks.
- **Issuers and administrators** see every check performed in the system.

Filter by credential ID or by result. Each row links to its receipt. The source
IP address of each check is shown.

> `[INSERT SCREENSHOT: verification history]`

---

## 8. Your profile

Select your name in the top-right corner to see your account details and last
sign-in time, and to change your password.

**Password requirements:** at least 12 characters, with at least one upper case
letter, one lower case letter and one digit. The new password must differ from
the current one.

> `[INSERT SCREENSHOT: profile page]`

---

## 9. Administration

*Administrators only.*

### Users

**Users** lists every account. From here you can:

- **Create a user** — username, full name, email, a temporary password, a role
  and an optional institution. Share the temporary password securely and ask the
  user to change it from their profile.
- **Change a role** — choose from the dropdown and select **Set**.
- **Deactivate / activate** — a deactivated user cannot sign in but their
  history is preserved.

You cannot remove your own administrator role or deactivate your own account —
this prevents locking the organisation out of its own system.

> `[INSERT SCREENSHOT: user management]`

### Institutions

Add awarding bodies with a name, a short code (MSU, UZ), a country and a contact
address. Deactivating an institution stops new registrations against it while
leaving credentials it has already issued fully verifiable.

> `[INSERT SCREENSHOT: institution management]`

### Audit trail

**Audit** shows every recorded event, newest first: sign-ins and failures,
sign-outs, credential registrations, edits, revocations and reinstatements,
every verification, user and institution changes, and denied access attempts.
Each entry records the action, who performed it, what it affected, a detail line
and the source IP address. Filter by action type.

**Audit entries cannot be edited or deleted by anyone through this system** —
including administrators. That is what makes the trail trustworthy.

> `[INSERT SCREENSHOT: audit trail]`

---

## 10. Error messages

| Message | Meaning | What to do |
| --- | --- | --- |
| Access denied (403) | Your role does not permit that page | Ask an administrator if you need the access |
| Page not found (404) | The address or record does not exist | Check the link |
| Too many requests (429) | Rate limit reached | Wait a minute |
| Something went wrong (500) | An unexpected fault, already logged | Try again; tell an administrator if it persists |
| Please sign in to access that page | Session expired | Sign in again; you will return to the page you wanted |

> `[INSERT SCREENSHOT: 403 page]`
> `[INSERT SCREENSHOT: 404 page]`

---

## 11. Quick reference

| I want to… | Where |
| --- | --- |
| Check whether a qualification is genuine | **Verify** |
| Find someone's qualifications | **Qualifications** → search by name |
| Add a new credential | **Register** (issuers) |
| Withdraw a credential | Open it → **Revoke** (issuers) |
| Prove I performed a check | **History** → **View** the receipt |
| Change my password | Your name → **Profile** |
| Add a colleague | **Users** (administrators) |
| See who did what | **Audit** (administrators) |

# Deployment Verification Record

Evidence that the system was actually deployed and actually works. Every result
below was produced by running the stated command against the live system.

**Live URL:** https://qvs-mim736.fly.dev
**Fly app:** `qvs-mim736` · **Org:** personal · **Region:** `jnb` (Johannesburg)
**Verified:** 7 September 2026

---

## 1. Deployment record

| Item | Value |
| --- | --- |
| Platform | Fly.io |
| Build method | `flyctl deploy --remote-only` (built on Fly's remote builder) |
| Image | `registry.fly.io/qvs-mim736:deployment-01M1WBG5KPG0745W3RYMCSR3EE` |
| Image size | 78 MB |
| Machine | `8ed047c7102448` |
| VM | `shared-cpu-1x`, 1 vCPU, 512 MB |
| Storage | Fly volume `qvs_data` (`vol_4y8x1203ypz28oer`), 1 GB, encrypted, mounted at `/data` |
| Database | SQLite on the persistent volume |
| Releases | v1 (initial), v2 (HSTS/proxy fix) |
| Health check | `GET /healthz` every 30s — **1 total, 1 passing** |

### Why the build was remote

Local Docker could not be used on the build machine: Docker Desktop's Linux
engine requires WSL2, and WSL2 reported *"virtualization is not enabled on this
machine"* (a BIOS/firmware setting). `flyctl deploy --remote-only` builds the
image on Fly's own builders, so the deployment is genuine and the `Dockerfile`
is genuinely exercised — just not on this laptop. The `docker-build` CI job
also builds and smoke-tests the image on GitHub's runners.

### A real problem encountered during first deploy

The first deployment reported:

```
Failed to provision IP addresses. Use `fly ips` commands to remediate it.
ERROR: error allocating ipv6 after detecting first deploy and presence of
services: failed to add ip to app: org_slug is only supported with private_v6 type
```

The machine launched correctly; only the public addresses failed to allocate.
Resolved by allocating them explicitly:

```bash
flyctl ips allocate-v4 --shared --app qvs-mim736    # 66.241.124.67
flyctl ips allocate-v6 --app qvs-mim736             # 2a09:8280:1::185:42e9:0
```

This is recorded here and in `docs/flyio-deployment.md` §7 because it will
happen again to anyone redeploying from scratch.

---

## 2. Health check

```
$ curl -sS https://qvs-mim736.fly.dev/healthz
{"checks":{"application":"ok","database":"ok"},"status":"healthy","version":"1.0.0"}
HTTP 200
```

**Result: PASS** — application and database both reachable.

## 3. Machine status

```
$ flyctl status --app qvs-mim736

App
 Name     │ qvs-mim736
 Owner    │ personal
 Hostname │ qvs-mim736.fly.dev
 Image    │ qvs-mim736:deployment-01M1WBG5KPG0745W3RYMCSR3EE

Machines
 PROCESS │ ID             │ VERSION │ REGION │ STATE   │ CHECKS
 app     │ 8ed047c7102448 │ 1       │ jnb    │ started │ 1 total, 1 passing
```

**Result: PASS**

## 4. Transport security

```
$ curl -sSI http://qvs-mim736.fly.dev/
HTTP/1.1 301 Moved Permanently
location: https://qvs-mim736.fly.dev/
```

```
$ curl -sSI https://qvs-mim736.fly.dev/login
HTTP/1.1 200 OK
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
strict-transport-security: max-age=31536000; includeSubDomains
content-security-policy: default-src 'self'; script-src 'self' https://cdn.tailwindcss.com
  'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;
  font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
```

**Result: PASS** — HTTP redirects to HTTPS; all hardening headers present on the
live deployment.

### A defect this verification found and fixed

The **first** live check showed **no `Strict-Transport-Security` header**, even
though `apply_security_headers` sets it for secure requests.

**Root cause.** Fly.io terminates TLS at its edge and forwards the request to
the container over plain HTTP. Flask's `request.is_secure` therefore returned
`False` for every request, so the HSTS branch never ran. The same fault meant
audit entries would have recorded the proxy's address rather than the client's.

**Fix.** `werkzeug.middleware.proxy_fix.ProxyFix` is now applied when
`TRUST_PROXY_HEADERS` is set, which `ProductionConfig` enables (`app/__init__.py`,
`app/config.py`). It is **off by default**, because trusting `X-Forwarded-*`
without a trusted proxy in front would let any client forge its own scheme and
address.

**Regression cover.** Four tests were added in
`tests/integration/test_security.py::TestProxyAwareness`: proxy headers are not
trusted by default; production does trust them; HSTS is sent for a forwarded
HTTPS request; HSTS is not sent over plain HTTP.

This is exactly the class of defect that only a real deployment reveals — it
passed every test and every local check beforehand.

---

## 5. Functional verification against the live system

Executed by an HTTP client driving the real application, signed in as
`admin` (script: see §7).

| # | Check | Expected | Actual | Result |
| --- | --- | --- | --- | --- |
| 1 | Health endpoint | `healthy` | `healthy` | PASS |
| 2 | Sign-in page renders | Page title present | Present | PASS |
| 3 | Administrator sign-in | Dashboard reached | Reached | PASS |
| 4 | Verify `QVS-2023-DEMO01` | `VALID` | `VALID` | PASS |
| 5 | Verify `QVS-2022-DEMO02` | `EXPIRED` | `EXPIRED` | PASS |
| 6 | Verify `QVS-2021-DEMO03` | `REVOKED` | `REVOKED` | PASS |
| 7 | Verify `QVS-2024-ZZZZZZ` | `INVALID` | `INVALID` | PASS |
| 8 | Search by holder name | Credential found | Found | PASS |
| 9 | Audit trail populated | `verification.performed` present | Present | PASS |
| 10 | User management | Accounts listed | Listed | PASS |
| 11 | Institution management | Institutions listed | Listed | PASS |
| 12 | Verification history | ≥ 4 records | 4+ records | PASS |
| 13 | Metrics endpoint | JSON counters | `{'total': 4, 'valid': 1, 'invalid': 1, 'revoked': 1, 'expired': 1}` | PASS |
| 14 | **Register a new credential live** | Created with a generated ID | `QVS-2026-4SWGA9` | PASS |
| 15 | **Verify the newly created credential** | `VALID` | `VALID` | PASS |

**15 of 15 passed.**

Checks 14 and 15 are the important ones: they prove the deployed system performs
a complete write-then-read cycle against its persistent volume, not merely that
it serves pre-seeded data.

---

## 6. Demonstration data

Seeded on the live machine with:

```bash
flyctl ssh console --app qvs-mim736 \
  -C "gosu qvs env FLASK_APP=wsgi.py python -m flask seed-demo"
```

**Institutions:** Midlands State University (MSU), University of Zimbabwe (UZ),
Institute of Chartered Accountants (ICA)

**Accounts:** `admin` (Administrator), `issuer` (Qualification Issuer),
`verifier` (Verifier) — passwords randomly generated at seed time and displayed
once. They are recorded in `deployment-credentials.local.md`, which is
git-ignored and **not** part of the submission.

**Credentials in the register:**

| Credential ID | Holder | Expected result |
| --- | --- | --- |
| `QVS-2023-DEMO01` | Tinashe Moyo | VALID |
| `QVS-2022-DEMO02` | Rudo Chikafu | EXPIRED |
| `QVS-2021-DEMO03` | Farai Ncube | REVOKED |
| `QVS-2026-4SWGA9` | Live Deploy Test | VALID (created during this verification) |

---

## 7. Reproducing this verification

```bash
curl -sS  https://qvs-mim736.fly.dev/healthz
curl -sSI https://qvs-mim736.fly.dev/login
curl -sSI http://qvs-mim736.fly.dev/
flyctl status   --app qvs-mim736
flyctl releases --app qvs-mim736
flyctl volumes list --app qvs-mim736
flyctl secrets list --app qvs-mim736      # names and digests only
flyctl logs     --app qvs-mim736
```

Then sign in through a browser and repeat checks 4–15 by hand — this is manual
test case **MT-11** in `docs/test-cases.md`, and screenshots go in section G of
`docs/evidence-checklist.md`.

---

## 8. What is *not* claimed

Stated explicitly so nothing here is overstated:

- **The Docker image was not built on the development machine.** Hardware
  virtualisation is disabled in BIOS, so Docker Desktop cannot start. The image
  was built by Fly's remote builder and is built again by the `docker-build` CI
  job. Local `docker build` evidence must come from a machine where Docker runs,
  or from that CI job.
- **PostgreSQL is not in use in this deployment.** The application supports it
  and CI runs the integration suite against PostgreSQL 16, but the live instance
  uses SQLite on a volume. The rationale and the one-command switch are in
  `docs/flyio-deployment.md` §5 and §11.
- **The CD pipeline has not yet run against this app.** `.github/workflows/cd.yml`
  is written and gated on CI success, but it needs `FLY_API_TOKEN` in the
  repository's Actions secrets and a push to `main`. Both deployments so far were
  performed manually with `flyctl deploy`. Setting up the token is step 12 of
  `docs/flyio-deployment.md`.
- **Load and performance were not measured.** No load testing was carried out.

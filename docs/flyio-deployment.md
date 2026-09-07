# Fly.io Deployment Guide

**Live system:** https://qvs-mim736.fly.dev
**App:** `qvs-mim736` · **Region:** `jnb` (Johannesburg) · **Deployed:** 6 September 2026

---

## 1. Prerequisites

| Requirement | Notes |
| --- | --- |
| A Fly.io account | https://fly.io/app/sign-up |
| `flyctl` installed | See section 2 |
| A payment method on the Fly account | Required even for small machines |
| Git repository access | For the automated CD path |

**Local Docker is not required.** `flyctl deploy --remote-only` builds the image
on Fly's remote builders. This is how this deployment was performed, because the
build machine could not run Docker (hardware virtualisation disabled in BIOS).

## 2. Install the Fly CLI

```bash
# Windows (PowerShell)
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"

# macOS / Linux
curl -L https://fly.io/install.sh | sh

flyctl version
```

## 3. Authenticate

```bash
flyctl auth login          # opens a browser
flyctl auth whoami         # confirms the signed-in account
```

## 4. Create the application

```bash
flyctl apps create qvs-mim736 --org personal
```

The name must be globally unique. If you choose a different one, update `app =`
in `fly.toml` and the URLs in `.github/workflows/cd.yml`.

## 5. Provision storage

This deployment runs SQLite on a persistent Fly volume.

```bash
flyctl volumes create qvs_data --app qvs-mim736 --region jnb --size 1 --yes
```

`fly.toml` mounts it:

```toml
[mounts]
  source = "qvs_data"
  destination = "/data"
```

> **Why SQLite here, and what it costs you.** The architecture
> (`docs/architecture.md`) specifies PostgreSQL for production, and the
> application supports it unchanged — `DATABASE_URL` is the only difference.
> SQLite on a volume was chosen for this demonstration deployment because it is
> a single small volume rather than a billed database cluster. The trade-off is
> real and worth stating: a volume attaches to **one machine**, so the app
> cannot be scaled horizontally, and `auto_stop_machines` plus a single writer
> means concurrent write throughput is limited. For a demonstration and
> assessment workload this is comfortably sufficient; for real institutional
> use, switch to PostgreSQL (section 11).

## 6. Set the secrets

Never put these in `fly.toml` or any committed file.

```bash
# Generate a strong key and set it without it appearing in shell history
SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
flyctl secrets set "SECRET_KEY=$SECRET" \
                   "DATABASE_URL=sqlite:////data/qvs.db" \
                   --app qvs-mim736
```

Note the four slashes in `sqlite:////data/qvs.db` — three for the URL scheme
plus one for the absolute path.

Verify (names and digests only; values are never displayed):

```bash
flyctl secrets list --app qvs-mim736
```

The application refuses to start in production without both of these — see
`ProductionConfig` in `app/config.py`. That is deliberate: a misconfigured
deployment should fail loudly rather than run on a default key.

## 7. Deploy

```bash
flyctl deploy --remote-only --app qvs-mim736
```

What happens:

1. The build context is uploaded to a Fly remote builder.
2. The multi-stage `Dockerfile` builds (final image ≈ 78 MB).
3. The image is pushed to `registry.fly.io`.
4. A machine is created, the volume is attached at `/data`.
5. `docker-entrypoint.sh` takes ownership of `/data`, creates the schema, then
   drops from root to the `qvs` user and starts gunicorn.
6. Fly polls `/healthz`; the machine takes traffic once it passes.

### If IP allocation fails

This deployment hit `ERROR: error allocating ipv6 ... org_slug is only supported
with private_v6 type` — a Fly-side API error during first deploy. The machine
still launched; the addresses just needed allocating by hand:

```bash
flyctl ips allocate-v4 --shared --app qvs-mim736
flyctl ips allocate-v6 --app qvs-mim736
flyctl ips list --app qvs-mim736
```

## 8. Seed the demonstration data

```bash
flyctl ssh console --app qvs-mim736 \
  -C "gosu qvs env FLASK_APP=wsgi.py python -m flask seed-demo"
```

This creates three institutions, one user per role and three credentials
(`QVS-2023-DEMO01` valid, `QVS-2022-DEMO02` expired, `QVS-2021-DEMO03` revoked).
Passwords are generated randomly and **printed once**. Record them somewhere
private; they are not stored anywhere retrievable.

To choose your own instead, set `SEED_ADMIN_PASSWORD`, `SEED_ISSUER_PASSWORD`
and `SEED_VERIFIER_PASSWORD` in the environment of that command.

The seed is idempotent — re-running it will not duplicate or overwrite anything.

## 9. Verify the deployment

```bash
# 1. Health
curl -sS https://qvs-mim736.fly.dev/healthz
# {"checks":{"application":"ok","database":"ok"},"status":"healthy","version":"1.0.0"}

# 2. Sign-in page renders
curl -sS https://qvs-mim736.fly.dev/login | grep -o "Qualification Verification System" | head -1

# 3. HTTPS is enforced
curl -sSI http://qvs-mim736.fly.dev/ | head -1        # expect 301 to https

# 4. Security headers
curl -sSI https://qvs-mim736.fly.dev/login | grep -iE "x-frame|content-security|x-content-type"
```

Then, in a browser: sign in, verify `QVS-2023-DEMO01` (VALID),
`QVS-2022-DEMO02` (EXPIRED), `QVS-2021-DEMO03` (REVOKED) and an unregistered
reference (INVALID); register a new qualification; check it appears in search
and verifies as VALID; open the audit trail as an administrator.

The results of this exact check on the live system are recorded in
`reports/deployment-verification.md`.

## 10. Operations

```bash
flyctl status   --app qvs-mim736       # machines, health, current release
flyctl logs     --app qvs-mim736       # live logs
flyctl logs     --app qvs-mim736 --no-tail | tail -100
flyctl ssh console --app qvs-mim736    # shell into the machine
flyctl releases --app qvs-mim736       # deployment history
flyctl machine list --app qvs-mim736
flyctl volumes list --app qvs-mim736
flyctl dashboard --app qvs-mim736      # open the web console
```

### Rollback

```bash
flyctl releases --app qvs-mim736                  # find the version to return to
flyctl releases rollback --app qvs-mim736         # roll back to the previous one
flyctl deploy --image registry.fly.io/qvs-mim736:deployment-XXXX --app qvs-mim736
```

Rollback is a deliberate human action rather than an automated response to a
failed deployment — an automatic rollback can hide a data-layer fault that the
next deployment would simply hit again. The CD workflow's `rollback-on-failure`
job prints the release list and the exact command.

### Backups

Volumes are encrypted, with scheduled snapshots and five-day retention:

```bash
flyctl volumes snapshots list vol_4y8x1203ypz28oer
flyctl volumes snapshots create vol_4y8x1203ypz28oer   # on demand
```

## 11. Switching to managed PostgreSQL

The application needs no code change — only a different `DATABASE_URL`.

```bash
flyctl postgres create --name qvs-db --region jnb --initial-cluster-size 1
flyctl postgres attach qvs-db --app qvs-mim736   # sets DATABASE_URL for you
flyctl deploy --remote-only --app qvs-mim736
```

`BaseConfig.normalise_database_url` rewrites the `postgres://` URL that Fly sets
into the `postgresql+psycopg://` form SQLAlchemy 2 requires, so the attach
command's output works as-is.

Afterwards you can remove the `[mounts]` block from `fly.toml` and destroy the
volume. **Existing SQLite data is not migrated** by this — export it first if it
matters.

## 12. Automated deployment (CD)

`.github/workflows/cd.yml` deploys automatically when CI succeeds on `main`.

One-time setup:

```bash
flyctl tokens create deploy --app qvs-mim736 --name github-actions
```

Add the printed token to GitHub as
**Settings → Secrets and variables → Actions → New repository secret**, named
`FLY_API_TOKEN`.

The workflow then deploys with `--strategy rolling`, polls `/healthz` until it
is healthy, smoke-tests the sign-in page, and records the deployment in the job
summary. It runs **only** when the CI conclusion was `success`, so code that
fails the quality gate is never deployed.

## 13. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `SECRET_KEY must be set...` in the logs | Secret missing or still the placeholder | `flyctl secrets set SECRET_KEY=...` |
| `DATABASE_URL must be set...` | Secret missing | `flyctl secrets set DATABASE_URL=...` |
| `unable to open database file` | Volume not mounted, or `/data` not writable | Check `[mounts]`; confirm the entrypoint chown ran (`flyctl logs`) |
| Health check failing, machine restarting | Application error at start-up | `flyctl logs --app qvs-mim736` |
| `no ip addresses assigned` | First-deploy allocation failure | See section 7 |
| 502 after deploying | Machine still starting | Wait for the grace period; then check logs |
| Deployment succeeds but the site is stale | Browser cache | Hard refresh, or check `flyctl releases` |
| Slow first request | `auto_stop_machines` stopped the machine | Expected; `min_machines_running = 1` limits it |

## 14. What is deliberately not in this repository

- `SECRET_KEY` — a Fly secret, generated at deployment time
- `DATABASE_URL` — a Fly secret
- `FLY_API_TOKEN` — a GitHub Actions secret
- Demo account passwords — generated at seed time, shown once
- Any `.env` file — excluded by `.gitignore` and `.dockerignore`

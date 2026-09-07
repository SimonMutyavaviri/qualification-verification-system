# Database migrations

Flask-Migrate (Alembic) is wired into the application factory. The baseline
schema is created by `db.create_all()` at container start, which is the right
trade-off for a project of this size: it makes a fresh deployment work with no
manual step.

From the first schema change onwards, use migrations so that deployed data is
preserved:

```bash
flask db init          # once, if the versions/ directory does not exist yet
flask db migrate -m "Add <column> to <table>"
flask db upgrade
```

Generated revisions live in `migrations/versions/` and must be committed.

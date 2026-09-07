#!/bin/sh
# Container entrypoint.
#
#  1. Take ownership of the data directory. A Fly volume is attached
#     root-owned, so without this the unprivileged application user cannot
#     write the SQLite database file.
#  2. Create the schema.
#  3. Drop privileges and exec the real command (gunicorn).
set -e

DATA_DIR="${DATA_DIR:-/data}"

if [ "$(id -u)" = "0" ]; then
    mkdir -p "$DATA_DIR"
    chown -R qvs:qvs "$DATA_DIR"
    RUN_AS="gosu qvs"
else
    # Already unprivileged (for example when the image is run with --user).
    RUN_AS=""
fi

echo "Applying database schema..."
$RUN_AS python -c "
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print('Database schema is up to date.')
"

echo "Starting application as uid $(id -u qvs)..."
exec $RUN_AS "$@"

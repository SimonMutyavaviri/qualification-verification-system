"""WSGI entry point used by Gunicorn in the container."""

import os

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":  # pragma: no cover - local convenience only
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))

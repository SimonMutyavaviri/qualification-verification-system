"""Local development entry point: ``python run.py``."""

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402 - must follow load_dotenv

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=app.config.get("DEBUG", False),
    )

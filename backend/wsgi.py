"""WSGI entry point for Flask app.

Ensures the backend directory is on sys.path so `app` package is importable
even when Flask is launched from another working directory.
"""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402

Config.ensure_dirs()
app = create_app()

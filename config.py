"""
config.py — Centralized configuration for MongoDB integration
(Phase 3.1 / STEP 1).

All sensitive values (connection string, database name) are read from
environment variables — nothing is hardcoded here. Set these in your
shell, a `.env` file (auto-loaded below if python-dotenv is installed),
or your hosting platform's secrets manager before running the app.

Environment variables used
---------------------------
MONGO_URI
    MongoDB connection string, e.g.
    "mongodb+srv://<user>:<password>@<cluster>.mongodb.net"
    Defaults to a local MongoDB instance for development:
    "mongodb://localhost:27017"

MONGO_DB_NAME
    Name of the database to use.
    Defaults to "student_grade_calculator".

MONGO_SERVER_SELECTION_TIMEOUT_MS
    How long (ms) to wait before giving up on connecting, so the app
    fails fast/gracefully instead of hanging when MongoDB is
    unreachable. Defaults to 5000ms.
"""

import os

# Optionally load a local .env file for development convenience. This is
# purely optional — the app works fine without python-dotenv installed
# or without a .env file present (env vars can be set any other way).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------
# MongoDB connection settings — read from environment, never hardcoded.
# ---------------------------------------------------------------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "student_grade_calculator")

MONGO_SERVER_SELECTION_TIMEOUT_MS = int(
    os.environ.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000")
)

# ---------------------------------------------------------------
# Collection names (Phase 3.1 / STEP 2)
# ---------------------------------------------------------------
STUDENTS_COLLECTION = "students"
RESULTS_COLLECTION = "results"

# ---------------------------------------------------------------
# Collection names (Phase 3.2 / STEP 1 — Authentication foundation)
# ---------------------------------------------------------------
USERS_COLLECTION = "users"
"""
database.py — MongoDB connection module (Phase 3.1 / STEP 1).

Responsible ONLY for:
    - Opening/reusing a MongoDB connection
    - Selecting the configured database
    - Handing back collection handles

No business logic (saving/searching students) lives here — see
student_operations.py for that. Keeping this module small and focused
means the rest of the app never talks to pymongo directly, which makes
it easy to swap MongoDB for another backend later if ever needed.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import config

# Module-level cache so the process opens a single MongoClient no matter
# how many times get_database()/get_collection() are called (Streamlit
# reruns the script constantly, so this avoids reconnecting every time).
_client = None
_db = None


def get_client():
    """Return a cached MongoClient, creating it on first use."""
    global _client
    if _client is None:
        _client = MongoClient(
            config.MONGO_URI,
            serverSelectionTimeoutMS=config.MONGO_SERVER_SELECTION_TIMEOUT_MS,
        )
    return _client


def get_database():
    """Return the configured MongoDB database (cached)."""
    global _db
    if _db is None:
        _db = get_client()[config.MONGO_DB_NAME]
    return _db


def get_collection(collection_name):
    """Return a handle to a specific collection in the configured database."""
    return get_database()[collection_name]


def test_connection():
    """
    Ping MongoDB to verify the connection is alive.

    Returns:
        (bool, str): (True, "Connected") on success, or
                      (False, error_message) on failure.

    The UI uses this to show a friendly status instead of crashing when
    MongoDB is unreachable or MONGO_URI isn't configured yet.
    """
    try:
        get_client().admin.command("ping")
        return True, "Connected"
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        return False, str(exc)
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)

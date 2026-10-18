"""
auth.py — Authentication foundation (Phase 3.2 / STEP 1).

This module owns user accounts and password security only. It does
NOT render any UI, touch st.session_state, or wire into app.py's
existing flow — that's later steps. It follows the same shape as
student_operations.py: use config.py for collection names, use
database.get_collection() for the connection, no new MongoClient.

Collection used (see config.py):
    users — one document per account (Admin / Teacher / Student)

Document shape
---------------
    {
        "username":      str,        # unique, stored lowercase
        "full_name":     str,
        "email":         str,
        "password_hash": bytes,      # bcrypt hash — never plain text
        "role":          str,        # "Admin" | "Teacher" | "Student"
        "roll_no":       str | None, # optional, Students only
        "status":        str,        # "active" | "disabled"
        "created_at":    datetime,   # UTC
    }
"""

from datetime import datetime

import bcrypt
from pymongo.errors import PyMongoError

import config
from database import get_collection

VALID_ROLES = ("Admin", "Teacher", "Student")


def _users_collection():
    return get_collection(config.USERS_COLLECTION)


def ensure_indexes():
    """
    Creates a unique index on `username` so duplicate accounts are
    rejected at the database level, not just in application code.
    Safe to call repeatedly — pymongo no-ops if the index already exists.
    """
    _users_collection().create_index("username", unique=True)


# ----------------------------------------------------------------------
# Password security
# ----------------------------------------------------------------------
def hash_password(password: str) -> bytes:
    """Hashes a plain-text password with bcrypt. Never store the input directly."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password: str, password_hash: bytes) -> bool:
    """Checks a plain-text password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)
    except (ValueError, TypeError):
        return False


# ----------------------------------------------------------------------
# Basic authentication functions
# ----------------------------------------------------------------------
def create_user(username, full_name, email, password, role, roll_no=None):
    """
    Creates a new user account.

    Args:
        username: unique login name (stored lowercase)
        full_name: display name
        email: contact email
        password: plain-text password (hashed before storage, never saved as-is)
        role: one of VALID_ROLES
        roll_no: optional, intended for Student accounts

    Returns:
        (success: bool, message: str)
    """
    username = (username or "").strip().lower()

    if not username or not password:
        return False, "Username and password are required."
    if role not in VALID_ROLES:
        return False, f"Role must be one of {VALID_ROLES}."

    try:
        if _users_collection().find_one({"username": username}):
            return False, f"Username '{username}' already exists."

        _users_collection().insert_one({
            "username": username,
            "full_name": (full_name or "").strip(),
            "email": (email or "").strip(),
            "password_hash": hash_password(password),
            "role": role,
            "roll_no": roll_no.strip() if roll_no else None,
            "status": "active",
            "created_at": datetime.utcnow(),
        })
        return True, f"User '{username}' created successfully."
    except PyMongoError as exc:
        return False, f"Could not create user: {exc}"


def verify_user(username, password):
    """
    Authenticates a username/password pair.

    Returns:
        The user document (dict, without password_hash) on success,
        or None if the username doesn't exist, the account isn't
        active, or the password is wrong.
    """
    username = (username or "").strip().lower()

    try:
        user = _users_collection().find_one({"username": username})
    except PyMongoError:
        return None

    if not user:
        return None
    if user.get("status") != "active":
        return None
    if not verify_password(password, user["password_hash"]):
        return None

    user.pop("password_hash", None)
    user["_id"] = str(user["_id"])
    return user


def get_user_by_username(username):
    """
    Plain lookup by username — no password involved.

    Returns:
        The user document (dict, without password_hash), or None if
        no such user exists.
    """
    username = (username or "").strip().lower()

    try:
        user = _users_collection().find_one({"username": username})
    except PyMongoError:
        return None

    if not user:
        return None

    user.pop("password_hash", None)
    user["_id"] = str(user["_id"])
    return user

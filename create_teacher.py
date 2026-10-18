"""
create_teacher.py — Default Teacher bootstrap script (Phase 3.3).

One-off setup script for local testing. Reuses the existing auth.py
(password hashing via bcrypt, user creation) and database.py (Mongo
connection) exactly as they already work — no new connection logic,
no changes to auth.py, database.py, or app.py.

What it does:
    1. Connects using the existing database.get_collection() pattern
       (the same one auth.py itself uses internally).
    2. Checks whether a user with username "teacher1" already exists.
    3. If none exists, creates one via auth.create_user() — which
       hashes the password with bcrypt and sets status="active".
    4. If the account already exists, prints a friendly message and
       exits without making any changes.

Default credentials (testing only — change the password after first
login):
    Username:  teacher1
    Full Name: Test Teacher
    Email:     teacher@example.com
    Role:      Teacher
    Status:    active   (set automatically by auth.create_user())

Run:
    python create_teacher.py
"""

import config
from database import get_collection
from auth import create_user, ensure_indexes

DEFAULT_TEACHER = {
    "username": "teacher1",
    "full_name": "Test Teacher",
    "email": "teacher@example.com",
    "role": "Teacher",
}


def teacher_exists():
    """
    Checks the users collection for an existing account with username
    "teacher1". Reuses database.get_collection() — the same connection
    pattern auth.py already uses internally (_users_collection()).

    Returns:
        True if the default Teacher account already exists, False otherwise.
    """
    users_collection = get_collection(config.USERS_COLLECTION)
    return users_collection.find_one({"username": DEFAULT_TEACHER["username"]}) is not None


def main():
    # Same index auth.py sets up for itself — safe to call repeatedly.
    ensure_indexes()

    if teacher_exists():
        print("ℹThe default Teacher account already exists. No action taken.")
        return

    success, message = create_user(
        username=DEFAULT_TEACHER["username"],
        full_name=DEFAULT_TEACHER["full_name"],
        email=DEFAULT_TEACHER["email"],
        password=DEFAULT_TEACHER["password"],
        role=DEFAULT_TEACHER["role"],
    )

    if success:
        print(f"{message}")
        print(f"   Username: {DEFAULT_TEACHER['username']}")
        print(f"   Password: {DEFAULT_TEACHER['password']}")
        print(" This is a default testing password — change it after first login.")
    else:
        print(f"Could not create default teacher: {message}")


if __name__ == "__main__":
    main()
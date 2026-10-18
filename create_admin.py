   from getpass import getpass
create_admin.py — Default Admin bootstrap script (Phase 3.2 / STEP 5).

One-off setup script for local testing. Reuses the existing auth.py
(password hashing via bcrypt, user creation) and database.py (Mongo
connection) exactly as they already work — no new connection logic,
no changes to auth.py, database.py, or app.py.

What it does:
    1. Connects using the existing database.get_collection() pattern
       (the same one auth.py itself uses internally).
    2. Checks whether a user with role "Admin" already exists.
    3. If none exists, creates one via auth.create_user() — which
       hashes the password with bcrypt and sets status="active".
    4. If an Admin already exists, prints a friendly message and exits
       without making any changes.

Default credentials (testing only — change the password after first
login):
    Username:  admin
    Full Name: System Administrator
    Email:     admin@example.com
    Role:      Admin
    Status:    active   (set automatically by auth.create_user())

Run:
    python create_admin.py
"""

import config
from database import get_collection
from auth import create_user, ensure_indexes
from getpass import getpass

DEFAULT_ADMIN = {
    "username": "admin",
    "full_name": "System Administrator",
    "email": "admin@example.com",
    "password": getpass("Password: "),
    "role": "Admin",
}


def admin_exists():
    """
    Checks the users collection for any existing account with role
    "Admin". Reuses database.get_collection() — the same connection
    pattern auth.py already uses internally (_users_collection()).

    Returns:
        True if at least one Admin account exists, False otherwise.
    """
    users_collection = get_collection(config.USERS_COLLECTION)
    return users_collection.find_one({"role": "Admin"}) is not None


def main():
    # Same index auth.py sets up for itself — safe to call repeatedly.
    ensure_indexes()

    if admin_exists():
        print("ℹAn Admin account already exists. No action taken.")
        return

    success, message = create_user(
        username=DEFAULT_ADMIN["username"],
        full_name=DEFAULT_ADMIN["full_name"],
        email=DEFAULT_ADMIN["email"],
        password=DEFAULT_ADMIN["password"],
        role=DEFAULT_ADMIN["role"],
    )

    if success:
        print(f"{message}")
        print(f"   Username: {DEFAULT_ADMIN['username']}")
        print(f"   Password: {DEFAULT_ADMIN['password']}")
        print(" This is a default testing password — change it after first login.")
    else:
        print(f"Could not create default admin: {message}")


if __name__ == "__main__":
    main()

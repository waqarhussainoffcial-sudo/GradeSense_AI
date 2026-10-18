"""
Phase 3.3 / STEP 2 — Admin Dashboard Implementation
dashboard/admin_dashboard.py

Purpose:
    Full Admin dashboard: header + role badge, statistics cards
    (Total Users / Students / Teachers / Results), and a User
    Management section with three tabs (View Users, Role Statistics,
    Account Management placeholders).

Data access:
    Reads only from MongoDB via database.get_collection(), using the
    existing collection-name constants in config.py:
        - config.USERS_COLLECTION   ("users")
        - config.RESULTS_COLLECTION ("results")
    "Total Students" / "Total Teachers" are derived from the `role`
    field on documents in the `users` collection (the same field
    auth.py already reads at login) — not from the separate `students`
    collection used by the calculator's "Save to Database" feature,
    since that collection holds saved report records, not accounts.

Scope / rules followed:
    - Read-only: no writes, no CRUD (Account Management tab is a
      placeholder only, per Step 2 instructions).
    - Does not modify calculator, grading, PDF, or Excel logic.
    - Does not modify auth.py, database.py, or config.py — imports
      them exactly as app.py already does elsewhere.
    - Wrapped in try/except so a missing pymongo/config/database still
      lets the rest of the dashboard render (with a warning) instead
      of crashing, matching the pattern already used in app.py.
    - Not wired into app.py yet.
"""

import streamlit as st
from dashboard.dashboard_utils import page_header, role_badge, metric_card

try:
    import config
    from database import get_collection, test_connection
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


# ==========================================================
# Data access helpers (read-only)
# ==========================================================

def _fetch_users():
    """Fetch all documents from the users collection.

    Returns:
        (bool, list | str): (True, list_of_user_docs) on success,
                             (False, error_message) on failure.
    """
    try:
        users_collection = get_collection(config.USERS_COLLECTION)
        users = list(users_collection.find({}))
        return True, users
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)


def _fetch_results_count():
    """Count all documents in the results collection.

    Returns:
        (bool, int | str): (True, count) on success,
                            (False, error_message) on failure.
    """
    try:
        results_collection = get_collection(config.RESULTS_COLLECTION)
        return True, results_collection.count_documents({})
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)


def _sanitize_users_for_display(users):
    """Return a copy of the user docs safe to show in the UI.

    - Removes password_hash entirely (never shown, per Step 2 spec).
    - Stringifies _id (ObjectId isn't directly display-friendly).
    """
    sanitized = []
    for user in users:
        clean = dict(user)
        clean.pop("password_hash", None)
        if "_id" in clean:
            clean["_id"] = str(clean["_id"])
        sanitized.append(clean)
    return sanitized


def _count_by_role(users, role_name):
    """Count how many user docs have role == role_name."""
    return sum(1 for u in users if u.get("role") == role_name)


# ==========================================================
# Section renderers
# ==========================================================

def _render_statistics_cards(users, results_count):
    """Render the four top-level statistics cards.

    Args:
        users (list): List of user documents (already fetched once,
            reused here instead of re-querying).
        results_count (int): Total documents in the results collection.
    """
    st.subheader("Overview")

    total_users = len(users)
    total_students = _count_by_role(users, "Student")
    total_teachers = _count_by_role(users, "Teacher")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Users", total_users, icon="")
    with c2:
        metric_card("Total Students", total_students, icon="")
    with c3:
        metric_card("Total Teachers", total_teachers, icon="")
    with c4:
        metric_card("Total Generated Results", results_count, icon="")


def _render_view_users_tab(users):
    """Tab 1 — View all users in a dataframe, password_hash hidden."""
    st.caption("All registered accounts. Password hashes are never displayed.")
    if not users:
        st.info("No users found in the `users` collection.")
        return

    display_rows = _sanitize_users_for_display(users)
    st.dataframe(display_rows, use_container_width=True, hide_index=True)


def _render_role_statistics_tab(users):
    """Tab 2 — Count of Admin / Teacher / Student accounts."""
    st.caption("Breakdown of accounts by role.")

    admin_count = _count_by_role(users, "Admin")
    teacher_count = _count_by_role(users, "Teacher")
    student_count = _count_by_role(users, "Student")

    r1, r2, r3 = st.columns(3)
    with r1:
        metric_card("Admin", admin_count, icon="")
    with r2:
        metric_card("Teacher", teacher_count, icon="")
    with r3:
        metric_card("Student", student_count, icon="")

    other_count = len(users) - (admin_count + teacher_count + student_count)
    if other_count > 0:
        st.caption(f"{other_count} user(s) have an unrecognized/blank role.")


def _render_account_management_tab():
    """Tab 3 — Placeholders only. No CRUD implemented in Step 2."""
    st.caption(
        "Account management actions — implementation planned for a "
        "future phase. Buttons below are placeholders and do not "
        "perform any action yet."
    )

    a1, a2, a3 = st.columns(3)
    with a1:
        st.button("Create User", use_container_width=True, disabled=True)
    with a2:
        st.button("Disable User", use_container_width=True, disabled=True)
    with a3:
        st.button("Delete User", use_container_width=True, disabled=True)

    st.info("CRUD operations (create/disable/delete) will be implemented later.")


# ==========================================================
# Main entry point
# ==========================================================

def render_admin_dashboard():
    """Render the full Admin dashboard.

    Phase 3.3 / STEP 2 — header, statistics cards, and a tabbed User
    Management section (View Users / Role Statistics / Account
    Management placeholder).
    """
    # ---------- Header ----------
    page_header("Admin Dashboard", subtitle="System Administration", icon="")

    full_name = st.session_state.get("full_name") or st.session_state.get("username")
    st.markdown(
        f"<div style='text-align:center; margin-bottom:12px;'>Welcome, <b>{full_name}</b></div>",
        unsafe_allow_html=True,
    )

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        role_badge(st.session_state.get("role", "Admin"), full_name)

    st.divider()

    # ---------- Data fetch (read-only, once per render) ----------
    if not MONGODB_AVAILABLE:
        st.warning(
            "MongoDB integration isn't available in this environment — "
            "install `pymongo` to enable Admin statistics and user management."
        )
        return

    db_connected, db_conn_msg = test_connection()
    if not db_connected:
        st.warning(f"Could not reach the database: {db_conn_msg}")
        return

    users_ok, users_or_error = _fetch_users()
    if not users_ok:
        st.error(f"Could not load users: {users_or_error}")
        return
    users = users_or_error

    results_ok, results_or_error = _fetch_results_count()
    results_count = results_or_error if results_ok else 0
    if not results_ok:
        st.caption(f"Could not load results count: {results_or_error}")

    # ---------- Statistics cards ----------
    _render_statistics_cards(users, results_count)

    st.divider()

    # ---------- User Management ----------
    st.subheader("User Management")
    tab_view, tab_roles, tab_accounts = st.tabs(
        ["View Users", "Role Statistics", "Account Management"]
    )

    with tab_view:
        _render_view_users_tab(users)

    with tab_roles:
        _render_role_statistics_tab(users)

    with tab_accounts:
        _render_account_management_tab()
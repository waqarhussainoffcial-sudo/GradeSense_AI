"""
Phase 3.3 / STEP 3 — Teacher Dashboard Implementation
dashboard/teacher_dashboard.py

Purpose:
    Full Teacher dashboard: header + role badge, statistics cards, and
    a Results Management section with three tabs (My Generated
    Results, Recent Activity, Class Overview placeholder).

IMPORTANT — schema limitation (read before extending):
    The `students` and `results` documents built in
    student_operations.py (build_student_documents / save_student_result)
    do NOT currently store who created them — there is no
    `created_by` / teacher-id field on either document. Because of
    that:
        - "My Generated Results" (Tab 1) cannot actually be filtered
          per teacher yet. It is implemented as an honest placeholder
          that explains this, rather than faking a filter or showing
          one teacher another's data.
        - The statistics cards and "Recent Activity" tab below are
          therefore SYSTEM-WIDE counts (all teachers combined), not
          per-teacher — clearly labeled as such in the UI.
    To make this genuinely per-teacher in a future phase, a
    `created_by` field would need to be added when saving results in
    student_operations.py / app.py (outside this step's allowed files).

Data access:
    Reads only from MongoDB via database.get_collection(), using the
    existing collection-name constants in config.py:
        - config.RESULTS_COLLECTION  ("results")
        - config.STUDENTS_COLLECTION ("students") — used only to
          count saved student records and to look up a student's name
          for display in Recent Activity.

Scope / rules followed:
    - Read-only: no CRUD.
    - Does not modify calculator, grading, PDF, or Excel logic.
    - Does not modify auth.py, database.py, config.py, or
      student_operations.py.
    - Wrapped in try/except so a missing pymongo/config/database still
      lets the rest of the dashboard render (with a warning) instead
      of crashing, matching the pattern already used in app.py and
      admin_dashboard.py.
    - Not wired into app.py yet.
"""

from datetime import datetime, timedelta

import streamlit as st
from dashboard.dashboard_utils import page_header, role_badge, metric_card

try:
    import config
    from database import get_collection, test_connection
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


# ==========================================================
# Data access helpers (read-only, system-wide — see module docstring)
# ==========================================================

def _fetch_students_count():
    """Count all documents in the students collection.

    Returns:
        (bool, int | str): (True, count) on success,
                            (False, error_message) on failure.
    """
    try:
        return True, get_collection(config.STUDENTS_COLLECTION).count_documents({})
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)


def _fetch_results_count():
    """Count all documents in the results collection.

    Returns:
        (bool, int | str): (True, count) on success,
                            (False, error_message) on failure.
    """
    try:
        return True, get_collection(config.RESULTS_COLLECTION).count_documents({})
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)


def _fetch_recent_results_count(days=7):
    """Count results created within the last `days` days.

    Returns:
        (bool, int | str): (True, count) on success,
                            (False, error_message) on failure.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        results_collection = get_collection(config.RESULTS_COLLECTION)
        return True, results_collection.count_documents({"created_date": {"$gte": cutoff}})
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)


def _fetch_recent_results(limit=10):
    """Fetch the most recently created result documents.

    Returns:
        (bool, list | str): (True, list_of_result_docs) on success,
                             (False, error_message) on failure.
    """
    try:
        results_collection = get_collection(config.RESULTS_COLLECTION)
        docs = list(results_collection.find({}).sort("created_date", -1).limit(limit))
        return True, docs
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)


def _lookup_students_by_ids(student_ids):
    """Fetch student docs for a list of student_ids, keyed by _id.

    Used only to show a readable student name in Recent Activity
    instead of a raw ObjectId. Read-only, no writes.

    Returns:
        (bool, dict | str): (True, {student_id: student_doc}) on
                             success, (False, error_message) on failure.
    """
    try:
        if not student_ids:
            return True, {}
        students_collection = get_collection(config.STUDENTS_COLLECTION)
        docs = list(students_collection.find({"_id": {"$in": student_ids}}))
        return True, {doc["_id"]: doc for doc in docs}
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return False, str(exc)


# ==========================================================
# Section renderers
# ==========================================================

def _render_statistics_cards(total_students, total_results, recent_count):
    """Render the three top-level statistics cards.

    All three are system-wide totals (see module docstring) since
    results/students aren't yet attributed to a specific teacher.
    """
    st.subheader("Overview")
    st.caption(
        "System-wide totals — results aren't linked to individual "
        "teachers yet, so these aren't scoped to you specifically."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Total Students Taught", total_students, icon="")
    with c2:
        metric_card("Total Results Generated", total_results, icon="")
    with c3:
        metric_card("Recent Results (7 days)", recent_count, icon="")


def _render_my_results_tab():
    """Tab 1 — 'My Generated Results'.

    Honest placeholder: the results/students documents have no
    created_by field, so there is nothing to filter by teacher yet.
    Does NOT fake a filter or show unattributed data as if it were
    "yours" — that would be misleading.
    """
    st.caption("Results generated by you, specifically.")
    st.info(
        "This can't be filtered by teacher yet — saved results don't "
        "currently record who generated them. Once a `created_by` "
        "field is added when saving results, this tab will show only "
        "your results here."
    )


def _render_recent_activity_tab(results, students_by_id):
    """Tab 2 — 'Recent Activity'.

    Shows the most recently generated results system-wide, with the
    student's name looked up for readability where available.
    """
    st.caption("Latest results generated across the system (most recent first).")

    if not results:
        st.info("No results have been generated yet.")
        return

    display_rows = []
    for r in results:
        student_doc = students_by_id.get(r.get("student_id"))
        display_rows.append({
            "Student": student_doc.get("name") if student_doc else "—",
            "Roll No": student_doc.get("roll_no") if student_doc else "—",
            "Result": r.get("result"),
            "Grade": r.get("grade"),
            "Percentage": r.get("percentage"),
            "GPA": r.get("gpa"),
            "Academic Standing": r.get("academic_standing"),
            "Generated On": (
                r["created_date"].strftime("%Y-%m-%d %H:%M")
                if r.get("created_date") else ""
            ),
        })

    st.dataframe(display_rows, use_container_width=True, hide_index=True)


def _render_class_overview_tab():
    """Tab 3 — 'Class Overview'. Placeholder for future analytics."""
    st.caption("Class-level analytics — planned for a future phase.")
    st.info(
        "This section will show class/section-level performance "
        "analytics once that functionality is implemented."
    )


# ==========================================================
# Main entry point
# ==========================================================

def render_teacher_dashboard():
    """Render the full Teacher dashboard.

    Phase 3.3 / STEP 3 — header, statistics cards, and a tabbed
    Results Management section (My Generated Results / Recent Activity
    / Class Overview placeholder).
    """
    # ---------- Header ----------
    page_header("Teacher Dashboard", subtitle="Class & Student Management", icon="")

    full_name = st.session_state.get("full_name") or st.session_state.get("username")
    st.markdown(
        f"<div style='text-align:center; margin-bottom:12px;'>Welcome, <b>{full_name}</b></div>",
        unsafe_allow_html=True,
    )

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        role_badge(st.session_state.get("role", "Teacher"), full_name)

    st.divider()

    # ---------- Data fetch (read-only, once per render) ----------
    if not MONGODB_AVAILABLE:
        st.warning(
            "MongoDB integration isn't available in this environment — "
            "install `pymongo` to enable Teacher statistics and results."
        )
        return

    db_connected, db_conn_msg = test_connection()
    if not db_connected:
        st.warning(f"Could not reach the database: {db_conn_msg}")
        return

    students_ok, students_count_or_error = _fetch_students_count()
    total_students = students_count_or_error if students_ok else 0
    if not students_ok:
        st.caption(f"Could not load student count: {students_count_or_error}")

    results_ok, results_count_or_error = _fetch_results_count()
    total_results = results_count_or_error if results_ok else 0
    if not results_ok:
        st.caption(f"Could not load results count: {results_count_or_error}")

    recent_ok, recent_count_or_error = _fetch_recent_results_count()
    recent_count = recent_count_or_error if recent_ok else 0
    if not recent_ok:
        st.caption(f"Could not load recent results count: {recent_count_or_error}")

    # ---------- Statistics cards ----------
    _render_statistics_cards(total_students, total_results, recent_count)

    st.divider()

    # ---------- Recent results (fetched once, shared with the tab below) ----------
    recent_results_ok, recent_results_or_error = _fetch_recent_results(limit=10)
    recent_results = recent_results_or_error if recent_results_ok else []
    if not recent_results_ok:
        st.caption(f"Could not load recent activity: {recent_results_or_error}")

    student_ids = [r.get("student_id") for r in recent_results if r.get("student_id")]
    lookup_ok, students_by_id_or_error = _lookup_students_by_ids(student_ids)
    students_by_id = students_by_id_or_error if lookup_ok else {}

    # ---------- Results Management ----------
    st.subheader("Results Management")
    tab_mine, tab_recent, tab_overview = st.tabs(
        ["My Generated Results", "Recent Activity", "Class Overview"]
    )

    with tab_mine:
        _render_my_results_tab()

    with tab_recent:
        _render_recent_activity_tab(recent_results, students_by_id)

    with tab_overview:
        _render_class_overview_tab()
"""
Phase 3.3 / STEP 4 — Student Dashboard Implementation
dashboard/student_dashboard.py

Purpose:
    Full Student dashboard: header + role badge, a profile section
    built from session_state, and a "My Results" section.

IMPORTANT — schema limitation (read before extending):
    There is currently NO stored link between a Student's login
    account (in the `users` collection) and any `students`/`results`
    record. Confirmed from the code already reviewed in this project:
        - At login, app.py only ever sets st.session_state.username,
          .full_name, and .role from the `users` document — no
          roll_no, no email, no student_id.
        - `results` documents (student_operations.py) only contain:
          total_marks, percentage, grade, result, gpa,
          academic_standing, created_date, student_id — no roll_no,
          no username.
        - `students` documents contain roll_no/name, but nothing
          linking back to a `users` account (no username field).
    Because there is no shared identifier between a logged-in Student
    account and any saved result, "My Results" (requirement 3) cannot
    be filtered correctly yet. Rather than guess a match (e.g. on name,
    which risks showing one student another's data) or invent a field
    that doesn't exist, this module:
        - Shows the Student Profile section using ONLY the fields
          actually present in st.session_state (full_name, username,
          role). Roll Number and Email are displayed as
          "Not available" since session_state never contains them.
        - Implements "My Results" as an honest placeholder explaining
          the missing link, consistent with the same limitation
          already flagged in teacher_dashboard.py (Phase 3.3 / STEP 3).
    To make this genuinely functional in a future phase, the `users`
    document (or session_state at login) would need to carry a
    roll_no or student_id — a change to auth.py / student_operations.py
    that is outside this step's allowed files.

Scope / rules followed:
    - Read-only: no CRUD.
    - Does not modify calculator, grading, PDF, or Excel logic.
    - Does not modify auth.py, database.py, config.py, or
      student_operations.py.
    - Does not invent fields that don't exist in the confirmed schema.
    - Not wired into app.py yet.
"""

import streamlit as st
from dashboard.dashboard_utils import page_header, role_badge, metric_card


# ==========================================================
# Section renderers
# ==========================================================

def _render_profile_section():
    """Student Profile section — built only from st.session_state.

    Roll Number and Email are shown as "Not available" because
    session_state never receives these values at login (see module
    docstring) — this is not a bug in this file, it reflects what the
    login flow in app.py actually stores today.
    """
    st.subheader("Student Profile")

    full_name = st.session_state.get("full_name") or "Not available"
    username = st.session_state.get("username") or "Not available"
    roll_no = st.session_state.get("roll_no") or "Not available"
    email = st.session_state.get("email") or "Not available"

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Full Name:**", full_name)
        st.write("**Username:**", username)
    with col2:
        st.write("**Roll Number:**", roll_no)
        st.write("**Email:**", email)


def _render_performance_summary(results):
    """Performance Summary cards: Total Results, Latest Percentage,
    Latest Grade.

    Args:
        results (list): The student's result documents, most recent
            first. Empty list is handled gracefully.
    """
    st.subheader("Performance Summary")

    total_results = len(results)
    latest = results[0] if results else None
    latest_percentage = f"{latest['percentage']:.2f}%" if latest and latest.get("percentage") is not None else "—"
    latest_grade = latest.get("grade") if latest else "—"

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Total Results", total_results, icon="")
    with c2:
        metric_card("Latest Percentage", latest_percentage, icon="")
    with c3:
        metric_card("Latest Grade", latest_grade, icon="")


def _render_results_section(results):
    """My Results section.

    Currently always shows the "no link yet" explanation (see module
    docstring) rather than a results table, since there is no
    identifier connecting a Student account to any saved result.
    `results` is accepted as a parameter so this function is ready to
    display real data as soon as that link exists — only the data
    source needs to change, not this rendering logic.
    """
    st.subheader("My Results")

    if not results:
        st.info(
            "Results can't be linked to your account yet — saved "
            "results don't currently store a roll number or username "
            "to match against. Once that link is added, your results "
            "will appear here automatically."
        )
        st.caption("No results available yet.")
        return

    # Ready for when a real identifier link exists: render a clean
    # dataframe of the student's own results.
    display_rows = [
        {
            "Result": r.get("result"),
            "Grade": r.get("grade"),
            "Percentage": r.get("percentage"),
            "GPA": r.get("gpa"),
            "Academic Standing": r.get("academic_standing"),
            "Date": (
                r["created_date"].strftime("%Y-%m-%d %H:%M")
                if r.get("created_date") else ""
            ),
        }
        for r in results
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)


# ==========================================================
# Main entry point
# ==========================================================

def render_student_dashboard():
    """Render the full Student dashboard.

    Phase 3.3 / STEP 4 — header, profile section, performance summary,
    and My Results section.
    """
    # ---------- Header ----------
    page_header("Student Dashboard", subtitle="Your Academic Overview", icon="")

    full_name = st.session_state.get("full_name") or st.session_state.get("username")
    st.markdown(
        f"<div style='text-align:center; margin-bottom:12px;'>Welcome, <b>{full_name}</b></div>",
        unsafe_allow_html=True,
    )

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        role_badge(st.session_state.get("role", "Student"), full_name)

    st.divider()

    # ---------- Profile ----------
    _render_profile_section()

    st.divider()

    # ---------- Results (no identifier link exists yet — see docstring) ----------
    # results is hardcoded to an empty list today because there is no
    # way to query "this student's" results (no shared identifier
    # between the users collection and students/results). Kept as a
    # variable — not a literal [] inline everywhere — so wiring in a
    # real query later is a one-line change here.
    results = []

    _render_performance_summary(results)

    st.divider()

    _render_results_section(results)
"""
Phase 3.3 / STEP 1 — Dashboard Architecture Base
dashboard/dashboard_utils.py

Purpose:
    Shared, reusable UI helper functions used by all role-based
    dashboards (Admin / Teacher / Student). Keeping these here avoids
    duplicating the same Streamlit markup across admin_dashboard.py,
    teacher_dashboard.py, and student_dashboard.py.

Scope / rules followed:
    - Pure presentation helpers only — no calculator, grading, PDF,
      Excel, or MongoDB logic lives here.
    - Does not import or touch auth.py, database.py, or config.py.
    - Not wired into app.py yet (Phase 3.3 Step 1 is architecture-only).
"""

import streamlit as st


def page_header(title, subtitle=None, icon=""):
    """Render a consistent, centered header for a dashboard page.

    Args:
        title (str): Main heading text (e.g. "Admin Dashboard").
        subtitle (str, optional): Secondary line shown below the title.
        icon (str, optional): Emoji/icon shown above the title.
    """
    subtitle_html = (
        f'<div style="font-size:0.9rem; color:#888; margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f"""
        <div style="text-align:center; padding: 40px 0 10px 0;">
            <div style="font-size: 48px; line-height:1;">{icon}</div>
            <div style="font-weight:700; font-size: 1.6rem; margin-top:10px;">
                {title}
            </div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, icon="", help_text=None):
    """Render a single metric using Streamlit's native st.metric.

    Thin wrapper so dashboards call one consistent function instead of
    invoking st.metric directly everywhere — makes future styling
    changes (e.g. switching to a custom HTML card) a one-place edit.

    Args:
        label (str): Metric label.
        value: Metric value (str/int/float) — display only.
        icon (str, optional): Emoji prefixed to the label.
        help_text (str, optional): Tooltip shown on hover.
    """
    st.metric(f"{icon} {label}", value, help=help_text)


def role_badge(role, full_name=None):
    """Render a small badge showing the current user's role (and name).

    Args:
        role (str): One of "Admin", "Teacher", "Student".
        full_name (str, optional): Display name shown alongside the role.
    """
    role_colors = {
        "Admin": "#8e44ad",
        "Teacher": "#2980b9",
        "Student": "#27ae60",
    }
    color = role_colors.get(role, "#888888")
    name_part = f"{full_name} · " if full_name else ""

    st.markdown(
        f"""
        <div style="display:inline-block; padding: 4px 14px; border-radius: 20px;
                     background-color: {color}22; border: 1px solid {color};
                     color: {color}; font-size: 0.85rem; font-weight: 600;">
            {name_part}{role}
        </div>
        """,
        unsafe_allow_html=True,
    )


def placeholder_notice(message):
    """Render a consistent 'coming soon' style notice for dashboards
    that haven't been implemented yet.

    Args:
        message (str): The notice text to display.
    """
    st.markdown(
        f"""
        <div style="font-size:0.95rem; color:#555; margin-top:24px;
                    border-top: 1px solid rgba(120,120,120,0.25);
                    padding-top:18px; text-align:center;">
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )

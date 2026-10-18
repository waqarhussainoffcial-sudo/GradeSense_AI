"""
student_operations.py — Database operations for student records
(Phase 3.1 / STEP 2, STEP 3, STEP 4).

This module owns the *shape* of what gets stored in MongoDB and how
it's read back. It does NOT perform any grade/GPA/percentage
calculation — it only persists/reads values that app.py has already
calculated, exactly as required by "Do not change School or University
logic."

Collections used (see config.py):
    students  — one document per saved student record (STEP 2)
    results   — one document per saved result, linked to a student via
                 student_id (STEP 2)
"""

from datetime import datetime

from pymongo.errors import PyMongoError

import config
from database import get_collection


def _students_collection():
    return get_collection(config.STUDENTS_COLLECTION)


def _results_collection():
    return get_collection(config.RESULTS_COLLECTION)


def build_student_documents(
    inst_type, session_state, subj_rows, overall_status,
    overall_grade, remark=None, gpa=None, academic_standing=None,
):
    """
    Build the `students` and `results` documents from values that have
    already been calculated in app.py. Pure data-shaping — no math here.

    Args:
        inst_type: "School" or "University"
        session_state: st.session_state (read-only access)
        subj_rows: list of per-subject dicts from build_subject_rows()
        overall_status: "PASS" or "FAIL"
        overall_grade: overall letter grade (from get_overall_grade)
        remark: teacher's remark (School only)
        gpa: semester GPA (University only)
        academic_standing: academic standing label (University only)

    Returns:
        (student_doc, result_doc): two plain dicts, ready to insert.
    """
    is_school = inst_type == "School"

    student_doc = {
        "name": session_state.get("name"),
        "roll_no": session_state.get("roll_no"),
        "institution_name": session_state.get("institution_name"),
        "institution_type": inst_type,
        "class_or_department": (
            session_state.get("student_class") if is_school
            else session_state.get("department")
        ),
        "section_or_semester": (
            session_state.get("section") if is_school
            else session_state.get("semester")
        ),
        "academic_session": (
            session_state.get("academic_session") if is_school
            else session_state.get("university_academic_session")
        ),
        "subjects": [r["subject"] for r in subj_rows],
        "marks": [r["obtained"] for r in subj_rows],
        "grades": [r["grade"] for r in subj_rows],
        "overall_grade": overall_grade,
        "gpa": gpa,
        "percentage": session_state.get("percentage"),
        "remarks": remark if is_school else academic_standing,
        "created_date": datetime.utcnow(),
    }

    result_doc = {
        "total_marks": session_state.get("total"),
        "percentage": session_state.get("percentage"),
        "grade": overall_grade,
        "result": overall_status,
        "gpa": gpa,
        "academic_standing": academic_standing,
        "created_date": datetime.utcnow(),
    }

    return student_doc, result_doc


def save_student_result(
    inst_type, session_state, subj_rows, overall_status,
    overall_grade, remark=None, gpa=None, academic_standing=None,
):
    """
    Persist a full student record (Phase 3.1 / STEP 3): inserts into
    `students`, then inserts a linked record into `results`.

    Returns:
        (success: bool, message: str)
    """
    try:
        student_doc, result_doc = build_student_documents(
            inst_type, session_state, subj_rows, overall_status,
            overall_grade, remark, gpa, academic_standing,
        )
        student_id = _students_collection().insert_one(student_doc).inserted_id
        result_doc["student_id"] = student_id
        _results_collection().insert_one(result_doc)
        return True, "Student result saved successfully."
    except PyMongoError as exc:
        return False, f"Could not save to database: {exc}"


def get_all_students(limit=200):
    """
    Fetch all saved students, most recent first (Phase 3.1 / STEP 4).

    Returns:
        (success: bool, students_or_error)
    """
    try:
        docs = list(
            _students_collection().find().sort("created_date", -1).limit(limit)
        )
        return True, docs
    except PyMongoError as exc:
        return False, str(exc)


def get_student_by_roll(roll_no):
    """
    Search saved students by exact Roll Number (Phase 3.1 / STEP 4).

    Returns:
        (success: bool, matches_or_error)
    """
    try:
        docs = list(
            _students_collection()
            .find({"roll_no": roll_no})
            .sort("created_date", -1)
        )
        return True, docs
    except PyMongoError as exc:
        return False, str(exc)


def get_result_for_student(student_id):
    """
    Fetch the linked `results` document for a given student_id.

    Returns:
        (success: bool, result_doc_or_error)
    """
    try:
        return True, _results_collection().find_one({"student_id": student_id})
    except PyMongoError as exc:
        return False, str(exc)

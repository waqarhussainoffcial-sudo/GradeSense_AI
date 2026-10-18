"""
ai_insights.py — GradeSense AI Insights Engine
================================================

This module adds the "AI touch" to GradeSense AI:

    1. generate_ai_feedback()   -> personalized strengths/weaknesses
                                    summary + study suggestions for the
                                    result that was just calculated.
    2. predict_next_performance() -> trend analysis + a simple forecast
                                    of the student's next percentage,
                                    based on their previously saved
                                    results in MongoDB (roll_no match).
    3. answer_student_question() -> a lightweight rule-based chatbot
                                    that answers common questions about
                                    the CURRENT result (grade, weakest
                                    subject, pass/fail, how to improve...).

Design notes
------------
- Fully self-contained: works out of the box with **no external API
  key**, so the app never breaks even if the user hasn't configured
  anything. It reasons directly over the marks/grades already
  calculated by app.py (no calculator/grading logic is touched or
  duplicated here — this module only *reads* results).
- If an `ANTHROPIC_API_KEY` is present in the environment (optional),
  `generate_ai_feedback()` will transparently upgrade to a real LLM
  call for a richer, more natural-sounding comment. Without a key, it
  falls back to a smart rule-based generator — so the AI feedback
  feature always works either way.
- `predict_next_performance()` is best-effort: it needs at least 2
  previously saved results for the same roll number. With 0 or 1
  saved results it returns a friendly "not enough data yet" message
  instead of failing.
"""

import os
import re

# Optional LLM upgrade path — never required.
try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


# ==========================================================
# 1. AI PERFORMANCE FEEDBACK
# ==========================================================

def _rule_based_feedback(name, subj_rows, percentage, overall_status, inst_type):
    """Offline, deterministic feedback generator (no API needed)."""
    if not subj_rows:
        return "Not enough subject data to generate feedback yet."

    scored = sorted(subj_rows, key=lambda r: r.get("obtained", 0), reverse=True)
    best = scored[0]
    worst = scored[-1]

    passed = [r for r in subj_rows if str(r.get("status", "")).upper() != "FAIL"]
    failed = [r for r in subj_rows if str(r.get("status", "")).upper() == "FAIL"]

    lines = []

    # Opening line based on overall performance band
    if percentage >= 90:
        lines.append(f"Outstanding work, {name}! An excellent, top-tier performance overall.")
    elif percentage >= 75:
        lines.append(f"Great job, {name} — a strong, consistent performance this term.")
    elif percentage >= 60:
        lines.append(f"Good effort, {name}. Your results are solid, with clear room to push higher.")
    elif percentage >= 40:
        lines.append(f"{name}, your results show potential, but a few subjects need focused attention.")
    else:
        lines.append(f"{name}, this result needs urgent attention — but every strong result starts with a plan.")

    # Strength / weakness callouts
    lines.append(
        f"Strongest subject: **{best['subject']}** ({best.get('obtained')} marks) — keep this momentum going."
    )
    lines.append(
        f"Needs the most attention: **{worst['subject']}** ({worst.get('obtained')} marks)."
    )

    # Failed subjects
    if failed:
        subj_names = ", ".join(r["subject"] for r in failed)
        lines.append(
            f"Subject(s) below the passing threshold: {subj_names}. "
            f"Prioritize these with extra practice, past papers, and a study buddy or tutor."
        )
    else:
        lines.append("No subject fell below the passing mark — a solid, well-rounded effort.")

    # Consistency check
    scores = [r.get("obtained", 0) for r in subj_rows]
    if scores:
        spread = max(scores) - min(scores)
        if spread >= 30:
            lines.append(
                "There's a wide gap between your best and weakest subject — balancing study "
                "time more evenly across subjects could raise your overall percentage significantly."
            )
        else:
            lines.append("Your performance is fairly consistent across subjects — good balance.")

    # Closing action-oriented suggestion
    if overall_status == "FAIL":
        lines.append(
            "Next step: build a subject-wise revision plan starting with the failed subject(s), "
            "aim for daily short practice sessions, and re-attempt sample papers before the next exam."
        )
    else:
        lines.append(
            "Next step: keep revising the weaker subject regularly, and set a target of "
            f"{min(100, round(percentage + 5))}% for the next exam."
        )

    return "\n\n".join(lines)


def generate_ai_feedback(name, subj_rows, percentage, overall_status, inst_type):
    """
    Generate personalized AI feedback for a student's result.

    Tries a real LLM (Anthropic Claude) if ANTHROPIC_API_KEY is set;
    otherwise falls back to the built-in rule-based generator, which
    always works.

    Returns:
        str: markdown-formatted feedback text.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if _ANTHROPIC_AVAILABLE and api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            subj_summary = ", ".join(
                f"{r['subject']}: {r.get('obtained')} marks ({r.get('status', '')})"
                for r in subj_rows
            )
            prompt = (
                f"You are an encouraging academic advisor. A {inst_type} student named {name} "
                f"scored {percentage:.2f}% overall, result: {overall_status}. "
                f"Subject-wise marks: {subj_summary}. "
                "Write a short (5-7 sentence) personalized feedback: mention their strongest "
                "and weakest subject by name, be honest but encouraging, and end with one concrete "
                "actionable study tip. Use a warm, motivating tone."
            )
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(block.text for block in resp.content if hasattr(block, "text"))
            if text.strip():
                return text.strip()
        except Exception:
            # Any API/network issue -> silently fall back, never break the app.
            pass

    return _rule_based_feedback(name, subj_rows, percentage, overall_status, inst_type)


# ==========================================================
# 2. AI GRADE / TREND PREDICTOR
# ==========================================================

def _linear_trend_forecast(percentages):
    """
    Very small pure-Python linear regression (least squares) to project
    the next value in a percentage sequence. No numpy dependency needed
    for such a small series.
    """
    n = len(percentages)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(percentages) / n

    num = sum((xs[i] - mean_x) * (percentages[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))

    if den == 0:
        slope = 0
    else:
        slope = num / den
    intercept = mean_y - slope * mean_x

    next_x = n
    predicted = intercept + slope * next_x
    predicted = max(0, min(100, predicted))
    return predicted, slope


def predict_next_performance(roll_no, mongodb_available, get_student_by_roll_fn):
    """
    Look up the student's past saved results by roll number and predict
    their likely next percentage using a simple trend line.

    Args:
        roll_no (str): roll number to search for.
        mongodb_available (bool): whether the DB layer is usable.
        get_student_by_roll_fn (callable): student_operations.get_student_by_roll

    Returns:
        dict with keys: ok (bool), message (str), and optionally
        history (list of percentages, oldest->newest), predicted (float),
        trend (str: "improving" | "declining" | "steady").
    """
    if not mongodb_available or not roll_no:
        return {
            "ok": False,
            "message": "Save results to the database first (with a Roll Number) "
                       "to unlock AI trend predictions.",
        }

    success, docs_or_error = get_student_by_roll_fn(roll_no)
    if not success:
        return {"ok": False, "message": f"Could not fetch history: {docs_or_error}"}

    docs = docs_or_error or []
    # docs are sorted most-recent-first by student_operations; reverse to oldest->newest
    docs = list(reversed(docs))
    percentages = [d.get("percentage") for d in docs if d.get("percentage") is not None]

    if len(percentages) < 2:
        return {
            "ok": False,
            "message": "Not enough saved history yet — the AI predictor needs at least "
                       "2 previously saved results for this Roll Number. "
                       f"Currently found: {len(percentages)}.",
        }

    predicted, slope = _linear_trend_forecast(percentages)

    if slope > 0.5:
        trend = "improving"
    elif slope < -0.5:
        trend = "declining"
    else:
        trend = "steady"

    return {
        "ok": True,
        "message": "Prediction generated.",
        "history": percentages,
        "predicted": round(predicted, 2),
        "trend": trend,
        "slope": round(slope, 2),
    }


# ==========================================================
# 3. AI CHATBOT (rule-based, works on the current result)
# ==========================================================

def build_chat_context(name, roll_no, subj_rows, percentage, overall_status, overall_grade, inst_type, gpa=None):
    """Bundle the current result into a small context dict the chatbot can reason over."""
    return {
        "name": name,
        "roll_no": roll_no,
        "subj_rows": subj_rows or [],
        "percentage": percentage,
        "overall_status": overall_status,
        "overall_grade": overall_grade,
        "inst_type": inst_type,
        "gpa": gpa,
    }


def answer_student_question(question, context):
    """
    Rule-based chatbot: matches the question against common intents and
    answers using the current result context. No external API needed.

    Returns:
        str: the chatbot's reply.
    """
    q = (question or "").strip().lower()
    subj_rows = context.get("subj_rows") or []
    percentage = context.get("percentage")
    name = context.get("name") or "there"
    status = context.get("overall_status")
    grade = context.get("overall_grade")
    gpa = context.get("gpa")

    if not q:
        return "Ask me anything about your result — e.g. \"What's my weakest subject?\" or \"Am I passing?\""

    if not subj_rows:
        return "I don't have a calculated result to look at yet — please calculate your grade first."

    scored = sorted(subj_rows, key=lambda r: r.get("obtained", 0), reverse=True)
    best, worst = scored[0], scored[-1]
    failed = [r for r in subj_rows if str(r.get("status", "")).upper() == "FAIL"]

    # Intent: weakest subject
    if re.search(r"weak|lowest|worst|struggl", q):
        return f"Your weakest subject is **{worst['subject']}** with {worst.get('obtained')} marks. Focus extra practice time there."

    # Intent: strongest subject
    if re.search(r"strong|best|highest|top subject", q):
        return f"Your strongest subject is **{best['subject']}** with {best.get('obtained')} marks. Great job — keep it up!"

    # Intent: pass/fail
    if re.search(r"pass|fail", q):
        if status == "FAIL":
            subj_names = ", ".join(r["subject"] for r in failed) if failed else "some subjects"
            return f"Currently your result is **FAIL**. You're below the passing mark in: {subj_names}."
        return "Good news — your current result is **PASS**!"

    # Intent: overall grade / percentage
    if re.search(r"percentage|score|marks total|overall", q):
        return f"Your overall percentage is **{percentage:.2f}%** with grade **{grade}**." if percentage is not None else "Percentage isn't available yet."

    if re.search(r"grade\b", q):
        return f"Your overall grade is **{grade}**."

    if re.search(r"gpa", q):
        return f"Your GPA is **{gpa}**." if gpa is not None else "GPA isn't applicable/available for this result."

    # Intent: how to improve
    if re.search(r"improve|better|tips|advice|study|help", q):
        return (
            f"To improve, focus first on **{worst['subject']}** since it's pulling your average down. "
            "Try daily 30-minute focused revision, past-paper practice, and asking your teacher for "
            "targeted feedback on that subject."
        )

    # Intent: subject-specific marks lookup ("marks in maths", "how did i do in physics")
    for r in subj_rows:
        subj_name = str(r.get("subject", "")).lower()
        if subj_name and subj_name in q:
            return f"In **{r['subject']}** you scored **{r.get('obtained')}** marks — status: {r.get('status', 'N/A')}."

    # Intent: greeting
    if re.search(r"^hi|^hello|^hey", q):
        return f"Hi {name}! Ask me about your grade, weakest/strongest subject, or how to improve."

    return (
        "I can help with questions like: \"What's my weakest subject?\", \"Am I passing?\", "
        "\"What's my percentage?\", or \"How can I improve?\" — try one of those!"
    )

"""
EduExaminer — Views
===================
All views use the service layer (services.py) — no direct ORM in view logic.

CO4: each view is a small named function.
CO2: exam_question iterates through question_order.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from .models import ExamConfig, Question, Subject, Attempt
from . import services


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_by_role(user):
    """Return the correct home redirect for a logged-in user."""
    if user.is_teacher():
        return redirect("examiner:teacher_dashboard")
    return redirect("examiner:student_menu")


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

def landing(request):
    """Public landing page offering Student / Teacher sign-in paths."""
    # If already logged in, skip to dashboard
    user = services.get_session_user(request.session)
    if user:
        return _redirect_by_role(user)
    return render(request, "examiner/landing.html")


# ---------------------------------------------------------------------------
# Auth — Teacher
# ---------------------------------------------------------------------------

def teacher_login(request):
    user = services.get_session_user(request.session)
    if user and user.is_teacher():
        return redirect("examiner:teacher_dashboard")

    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        teacher = services.authenticate_teacher(email, password)
        if teacher:
            services.login_user(request.session, teacher)
            return redirect("examiner:teacher_dashboard")
        error = "Invalid email or password."

    return render(request, "examiner/teacher_login.html", {"error": error})


def logout_view(request):
    services.logout_user(request.session)
    return redirect("examiner:landing")


# ---------------------------------------------------------------------------
# Auth — Student
# ---------------------------------------------------------------------------

def student_login(request):
    user = services.get_session_user(request.session)
    if user and user.is_student():
        return redirect("examiner:student_menu")

    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        reg_num = request.POST.get("register_number", "").strip()
        student = services.authenticate_student(email, password, reg_num)
        if student:
            services.login_user(request.session, student)
            return redirect("examiner:student_menu")
        error = "Invalid credentials. Check your email, password, and register number."

    return render(request, "examiner/student_login.html", {"error": error})


# ---------------------------------------------------------------------------
# Teacher Dashboard
# ---------------------------------------------------------------------------

def teacher_dashboard(request):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    subjects = services.list_subjects()
    exams = services.list_exams(teacher=teacher)
    total_questions = sum(
        s.questions.count() for s in subjects
    )

    return render(request, "examiner/teacher_dashboard.html", {
        "teacher": teacher,
        "subjects": subjects,
        "exams": exams,
        "total_questions": total_questions,
    })


# ---------------------------------------------------------------------------
# Question Management
# ---------------------------------------------------------------------------

def question_list(request):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    subject_id = request.GET.get("subject")
    query = request.GET.get("q", "").strip()
    subjects = services.list_subjects()
    questions = []

    selected_subject = None
    if subject_id:
        selected_subject = services.get_subject(int(subject_id))
        if selected_subject:
            questions = services.search_questions(selected_subject.pk, query)

    return render(request, "examiner/question_list.html", {
        "teacher": teacher,
        "subjects": subjects,
        "selected_subject": selected_subject,
        "questions": questions,
        "query": query,
    })


def question_add(request):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    subjects = services.list_subjects()
    error = None

    if request.method == "POST":
        subject_id = request.POST.get("subject_id")
        question_text = request.POST.get("question_text", "").strip()
        correct_option = request.POST.get("correct_option", "").strip()
        explanation = request.POST.get("explanation", "").strip()

        # Build options list from dynamic POST fields
        # Fields: option_id_0, option_text_0, option_id_1, option_text_1, ...
        options = []
        idx = 0
        while True:
            opt_id = request.POST.get(f"option_id_{idx}", "").strip()
            opt_text = request.POST.get(f"option_text_{idx}", "").strip()
            if not opt_id and not opt_text:
                break
            if opt_id:
                options.append({"id": opt_id, "text": opt_text})
            idx += 1

        subject = services.get_subject(int(subject_id)) if subject_id else None
        if not subject:
            error = "Please select a valid subject."
        else:
            q, err_msg = services.add_question(
                subject=subject,
                question_text=question_text,
                options=options,
                correct_option=correct_option,
                explanation=explanation,
                created_by=teacher,
            )
            if q:
                messages.success(request, "Question added successfully.")
                return redirect("examiner:question_list")
            error = err_msg

    return render(request, "examiner/question_form.html", {
        "teacher": teacher,
        "subjects": subjects,
        "error": error,
        "mode": "add",
    })


def question_edit(request, pk):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    question = get_object_or_404(Question, pk=pk)
    subjects = services.list_subjects()
    error = None

    if request.method == "POST":
        question_text = request.POST.get("question_text", "").strip()
        correct_option = request.POST.get("correct_option", "").strip()
        explanation = request.POST.get("explanation", "").strip()

        options = []
        idx = 0
        while True:
            opt_id = request.POST.get(f"option_id_{idx}", "").strip()
            opt_text = request.POST.get(f"option_text_{idx}", "").strip()
            if not opt_id and not opt_text:
                break
            if opt_id:
                options.append({"id": opt_id, "text": opt_text})
            idx += 1

        q, err_msg = services.edit_question(
            question_id=pk,
            question_text=question_text,
            options=options,
            correct_option=correct_option,
            explanation=explanation,
        )
        if q:
            messages.success(request, "Question updated successfully.")
            return redirect("examiner:question_list")
        error = err_msg

    return render(request, "examiner/question_form.html", {
        "teacher": teacher,
        "subjects": subjects,
        "question": question,
        "error": error,
        "mode": "edit",
    })


@require_POST
def question_delete(request, pk):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    ok, err_msg = services.delete_question(pk)
    if ok:
        messages.success(request, "Question deleted.")
    else:
        messages.error(request, err_msg or "Could not delete question.")
    return redirect("examiner:question_list")


# ---------------------------------------------------------------------------
# Exam Configuration
# ---------------------------------------------------------------------------

def exam_list(request):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    exams = services.list_exams(teacher=teacher)
    return render(request, "examiner/exam_list.html", {
        "teacher": teacher,
        "exams": exams,
    })


def exam_create(request):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    subjects = services.list_subjects()
    error = None

    if request.method == "POST":
        from django.utils.dateparse import parse_datetime
        subject_id = request.POST.get("subject_id")
        title = request.POST.get("title", "").strip()
        num_q = request.POST.get("num_questions", "10")
        shuffle = request.POST.get("shuffle_questions") == "on"
        duration = request.POST.get("duration_minutes", "30")
        start_str = request.POST.get("start_datetime", "")
        end_str = request.POST.get("end_datetime", "")

        subject = services.get_subject(int(subject_id)) if subject_id else None
        if not subject:
            error = "Please select a valid subject."
        else:
            try:
                num_q = int(num_q)
                duration = int(duration)
                from django.utils import timezone as tz
                import datetime
                # HTML datetime-local gives "YYYY-MM-DDTHH:MM" — convert to aware datetime
                start_dt = tz.make_aware(datetime.datetime.fromisoformat(start_str))
                end_dt = tz.make_aware(datetime.datetime.fromisoformat(end_str))
            except (ValueError, TypeError):
                error = "Invalid number or date values."
                start_dt = end_dt = None

            if not error:
                exam, err_msg = services.create_exam(
                    subject=subject,
                    title=title,
                    num_questions=num_q,
                    shuffle=shuffle,
                    duration_minutes=duration,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    created_by=teacher,
                )
                if exam:
                    messages.success(request, f"Exam '{exam.title}' created.")
                    return redirect("examiner:exam_detail", pk=exam.pk)
                error = err_msg

    return render(request, "examiner/exam_form.html", {
        "teacher": teacher,
        "subjects": subjects,
        "error": error,
    })


def exam_detail(request, pk):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    exam = get_object_or_404(ExamConfig, pk=pk)
    attempts = exam.attempts.select_related("student").order_by("-start_time")
    return render(request, "examiner/exam_detail.html", {
        "teacher": teacher,
        "exam": exam,
        "attempts": attempts,
    })


@require_POST
def exam_status_update(request, pk):
    teacher, err = services.require_teacher(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:teacher_login")

    new_status = request.POST.get("status", "")
    exam, err_msg = services.update_exam_status(pk, new_status)
    if exam:
        messages.success(request, f"Exam status updated to '{exam.get_status_display()}'.")
    else:
        messages.error(request, err_msg or "Could not update status.")
    return redirect("examiner:exam_detail", pk=pk)


# ---------------------------------------------------------------------------
# Student — Menu
# ---------------------------------------------------------------------------

def student_menu(request):
    student, err = services.require_student(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:student_login")

    all_exams = services.get_all_published_exams()
    return render(request, "examiner/student_menu.html", {
        "student": student,
        "all_exams": all_exams,
    })


# ---------------------------------------------------------------------------
# Student — Exam Flow
# ---------------------------------------------------------------------------

def exam_confirm(request, exam_id):
    """
    Confirmation dialog before the exam begins.
    Shows: exam info, live time (HH:MM:SS via JS), Continue / Go Back.
    """
    student, err = services.require_student(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:student_login")

    exam = get_object_or_404(ExamConfig, pk=exam_id)
    if not exam.is_open():
        messages.error(request, "This exam is not currently available.")
        return redirect("examiner:student_menu")

    if request.method == "POST":
        # Student clicked "Continue" — start the attempt
        attempt, err_msg = services.start_attempt(student, exam)
        if attempt:
            return redirect("examiner:exam_question", attempt_id=attempt.pk, index=0)
        messages.error(request, err_msg or "Could not start exam.")
        return redirect("examiner:student_menu")

    return render(request, "examiner/exam_confirm.html", {
        "student": student,
        "exam": exam,
    })


def exam_question(request, attempt_id, index):
    """
    Show one question at a time (CO2 — loop iteration via index).
    After the student selects an answer, show the Continue button.
    """
    student, err = services.require_student(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:student_login")

    attempt = get_object_or_404(Attempt, pk=attempt_id, student=student)

    # Block access if attempt is already finished (prevents back-button re-answer)
    if attempt.status != Attempt.STATUS_IN_PROGRESS:
        return redirect("examiner:exam_result", attempt_id=attempt.pk)

    # CO2: bounds check for the question loop
    total = len(attempt.question_order)
    if index < 0 or index >= total:
        return redirect("examiner:exam_finish", attempt_id=attempt.pk)

    # CO3: look up this question from the ordered list
    q_pk = attempt.question_order[index]
    question = get_object_or_404(Question, pk=q_pk)

    error = None
    already_answered = str(q_pk) in attempt.selected_answers

    if request.method == "POST":
        chosen = request.POST.get("selected_option", "").strip()
        if not chosen:
            error = "Please select an answer before continuing."
        else:
            ok, err_msg = services.record_answer(attempt.pk, q_pk, chosen)
            if ok:
                next_index = index + 1
                if next_index >= total:
                    return redirect("examiner:exam_finish", attempt_id=attempt.pk)
                return redirect("examiner:exam_question", attempt_id=attempt.pk, index=next_index)
            error = err_msg

    # Reload to get the latest selected_answers after save
    attempt.refresh_from_db()
    current_answer = attempt.selected_answers.get(str(q_pk), "")

    return render(request, "examiner/exam_question.html", {
        "student": student,
        "attempt": attempt,
        "exam": attempt.exam,
        "question": question,
        "question_index": index,
        "question_number": index + 1,
        "total_questions": total,
        "current_answer": current_answer,
        "already_answered": already_answered,
        "error": error,
    })


def exam_finish(request, attempt_id):
    """Finish the attempt and redirect to result."""
    student, err = services.require_student(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:student_login")

    attempt = get_object_or_404(Attempt, pk=attempt_id, student=student)
    finished, err_msg = services.finish_attempt(attempt.pk)
    if err_msg:
        messages.error(request, err_msg)
    return redirect("examiner:exam_result", attempt_id=attempt.pk)


def exam_result(request, attempt_id):
    """
    CO4: displayResult — Examination Finished page.
    Shows: Well Done message, timer (elapsed HH:MM:SS), detailed score
    breakdown (correct / wrong / unanswered), and Log Out button.
    Score is computed once at finish; refreshing cannot alter it.
    """
    student, err = services.require_student(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:student_login")

    attempt = get_object_or_404(Attempt, pk=attempt_id, student=student)

    elapsed_seconds = None
    if attempt.end_time and attempt.start_time:
        elapsed_seconds = int((attempt.end_time - attempt.start_time).total_seconds())

    # CO4: evaluateAttempt — detailed breakdown without exposing correct answers
    breakdown = services.evaluate_attempt(attempt)

    return render(request, "examiner/exam_result.html", {
        "student": student,
        "attempt": attempt,
        "exam": attempt.exam,
        "elapsed_seconds": elapsed_seconds,
        "breakdown": breakdown,
    })


# ---------------------------------------------------------------------------
# Student — Attempt History
# ---------------------------------------------------------------------------

def student_history(request):
    """
    CO4: getStudentAttempts — show past completed and timed-out attempts.
    CO2: iterate through the attempts list in the template.
    CO3: sorted by most-recent first; best score identified by max search.
    """
    student, err = services.require_student(request.session)
    if err:
        messages.error(request, err)
        return redirect("examiner:student_login")

    attempts = services.get_student_attempts(student)
    best_score = services.get_best_attempt(student)

    return render(request, "examiner/student_history.html", {
        "student": student,
        "attempts": attempts,
        "best_score": best_score,
    })


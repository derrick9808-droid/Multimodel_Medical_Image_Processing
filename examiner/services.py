"""
EduExaminer — Service / Storage Layer
======================================
All data operations go through this module.
UI views and templates never call model methods or ORM queries directly
(except through these functions).  This keeps the CO4 "small named functions"
contract visible and testable.

CO4 functions defined here:
  Authentication: authenticate_teacher(), authenticate_student(), get_session_user()
  Subjects:       list_subjects(), get_subject()
  Questions:      list_questions_for_subject(), add_question(), edit_question(),
                  delete_question(), search_questions()
  Exam config:    list_exams(), get_exam(), create_exam(), update_exam()
  Exam flow:      select_questions_for_attempt(), start_attempt(),
                  record_answer(), finish_attempt()
  Seed data:      seed_demo_data()
"""

import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from .models import ExamUser, Subject, Question, ExamConfig, Attempt


# ===========================================================================
# AUTHENTICATION  (CO4)
# ===========================================================================

def authenticate_teacher(email: str, password: str):
    """
    Verify teacher credentials.
    Returns the ExamUser or None.
    NOTE: prototype only — do not use as production authentication.
    """
    try:
        user = ExamUser.objects.get(email=email, role=ExamUser.ROLE_TEACHER, is_active=True)
    except ExamUser.DoesNotExist:
        return None
    if check_password(password, user.password_hash):
        return user
    return None


def authenticate_student(email: str, password: str, register_number: str):
    """
    Verify student credentials (email + password + register number).
    Returns the ExamUser or None.
    NOTE: prototype only — do not use as production authentication.
    """
    try:
        user = ExamUser.objects.get(
            email=email,
            register_number=register_number,
            role=ExamUser.ROLE_STUDENT,
            is_active=True,
        )
    except ExamUser.DoesNotExist:
        return None
    if check_password(password, user.password_hash):
        return user
    return None


def get_session_user(session) -> ExamUser | None:
    """Return the currently logged-in ExamUser from the Django session, or None."""
    user_id = session.get("exam_user_id")
    if not user_id:
        return None
    try:
        return ExamUser.objects.get(pk=user_id, is_active=True)
    except ExamUser.DoesNotExist:
        return None


def login_user(session, user: ExamUser):
    """Write the user's PK to the session."""
    session["exam_user_id"] = user.pk
    session["exam_user_role"] = user.role


def logout_user(session):
    """Clear exam-related session keys."""
    session.pop("exam_user_id", None)
    session.pop("exam_user_role", None)


# ===========================================================================
# ROLE GUARDS  (CO4)
# ===========================================================================

def require_teacher(session):
    """
    Return (user, error_message).
    If the session holds a teacher, error_message is None.
    Frontend checks only — not production security.
    """
    user = get_session_user(session)
    if user is None:
        return None, "Please sign in as a teacher."
    if not user.is_teacher():
        return None, "Access restricted to teachers."
    return user, None


def require_student(session):
    """Return (user, error_message) for a student session."""
    user = get_session_user(session)
    if user is None:
        return None, "Please sign in as a student."
    if not user.is_student():
        return None, "Access restricted to students."
    return user, None


# ===========================================================================
# SUBJECTS  (CO3 — searching/filtering by subject)
# ===========================================================================

def list_subjects() -> list[Subject]:
    """Return all subjects ordered alphabetically."""
    return list(Subject.objects.all())


def get_subject(subject_id: int) -> Subject | None:
    """Return a Subject by PK or None."""
    try:
        return Subject.objects.get(pk=subject_id)
    except Subject.DoesNotExist:
        return None


# ===========================================================================
# QUESTIONS  (CO2 — iterating; CO3 — searching/sorting; CO4 — CRUD)
# ===========================================================================

def list_questions_for_subject(subject_id: int) -> list[Question]:
    """
    CO3: Return all questions for a subject (search/filter by subject).
    Ordered by creation date (most recent first).
    """
    return list(Question.objects.filter(subject_id=subject_id).select_related("subject"))


def search_questions(subject_id: int, query: str) -> list[Question]:
    """
    CO3: Search questions whose text contains `query` (case-insensitive).
    Demonstrates searching within a structured collection.
    """
    qs = Question.objects.filter(subject_id=subject_id)
    if query:
        qs = qs.filter(question_text__icontains=query)
    return list(qs.select_related("subject"))


def add_question(
    subject: Subject,
    question_text: str,
    options: list[dict],
    correct_option: str,
    explanation: str = "",
    created_by: ExamUser = None,
) -> tuple[Question | None, str | None]:
    """
    CO4: Create a new MCQ question.
    Returns (question, None) on success or (None, error_message) on failure.

    Validates:
    - question_text not empty
    - at least two options
    - exactly one correct answer (correct_option matches an option id)
    """
    if not question_text.strip():
        return None, "Question text cannot be empty."
    if len(options) < 2:
        return None, "A question must have at least two options."
    ids = {o.get("id") for o in options}
    if correct_option not in ids:
        return None, f"correct_option '{correct_option}' must match one of the option IDs."
    # Prevent duplicate empty option texts
    texts = [o.get("text", "").strip() for o in options]
    if any(t == "" for t in texts):
        return None, "Option texts must not be empty."

    q = Question.objects.create(
        subject=subject,
        question_text=question_text.strip(),
        options=options,
        correct_option=correct_option,
        explanation=explanation,
        created_by=created_by,
    )
    return q, None


def edit_question(
    question_id: int,
    question_text: str = None,
    options: list[dict] = None,
    correct_option: str = None,
    explanation: str = None,
) -> tuple[Question | None, str | None]:
    """CO4: Update an existing question's fields."""
    try:
        q = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return None, "Question not found."

    if question_text is not None:
        if not question_text.strip():
            return None, "Question text cannot be empty."
        q.question_text = question_text.strip()
    if options is not None:
        if len(options) < 2:
            return None, "A question must have at least two options."
        q.options = options
    if correct_option is not None:
        ids = {o.get("id") for o in q.options}
        if correct_option not in ids:
            return None, f"correct_option '{correct_option}' not found in options."
        q.correct_option = correct_option
    if explanation is not None:
        q.explanation = explanation

    q.save()
    return q, None


def delete_question(question_id: int) -> tuple[bool, str | None]:
    """CO4: Delete a question by PK. Returns (True, None) or (False, error)."""
    try:
        Question.objects.get(pk=question_id).delete()
        return True, None
    except Question.DoesNotExist:
        return False, "Question not found."


# ===========================================================================
# EXAM CONFIGURATION  (CO4)
# ===========================================================================

def list_exams(teacher: ExamUser = None) -> list[ExamConfig]:
    """Return all exam configs, optionally filtered to a specific teacher."""
    qs = ExamConfig.objects.select_related("subject")
    if teacher:
        qs = qs.filter(created_by=teacher)
    return list(qs)


def get_exam(exam_id: int) -> ExamConfig | None:
    """Return an ExamConfig by PK or None."""
    try:
        return ExamConfig.objects.select_related("subject").get(pk=exam_id)
    except ExamConfig.DoesNotExist:
        return None


def create_exam(
    subject: Subject,
    title: str,
    num_questions: int,
    shuffle: bool,
    duration_minutes: int,
    start_datetime,
    end_datetime,
    created_by: ExamUser,
) -> tuple[ExamConfig | None, str | None]:
    """CO4: Create a new ExamConfig."""
    if not title.strip():
        return None, "Exam title cannot be empty."
    if num_questions < 1:
        return None, "Number of questions must be at least 1."
    if end_datetime <= start_datetime:
        return None, "End date/time must be after start date/time."
    bank_size = subject.questions.count()
    if num_questions > bank_size:
        return None, (
            f"Only {bank_size} questions exist for '{subject.name}'. "
            f"Cannot configure {num_questions} questions."
        )

    exam = ExamConfig.objects.create(
        subject=subject,
        title=title.strip(),
        num_questions=num_questions,
        shuffle_questions=shuffle,
        duration_minutes=duration_minutes,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        created_by=created_by,
        status=ExamConfig.STATUS_DRAFT,
    )
    return exam, None


def update_exam_status(exam_id: int, status: str) -> tuple[ExamConfig | None, str | None]:
    """CO4: Publish or close an exam."""
    exam = get_exam(exam_id)
    if exam is None:
        return None, "Exam not found."
    valid = {s for s, _ in ExamConfig.STATUS_CHOICES}
    if status not in valid:
        return None, f"Invalid status '{status}'."
    exam.status = status
    exam.save(update_fields=["status", "updated_at"])
    return exam, None


# ===========================================================================
# EXAM FLOW  (CO2 — repeated loop; CO3 — select/shuffle; CO4 — functions)
# ===========================================================================

def select_questions_for_attempt(exam: ExamConfig) -> list[int]:
    """
    CO3: Select `exam.num_questions` question PKs from the subject's bank.
    If shuffle is on, the selection is randomized (CO3 — sorting/shuffling).
    Returns a list of PKs in presentation order.
    """
    all_pks = list(
        exam.subject.questions.values_list("pk", flat=True)
    )

    # CO3 — shuffling (a sort operation on a collection)
    if exam.shuffle_questions:
        random.shuffle(all_pks)

    # CO2 — take the first N (iteration over the bank)
    selected = all_pks[: exam.num_questions]
    return selected


def start_attempt(student: ExamUser, exam: ExamConfig) -> tuple[Attempt | None, str | None]:
    """
    CO4: Begin a new attempt.
    - Checks the exam window (prototype: browser/server time comparison).
    - Prevents duplicate active attempts.
    - Selects and orders questions.

    NOTE (prototype): exam window is checked here server-side.
    In production, all time checks must happen server-side only.
    """
    if not exam.is_open():
        return None, "This exam is not currently open."

    # Prevent a second active attempt
    if Attempt.objects.filter(
        student=student, exam=exam, status=Attempt.STATUS_IN_PROGRESS
    ).exists():
        existing = Attempt.objects.get(
            student=student, exam=exam, status=Attempt.STATUS_IN_PROGRESS
        )
        return existing, None  # Resume the existing attempt

    pks = select_questions_for_attempt(exam)
    if not pks:
        return None, "No questions available for this exam."

    attempt = Attempt.objects.create(
        student=student,
        exam=exam,
        question_order=pks,
        selected_answers={},
        total_questions=len(pks),
        status=Attempt.STATUS_IN_PROGRESS,
    )
    return attempt, None


def record_answer(attempt_id: int, question_pk: int, option_id: str) -> tuple[bool, str | None]:
    """
    CO4: Store the student's answer for one question.
    Returns (True, None) on success or (False, error) on failure.
    """
    try:
        attempt = Attempt.objects.get(pk=attempt_id, status=Attempt.STATUS_IN_PROGRESS)
    except Attempt.DoesNotExist:
        return False, "Active attempt not found."

    if question_pk not in attempt.question_order:
        return False, "Question is not part of this attempt."

    attempt.selected_answers[str(question_pk)] = option_id
    attempt.save(update_fields=["selected_answers"])
    return True, None


def finish_attempt(attempt_id: int) -> tuple["Attempt | None", str | None]:
    """
    CO4: Mark the attempt as completed, compute and store the score.
    CO2+CO3: delegates to complete_attempt() → calculate_score() → evaluate_attempt().
    Idempotent: safe to call multiple times (double-submit / refresh protection).
    """
    return complete_attempt(attempt_id, status=Attempt.STATUS_COMPLETED)


def evaluate_attempt(attempt: "Attempt") -> dict:
    """
    CO4: evaluateAttempt — produce a detailed breakdown of the finished attempt.
    CO2: loops through question_order to classify each answer.
    CO3: uses selected_answers dict (key lookup by str(pk)) and question map.

    Returns a dict:
      {
        'correct':    <int>,
        'wrong':      <int>,
        'unanswered': <int>,
        'total':      <int>,
        'score':      <int>,   # same as correct
      }
    Does NOT expose which option was correct — just counts.
    """
    order = attempt.question_order           # CO3: ordered list of PKs
    answers = attempt.selected_answers       # CO3: {str(pk): option_id}

    # CO3: build a question map (associative array keyed by str pk)
    questions_map = {
        str(q.pk): q
        for q in Question.objects.filter(pk__in=order)
    }

    correct = 0
    wrong = 0
    unanswered = 0

    # CO2: loop through each question in attempt order
    for pk in order:
        q = questions_map.get(str(pk))
        if q is None:
            unanswered += 1
            continue
        chosen = answers.get(str(pk), "")
        if not chosen:
            unanswered += 1
        elif chosen == q.correct_option:
            correct += 1
        else:
            wrong += 1

    return {
        "correct": correct,
        "wrong": wrong,
        "unanswered": unanswered,
        "total": len(order),
        "score": correct,
    }


def calculate_score(attempt: "Attempt") -> tuple[int, int]:
    """
    CO4: calculateScore — thin wrapper returning (score, total).
    Delegates detail to evaluate_attempt for DRY compliance.
    """
    result = evaluate_attempt(attempt)
    return result["score"], result["total"]


def complete_attempt(attempt_id: int, status: str = None) -> tuple["Attempt | None", str | None]:
    """
    CO4: completeAttempt — safely finish an attempt, handling idempotency.
    If the attempt is already finished, returns it unchanged (prevents duplicate scoring).
    Optional status override allows setting STATUS_TIMED_OUT vs STATUS_COMPLETED.
    """
    try:
        attempt = Attempt.objects.get(pk=attempt_id)
    except Attempt.DoesNotExist:
        return None, "Attempt not found."

    # Idempotency: already finished — return as-is without altering score
    if attempt.status != Attempt.STATUS_IN_PROGRESS:
        return attempt, None

    score, total = calculate_score(attempt)
    final_status = status or Attempt.STATUS_COMPLETED

    attempt.score = score
    attempt.total_questions = total
    attempt.status = final_status
    attempt.end_time = timezone.now()
    attempt.save(update_fields=["score", "total_questions", "status", "end_time"])
    return attempt, None


def get_student_attempts(student: "ExamUser") -> list["Attempt"]:
    """
    CO3: getStudentAttempts — return all completed/timed-out attempts for a student.
    CO2: results are iterable for history display.
    CO4: focused named function; no business logic in view.
    """
    return list(
        Attempt.objects.filter(
            student=student,
            status__in=[Attempt.STATUS_COMPLETED, Attempt.STATUS_TIMED_OUT],
        )
        .select_related("exam", "exam__subject")
        .order_by("-start_time")
    )


def get_best_attempt(student: "ExamUser") -> "Attempt | None":
    """
    CO3: Find the student's highest-scoring completed attempt (search/sort on score).
    Returns the Attempt with the maximum score, or None if no attempts exist.
    """
    attempts = get_student_attempts(student)
    if not attempts:
        return None
    # CO3: find maximum by key — equivalent to searching a sorted array for max
    return max(attempts, key=lambda a: (a.score or 0))


def get_open_exams_for_student() -> list[ExamConfig]:
    """
    CO3: Return all currently open published exams (window is active).
    Students see this list on their menu.
    """
    now = timezone.now()
    return list(
        ExamConfig.objects.filter(
            status=ExamConfig.STATUS_PUBLISHED,
            start_datetime__lte=now,
            end_datetime__gte=now,
        ).select_related("subject")
    )


def get_all_published_exams() -> list[dict]:
    """
    CO3: Return all published exams with availability annotation.
    CO2: Loops through exam list to classify each one.
    CO4: get_all_published_exams — provides context for student menu.

    Each item is a dict:
      {
        'exam': ExamConfig,
        'is_open': bool,       # can start now
        'is_upcoming': bool,   # not yet started
        'is_closed': bool,     # window has passed
        'reason': str,         # human-readable unavailability note
      }
    """
    now = timezone.now()
    exams = list(
        ExamConfig.objects.filter(status=ExamConfig.STATUS_PUBLISHED)
        .select_related("subject")
        .order_by("start_datetime")
    )

    # CO2: iterate through published exams and annotate each
    result = []
    for exam in exams:
        is_open = exam.start_datetime <= now <= exam.end_datetime
        is_upcoming = now < exam.start_datetime
        is_closed = now > exam.end_datetime
        if is_open:
            reason = ""
        elif is_upcoming:
            reason = f"Opens {exam.start_datetime.strftime('%b %d, %H:%M')}"
        else:
            reason = "Window closed"
        result.append({
            "exam": exam,
            "is_open": is_open,
            "is_upcoming": is_upcoming,
            "is_closed": is_closed,
            "reason": reason,
        })
    return result


# ===========================================================================
# SEED DEMO DATA  (runs once; never duplicates)
# ===========================================================================

def seed_demo_data():
    """
    Insert demo teachers, students, subjects, questions, and an exam config.
    Safe to call on every startup — checks for existence before inserting.

    PROTOTYPE ONLY: passwords are hashed with Django's PBKDF2 hasher.
    Demo credentials are intentionally visible in source for development.
    """
    # ----- Teachers -----
    teacher_data = [
        {
            "email": "teacher@edu.example",
            "display_name": "Dr. Ananya Krishnan",
            "password": "teach123",
            "role": ExamUser.ROLE_TEACHER,
        }
    ]
    teachers = {}
    for td in teacher_data:
        t, created = ExamUser.objects.get_or_create(
            email=td["email"],
            defaults={
                "display_name": td["display_name"],
                "password_hash": make_password(td["password"]),
                "role": td["role"],
            },
        )
        teachers[td["email"]] = t

    teacher = teachers["teacher@edu.example"]

    # ----- Students -----
    student_data = [
        {
            "email": "student1@edu.example",
            "display_name": "Arjun Mehta",
            "password": "student123",
            "register_number": "REG2024001",
        },
        {
            "email": "student2@edu.example",
            "display_name": "Priya Sharma",
            "password": "student123",
            "register_number": "REG2024002",
        },
    ]
    for sd in student_data:
        ExamUser.objects.get_or_create(
            email=sd["email"],
            defaults={
                "display_name": sd["display_name"],
                "password_hash": make_password(sd["password"]),
                "role": ExamUser.ROLE_STUDENT,
                "register_number": sd["register_number"],
            },
        )

    # ----- Subjects -----
    cs_sub, _ = Subject.objects.get_or_create(
        name="Computer Science Fundamentals",
        defaults={
            "description": "Core CS concepts: algorithms, data structures, and programming.",
            "created_by": teacher,
        },
    )
    maths_sub, _ = Subject.objects.get_or_create(
        name="Discrete Mathematics",
        defaults={
            "description": "Logic, sets, graph theory, and combinatorics.",
            "created_by": teacher,
        },
    )

    # ----- Questions: Computer Science -----
    cs_questions = [
        {
            "question_text": "Which data structure uses LIFO (Last In, First Out) ordering?",
            "options": [
                {"id": "A", "text": "Queue"},
                {"id": "B", "text": "Stack"},
                {"id": "C", "text": "Linked List"},
                {"id": "D", "text": "Binary Tree"},
            ],
            "correct_option": "B",
            "explanation": "A Stack follows LIFO — the last element pushed is the first popped.",
        },
        {
            "question_text": "What is the time complexity of binary search on a sorted array?",
            "options": [
                {"id": "A", "text": "O(n)"},
                {"id": "B", "text": "O(n²)"},
                {"id": "C", "text": "O(log n)"},
                {"id": "D", "text": "O(1)"},
            ],
            "correct_option": "C",
            "explanation": "Binary search halves the search space each iteration, giving O(log n).",
        },
        {
            "question_text": "Which sorting algorithm has the best average-case time complexity?",
            "options": [
                {"id": "A", "text": "Bubble Sort — O(n²)"},
                {"id": "B", "text": "Selection Sort — O(n²)"},
                {"id": "C", "text": "Merge Sort — O(n log n)"},
                {"id": "D", "text": "Insertion Sort — O(n²)"},
            ],
            "correct_option": "C",
            "explanation": "Merge Sort guarantees O(n log n) in all cases.",
        },
        {
            "question_text": "In C, what does the keyword 'static' do when applied to a local variable?",
            "options": [
                {"id": "A", "text": "Makes the variable read-only"},
                {"id": "B", "text": "Allocates the variable on the heap"},
                {"id": "C", "text": "Retains the variable's value between function calls"},
                {"id": "D", "text": "Exports the variable for external linkage"},
            ],
            "correct_option": "C",
            "explanation": "A static local variable persists between calls; it is initialised once.",
        },
        {
            "question_text": "Which of the following is NOT a characteristic of a queue?",
            "options": [
                {"id": "A", "text": "FIFO ordering"},
                {"id": "B", "text": "Enqueue at the rear"},
                {"id": "C", "text": "Dequeue from the front"},
                {"id": "D", "text": "Access any element by index"},
            ],
            "correct_option": "D",
            "explanation": "Queues only allow access at the front and rear, not arbitrary indexing.",
        },
        {
            "question_text": "What is the output of: printf(\"%d\", 5 & 3); in C?",
            "options": [
                {"id": "A", "text": "8"},
                {"id": "B", "text": "1"},
                {"id": "C", "text": "0"},
                {"id": "D", "text": "15"},
            ],
            "correct_option": "B",
            "explanation": "5 is 101 in binary, 3 is 011. Bitwise AND = 001 = 1.",
        },
    ]

    for qd in cs_questions:
        Question.objects.get_or_create(
            subject=cs_sub,
            question_text=qd["question_text"],
            defaults={
                "options": qd["options"],
                "correct_option": qd["correct_option"],
                "explanation": qd["explanation"],
                "created_by": teacher,
            },
        )

    # ----- Questions: Discrete Mathematics -----
    maths_questions = [
        {
            "question_text": "What is the negation of the statement 'All cats are black'?",
            "options": [
                {"id": "A", "text": "No cats are black"},
                {"id": "B", "text": "Some cats are not black"},
                {"id": "C", "text": "All cats are not black"},
                {"id": "D", "text": "Some cats are black"},
            ],
            "correct_option": "B",
            "explanation": "The negation of ∀x P(x) is ∃x ¬P(x): at least one cat is not black.",
        },
        {
            "question_text": "How many edges does a complete graph K₅ have?",
            "options": [
                {"id": "A", "text": "5"},
                {"id": "B", "text": "10"},
                {"id": "C", "text": "15"},
                {"id": "D", "text": "20"},
            ],
            "correct_option": "B",
            "explanation": "K₅ has n(n-1)/2 = 5×4/2 = 10 edges.",
        },
        {
            "question_text": "What is 2^8 (2 raised to the power 8)?",
            "options": [
                {"id": "A", "text": "128"},
                {"id": "B", "text": "512"},
                {"id": "C", "text": "256"},
                {"id": "D", "text": "64"},
            ],
            "correct_option": "C",
            "explanation": "2^8 = 256.",
        },
        {
            "question_text": "Which of the following sets is the power set of {a, b}?",
            "options": [
                {"id": "A", "text": "{ {}, {a}, {b} }"},
                {"id": "B", "text": "{ {a}, {b}, {a,b} }"},
                {"id": "C", "text": "{ {}, {a}, {b}, {a,b} }"},
                {"id": "D", "text": "{ {a,b} }"},
            ],
            "correct_option": "C",
            "explanation": "The power set of a 2-element set has 2² = 4 subsets, including the empty set.",
        },
        {
            "question_text": "In how many ways can 4 students be arranged in a row?",
            "options": [
                {"id": "A", "text": "4"},
                {"id": "B", "text": "16"},
                {"id": "C", "text": "24"},
                {"id": "D", "text": "12"},
            ],
            "correct_option": "C",
            "explanation": "4! = 4×3×2×1 = 24 permutations.",
        },
        {
            "question_text": "Which logical connective represents 'if and only if'?",
            "options": [
                {"id": "A", "text": "∧ (AND)"},
                {"id": "B", "text": "∨ (OR)"},
                {"id": "C", "text": "→ (implication)"},
                {"id": "D", "text": "↔ (biconditional)"},
            ],
            "correct_option": "D",
            "explanation": "The biconditional (↔) is true when both sides have the same truth value.",
        },
    ]

    for qd in maths_questions:
        Question.objects.get_or_create(
            subject=maths_sub,
            question_text=qd["question_text"],
            defaults={
                "options": qd["options"],
                "correct_option": qd["correct_option"],
                "explanation": qd["explanation"],
                "created_by": teacher,
            },
        )

    # ----- Demo ExamConfig -----
    now = timezone.now()
    ExamConfig.objects.get_or_create(
        title="CS Fundamentals — Demo Exam",
        defaults={
            "subject": cs_sub,
            "num_questions": 5,
            "shuffle_questions": True,
            "duration_minutes": 15,
            "start_datetime": now - timedelta(hours=1),
            "end_datetime": now + timedelta(hours=23),
            "status": ExamConfig.STATUS_PUBLISHED,
            "created_by": teacher,
        },
    )


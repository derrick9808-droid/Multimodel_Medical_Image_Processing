"""
EduExaminer — Data Models
=========================
Covers all entities described in the product brief:
  User (teacher / student), Subject, Question, ExamConfig, Attempt.

CO4 mapping: each model is a small, clearly named "structure" mirroring
C struct usage; relationships map to C array-of-structs patterns.
"""

import uuid
import json
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_uuid():
    """Return a new UUID4 string — stable, collision-free question IDs."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class ExamUser(models.Model):
    """
    Represents either a Teacher or a Student.
    Kept separate from Django's built-in User to avoid coupling with the
    existing MedAI auth system.

    CO4: authentication, role-based access, login/logout functions operate
    on this model.
    """
    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"
    ROLE_CHOICES = [
        (ROLE_TEACHER, "Teacher"),
        (ROLE_STUDENT, "Student"),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    display_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    # Hashed password (use Django's make_password / check_password helpers)
    password_hash = models.CharField(max_length=256)
    # Student-only: register number (blank for teachers)
    register_number = models.CharField(max_length=50, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["role", "display_name"]
        verbose_name = "Exam User"

    def __str__(self):
        return f"{self.display_name} ({self.get_role_display()})"

    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    def is_student(self):
        return self.role == self.ROLE_STUDENT


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

class Subject(models.Model):
    """
    An academic subject / paper that questions belong to.
    CO3: questions are searched/filtered by subject.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        ExamUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_subjects",
        limit_choices_to={"role": ExamUser.ROLE_TEACHER},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------

class Question(models.Model):
    """
    A single MCQ question with a variable-length list of options.

    Options are stored as a JSON array: [{"id": "A", "text": "..."}, ...]
    correct_option holds the matching id string (e.g. "A").

    CO2: iterating through the question bank to build an exam.
    CO3: questions can be searched by subject or text; sorted by creation.
    CO4: add_question(), edit_question(), delete_question() operate here.
    """
    # Stable external ID (survives row re-numbering)
    stable_id = models.CharField(
        max_length=36, default=_new_uuid, unique=True, editable=False
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="questions"
    )
    question_text = models.TextField()
    # JSON: [{"id": "A", "text": "Option text"}, ...]
    options = models.JSONField(default=list)
    # Must match one of the ids in options
    correct_option = models.CharField(max_length=10)
    # Optional explanation shown after the exam (not during)
    explanation = models.TextField(blank=True)
    created_by = models.ForeignKey(
        ExamUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_questions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.subject.name}] {self.question_text[:60]}"

    def clean(self):
        """
        Validate that:
          - at least two options exist
          - correct_option matches one of the option ids
        """
        from django.core.exceptions import ValidationError
        opts = self.options or []
        if len(opts) < 2:
            raise ValidationError("A question must have at least two options.")
        ids = {o.get("id") for o in opts}
        if self.correct_option not in ids:
            raise ValidationError(
                f"correct_option '{self.correct_option}' is not among the option ids."
            )


# ---------------------------------------------------------------------------
# ExamConfig
# ---------------------------------------------------------------------------

class ExamConfig(models.Model):
    """
    Teacher-defined exam settings for a subject.

    CO2: num_questions controls the loop count when presenting the exam.
    CO3: shuffle_questions triggers a random selection/sort of the bank.
    CO4: configure_exam(), publish_exam(), check_exam_window() functions.
    """
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CLOSED, "Closed"),
    ]

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="exam_configs"
    )
    title = models.CharField(max_length=300)
    num_questions = models.PositiveIntegerField(
        default=10, help_text="How many questions to draw from the bank per attempt."
    )
    shuffle_questions = models.BooleanField(
        default=True,
        help_text="Randomly order the selected questions for each student.",
    )
    # Duration in minutes
    duration_minutes = models.PositiveIntegerField(
        default=30, help_text="Exam duration in minutes."
    )
    start_datetime = models.DateTimeField(
        help_text="Students may begin the exam from this time."
    )
    end_datetime = models.DateTimeField(
        help_text="Students may no longer start after this time."
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    created_by = models.ForeignKey(
        ExamUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_exams",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_datetime"]

    def __str__(self):
        return f"{self.title} ({self.subject.name})"

    def is_open(self):
        """Return True if the exam window is currently active (browser-side check)."""
        now = timezone.now()
        return (
            self.status == self.STATUS_PUBLISHED
            and self.start_datetime <= now <= self.end_datetime
        )

    def available_question_count(self):
        """Return how many questions exist in the subject bank."""
        return self.subject.questions.count()


# ---------------------------------------------------------------------------
# Attempt
# ---------------------------------------------------------------------------

class Attempt(models.Model):
    """
    One student's attempt at an exam.

    question_order: JSON list of Question PKs in the order presented.
    selected_answers: JSON dict {question_pk: chosen_option_id}.

    CO2: looping through question_order to grade each answer.
    CO3: searching selected_answers dict (key lookup) to score.
    CO4: start_attempt(), record_answer(), finish_attempt(), grade_attempt().
    """
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_TIMED_OUT = "timed_out"
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_TIMED_OUT, "Timed Out"),
    ]

    student = models.ForeignKey(
        ExamUser,
        on_delete=models.CASCADE,
        related_name="attempts",
        limit_choices_to={"role": ExamUser.ROLE_STUDENT},
    )
    exam = models.ForeignKey(
        ExamConfig, on_delete=models.CASCADE, related_name="attempts"
    )
    # Ordered list of Question PKs the student will see
    question_order = models.JSONField(default=list)
    # {str(question_pk): "option_id", ...}
    selected_answers = models.JSONField(default=dict)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS
    )
    # Computed at finish time
    score = models.PositiveIntegerField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-start_time"]
        # One in-progress attempt per student per exam at a time
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam"],
                condition=models.Q(status="in_progress"),
                name="unique_active_attempt_per_student_exam",
            )
        ]

    def __str__(self):
        return (
            f"Attempt by {self.student.display_name} on {self.exam.title} "
            f"[{self.get_status_display()}]"
        )

    def grade(self):
        """
        CO2+CO3+CO4: Iterate through question_order, look up each answer,
        compare to correct_option, accumulate score.
        Returns (score, total).
        """
        score = 0
        order = self.question_order  # list of PKs
        answers = self.selected_answers  # {str(pk): option_id}

        # CO2 — loop through each question
        questions_map = {
            str(q.pk): q
            for q in Question.objects.filter(pk__in=order)
        }

        for pk in order:
            q = questions_map.get(str(pk))
            if q is None:
                continue
            chosen = answers.get(str(pk), "")
            # CO3 — simple equality search
            if chosen == q.correct_option:
                score += 1

        return score, len(order)


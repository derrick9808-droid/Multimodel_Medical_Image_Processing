"""
EduExaminer — URL Configuration
"""
from django.urls import path
from . import views

app_name = "examiner"

urlpatterns = [
    # ── Landing ──────────────────────────────────────────────────────
    path("", views.landing, name="landing"),

    # ── Teacher auth ─────────────────────────────────────────────────
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    path("teacher/logout/", views.logout_view, name="logout"),

    # ── Teacher dashboard & question management ───────────────────────
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/questions/", views.question_list, name="question_list"),
    path("teacher/questions/add/", views.question_add, name="question_add"),
    path("teacher/questions/<int:pk>/edit/", views.question_edit, name="question_edit"),
    path("teacher/questions/<int:pk>/delete/", views.question_delete, name="question_delete"),

    # ── Exam configuration ────────────────────────────────────────────
    path("teacher/exams/", views.exam_list, name="exam_list"),
    path("teacher/exams/create/", views.exam_create, name="exam_create"),
    path("teacher/exams/<int:pk>/", views.exam_detail, name="exam_detail"),
    path("teacher/exams/<int:pk>/status/", views.exam_status_update, name="exam_status_update"),

    # ── Student auth ──────────────────────────────────────────────────
    path("student/login/", views.student_login, name="student_login"),

    # ── Student exam flow ─────────────────────────────────────────────
    path("student/menu/", views.student_menu, name="student_menu"),
    path("student/exam/<int:exam_id>/confirm/", views.exam_confirm, name="exam_confirm"),
    path("student/exam/<int:attempt_id>/question/<int:index>/", views.exam_question, name="exam_question"),
    path("student/exam/<int:attempt_id>/finish/", views.exam_finish, name="exam_finish"),
    path("student/exam/<int:attempt_id>/result/", views.exam_result, name="exam_result"),
    path("student/history/", views.student_history, name="student_history"),
]


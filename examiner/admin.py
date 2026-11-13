from django.contrib import admin
from .models import ExamUser, Subject, Question, ExamConfig, Attempt


@admin.register(ExamUser)
class ExamUserAdmin(admin.ModelAdmin):
    list_display = ["display_name", "email", "role", "register_number", "is_active"]
    list_filter = ["role", "is_active"]
    search_fields = ["display_name", "email", "register_number"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "created_by", "created_at"]
    search_fields = ["name"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_text_short", "subject", "correct_option", "created_at"]
    list_filter = ["subject"]
    search_fields = ["question_text"]

    def question_text_short(self, obj):
        return obj.question_text[:60]
    question_text_short.short_description = "Question"


@admin.register(ExamConfig)
class ExamConfigAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "num_questions", "status", "start_datetime", "end_datetime"]
    list_filter = ["status", "subject"]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ["student", "exam", "status", "score", "total_questions", "start_time"]
    list_filter = ["status"]


"""
EduExaminer AppConfig — auto-seeds demo data on startup.
"""
from django.apps import AppConfig


class ExaminerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "examiner"
    verbose_name = "EduExaminer"

    def ready(self):
        """
        Run seed_demo_data() once when Django starts.
        Uses get_or_create internally — safe on every restart.
        Wrapped in try/except so a missing migration doesn't crash startup.
        """
        try:
            from .services import seed_demo_data
            seed_demo_data()
        except Exception:
            # Tables may not exist yet (before first migrate) — skip silently.
            pass

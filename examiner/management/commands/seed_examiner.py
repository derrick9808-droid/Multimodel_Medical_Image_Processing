"""
Management command: python manage.py seed_examiner

Seeds demo data for EduExaminer. Safe to run multiple times —
it uses get_or_create so no duplicate records are produced.
"""
from django.core.management.base import BaseCommand
from examiner.services import seed_demo_data


class Command(BaseCommand):
    help = "Seed EduExaminer demo data (teachers, students, subjects, questions, exam)."

    def handle(self, *args, **options):
        seed_demo_data()
        self.stdout.write(self.style.SUCCESS(
            "EduExaminer demo data seeded successfully.\n"
            "  Teacher login : teacher@edu.example / teach123\n"
            "  Student login : student1@edu.example / student123 / REG2024001\n"
            "  Student login : student2@edu.example / student123 / REG2024002\n"
        ))


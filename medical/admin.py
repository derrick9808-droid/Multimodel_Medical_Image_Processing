from django.contrib import admin
from .models import PatientCase, ScanImage, AnalysisReport

@admin.register(PatientCase)
class PatientCaseAdmin(admin.ModelAdmin):
    list_display = ("patient_name", "patient_id", "created_at")

@admin.register(ScanImage)
class ScanImageAdmin(admin.ModelAdmin):
    list_display = ("case", "scan_type", "uploaded_at")

@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ("case", "created_at", "status")

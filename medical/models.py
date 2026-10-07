from django.db import models


class PatientCase(models.Model):
    """Stores all patient information submitted by the doctor."""
    patient_name = models.CharField(max_length=200, default="Anonymous Patient")
    patient_id = models.CharField(max_length=100, blank=True, help_text="Hospital/clinic patient ID")
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[
        ("male", "Male"), ("female", "Female"), ("other", "Other")
    ], blank=True)
    chief_complaint = models.TextField(blank=True, help_text="Primary complaint / reason for visit")
    clinical_history = models.TextField(blank=True, help_text="Detailed patient history, symptoms, duration")
    medications = models.TextField(blank=True, help_text="Current medications and dosages")
    allergies = models.TextField(blank=True)
    lab_results = models.TextField(blank=True, help_text="Blood work, urine, pathology results")
    vital_signs = models.TextField(blank=True, help_text="BP, HR, temperature, SpO2, weight, height")
    referring_doctor = models.CharField(max_length=200, blank=True)
    specialty_context = models.CharField(max_length=100, blank=True,
        help_text="e.g., Cardiology, Radiology, Neurology")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient_name} ({self.patient_id or 'No ID'}) - {self.created_at.strftime('%Y-%m-%d')}"


class ScanImage(models.Model):
    """Individual scan/image uploaded for a patient case."""
    SCAN_TYPES = [
        ("xray", "X-Ray"),
        ("mri", "MRI"),
        ("ct", "CT Scan"),
        ("ultrasound", "Ultrasound"),
        ("pet", "PET Scan"),
        ("other", "Other"),
    ]
    case = models.ForeignKey(PatientCase, on_delete=models.CASCADE, related_name="scans")
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPES, default="xray")
    body_region = models.CharField(max_length=100, blank=True, help_text="e.g., Chest, Brain, Abdomen")
    original_image = models.ImageField(upload_to="scans/original/")
    heatmap_image = models.ImageField(upload_to="scans/heatmap/", blank=True, null=True)
    notes = models.TextField(blank=True, help_text="Radiologist notes or scan context")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_scan_type_display()} - {self.body_region} ({self.case.patient_name})"


class AnalysisReport(models.Model):
    """AI-generated analysis report for a patient case."""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("complete", "Complete"),
        ("error", "Error"),
    ]
    case = models.OneToOneField(PatientCase, on_delete=models.CASCADE, related_name="report")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    raw_findings = models.TextField(blank=True, help_text="Raw AI analysis text")
    diagnoses = models.JSONField(default=list, help_text="List of {name, probability, explanation, severity, icd_code}")
    imaging_findings = models.JSONField(default=dict, help_text="Per-scan findings and abnormalities")
    differential_summary = models.TextField(blank=True)
    recommendations = models.JSONField(default=list, help_text="Next steps / tests recommended")
    disclaimer = models.TextField(
        default="This AI-generated analysis is intended as a second opinion tool for licensed medical professionals. "
                "It does not replace clinical judgment. All findings must be verified by a qualified physician."
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report for {self.case.patient_name} [{self.status}]"

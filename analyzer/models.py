from django.db import models

class JobPosting(models.Model):
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100, default="Engineering")
    description = models.TextField()
    required_skills = models.JSONField(default=list, help_text="List of required skills")
    experience_years = models.PositiveIntegerField(default=3)
    threshold_score = models.FloatField(default=70.0, help_text="Recruiter score threshold for shortlisting (%)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.department})"


class Resume(models.Model):
    candidate_name = models.CharField(max_length=200, default="Candidate")
    email = models.EmailField(blank=True, null=True)
    resume_file = models.FileField(upload_to="resumes/")
    raw_text = models.TextField(blank=True)
    extracted_entities = models.JSONField(default=dict, help_text="spaCy custom NER entities (SKILL, DEGREE, EXPERIENCE, DATE)")
    claude_structured_data = models.JSONField(default=dict, help_text="Structured JSON from Claude API (skills, experience, education)")
    word_layout_data = models.JSONField(default=list, help_text="pdfplumber word bounding boxes and layout geometry")
    page_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate_name} - {self.resume_file.name}"


class EvaluationResult(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name="evaluations")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="evaluations")
    overall_score = models.FloatField()
    is_shortlisted = models.BooleanField(default=False)
    model_scores = models.JSONField(default=dict)
    shap_data = models.JSONField(default=dict)
    role_fit_data = models.JSONField(default=dict)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    extra_skills = models.JSONField(default=list)
    scan_simulation = models.JSONField(default=dict)
    learning_path = models.JSONField(default=dict, blank=True, null=True, help_text="Personalized learning path from Claude for rejected candidates")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Shortlisted" if self.is_shortlisted else "Rejected"
        return f"{self.resume.candidate_name} -> {self.job.title}: {self.overall_score}% ({status})"


class InterviewSession(models.Model):
    evaluation = models.OneToOneField(EvaluationResult, on_delete=models.CASCADE, related_name="interview_session")
    questions = models.JSONField(default=list, help_text="AI generated role-specific interview questions")
    candidate_answers = models.JSONField(default=dict, help_text="Keyed by question index or ID")
    evaluation_report = models.JSONField(default=dict, blank=True, null=True)
    overall_score = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview for {self.evaluation.resume.candidate_name} ({self.evaluation.job.title})"

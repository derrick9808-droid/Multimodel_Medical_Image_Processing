import os
from pathlib import Path
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import JobPosting, Resume, EvaluationResult, InterviewSession
from .modules.pdf_parser import extract_pdf_data
from .modules.spacy_ner import extract_entities_from_text, get_or_train_custom_ner
from .modules.matcher import clean_text, canonicalize_skill, match_skills
from .modules.scoring_engine import calculate_multi_model_score
from .modules.role_fit import calculate_role_fit_matrix
from .modules.scan_simulator import simulate_recruiter_scan
from .modules.claude_service import (
    parse_resume_structured,
    generate_learning_path,
    generate_mock_interview_questions,
    evaluate_interview_answers
)
from .modules.report_generator import generate_pdf_report


class ATSTestSuite(TestCase):
    def setUp(self):
        self.client = Client()
        self.backend_job = JobPosting.objects.create(
            title="Senior Backend Engineer",
            department="Infrastructure",
            description="Seeking Senior Backend Engineer proficient in Python, Django, PostgreSQL, Docker, AWS, Redis, REST APIs, CI/CD.",
            required_skills=["Python", "Django", "PostgreSQL", "Docker", "AWS", "Redis", "REST APIs", "CI/CD"],
            experience_years=4,
            threshold_score=70.0
        )
        self.media_dir = Path(__file__).resolve().parent.parent / "media" / "resumes"

    def test_01_matcher_and_synonyms(self):
        """Test Tier 1 cleanup, Tier 2 canonical synonyms, and Tier 3 semantic fallback."""
        self.assertEqual(clean_text(" Python, Django! "), "python django")
        self.assertEqual(canonicalize_skill("website developer"), "web developer")
        self.assertEqual(canonicalize_skill("ml"), "machine learning")
        self.assertEqual(canonicalize_skill("k8s"), "kubernetes")
        self.assertEqual(canonicalize_skill("postgres"), "postgresql")

        # Matching
        res_skills = ["py", "django", "postgresql", "docker", "k8s"]
        jd_skills = ["Python", "Django", "PostgreSQL", "Kubernetes", "Redis"]
        match_res = match_skills(res_skills, jd_skills)

        self.assertEqual(match_res["total_matched"], 4)
        self.assertIn("Redis", match_res["missing"])
        self.assertGreaterEqual(match_res["match_ratio"], 0.75)

    def test_02_spacy_custom_ner(self):
        """Test spaCy custom NER recognition of SKILL, DEGREE, EXPERIENCE, DATE."""
        sample_text = (
            "Senior Software Engineer with 5 years experience at Google from 2019 to Present. "
            "Graduated with a Master of Science in Computer Science. "
            "Skilled in Python, Django, Docker, Kubernetes, and PostgreSQL."
        )
        entities = extract_entities_from_text(sample_text)
        self.assertIn("SKILL", entities)
        self.assertIn("DEGREE", entities)
        self.assertIn("EXPERIENCE", entities)
        self.assertIn("DATE", entities)

        # Check that expected entities were detected
        self.assertTrue(any("python" in s.lower() for s in entities["SKILL"]))
        self.assertTrue(any("master" in d.lower() for d in entities["DEGREE"]))

    def test_03_pdf_parser(self):
        """Test pdfplumber extraction on generated sample resume."""
        sample_pdf = self.media_dir / "Alex_Mercer_Senior_Backend.pdf"
        if sample_pdf.exists():
            data = extract_pdf_data(str(sample_pdf))
            self.assertIn("text", data)
            self.assertIn("word_boxes", data)
            self.assertGreater(len(data["text"]), 50)
            self.assertGreater(len(data["word_boxes"]), 10)

    def test_04_scoring_engine_and_shap(self):
        """Test Multi-Model scoring and SHAP feature attributions."""
        resume_text = "Experienced Senior Software Engineer specializing in Python, Django, PostgreSQL, AWS, Docker, Redis."
        jd_text = self.backend_job.description
        r_skills = ["Python", "Django", "PostgreSQL", "AWS", "Docker", "Redis"]
        jd_skills = self.backend_job.required_skills
        entities = {"SKILL": r_skills, "DEGREE": ["B.S."], "EXPERIENCE": ["Senior Software Engineer"], "DATE": ["2020-2024"]}

        scoring = calculate_multi_model_score(
            resume_text=resume_text,
            jd_text=jd_text,
            resume_skills=r_skills,
            jd_skills=jd_skills,
            extracted_entities=entities,
            required_years=self.backend_job.experience_years,
            job_title=self.backend_job.title
        )

        self.assertIn("overall_score", scoring)
        self.assertIn("models", scoring)
        self.assertIn("shap", scoring)
        self.assertGreaterEqual(scoring["overall_score"], 65.0)
        self.assertIn("features", scoring["shap"])
        self.assertEqual(len(scoring["shap"]["features"]), 6)

    def test_05_role_fit_radar(self):
        """Test role-fit benchmark radar chart datasets."""
        skills = ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker"]
        rf = calculate_role_fit_matrix(skills)
        self.assertIn("radar_data", rf)
        self.assertIn("ranked_roles", rf)
        self.assertEqual(len(rf["radar_data"]["labels"]), 7)
        self.assertEqual(rf["best_fit_role"], "Backend Engineer")

    def test_06_recruiter_scan_simulation(self):
        """Test 6-second scan simulation F-pattern gaze and heatmap coordinates."""
        dummy_words = [
            {"text": "John Doe", "x0": 50, "top": 40, "x1": 150, "bottom": 60, "size": 20, "page": 1},
            {"text": "Software Engineer", "x0": 50, "top": 120, "x1": 200, "bottom": 135, "size": 13, "page": 1},
            {"text": "Skills", "x0": 50, "top": 240, "x1": 100, "bottom": 255, "size": 12, "page": 1}
        ]
        dims = [{"page_number": 1, "width": 612.0, "height": 792.0}]
        scan = simulate_recruiter_scan(dummy_words, dims, {})
        self.assertIn("fixation_timeline", scan)
        self.assertIn("heatmap_points", scan)
        self.assertEqual(len(scan["fixation_timeline"]), 5)
        self.assertGreater(len(scan["heatmap_points"]), 5)

    def test_07_claude_learning_path_for_rejected(self):
        """Test requirement #8: personalized learning path generated for rejected candidate missing skills."""
        missing = ["Kubernetes", "AWS", "Terraform", "PostgreSQL"]
        lpath = generate_learning_path(missing, "Senior Backend Engineer", "Jordan Reed")
        self.assertIn("summary", lpath)
        self.assertIn("milestones", lpath)
        self.assertIn("capstone_project", lpath)
        self.assertGreaterEqual(len(lpath["milestones"]), 2)

    def test_08_pdf_report_generation(self):
        """Test ReportLab PDF generation with all aggregated fields."""
        model_scores = {
            "m1": {"name": "TF-IDF", "score": 85.0, "weight": "25%", "description": "Text similarity"},
            "m2": {"name": "Skill Coverage", "score": 90.0, "weight": "40%", "description": "Overlap"},
            "m3": {"name": "ML", "score": 88.0, "weight": "35%", "description": "Random Forest"}
        }
        shap_insights = ["High skill overlap added +12.5% to candidate score."]
        role_fit = [{"role_name": "Backend Engineer", "category": "Core", "score": 95.0}]
        
        pdf_bytes = generate_pdf_report(
            candidate_name="Alex Mercer",
            job_title="Senior Backend Engineer",
            overall_score=87.5,
            threshold=70.0,
            is_shortlisted=True,
            model_scores=model_scores,
            shap_insights=shap_insights,
            matched_skills=["Python", "Django", "PostgreSQL"],
            missing_skills=["Kubernetes"],
            role_fit_data=role_fit
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_09_end_to_end_upload_pipeline(self):
        """Test end-to-end upload and evaluation view."""
        sample_pdf_path = self.media_dir / "Alex_Mercer_Senior_Backend.pdf"
        if sample_pdf_path.exists():
            with open(sample_pdf_path, 'rb') as f:
                uploaded_file = SimpleUploadedFile("alex_resume.pdf", f.read(), content_type="application/pdf")

            response = self.client.post(
                reverse('upload_resume'),
                {
                    'job_id': self.backend_job.id,
                    'candidate_name': 'Alex Mercer',
                    'candidate_email': 'alex@example.com',
                    'resume_file': uploaded_file
                },
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(EvaluationResult.objects.filter(resume__candidate_name='Alex Mercer').exists())

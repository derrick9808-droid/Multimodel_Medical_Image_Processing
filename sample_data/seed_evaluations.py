"""
Seed Evaluations Script.
Evaluates the two sample resumes against the 'Senior Backend Engineer' job:
1. Alex Mercer -> Shortlisted (score >= 70%) with ATS preview, diff view, 6-sec scan, and interview questions.
2. Jordan Reed -> Rejected (score < 70%) with Skill Gap & Claude AI Learning Path roadmap.
"""

import os
import sys
from pathlib import Path
from django.core.files import File

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_platform.settings')
django.setup()

from analyzer.models import JobPosting, Resume, EvaluationResult, InterviewSession
from analyzer.modules.pdf_parser import extract_pdf_data
from analyzer.modules.spacy_ner import extract_entities_from_text
from analyzer.modules.claude_service import (
    parse_resume_structured,
    generate_learning_path,
    generate_mock_interview_questions,
    evaluate_interview_answers
)
from analyzer.modules.scoring_engine import calculate_multi_model_score
from analyzer.modules.role_fit import calculate_role_fit_matrix
from analyzer.modules.scan_simulator import simulate_recruiter_scan

def evaluate_file(job: JobPosting, pdf_path: Path, candidate_name: str, email: str):
    print(f"\n--- Processing {candidate_name} against {job.title} ---")
    
    with open(pdf_path, 'rb') as f:
        resume_obj = Resume.objects.create(
            candidate_name=candidate_name,
            email=email,
            resume_file=File(f, name=pdf_path.name)
        )

    # 1. pdfplumber
    pdf_data = extract_pdf_data(resume_obj.resume_file.path)
    raw_text = pdf_data["text"]
    word_boxes = pdf_data["word_boxes"]
    page_dims = pdf_data["page_dimensions"]

    # 2. spaCy custom NER
    ner_entities = extract_entities_from_text(raw_text)

    # 3. Claude structured extraction
    claude_structured = parse_resume_structured(raw_text)

    all_skills = list(set(ner_entities.get("SKILL", []) + claude_structured.get("skills", [])))

    resume_obj.raw_text = raw_text
    resume_obj.extracted_entities = ner_entities
    resume_obj.claude_structured_data = claude_structured
    resume_obj.word_layout_data = word_boxes
    resume_obj.page_count = pdf_data["page_count"]
    resume_obj.save()

    # 4. Multi-model scoring & SHAP
    scoring_res = calculate_multi_model_score(
        resume_text=raw_text,
        jd_text=job.description,
        resume_skills=all_skills,
        jd_skills=job.required_skills,
        extracted_entities=ner_entities,
        required_years=job.experience_years,
        job_title=job.title
    )

    overall_score = scoring_res["overall_score"]
    model_scores = scoring_res["models"]
    shap_data = scoring_res["shap"]
    skill_matching = scoring_res["skill_matching"]

    # 5. Role-fit matrix
    role_fit_data = calculate_role_fit_matrix(all_skills)

    # 6. Decision & Branching
    is_shortlisted = (overall_score >= job.threshold_score)
    scan_sim = simulate_recruiter_scan(word_boxes, page_dims, ner_entities)

    learning_path_data = None
    if not is_shortlisted:
        # Rejected Branch: Claude Learning Path
        learning_path_data = generate_learning_path(
            missing_skills=skill_matching.get("missing", []),
            job_title=job.title,
            candidate_name=candidate_name
        )

    eval_record = EvaluationResult.objects.create(
        job=job,
        resume=resume_obj,
        overall_score=overall_score,
        is_shortlisted=is_shortlisted,
        model_scores=model_scores,
        shap_data=shap_data,
        role_fit_data=role_fit_data,
        matched_skills=[m["canonical"].title() for m in skill_matching.get("matched", [])],
        missing_skills=skill_matching.get("missing", []),
        extra_skills=skill_matching.get("extra_skills", []),
        scan_simulation=scan_sim,
        learning_path=learning_path_data
    )

    if is_shortlisted:
        # Shortlisted Branch: Mock Interview setup with sample evaluated answers
        questions = generate_mock_interview_questions(
            job_title=job.title,
            job_description=job.description,
            candidate_skills=all_skills,
            count=5
        )
        answers = {
            "1": "I design distributed microservices by decoupling domains using asynchronous event-driven queues like Redis/Kafka, implementing database read-replicas, and using horizontal auto-scaling on Kubernetes.",
            "2": "For query performance bottlenecks, I run EXPLAIN ANALYZE on slow PostgreSQL queries, add compound B-tree indexes, prevent N+1 queries in Django ORM with select_related, and cache hot data in Redis.",
            "3": "During a 500 error spike, I inspect centralized Datadog/ELK logs, roll back if triggered by recent canary deploy, reproduce in staging, and push regression unit tests.",
            "4": "For zero-downtime migrations, we use expand-and-contract patterns: add nullable column, deploy dual-write code, asynchronously backfill, and finally enforce constraints.",
            "5": "When disagreeing on architecture, I set up a time-boxed spike to benchmark throughput and latency with real traffic profiles, present data objectively, and align with team consensus."
        }
        qa_pairs = [{"question": q["question"], "candidate_answer": answers.get(str(q["id"]), ""), "category": q["category"]} for q in questions]
        eval_report = evaluate_interview_answers(qa_pairs, job.title)

        InterviewSession.objects.create(
            evaluation=eval_record,
            questions=questions,
            candidate_answers=answers,
            evaluation_report=eval_report,
            overall_score=eval_report.get("overall_score", 88.0),
            completed=True
        )

    print(f"Result for {candidate_name}: Score = {overall_score}%, Shortlisted = {is_shortlisted}")


def run():
    job = JobPosting.objects.filter(title__icontains="Backend").first()
    if not job:
        print("Backend job not found!")
        return

    media_dir = BASE_DIR / "media" / "resumes"
    p1 = media_dir / "Alex_Mercer_Senior_Backend.pdf"
    p2 = media_dir / "Jordan_Reed_Junior_Developer.pdf"

    if p1.exists():
        evaluate_file(job, p1, "Alex Mercer", "alex.mercer@example.com")
    if p2.exists():
        evaluate_file(job, p2, "Jordan Reed", "jordan.reed@example.com")

    print("\nSeed evaluations complete!")

if __name__ == "__main__":
    run()

import json
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.files.storage import default_storage

from .models import JobPosting, Resume, EvaluationResult, InterviewSession
from .modules.pdf_parser import extract_pdf_data
from .modules.spacy_ner import extract_entities_from_text
from .modules.claude_service import (
    parse_resume_structured,
    generate_learning_path,
    generate_mock_interview_questions,
    evaluate_interview_answers
)
from .modules.matcher import match_skills, clean_text
from .modules.scoring_engine import calculate_multi_model_score
from .modules.role_fit import calculate_role_fit_matrix
from .modules.scan_simulator import simulate_recruiter_scan
from .modules.report_generator import generate_pdf_report


def dashboard(request):
    """Recruiter dashboard summarizing jobs, applicants, and platform activity."""
    jobs = JobPosting.objects.all().order_by('-created_at')
    evaluations = EvaluationResult.objects.select_related('job', 'resume').all().order_by('-created_at')[:10]
    
    total_candidates = Resume.objects.count()
    shortlisted_count = EvaluationResult.objects.filter(is_shortlisted=True).count()
    rejected_count = EvaluationResult.objects.filter(is_shortlisted=False).count()
    shortlist_rate = round((shortlisted_count / max(1, (shortlisted_count + rejected_count))) * 100, 1)

    context = {
        "jobs": jobs,
        "evaluations": evaluations,
        "total_jobs": jobs.count(),
        "total_candidates": total_candidates,
        "shortlisted_count": shortlisted_count,
        "rejected_count": rejected_count,
        "shortlist_rate": shortlist_rate
    }
    return render(request, "dashboard.html", context)


def job_list(request):
    """List of all job postings with applicant count and threshold settings."""
    jobs = JobPosting.objects.all().order_by('-created_at')
    return render(request, "job_list.html", {"jobs": jobs})


def job_create(request):
    """Create a new job posting."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        department = request.POST.get("department", "Engineering").strip()
        description = request.POST.get("description", "").strip()
        skills_raw = request.POST.get("required_skills", "").strip()
        experience_years = int(request.POST.get("experience_years", 3))
        threshold_score = float(request.POST.get("threshold_score", 70.0))

        # Parse comma or newline separated skills
        skills_list = [s.strip() for s in skills_raw.replace('\n', ',').split(',') if s.strip()]

        job = JobPosting.objects.create(
            title=title,
            department=department,
            description=description,
            required_skills=skills_list,
            experience_years=experience_years,
            threshold_score=threshold_score
        )
        messages.success(request, f"Job Posting '{job.title}' created successfully.")
        return redirect("job_detail", job_id=job.id)

    return render(request, "job_create.html")


def job_detail(request, job_id):
    """View job details and all evaluated candidate resumes."""
    job = get_object_or_404(JobPosting, id=job_id)
    evaluations = job.evaluations.select_related('resume').all().order_by('-overall_score')

    if request.method == "POST" and "update_threshold" in request.POST:
        new_threshold = float(request.POST.get("threshold_score", job.threshold_score))
        job.threshold_score = new_threshold
        job.save()
        # Recalculate shortlist status for candidates
        for ev in evaluations:
            ev.is_shortlisted = (ev.overall_score >= new_threshold)
            # If changed to rejected and no learning path yet, generate it
            if not ev.is_shortlisted and not ev.learning_path:
                ev.learning_path = generate_learning_path(ev.missing_skills, job.title, ev.resume.candidate_name)
            ev.save()
        messages.success(request, f"Updated shortlisting threshold to {new_threshold}%. Candidate decisions refreshed.")
        return redirect("job_detail", job_id=job.id)

    context = {
        "job": job,
        "evaluations": evaluations,
        "total_applicants": evaluations.count(),
        "shortlisted": evaluations.filter(is_shortlisted=True).count(),
        "rejected": evaluations.filter(is_shortlisted=False).count(),
    }
    return render(request, "job_detail.html", context)


def upload_resume(request, job_id=None):
    """
    Core Pipeline Handler:
    1. Upload PDF
    2. Extract text & layout using pdfplumber
    3. Custom spaCy NER (SKILL, DEGREE, EXPERIENCE, DATE)
    4. Claude API structured extraction (skills, experience, education)
    5. Normalization + Canonical Synonyms + Semantic Similarity matching
    6. Multi-Model Scoring (TF-IDF, Skill Coverage, Random Forest) + SHAP Explainer
    7. Role-Fit Radar Heatmap
    8. Threshold Decision check:
       - REJECTED: Generate personalized learning path using Claude API
       - SHORTLISTED: Generate ATS preview, JD diff view, 6-second scan simulation, and mock interview questions
    """
    jobs = JobPosting.objects.all()
    selected_job = get_object_or_404(JobPosting, id=job_id) if job_id else jobs.first()

    if request.method == "POST" and request.FILES.get("resume_file"):
        target_job_id = request.POST.get("job_id") or (selected_job.id if selected_job else None)
        target_job = get_object_or_404(JobPosting, id=target_job_id)
        uploaded_file = request.FILES["resume_file"]

        # 1. Save Resume File
        candidate_name_input = request.POST.get("candidate_name", "").strip() or "Candidate"
        candidate_email_input = request.POST.get("candidate_email", "").strip() or None

        resume_obj = Resume.objects.create(
            candidate_name=candidate_name_input,
            email=candidate_email_input,
            resume_file=uploaded_file
        )

        pdf_path = resume_obj.resume_file.path

        # 2. Extract Text and Word Layout via pdfplumber
        try:
            pdf_data = extract_pdf_data(pdf_path)
            raw_text = pdf_data["text"]
            word_boxes = pdf_data["word_boxes"]
            page_dims = pdf_data["page_dimensions"]
            page_count = pdf_data["page_count"]
        except Exception as e:
            raw_text = f"Error reading PDF: {e}"
            word_boxes = []
            page_dims = []
            page_count = 1

        # 3. Custom spaCy Named Entity Recognition (SKILL, DEGREE, EXPERIENCE, DATE)
        ner_entities = extract_entities_from_text(raw_text)

        # 4. Claude API Structured Extraction
        claude_structured = parse_resume_structured(raw_text)

        # Merge skills identified from both spaCy custom NER and Claude structured extraction
        all_skills = list(set(ner_entities.get("SKILL", []) + claude_structured.get("skills", [])))

        # Update candidate name if extracted
        if candidate_name_input == "Candidate" and raw_text:
            first_line = raw_text.split('\n')[0].strip()
            if len(first_line) < 40 and not any(kw in first_line.lower() for kw in ["resume", "curriculum", "page", "email"]):
                resume_obj.candidate_name = first_line

        resume_obj.raw_text = raw_text
        resume_obj.extracted_entities = ner_entities
        resume_obj.claude_structured_data = claude_structured
        resume_obj.word_layout_data = word_boxes
        resume_obj.page_count = page_count
        resume_obj.save()

        # 5 & 6. Multi-Model Scoring + SHAP Explainable AI
        scoring_res = calculate_multi_model_score(
            resume_text=raw_text,
            jd_text=target_job.description,
            resume_skills=all_skills,
            jd_skills=target_job.required_skills,
            extracted_entities=ner_entities,
            required_years=target_job.experience_years,
            job_title=target_job.title
        )

        overall_score = scoring_res["overall_score"]
        model_scores = scoring_res["models"]
        shap_data = scoring_res["shap"]
        skill_matching = scoring_res["skill_matching"]

        # 7. Role-Fit Heatmap & Radar comparison
        role_fit_data = calculate_role_fit_matrix(all_skills)

        # 8. Decision — score above threshold?
        is_shortlisted = (overall_score >= target_job.threshold_score)

        # 6-Second Scan Simulation
        scan_sim = simulate_recruiter_scan(word_boxes, page_dims, ner_entities)

        # Branching:
        learning_path_data = None
        if not is_shortlisted:
            # REJECTED BRANCH: Skill gap + Claude API personalized learning path
            missing_skills = skill_matching.get("missing", [])
            learning_path_data = generate_learning_path(
                missing_skills=missing_skills,
                job_title=target_job.title,
                candidate_name=resume_obj.candidate_name
            )

        # Create Evaluation Result Record
        eval_record = EvaluationResult.objects.create(
            job=target_job,
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

        # If SHORTLISTED: Generate Mock Interview Questions
        if is_shortlisted:
            interview_questions = generate_mock_interview_questions(
                job_title=target_job.title,
                job_description=target_job.description,
                candidate_skills=all_skills,
                count=5
            )
            InterviewSession.objects.create(
                evaluation=eval_record,
                questions=interview_questions
            )

        messages.success(request, f"Resume parsed and evaluated. Match score: {overall_score}%.")
        return redirect("evaluation_detail", eval_id=eval_record.id)

    context = {
        "jobs": jobs,
        "selected_job": selected_job
    }
    return render(request, "candidate_upload.html", context)


def evaluation_detail(request, eval_id):
    """
    Unified Evaluation View:
    - Overall score vs threshold status banner
    - Multi-model scoring breakdown
    - SHAP Explainability waterfall & contribution bars
    - Role-Fit Radar Chart (Chart.js)
    - Shortlisted branch: ATS Parsing Preview, JD Diff View, 6-Second Scan Simulation, Mock Interview Simulator
    - Rejected branch: Skill Gap breakdown and Claude-generated Learning Path roadmap
    """
    eval_record = get_object_or_404(
        EvaluationResult.objects.select_related('job', 'resume'),
        id=eval_id
    )

    # Interview session if shortlisted
    interview_session = getattr(eval_record, 'interview_session', None)

    # Format JD Diff View data
    # green = matched / present in resume; red = missing
    jd_skills = eval_record.job.required_skills
    matched_skills = set([s.lower() for s in eval_record.matched_skills])
    diff_items = []
    for s in jd_skills:
        clean_s = s.lower()
        is_matched = any(clean_s in m or m in clean_s for m in matched_skills)
        diff_items.append({
            "skill": s,
            "status": "present" if is_matched else "missing"
        })

    # Prepare JSON serializable radar chart data
    radar_data_json = json.dumps(eval_record.role_fit_data.get("radar_data", {}))
    shap_features_json = json.dumps(eval_record.shap_data.get("features", []))
    heatmap_points_json = json.dumps(eval_record.scan_simulation.get("heatmap_points", []))
    fixation_timeline_json = json.dumps(eval_record.scan_simulation.get("fixation_timeline", []))

    context = {
        "eval": eval_record,
        "job": eval_record.job,
        "resume": eval_record.resume,
        "interview_session": interview_session,
        "diff_items": diff_items,
        "radar_data_json": radar_data_json,
        "shap_features_json": shap_features_json,
        "heatmap_points_json": heatmap_points_json,
        "fixation_timeline_json": fixation_timeline_json,
    }
    return render(request, "evaluation_detail.html", context)


@require_POST
def submit_interview_answer(request, eval_id):
    """
    Evaluates candidate interview answers using Claude NLP rubric.
    """
    eval_record = get_object_or_404(EvaluationResult, id=eval_id)
    interview_session = get_object_or_404(InterviewSession, evaluation=eval_record)

    # Collect answers from POST
    answers = {}
    qa_pairs = []
    for q in interview_session.questions:
        q_id = str(q.get("id"))
        ans_text = request.POST.get(f"answer_{q_id}", "").strip()
        answers[q_id] = ans_text
        qa_pairs.append({
            "question": q.get("question", ""),
            "candidate_answer": ans_text,
            "category": q.get("category", "General")
        })

    # Run NLP evaluation via Claude API
    eval_result = evaluate_interview_answers(qa_pairs, eval_record.job.title)
    
    interview_session.candidate_answers = answers
    interview_session.evaluation_report = eval_result
    interview_session.overall_score = eval_result.get("overall_score", 75.0)
    interview_session.completed = True
    interview_session.save()

    messages.success(request, f"Mock interview submitted and scored: {interview_session.overall_score}/100.")
    return redirect("evaluation_detail", eval_id=eval_record.id)


def download_report_pdf(request, eval_id):
    """Generates and downloads the ReportLab PDF final report."""
    eval_record = get_object_or_404(
        EvaluationResult.objects.select_related('job', 'resume'),
        id=eval_id
    )
    interview_session = getattr(eval_record, 'interview_session', None)
    interview_data = interview_session.evaluation_report if (interview_session and interview_session.completed) else None

    pdf_bytes = generate_pdf_report(
        candidate_name=eval_record.resume.candidate_name,
        job_title=eval_record.job.title,
        overall_score=eval_record.overall_score,
        threshold=eval_record.job.threshold_score,
        is_shortlisted=eval_record.is_shortlisted,
        model_scores=eval_record.model_scores,
        shap_insights=eval_record.shap_data.get("insights", []),
        matched_skills=eval_record.matched_skills,
        missing_skills=eval_record.missing_skills,
        role_fit_data=eval_record.role_fit_data.get("ranked_roles", []),
        interview_data=interview_data,
        learning_path=eval_record.learning_path
    )

    filename = f"Evaluation_Report_{eval_record.resume.candidate_name.replace(' ', '_')}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

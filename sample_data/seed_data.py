"""
Seed Data Script.
Creates realistic sample Job Postings and generates sample PDF resumes
(one passing threshold, one failing threshold) using ReportLab.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats_platform.settings')
django.setup()

from analyzer.models import JobPosting
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media" / "resumes"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

def generate_sample_pdf(filename: str, name: str, title: str, summary: str, experiences: list, skills: list, education: list):
    pdf_path = MEDIA_DIR / filename
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=50, leftMargin=50, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle('Head', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.HexColor("#0F172A"))
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#475569"))
    sec_style = ParagraphStyle('Sec', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor("#1E40AF"), spaceBefore=12, spaceAfter=4)
    item_title = ParagraphStyle('ItemTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.HexColor("#1E293B"))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor("#334155"))

    story = [
        Paragraph(name, header_style),
        Paragraph(f"{title} | San Francisco, CA | {name.lower().replace(' ', '.')}@example.com | (555) 234-5678", sub_style),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=8),
        Paragraph("PROFESSIONAL SUMMARY", sec_style),
        Paragraph(summary, body_style),
        Spacer(1, 6),
        Paragraph("TECHNICAL SKILLS", sec_style),
        Paragraph(f"<b>Core Competencies:</b> {', '.join(skills)}", body_style),
        Spacer(1, 6),
        Paragraph("WORK EXPERIENCE", sec_style)
    ]

    for exp in experiences:
        story.append(Paragraph(f"<b>{exp['role']}</b> &bull; {exp['company']} <i>({exp['dates']})</i>", item_title))
        for bullet in exp['bullets']:
            story.append(Paragraph(f"&bull; {bullet}", body_style))
        story.append(Spacer(1, 4))

    story.append(Paragraph("EDUCATION & CREDENTIALS", sec_style))
    for edu in education:
        story.append(Paragraph(f"<b>{edu['degree']}</b> &bull; {edu['school']} <i>({edu['year']})</i>", body_style))

    doc.build(story)
    print(f"Generated sample resume: {pdf_path}")
    return str(pdf_path)


def seed():
    print("Seeding sample Job Postings...")
    
    # Job 1: Senior Backend Engineer
    job1, _ = JobPosting.objects.get_or_create(
        title="Senior Backend Engineer",
        defaults={
            "department": "Core Infrastructure",
            "description": (
                "We are seeking an experienced Senior Backend Engineer to architect, build, and optimize high-throughput distributed microservices. "
                "You will lead database architecture using PostgreSQL, manage in-memory caching with Redis, containerize microservices using Docker "
                "and deploy production services to AWS with automated CI/CD pipelines. Strong proficiency in Python and Django is mandatory."
            ),
            "required_skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS", "Redis", "REST APIs", "CI/CD"],
            "experience_years": 4,
            "threshold_score": 70.0
        }
    )

    # Job 2: Machine Learning Engineer
    job2, _ = JobPosting.objects.get_or_create(
        title="Machine Learning Engineer",
        defaults={
            "department": "Applied AI Research",
            "description": (
                "Seeking an ML Engineer to design and deploy production-grade NLP and predictive models. Experience with Python, PyTorch, scikit-learn, "
                "Pandas, and SQL is essential. Experience with SHAP explainability and Large Language Models (LLM) is highly desired."
            ),
            "required_skills": ["Python", "Machine Learning", "PyTorch", "scikit-learn", "Pandas", "SQL", "NLP", "SHAP"],
            "experience_years": 3,
            "threshold_score": 75.0
        }
    )

    # Job 3: DevOps & Cloud Architect
    job3, _ = JobPosting.objects.get_or_create(
        title="DevOps & Cloud Architect",
        defaults={
            "department": "Platform Operations",
            "description": (
                "Looking for a DevOps Architect to scale Kubernetes infrastructure on AWS using Terraform and Docker. "
                "Responsible for setting up robust CI/CD pipelines, automated testing, and zero-downtime deployments."
            ),
            "required_skills": ["Kubernetes", "Docker", "AWS", "Terraform", "CI/CD", "Linux", "Bash"],
            "experience_years": 5,
            "threshold_score": 68.0
        }
    )

    print("Generating sample candidate resumes...")
    # Candidate 1: Alex Mercer (High match for Senior Backend Engineer)
    generate_sample_pdf(
        filename="Alex_Mercer_Senior_Backend.pdf",
        name="Alex Mercer",
        title="Senior Backend Engineer",
        summary="Senior Software Engineer with 5+ years of production experience designing scalable RESTful APIs, distributed microservices, and database systems with Python, Django, PostgreSQL, and AWS.",
        experiences=[
            {
                "role": "Senior Software Engineer",
                "company": "Nexus Cloud Technologies",
                "dates": "January 2021 - Present",
                "bullets": [
                    "Architected high-throughput microservices using Python and Django processing over 50M requests daily.",
                    "Optimized PostgreSQL database queries and connection pooling, reducing p99 latency by 35%.",
                    "Integrated Redis caching layer and deployed containerized Docker services to AWS EKS.",
                    "Established automated CI/CD deployment pipelines using GitHub Actions and Docker."
                ]
            },
            {
                "role": "Backend Developer",
                "company": "DataStream Solutions",
                "dates": "June 2018 - December 2020",
                "bullets": [
                    "Engineered REST APIs and background worker tasks handling high-volume async processing.",
                    "Collaborated with frontend teams to define secure authentication and RESTful API standards."
                ]
            }
        ],
        skills=["Python", "Django", "PostgreSQL", "Docker", "AWS", "Redis", "REST APIs", "CI/CD", "Git", "Linux"],
        education=[{"degree": "Bachelor of Science in Computer Science", "school": "University of California, Berkeley", "year": "2018"}]
    )

    # Candidate 2: Jordan Reed (Junior / Lacking backend skills - triggers Rejected Learning Path branch)
    generate_sample_pdf(
        filename="Jordan_Reed_Junior_Developer.pdf",
        name="Jordan Reed",
        title="Junior Frontend Developer",
        summary="Enthusiastic Junior Developer with 1.5 years experience building responsive web interfaces using JavaScript, React, and CSS. Looking to transition into backend development.",
        experiences=[
            {
                "role": "Junior Web Developer",
                "company": "BrightWeb Studio",
                "dates": "March 2023 - Present",
                "bullets": [
                    "Developed client-side components using React, HTML5, and CSS3.",
                    "Consumed REST APIs and managed local application state with Redux.",
                    "Wrote basic Python scripts for local data scraping."
                ]
            }
        ],
        skills=["JavaScript", "React", "HTML5", "CSS3", "Git", "Figma", "Basic Python"],
        education=[{"degree": "Associate Degree in Web Development", "school": "Community College", "year": "2023"}]
    )

    print("Seed completed successfully!")

if __name__ == "__main__":
    seed()

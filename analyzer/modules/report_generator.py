"""
PDF Final Report Generator using ReportLab.
Aggregates candidate profile, match scores, multi-model breakdown, SHAP explainability insights,
role-fit scores, interview evaluations, and learning path / skill gap analysis into a professional PDF.
"""

import io
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether

def generate_pdf_report(
    candidate_name: str,
    job_title: str,
    overall_score: float,
    threshold: float,
    is_shortlisted: bool,
    model_scores: Dict[str, Any],
    shap_insights: list,
    matched_skills: list,
    missing_skills: list,
    role_fit_data: list,
    interview_data: Dict[str, Any] = None,
    learning_path: Dict[str, Any] = None
) -> bytes:
    """
    Builds a multi-page executive recruitment evaluation PDF report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1E293B")   # Slate 800
    c_indigo = colors.HexColor("#4F46E5")    # Indigo 600
    c_emerald = colors.HexColor("#059669")   # Emerald 600
    c_rose = colors.HexColor("#E11D48")      # Rose 600
    c_slate = colors.HexColor("#475569")     # Slate 600
    c_light = colors.HexColor("#F8FAFC")     # Slate 50
    c_border = colors.HexColor("#E2E8F0")

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_indigo,
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_slate
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.white,
        alignment=1
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph(f"<b>AI RECRUITMENT INTELLIGENCE REPORT</b>", title_style),
            Paragraph(f"<b>{'SHORTLISTED' if is_shortlisted else 'REJECTED / UPSKILL'}</b>", badge_style)
        ],
        [
            Paragraph(f"Candidate: <b>{candidate_name}</b> | Target Role: <b>{job_title}</b>", body_style),
            Paragraph(f"Overall Match Score: <b>{overall_score}%</b> (Threshold: {threshold}%)", body_style)
        ]
    ]
    status_bg = c_emerald if is_shortlisted else c_rose
    header_table = Table(header_data, colWidths=[380, 150])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (1, 0), (1, 0), status_bg),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=12))

    # 2. Multi-Model Scoring Breakdown
    story.append(Paragraph("1. MULTI-MODEL SCORING SYNTHESIS", h2_style))
    m_data = [["Scoring Method", "Weight", "Calculated Score", "Description"]]
    for k, v in model_scores.items():
        m_data.append([
            v.get("name", k),
            v.get("weight", "33%"),
            f"{v.get('score', 0)}%",
            v.get("description", "")[:55] + "..."
        ])
    m_data.append(["Reconciled Composite Score", "100%", f"{overall_score}%", "Weighted ensemble recommendation"])

    model_table = Table(m_data, colWidths=[140, 50, 95, 245])
    model_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_light),
        ('TEXTCOLOR', (0, 0), (-1, 0), c_primary),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, c_light]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#EEF2F6")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(model_table)
    story.append(Spacer(1, 10))

    # 3. Explainable AI (SHAP Insights)
    story.append(Paragraph("2. EXPLAINABLE AI (SHAP FEATURE IMPACT)", h2_style))
    story.append(Paragraph("Why the candidate received this score (Individual Shapley value attributions):", body_style))
    story.append(Spacer(1, 4))
    for ins in shap_insights:
        story.append(Paragraph(f"• {ins}", body_style))
    story.append(Spacer(1, 10))

    # 4. Skills Analysis
    story.append(Paragraph("3. SKILLS MATCH & GAP ANALYSIS", h2_style))
    matched_str = ", ".join(matched_skills) if matched_skills else "None explicitly matched"
    missing_str = ", ".join(missing_skills) if missing_skills else "None - all required skills satisfied"
    skills_data = [
        [Paragraph("<b>Matched Skills:</b>", body_style), Paragraph(matched_str, body_style)],
        [Paragraph("<b>Missing / Weak Skills:</b>", body_style), Paragraph(missing_str, body_style)]
    ]
    skills_table = Table(skills_data, colWidths=[130, 400])
    skills_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), c_light),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 10))

    # 5. Role-Fit Benchmark Radar Summary
    story.append(Paragraph("4. ROLE-FIT MATRIX BENCHMARKS", h2_style))
    rf_rows = [["Benchmark Role Profile", "Category", "Alignment Percentage"]]
    for r in role_fit_data[:6]:
        rf_rows.append([r.get("role_name", ""), r.get("category", ""), f"{r.get('score', 0)}%"])
    rf_table = Table(rf_rows, colWidths=[200, 180, 150])
    rf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_light),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(rf_table)
    story.append(Spacer(1, 10))

    # 6. Branch Specific Section:
    if is_shortlisted and interview_data:
        story.append(KeepTogether([
            Paragraph("5. AI MOCK INTERVIEW EVALUATION", h2_style),
            Paragraph(f"Interview Overall Score: <b>{interview_data.get('overall_score', 'N/A')}%</b>", body_style),
            Spacer(1, 4)
        ]))
        for ev in interview_data.get("evaluations", [])[:3]:
            q_text = ev.get("question", "")[:120]
            fb_text = ev.get("feedback", "")
            score_val = ev.get("score", 80)
            story.append(Paragraph(f"<b>Q:</b> {q_text} (Score: {score_val}%)", body_style))
            story.append(Paragraph(f"<i>Feedback:</i> {fb_text}", body_style))
            story.append(Spacer(1, 4))
    elif not is_shortlisted and learning_path:
        story.append(KeepTogether([
            Paragraph("5. AI PERSONALIZED LEARNING PATH (ROADMAP)", h2_style),
            Paragraph(f"<b>Advisor Note:</b> {learning_path.get('summary', '')}", body_style),
            Spacer(1, 4)
        ]))
        for m in learning_path.get("milestones", [])[:3]:
            phase = m.get("phase", "")
            actions = "; ".join(m.get("actions", [])[:2])
            story.append(Paragraph(f"<b>{phase}</b>", body_style))
            story.append(Paragraph(f"Key Action Items: {actions}", body_style))
            story.append(Spacer(1, 3))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

"""
Views for Medical Second Opinion AI Platform.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import PatientCase, ScanImage, AnalysisReport
from .modules.claude_medical import analyze_medical_case
from .modules.heatmap_generator import generate_heatmaps_for_case
from django.shortcuts import render

def home(request):
    return render(request, 'medical/index.html')


def index(request):
    """Landing / home page."""
    recent_cases = PatientCase.objects.all().order_by("-created_at")[:5]
    total_cases = PatientCase.objects.count()
    completed_reports = AnalysisReport.objects.filter(status="complete").count()
    context = {
        "recent_cases": recent_cases,
        "total_cases": total_cases,
        "completed_reports": completed_reports,
    }
    return render(request, "index.html", context)


def new_case(request):
    """Form to create a new patient case with file uploads."""
    if request.method == "POST":
        # Create patient case
        case = PatientCase.objects.create(
            patient_name=request.POST.get("patient_name", "Anonymous Patient").strip(),
            patient_id=request.POST.get("patient_id", "").strip(),
            age=request.POST.get("age") or None,
            gender=request.POST.get("gender", ""),
            chief_complaint=request.POST.get("chief_complaint", "").strip(),
            clinical_history=request.POST.get("clinical_history", "").strip(),
            medications=request.POST.get("medications", "").strip(),
            allergies=request.POST.get("allergies", "").strip(),
            lab_results=request.POST.get("lab_results", "").strip(),
            vital_signs=request.POST.get("vital_signs", "").strip(),
            referring_doctor=request.POST.get("referring_doctor", "").strip(),
            specialty_context=request.POST.get("specialty_context", "").strip(),
        )

        # Handle multiple scan uploads
        scan_types = request.POST.getlist("scan_type")
        body_regions = request.POST.getlist("body_region")
        scan_notes = request.POST.getlist("scan_notes")
        scan_files = request.FILES.getlist("scan_files")

        for i, scan_file in enumerate(scan_files):
            ScanImage.objects.create(
                case=case,
                scan_type=scan_types[i] if i < len(scan_types) else "xray",
                body_region=body_regions[i] if i < len(body_regions) else "",
                notes=scan_notes[i] if i < len(scan_notes) else "",
                original_image=scan_file,
            )

        messages.success(request, f"Patient case created successfully. Now run the AI analysis.")
        return redirect("case_detail", case_id=case.id)

    return render(request, "new_case.html")


def case_detail(request, case_id):
    """View case details and uploaded scans."""
    case = get_object_or_404(PatientCase, id=case_id)
    scans = case.scans.all()
    report = getattr(case, "report", None)
    context = {
        "case": case,
        "scans": scans,
        "report": report,
        "has_report": report is not None and report.status == "complete",
    }
    return render(request, "case_detail.html", context)


def analyze_case(request, case_id):
    """
    Triggers the AI analysis pipeline:
    1. Generate heatmap overlays on scans
    2. Call Claude Vision API with all patient data + images
    3. Store and display results
    """
    case = get_object_or_404(PatientCase, id=case_id)
    scans = list(case.scans.all())

    # Create or update report record
    report, _ = AnalysisReport.objects.get_or_create(case=case)
    report.status = "processing"
    report.save()

    try:
        # Step 1: Generate heatmaps
        heatmap_results = generate_heatmaps_for_case(scans, settings.MEDIA_ROOT)

        # Step 2: Prepare scan data for Claude
        scan_data = []
        for scan in scans:
            scan_path = scan.original_image.path if scan.original_image else None
            if scan_path:
                scan_data.append({
                    "path": scan_path,
                    "scan_type": scan.scan_type,
                    "body_region": scan.body_region,
                    "notes": scan.notes,
                })

        # Step 3: Prepare patient data
        patient_data = {
            "patient_name": case.patient_name,
            "patient_id": case.patient_id,
            "age": case.age,
            "gender": case.gender,
            "chief_complaint": case.chief_complaint,
            "clinical_history": case.clinical_history,
            "medications": case.medications,
            "allergies": case.allergies,
            "lab_results": case.lab_results,
            "vital_signs": case.vital_signs,
            "specialty_context": case.specialty_context,
        }

        # Step 4: Run AI analysis
        analysis = analyze_medical_case(patient_data, scan_data)

        # Step 5: Save results
        report.diagnoses = analysis.get("diagnoses", [])
        report.imaging_findings = analysis.get("imaging_findings", {})
        report.differential_summary = analysis.get("differential_summary", "")
        report.recommendations = analysis.get("recommendations", [])
        report.raw_findings = json.dumps(analysis, indent=2)
        report.status = "complete"
        report.save()

        messages.success(request, "AI analysis complete. View the full report below.")

    except Exception as e:
        report.status = "error"
        report.error_message = str(e)
        report.save()
        messages.error(request, f"Analysis error: {e}")

    return redirect("report_view", case_id=case_id)


def report_view(request, case_id):
    """Full analysis report view with heatmaps and diagnoses."""
    case = get_object_or_404(PatientCase, id=case_id)
    scans = list(case.scans.all())
    report = getattr(case, "report", None)

    if not report:
        messages.warning(request, "No analysis report found. Please run the analysis first.")
        return redirect("case_detail", case_id=case_id)

    # Prepare diagnoses with severity color classes
    severity_classes = {
        "Critical": "severity-critical",
        "High": "severity-high",
        "Moderate": "severity-moderate",
        "Low": "severity-low",
    }

    diagnoses = report.diagnoses or []
    for d in diagnoses:
        d["severity_class"] = severity_classes.get(d.get("severity", "Low"), "severity-low")

    # Pair scans with their imaging findings
    scan_findings = []
    for i, scan in enumerate(scans):
        key = f"scan_{i+1}"
        finding = report.imaging_findings.get(key, {})
        scan_findings.append({
            "scan": scan,
            "finding": finding,
            "has_heatmap": bool(scan.heatmap_image),
        })

    recommendations = report.recommendations or []
    priority_order = {"Urgent": 0, "High": 1, "Routine": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.get("priority", "Routine"), 2))

    rag_citations = []
    if report.raw_findings:
        try:
            raw_data = json.loads(report.raw_findings)
            rag_citations = raw_data.get("rag_citations", [])
        except Exception:
            pass

    context = {
        "case": case,
        "report": report,
        "diagnoses": diagnoses,
        "scan_findings": scan_findings,
        "recommendations": recommendations,
        "rag_citations": rag_citations,
        "red_flags": report.diagnoses[0].get("red_flags", []) if diagnoses else [],
        "top_diagnosis": diagnoses[0] if diagnoses else None,
    }
    return render(request, "report.html", context)


def history(request):
    """List all past patient cases."""
    cases = PatientCase.objects.all().order_by("-created_at")
    context = {"cases": cases}
    return render(request, "history.html", context)

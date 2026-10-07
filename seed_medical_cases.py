"""
Seed realistic clinical cases with medical scans, AI heatmaps, and differential reports.
"""

import os
import sys
import json
import django
from pathlib import Path

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medai_platform.settings")
django.setup()

from django.core.files import File
from medical.models import PatientCase, ScanImage, AnalysisReport
from medical.modules.heatmap_generator import generate_heatmap_overlay
from PIL import Image, ImageDraw, ImageFilter
import numpy as np


def create_chest_xray(filepath: str):
    """Generates a realistic synthetic Chest X-Ray radiograph."""
    width, height = 512, 512
    img = Image.new("L", (width, height), 15)
    draw = ImageDraw.Draw(img)

    # Rib cage outline & spine
    draw.line([(width // 2, 20), (width // 2, height - 30)], fill=180, width=16)

    # Thoracic cage ellipse
    draw.ellipse([50, 40, width - 50, height - 40], outline=90, width=10)

    # Left & Right lung fields (dark air-filled zones)
    draw.ellipse([70, 70, width // 2 - 25, height - 90], fill=35)
    draw.ellipse([width // 2 + 25, 70, width - 70, height - 90], fill=35)

    # Rib shadows
    for y in range(90, height - 90, 42):
        draw.arc([60, y - 20, width // 2 - 15, y + 40], 190, 350, fill=110, width=8)
        draw.arc([width // 2 + 15, y - 20, width - 60, y + 40], 190, 350, fill=110, width=8)

    # Cardiac silhouette
    draw.ellipse([width // 2 - 75, height // 2 - 20, width // 2 + 35, height // 2 + 120], fill=145)

    # Focal lobar consolidation (pneumonic infiltrate in right lower/middle zone)
    draw.ellipse([width // 2 + 45, height // 2 - 10, width // 2 + 160, height // 2 + 95], fill=130)

    # Diaphragm domes
    draw.arc([60, height - 140, width // 2 - 20, height - 20], 190, 350, fill=175, width=12)
    draw.arc([width // 2 + 20, height - 130, width - 60, height - 10], 190, 350, fill=175, width=12)

    # Soft Gaussian blur for radiographic look
    img = img.filter(ImageFilter.GaussianBlur(radius=3.5))

    # Add anatomical noise
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, 5, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr).convert("RGB")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath, "JPEG", quality=90)


def create_brain_mri(filepath: str):
    """Generates a realistic synthetic Brain MRI (Axial slice)."""
    width, height = 512, 512
    img = Image.new("L", (width, height), 10)
    draw = ImageDraw.Draw(img)

    # Calvarium (skull)
    draw.ellipse([50, 40, width - 50, height - 40], fill=45, outline=200, width=8)

    # Brain parenchyma (gray/white matter)
    draw.ellipse([70, 60, width - 70, height - 60], fill=100)

    # Longitudinal fissure
    draw.line([(width // 2, 70), (width // 2, height - 70)], fill=30, width=4)

    # Ventricles (CSF - dark on T1)
    draw.ellipse([width // 2 - 40, height // 2 - 50, width // 2 - 8, height // 2 + 40], fill=25)
    draw.ellipse([width // 2 + 8, height // 2 - 50, width // 2 + 40, height // 2 + 40], fill=25)

    # Acute ischemic lesion (hyperintense on DWI / T2 in right MCA territory)
    draw.ellipse([width // 2 + 45, height // 2 - 60, width // 2 + 130, height // 2 + 35], fill=210)

    # Blur
    img = img.filter(ImageFilter.GaussianBlur(radius=3))
    img = img.convert("RGB")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath, "JPEG", quality=90)


def seed_database():
    print("Clearing old cases...")
    PatientCase.objects.all().delete()

    media_root = Path("media")
    os.makedirs(media_root / "scans" / "original", exist_ok=True)
    os.makedirs(media_root / "scans" / "heatmap", exist_ok=True)

    # Case 1: Eleanor Vance (CAP / Pneumonia)
    c1_orig_path = media_root / "scans" / "original" / "chest_xray_vance.jpg"
    create_chest_xray(str(c1_orig_path))

    c1 = PatientCase.objects.create(
        patient_name="Eleanor Vance",
        patient_id="MED-2026-8941",
        age=64,
        gender="female",
        chief_complaint="Productive cough with rust-colored sputum, fevers up to 38.8°C, and pleuritic right-sided chest pain for 4 days.",
        clinical_history="64-year-old female presents with acute worsening of respiratory symptoms. Denies hemoptysis. Former smoker (20 pack-years, quit 8 years ago). Mild baseline COPD. Decreased right lower lung field breath sounds with coarse inspiratory crackles.",
        medications="Albuterol MDI 2 puffs PRN, Atorvastatin 20mg daily, Lisinopril 10mg daily",
        allergies="Penicillin (erythematous rash)",
        vital_signs="BP: 128/78 mmHg | HR: 98 bpm | Temp: 38.8 °C (101.8 °F) | RR: 24/min | SpO2: 92% on ambient air",
        lab_results="WBC: 16.4 x10^3/uL (86% neutrophils, 8% band forms) | CRP: 112 mg/L | Procalcitonin: 1.45 ng/mL | BUN: 22 mg/dL | Cr: 1.0 mg/dL",
        referring_doctor="Dr. Marcus Chen",
        specialty_context="Pulmonology"
    )

    s1 = ScanImage.objects.create(
        case=c1,
        scan_type="xray",
        body_region="Chest (PA View)",
        original_image="scans/original/chest_xray_vance.jpg",
        notes="PA projection upright chest radiograph demonstrating right middle/lower zone airspace opacity."
    )

    # Generate heatmap for Case 1
    c1_heat_path = media_root / "scans" / "heatmap" / f"heatmap_{s1.id}_chest_xray_vance.jpg"
    generate_heatmap_overlay(
        original_image_path=str(c1_orig_path),
        output_path=str(c1_heat_path),
        abnormality_regions=[(290, 220, 120, 110, 0.96)]
    )
    s1.heatmap_image = f"scans/heatmap/heatmap_{s1.id}_chest_xray_vance.jpg"
    s1.save()

    # Create Report for Case 1
    AnalysisReport.objects.create(
        case=c1,
        status="complete",
        differential_summary=(
            "Patient is a 64-year-old female presenting with acute febrile respiratory illness characterized by productive cough, "
            "leukocytosis with prominent left shift (WBC 16.4k, 8% bands), and elevated systemic inflammatory markers (CRP 112, Procalcitonin 1.45). "
            "Chest radiography confirms dense airspace consolidation in the right middle and lower lung zones with air bronchograms. "
            "In concordance with ATS/IDSA guidelines, the clinical constellation strongly supports Community-Acquired Lobar Pneumonia (CURB-65 score: 1). "
            "Given documented penicillin allergy, targeted empiric coverage with a respiratory fluoroquinolone or macrolide combination is indicated."
        ),
        imaging_findings={
            "scan_1": {
                "scan_type": "CHEST X-RAY (PA VIEW)",
                "body_region": "Thoracic",
                "findings": "Significant homogeneous opacity with air bronchogram signs identified in the right middle and lower lung fields. Costophrenic sulci demonstrate mild reactive blunting on the right side. Trachea is midline. Cardiothoracic ratio is normal (< 0.50).",
                "abnormalities": [
                    "Dense alveolar consolidation in right lung zone (heatmap focal hotspot > 95% intensity)",
                    "Air bronchograms indicative of parenchymal filling rather than atelectasis",
                    "Mild right reactive parapneumonic pleural fluid accumulation"
                ],
                "normal_structures": [
                    "Left lung parenchyma clear and well-aerated",
                    "Cardiomediastinal silhouette within anatomical limits",
                    "Bony thorax intact without osteolytic lesions or acute fracture"
                ],
                "impression": "Right middle/lower lobe consolidation characteristic of acute bacterial lobar pneumonia. Heatmap highlights high-intensity focal inflammatory infiltrate."
            }
        },
        diagnoses=[
            {
                "rank": 1,
                "name": "Community-Acquired Lobar Pneumonia (Streptococcus pneumoniae)",
                "icd_code": "J13",
                "probability": 84,
                "severity": "High",
                "explanation": "Triad of high fever (38.8°C), marked neutrophilic leukocytosis (16.4k), and classic focal lobar airspace consolidation with air bronchograms provides definitive evidence of bacterial pneumonia. Procalcitonin > 0.5 strongly corroborates bacterial etiology.",
                "supporting_evidence": [
                    "CXR shows right middle/lower zone dense consolidation (heatmap confirmed)",
                    "Elevated procalcitonin (1.45 ng/mL) and CRP (112 mg/L)",
                    "Hypoxemia SpO2 92% on room air with tachypnea (RR 24/min)"
                ],
                "against_evidence": [
                    "Absence of diffuse multi-lobar cavitations argues against Klebsiella or S. aureus"
                ],
                "guideline_citation": "ATS/IDSA Guidelines: Stratify using CURB-65 / PSI score. Early empiric macrolide + beta-lactam or respiratory fluoroquinolone."
            },
            {
                "rank": 2,
                "name": "Atypical / Mycoplasma Lower Respiratory Infection",
                "icd_code": "J15.7",
                "probability": 38,
                "severity": "Moderate",
                "explanation": "Atypical pathogens can produce lower respiratory consolidations, but the acuity, marked neutrophilia, and high procalcitonin make typical bacterial CAP significantly more likely.",
                "supporting_evidence": [
                    "Subacute prodrome over 4 days",
                    "Pleuritic pain component"
                ],
                "against_evidence": [
                    "High procalcitonin (1.45 ng/mL) specifically argues against atypical intracellular or viral etiology"
                ],
                "guideline_citation": "ATS/IDSA Guidelines: Empiric coverage should include atypical coverage unless ruled out by antigen testing."
            },
            {
                "rank": 3,
                "name": "Acute Pulmonary Embolism with Secondary Infarction",
                "icd_code": "I26.99",
                "probability": 24,
                "severity": "High",
                "explanation": "Must be considered in patients with pleuritic chest pain and hypoxemia, although purulent sputum and procalcitonin rise favor primary infectious consolidation over sterile pulmonary infarction.",
                "supporting_evidence": [
                    "Pleuritic chest pain with SpO2 92%",
                    "Focal peripheral wedge-like density"
                ],
                "against_evidence": [
                    "Fever > 38.5°C and procalcitonin > 1.0 strongly favor infectious pneumonia"
                ],
                "guideline_citation": "ESC/ERS Guidelines: Wells score rule-out; proceed to CTPA if clinical deterioration occurs despite antibiotic therapy."
            }
        ],
        recommendations=[
            {
                "priority": "Urgent",
                "action": "Initiate empiric antimicrobial therapy (Levofloxacin 750mg IV/PO daily due to penicillin allergy)",
                "rationale": "Early initiation within 4 hours is correlated with improved clinical stability and reduced 30-day mortality."
            },
            {
                "priority": "Urgent",
                "action": "Supplementary low-flow oxygen via nasal cannula to maintain SpO2 >= 94%",
                "rationale": "Mitigate tissue hypoxemia and prevent respiratory muscle fatigue."
            },
            {
                "priority": "High",
                "action": "Obtain two sets of blood cultures and sputum Gram stain/culture prior to second antibiotic dose",
                "rationale": "Permits targeted de-escalation once pathogen identification and susceptibility testing are complete."
            },
            {
                "priority": "Routine",
                "action": "Follow-up chest radiograph at 6 weeks post-discharge",
                "rationale": "Confirm complete radiologic resolution and exclude underlying endobronchial malignancy."
            }
        ],
        raw_findings=json.dumps({
            "rag_citations": [
                "ATS/IDSA Guidelines (2019): Consensus Guidelines on the Management of Community-Acquired Pneumonia in Adults",
                "BTS Guidelines for the Management of Community Acquired Pneumonia in Adults",
                "ACR Appropriateness Criteria: Acute Respiratory Illness in Immunocompetent Adults"
            ],
            "red_flags": [
                "SpO2 dropping below 90% or RR > 30/min warrants immediate ICU escalation",
                "Development of hypotension (SBP < 90 mmHg) indicating septic shock requires urgent vasopressor protocol"
            ]
        })
    )

    # Case 2: Robert Henderson (Acute Ischemic Stroke)
    c2_orig_path = media_root / "scans" / "original" / "brain_mri_henderson.jpg"
    create_brain_mri(str(c2_orig_path))

    c2 = PatientCase.objects.create(
        patient_name="Robert Henderson",
        patient_id="MED-2026-3392",
        age=71,
        gender="male",
        chief_complaint="Acute onset right facial droop, left arm flaccid weakness, and severe expressive dysphasia starting 1.5 hours ago.",
        clinical_history="71-year-old male was in usual state of health until breakfast when wife noted sudden right facial paralysis and loss of speech fluency. History of essential hypertension, atrial fibrillation on oral anticoagulation (poor adherence), and type 2 diabetes. NIH Stroke Scale (NIHSS) score estimated at 14.",
        medications="Metformin 1000mg BID, Amlodipine 10mg daily, Warfarin 5mg daily",
        allergies="NKDA",
        vital_signs="BP: 176/98 mmHg | HR: 94 bpm (irregularly irregular) | Temp: 37.1 °C | RR: 18/min | SpO2: 97% on room air",
        lab_results="INR: 1.3 (subtherapeutic) | Blood Glucose: 138 mg/dL | Platelets: 228 x10^3/uL | Serum Creatinine: 1.1 mg/dL",
        referring_doctor="Dr. Sarah Al-Mansoor",
        specialty_context="Neurology"
    )

    s2 = ScanImage.objects.create(
        case=c2,
        scan_type="mri",
        body_region="Brain (Axial DWI/T2)",
        original_image="scans/original/brain_mri_henderson.jpg",
        notes="Axial magnetic resonance imaging demonstrating high signal restriction in the right middle cerebral artery territory."
    )

    c2_heat_path = media_root / "scans" / "heatmap" / f"heatmap_{s2.id}_brain_mri_henderson.jpg"
    generate_heatmap_overlay(
        original_image_path=str(c2_orig_path),
        output_path=str(c2_heat_path),
        abnormality_regions=[(295, 195, 90, 95, 0.98)]
    )
    s2.heatmap_image = f"scans/heatmap/heatmap_{s2.id}_brain_mri_henderson.jpg"
    s2.save()

    AnalysisReport.objects.create(
        case=c2,
        status="complete",
        differential_summary=(
            "Acute vascular neurological emergency in a 71-year-old male with atrial fibrillation presenting within the hyperacute window (1.5 hours) "
            "with NIHSS 14. Neuroimaging confirms acute restricted diffusion in the right MCA territory consistent with acute thromboembolic ischemic infarction. "
            "Subtherapeutic INR (1.3) corroborates cardioembolic pathogenesis. No evidence of intracranial hemorrhage or midline shift. "
            "Immediate multidisciplinary evaluation for systemic thrombolysis and endovascular thrombectomy (EVT) is strongly indicated."
        ),
        imaging_findings={
            "scan_1": {
                "scan_type": "BRAIN MRI (AXIAL DWI)",
                "body_region": "Cerebral",
                "findings": "Hyperacute cytotoxic edema evidenced by restricted water diffusion in the right MCA cortical and subcortical territory. Ventricular system is symmetric without hydrocephalus. Basal cisterns remain patent.",
                "abnormalities": [
                    "Focal region of acute restricted diffusion in right MCA territory (Heatmap hotspot intensity 98%)",
                    "Early sulcal effacement in right frontoparietal cortex",
                    "Loss of gray-white differentiation along insular ribbon"
                ],
                "normal_structures": [
                    "No intracranial hemorrhage or microbleeds detected",
                    "Midline structures aligned without uncal or subfalcine herniation",
                    "Posterior fossa and cerebellum unremarkable"
                ],
                "impression": "Acute ischemic stroke involving right middle cerebral artery distribution. Time-critical candidate for emergent reperfusion therapy."
            }
        },
        diagnoses=[
            {
                "rank": 1,
                "name": "Acute Cardioembolic Ischemic Stroke (Right MCA Territory)",
                "icd_code": "I63.4",
                "probability": 89,
                "severity": "Critical",
                "explanation": "Hyperacute onset of severe hemispheric focal deficits (NIHSS 14) in a patient with chronic atrial fibrillation and subtherapeutic anticoagulation (INR 1.3) is virtually pathognomonic for cardioembolic MCA occlusion, confirmed by DWI restricted diffusion.",
                "supporting_evidence": [
                    "MRI DWI confirms acute cytotoxic edema in right MCA territory",
                    "Subtherapeutic INR (1.3) with chronic atrial fibrillation",
                    "Hyperacute symptom onset 1.5 hours prior to presentation (within thrombolytic window)"
                ],
                "against_evidence": [
                    "Complete absence of blood on non-contrast imaging rules out hemorrhagic transformation at baseline"
                ],
                "guideline_citation": "AHA/ASA Stroke Guidelines: Endovascular thrombectomy (EVT) for large vessel occlusion within 6-24 hours."
            },
            {
                "rank": 2,
                "name": "High-Risk Transient Ischemic Attack (ABCD2 Score: 6)",
                "icd_code": "G45.9",
                "probability": 22,
                "severity": "Moderate",
                "explanation": "If deficits were to resolve within 24 hours, diagnosis would reclassify to TIA, though clear parenchymal cytotoxic changes on MRI indicate completed acute tissue infarction.",
                "supporting_evidence": [
                    "High vascular risk profile and atrial fibrillation"
                ],
                "against_evidence": [
                    "Presence of acute cytotoxic lesion on MRI confirms definitive infarction rather than transient ischemia"
                ],
                "guideline_citation": "AHA/ASA Guidelines: Dual antiplatelet or therapeutic anticoagulation depending on etiology."
            }
        ],
        recommendations=[
            {
                "priority": "Urgent",
                "action": "Immediate CT Angiography (CTA) of Head and Neck to assess for Large Vessel Occlusion (LVO)",
                "rationale": "Determine eligibility for emergent endovascular thrombectomy (EVT) within 6-24 hour window."
            },
            {
                "priority": "Urgent",
                "action": "IV Thrombolytic Evaluation (Tenecteplase 0.25 mg/kg or Alteplase) if blood pressure safely managed < 185/110 mmHg",
                "rationale": "Patient is well within the 4.5-hour intravenous thrombolysis therapeutic window."
            },
            {
                "priority": "High",
                "action": "Continuous cardiac telemetry monitoring and admission to dedicated Neuro-ICU / Stroke Unit",
                "rationale": "Surveillance for malignant MCA edema, hemorrhagic transformation, and secondary embolic showers."
            }
        ],
        raw_findings=json.dumps({
            "rag_citations": [
                "AHA/ASA Guidelines for the Early Management of Patients With Acute Ischemic Stroke (2024)",
                "ESO Guidelines on Intravenous Thrombolysis and Mechanical Thrombectomy in Acute Ischemic Stroke",
                "ACR Appropriateness Criteria: Cerebrovascular Disease and Acute Neurologic Deficit"
            ],
            "red_flags": [
                "Acute decline in Glasgow Coma Scale (GCS) or pupillary asymmetry indicates herniation",
                "Severe hypertension exceeding SBP > 185 mmHg increases intracranial hemorrhage risk with thrombolysis"
            ]
        })
    )

    print(f"Successfully seeded {PatientCase.objects.count()} clinical cases with scans, heatmaps, and reports!")


if __name__ == "__main__":
    seed_database()

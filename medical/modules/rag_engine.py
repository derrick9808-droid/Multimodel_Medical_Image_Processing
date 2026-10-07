"""
RAG (Retrieval-Augmented Generation) Clinical Knowledge Engine
Retrieves evidence-based clinical guidelines, diagnostic criteria, and radiologic sign patterns
to ground Anthropic Claude's second opinion analysis.
"""

import re
from typing import List, Dict, Any

CLINICAL_KNOWLEDGE_BASE = [
    {
        "id": "pulm_pneumonia_curb65",
        "category": "Pulmonology",
        "condition": "Community-Acquired Pneumonia (CAP) & Atypical Pneumonia",
        "keywords": ["fever", "cough", "sputum", "infiltrate", "consolidation", "curb-65", "dyspnea", "crackles", "leukocytosis", "procalcitonin", "chest pain", "pleuritic", "rales"],
        "imaging_patterns": ["Lobar consolidation with air bronchograms", "Patchy alveolar infiltrates", "Silhouette sign", "Reactive pleural effusion"],
        "diagnostic_criteria": "New pulmonary infiltrate on chest radiography plus >= 2 of: fever >= 38.0C, cough/purulent sputum, dyspnea, leukocytosis >= 10,000/uL.",
        "guidelines": "ATS/IDSA Guidelines: Stratify using CURB-65 / PSI score. Early empiric macrolide + beta-lactam or respiratory fluoroquinolone. Sputum/blood cultures prior to antibiotics.",
        "red_flags": ["Hypoxemia SpO2 < 90%", "Multilobar involvement on CXR", "Confusion/altered mental state", "Hypotension SBP < 90 mmHg"]
    },
    {
        "id": "cardio_acs_nstemi",
        "category": "Cardiology",
        "condition": "Acute Coronary Syndrome (NSTEMI / Unstable Angina)",
        "keywords": ["chest pain", "pressure", "substernal", "radiation", "arm pain", "jaw pain", "troponin", "diaphoresis", "ecg", "st depression", "t-wave inversion", "coronary", "ischemia"],
        "imaging_patterns": ["CXR typically excludes aortic dissection / pneumothorax", "May show pulmonary edema / cardiomegaly in decompensation"],
        "diagnostic_criteria": "Ischemic symptoms consistent with myocardial ischemia with rise/fall of cardiac troponin (hs-cTn > 99th percentile URL) without persistent ST-segment elevation on ECG.",
        "guidelines": "AHA/ACC NSTEMI Guidelines: Immediate dual antiplatelet therapy (DAPT - Aspirin + P2Y12 inhibitor), therapeutic anticoagulation (Heparin/Enoxaparin), high-intensity statin. Calculate TIMI / GRACE score for early invasive strategy (<24h).",
        "red_flags": ["Hemodynamic instability / cardiogenic shock", "Refractory chest pain despite medical therapy", "Sustained ventricular arrhythmia", "New murmur of mitral regurgitation"]
    },
    {
        "id": "pulm_pulmonary_embolism",
        "category": "Pulmonology & Vascular",
        "condition": "Acute Pulmonary Embolism (PE)",
        "keywords": ["sudden dyspnea", "pleuritic pain", "hemoptysis", "tachycardia", "d-dimer", "dvt", "leg swelling", "wells score", "ctpa", "hypoxemia", "tachypnea", "oral contraceptive", "immobilization"],
        "imaging_patterns": ["CTPA shows intraluminal filling defects in pulmonary arterial tree", "Westermark sign (oligemia)", "Hampton hump (wedge-shaped opacity)", "RV strain with RV/LV ratio > 1.0"],
        "diagnostic_criteria": "Wells score stratification. High risk: proceed directly to CT Pulmonary Angiography (CTPA). Low/Intermediate: high-sensitivity D-dimer rule-out (age-adjusted D-dimer threshold).",
        "guidelines": "ESC/ERS Guidelines: Hemodynamically unstable PE requires emergent reperfusion (systemic thrombolysis or catheter-directed). Stable patients require immediate therapeutic anticoagulation (DOAC - Apixaban/Rivaroxaban preferred).",
        "red_flags": ["Systemic hypotension SBP < 90 mmHg or shock", "RV dysfunction on echo/CTPA", "Elevated cardiac biomarkers (troponin/BNP) indicating RV strain"]
    },
    {
        "id": "neuro_acute_ischemic_stroke",
        "category": "Neurology",
        "condition": "Acute Ischemic Stroke (AIS) vs Hemorrhagic Stroke",
        "keywords": ["facial droop", "arm weakness", "hemiplegia", "aphasia", "slurred speech", "ataxia", "nihss", "onset time", "brain mri", "ncct", "dwi", "flair", "hyperdense mca", "numbness"],
        "imaging_patterns": ["NCCT: Early loss of gray-white differentiation, insular ribbon sign, hyperdense MCA sign; excludes hemorrhage", "MRI DWI: Hyperintensity with corresponding ADC hypointensity confirming acute cytotoxic edema"],
        "diagnostic_criteria": "Sudden focal neurological deficit attributable to a specific vascular territory. Urgent non-contrast head CT to rule out intracranial hemorrhage before thrombolytic therapy.",
        "guidelines": "AHA/ASA Stroke Guidelines: IV Thrombolysis (Tenecteplase or Alteplase) within 4.5 hours of symptom onset if eligible. Endovascular thrombectomy (EVT) for large vessel occlusion (LVO) within 6-24 hours guided by CT/MR perfusion.",
        "red_flags": ["Rapidly declining GCS score", "Signs of herniation (blown pupil, Cushing reflex)", "Contraindications to thrombolysis (active bleed, recent major surgery, INR > 1.7)"]
    },
    {
        "id": "pulm_pneumothorax",
        "category": "Pulmonology",
        "condition": "Pneumothorax (Spontaneous / Tension)",
        "keywords": ["sudden chest pain", "dyspnea", "tall young male", "copd", "emphysema", "absent breath sounds", "hyperresonance", "hypotension", "tracheal deviation", "subcutaneous emphysema"],
        "imaging_patterns": ["Visceral pleural line visible with absent peripheral lung markings", "Deep sulcus sign on supine view", "Tracheal/mediastinal shift away from affected side in tension pneumothorax"],
        "diagnostic_criteria": "Identification of visceral pleural line separated from chest wall by radiolucent gas on upright expiratory or inspiratory CXR, or thoracic ultrasound (loss of lung sliding).",
        "guidelines": "BTS Guidelines: Primary spontaneous pneumothorax < 2cm without dyspnea: conservative or needle aspiration. Tension pneumothorax: immediate needle decompression at 2nd intercostal space midclavicular line or 5th intercostal anterior axillary line, followed by tube thoracostomy.",
        "red_flags": ["Tension physiology: hypotension, tracheal deviation, severe respiratory distress - do NOT delay decompression for imaging"]
    },
    {
        "id": "gi_acute_appendicitis",
        "category": "Gastroenterology / Surgery",
        "condition": "Acute Appendicitis",
        "keywords": ["right lower quadrant", "mcburney", "periumbilical pain", "anorexia", "nausea", "vomiting", "fever", "rebound tenderness", "alvarado score", "leukocytosis", "ultrasound", "ct abdomen", "rlq"],
        "imaging_patterns": ["CT Abdomen/Pelvis: Dilated appendix > 6mm with wall thickening (> 2mm), periappendiceal fat stranding, appendicolith in 30%", "Ultrasound: Non-compressible, blind-ending tubular structure > 6mm diameter"],
        "diagnostic_criteria": "Alvarado score >= 7 indicates high probability. Confirmed with intravenous contrast-enhanced abdominopelvic CT (sensitivity 98%) or ultrasound (first-line in children/pregnant patients).",
        "guidelines": "WSES Jerusalem Guidelines: Early laparoscopic appendectomy within 24 hours of diagnosis reduces perforation risk. Preoperative prophylactic single-dose broad-spectrum antibiotics (Cefoxitin or Ceftriaxone + Metronidazole).",
        "red_flags": ["High fever > 38.5C with diffuse peritonitis signs indicating perforation", "Palpable mass in RLQ (phlegmon/abscess)", "Sepsis markers qSOFA >= 2"]
    },
    {
        "id": "pulm_pleural_effusion",
        "category": "Pulmonology",
        "condition": "Pleural Effusion (Exudative vs Transudative)",
        "keywords": ["dullness to percussion", "decreased breath sounds", "blunting", "costophrenic", "meniscus sign", "thoracentesis", "lights criteria", "chf", "malignancy", "infection"],
        "imaging_patterns": ["Blunting of lateral costophrenic angle on PA film (> 175 mL fluid)", "Meniscus sign", "Massive effusion with contralateral mediastinal shift", "Loculation on ultrasound or CT"],
        "diagnostic_criteria": "Diagnostic thoracentesis for new unexplained pleural effusion > 10mm thickness on decubitus or ultrasound. Light's Criteria to differentiate exudate vs transudate: pleural/serum protein > 0.5, pleural/serum LDH > 0.6, or pleural LDH > 2/3 upper limit of normal.",
        "guidelines": "BTS Pleural Disease Guidelines: Diagnostic ultrasound guidance mandatory for thoracentesis. Transudate (CHF, cirrhosis, nephrotic): treat underlying etiology. Exudate: analyze cytology, Gram stain, culture, pH, glucose, ADA.",
        "red_flags": ["Pleural fluid pH < 7.20 or frankly purulent fluid (empyema) requires prompt chest tube drainage"]
    },
    {
        "id": "cardio_heart_failure",
        "category": "Cardiology",
        "condition": "Acute Decompensated Heart Failure (ADHF)",
        "keywords": ["orthopnea", "pnd", "paroxysmal nocturnal dyspnea", "bipedal edema", "jvd", "s3 gallop", "bnp", "nt-probnp", "cardiomegaly", "kerley b lines", "pulmonary edema", "bat wing", "congestion"],
        "imaging_patterns": ["Cardiomegaly (cardiothoracic ratio > 0.5)", "Cephalization of pulmonary venous vasculature", "Kerley B lines (septal lines at costophrenic angles)", "Peribronchial cuffing and alveolar bat-wing edema"],
        "diagnostic_criteria": "Framingham criteria for CHF (>=2 major or 1 major + 2 minor criteria) alongside elevated BNP > 100 pg/mL or NT-proBNP > 300 pg/mL with objective evidence of cardiac structural or functional abnormality on echocardiography.",
        "guidelines": "AHA/ACC/HFSA Guidelines: IV loop diuretics (furosemide 1-2.5x oral dose), vasodilator therapy (nitroglycerin/nitroprusside) if SBP > 140 mmHg without severe aortic stenosis. Non-invasive positive pressure ventilation (CPAP/BiPAP) for severe respiratory distress.",
        "red_flags": ["Cardiogenic shock (hypoperfusion, cold extremities, elevated lactate, oliguria)", "Refractory pulmonary edema requiring emergent intubation"]
    }
]

def retrieve_clinical_knowledge(patient_text: str, scan_types: list = None, top_k: int = 3) -> list:
    """
    Retrieves the most relevant clinical guidelines and diagnostic protocols
    based on the patient's symptoms, lab tests, history, and imaging types.
    """
    patient_text_lower = patient_text.lower()
    scored_records = []

    for item in CLINICAL_KNOWLEDGE_BASE:
        score = 0
        matched_keywords = []

        # Keyword matching
        for kw in item["keywords"]:
            if re.search(r'\b' + re.escape(kw) + r'\b', patient_text_lower):
                score += 3
                matched_keywords.append(kw)
            elif kw in patient_text_lower:
                score += 1.5
                matched_keywords.append(kw)

        # Condition name match
        condition_words = item["condition"].lower().split()
        for cw in condition_words:
            if len(cw) > 3 and cw in patient_text_lower:
                score += 2

        # Category relevance
        if item["category"].lower() in patient_text_lower:
            score += 2

        # Scan type bonus
        if scan_types:
            for st in scan_types:
                st_lower = str(st).lower()
                for pat in item["imaging_patterns"]:
                    if any(term in pat.lower() for term in ["cxr", "chest", "x-ray"]) and any(term in st_lower for term in ["xray", "x-ray", "chest"]):
                        score += 2
                    if "ct" in pat.lower() and "ct" in st_lower:
                        score += 2
                    if "mri" in pat.lower() and "mri" in st_lower:
                        score += 2

        if score > 0:
            scored_records.append({
                "score": score,
                "condition": item["condition"],
                "category": item["category"],
                "diagnostic_criteria": item["diagnostic_criteria"],
                "guidelines": item["guidelines"],
                "imaging_patterns": item["imaging_patterns"],
                "red_flags": item["red_flags"],
                "matched_keywords": list(set(matched_keywords))
            })

    # Sort descending by relevance score
    scored_records.sort(key=lambda x: x["score"], reverse=True)
    
    # If no specific matches found, return the top general pulmonology & cardiology guidelines
    if not scored_records:
        return CLINICAL_KNOWLEDGE_BASE[:top_k]

    return scored_records[:top_k]

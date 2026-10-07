# Multimodal Medical Image Processing & Clinical Second Opinion Platform

A clinical decision support web application designed for physicians and radiologists to receive AI-powered second opinions. The platform integrates **Anthropic Claude's multimodal vision model** with a **Clinical Retrieval-Augmented Generation (RAG) engine** and automated **radiological heatmap visualization**.

---

## Key Features

- **Multimodal Visual AI**: Reads and analyzes medical imaging studies including **X-Rays, Brain & Spine MRIs, and CT Scans**.
- **Radiological Heatmap Generation**: Produces Gaussian thermal overlays highlighting focal abnormalities and lesions with an anatomical scale bar.
- **RAG Clinical Knowledge Retrieval**: Retrieves guideline recommendations and diagnostic criteria from clinical knowledge bases (ATS/IDSA for CAP, AHA/ACC for ACS/NSTEMI, AHA/ASA for Acute Ischemic Stroke, ESC/ERS for PE, WSES for Appendicitis).
- **Ranked Differential Diagnoses**: Outputs probabilities (e.g. 84%, 38%), ICD-10 coding, clinical reasoning explanations, and supporting vs. counter-evidence.
- **Actionable Clinical Recommendations**: Stratified by priority (*Urgent*, *High*, *Routine*).
- **Professional Clinical UI**: Designed in a clean white base with medical blue accents for hospital and clinic environments.

---

## Tech Stack

- **Backend**: Python 3.14, Django 6.1
- **AI & LLM**: Anthropic Claude Vision API (`claude-3-7-sonnet`)
- **RAG Engine**: Clinical guidelines retrieval module (`rag_engine.py`)
- **Computer Vision & Heatmaps**: Pillow (PIL), NumPy, SciPy
- **Frontend**: HTML5, Vanilla CSS3 (Custom design system), JavaScript

---

## Project Structure

```
├── medai_platform/             # Django project configuration & settings
├── medical/                    # Core clinical decision support application
│   ├── modules/
│   │   ├── claude_medical.py   # Claude Vision AI & diagnostic reasoning
│   │   ├── heatmap_generator.py# Thermal anomaly heatmap generator
│   │   └── rag_engine.py       # Clinical knowledge RAG retrieval
│   ├── models.py               # PatientCase, ScanImage, AnalysisReport
│   ├── views.py                # Dashboard, new case, detail & report views
│   └── urls.py                 # Application routing
├── templates/                  # Responsive HTML templates
│   ├── base.html
│   ├── index.html              # Clinical dashboard
│   ├── new_case.html           # Case intake form with quick-fill demos
│   ├── case_detail.html        # Patient scans & clinical records
│   ├── report.html             # Heatmap viewer & differential diagnoses
│   └── history.html            # Case registry
├── static/                     # CSS stylesheets & client JavaScript
│   ├── css/style.css
│   └── js/main.js
├── media/                      # Uploaded scans & generated heatmaps
├── manage.py
├── seed_medical_cases.py       # Seed script with realistic clinical cases
└── requirements.txt
```

---

## Getting Started

### 1. Clone & Setup Environment

```bash
git clone https://github.com/derrick9808-droid/Multimodel_Medical_Image_Processing.git
cd Multimodel_Medical_Image_Processing

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DJANGO_SECRET_KEY=your_secret_key_here
```

*(Note: If no API key is provided, the platform automatically runs in intelligent clinical demo mode with pre-computed differential logic).*

### 3. Run Migrations & Seed Sample Cases

```bash
python manage.py migrate
python seed_medical_cases.py
```

### 4. Start Development Server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Medical Disclaimer

MedAI is a clinical decision support tool designed for licensed medical professionals. All AI-generated diagnostic outputs and radiological findings must be verified by a qualified physician. This system does not replace direct clinical judgment.

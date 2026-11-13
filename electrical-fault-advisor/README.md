# Electrical Fault First-Response Advisor
> **A Rule-Based Decision-Support System for Campus Substation Operations**  
> *Course: 25DC204 — Fundamentals of Artificial Intelligence (CO1, CO2, CO3)*  
> *Division of Data Science and Cyber Security, Karunya Institute of Technology and Sciences*

---

## ⚠️ Substation Safety Boundary & Operational Disclaimer
**Advisory System Only:** The Electrical Fault First-Response Advisor is an educational, rule-based decision-support prototype. It **does not** actuate physical switchgear, trip breakers, reset relays, or replace a qualified electrical technician or safety officer. All thresholds, current limits, and operational sequences shown are illustrative and **must be reviewed and approved by qualified high-voltage electrical personnel** before being applied to live campus distribution infrastructure.

---

## 👥 Project Attribution & Team
- **Derrick J** — `URK26AI1060`
- **Mani Kandan A** — `URK26AI1108`
- **A Jayas Shiny** — `URK26AI1062`
- **S Vishnu Priya** — `URK26AI1057`

---

## ⚡ Quick Start (Two-Command Run)

### Option A: Zero-Dependency Python Run (Recommended)
The backend features an automated dual-mode engine. Running `python backend/main.py` starts a built-in server that serves both the JSON API and the complete frontend UI on port 8000 using only Python's standard library:

```bash
# 1. Navigate to the project root
cd electrical-fault-advisor

# 2. Launch the application server
python backend/main.py
```
Open **[http://localhost:8000](http://localhost:8000)** in any modern web browser.

---

### Option B: Full-Stack Dev Mode (FastAPI + Vite)
If Python dependencies and Node.js are installed:

```bash
# 1. Start FastAPI backend (Port 8000)
cd electrical-fault-advisor/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# 2. In a separate terminal, start Vite frontend (Port 5173)
cd ../frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser (Vite automatically proxies `/api` calls to `http://localhost:8000`).

---

## 🧪 Running Unit & Integration Tests

```bash
# 1. Run core advisor reasoning tests (100% pass on 17 benchmark events)
python backend/test_advisor.py

# 2. Run backend integration tests (validates 422 errors and response schemas)
python backend/test_server.py
```

---

## 🏛️ System Architecture & Inference Engine

```
[ Operator Input / Sensor Readings ]
               │
               ▼
   [ 1. Fact Derivation & Schema Validation ] (422 HTTP check)
               │
               ▼
      [ 2. Forward Chaining ] (Evaluates rules R1–R12 against facts)
               │
               ▼
   [ 3. Conflict Resolution ] (Priority wins; Specificity breaks ties)
               │
               ▼
      [ 4. Alert Level Mapping ] (1-2: ADVISORY, 3-4: WARNING, 5-6: CRITICAL)
               │
               ▼
[ 5. Explainable Advice, Safety Steps & Audit Trace ]
```

### 12 Deterministic Production Rules

| Rule ID | IF Antecedent Conditions | THEN Action | Priority | Specificity |
| :---: | :--- | :--- | :---: | :---: |
| **R1** | `alarm=overcurrent` AND `load ∈ {low, medium}` | `monitor` | 1 | 2 |
| **R2** | `alarm=overcurrent` AND `load=high` | `isolate_feeder` | 3 | 2 |
| **R3** | `alarm=overcurrent` AND `load=high` AND `backup=available` | `switch_to_backup` | 4 | 3 |
| **R4** | `alarm=earth_fault` | `isolate_feeder` | 4 | 1 |
| **R5** | `alarm=earth_fault` AND `weather=storm` AND `backup=unavailable` | `call_utility` | 5 | 3 |
| **R6** | `alarm=transformer_temp` AND `load ∈ {low, medium}` | `monitor` | 2 | 2 |
| **R7** | `alarm=transformer_temp` AND `load=high` | `call_utility` | 5 | 2 |
| **R8** | `alarm=breaker_trip` AND `backup=available` | `switch_to_backup` | 4 | 2 |
| **R9** | `alarm=breaker_trip` AND `backup=unavailable` | `call_utility` | 5 | 2 |
| **R10** | `alarm=abnormal_voltage` | `monitor` | 2 | 1 |
| **R11** | `alarm=abnormal_voltage` AND `weather=storm` | `call_utility` | 5 | 2 |
| **R12** | `alarm=smoke_or_fire` | `call_utility` | 6 | 1 |

*Note on Conflict Resolution:* If multiple rules fire simultaneously, the system selects the rule with the highest numerical priority. If priority is equal, the rule with the higher condition count (specificity) wins. When no rule matches, the system outputs `UNCERTAIN` and advises calling utility/requesting inspection.

---

## 📊 Benchmark Evaluation: Advisor vs. Baseline

The system is evaluated against the naive single-attribute baseline on the 17 canonical operational scenarios:

| Metric | Multi-Condition Expert Advisor | Naive Alarm-Only Baseline |
| :--- | :---: | :---: |
| **Overall Accuracy** | **17 / 17 (100.0%)** | **9 / 17 (52.9%)** |
| **Overcurrent with Low Load** | `monitor` (Correct) | `isolate_feeder` (Unnecessary outage) |
| **Overcurrent with Backup Available** | `switch_to_backup` (Correct) | `isolate_feeder` (Disregards backup) |
| **Earth Fault during Storm (No Backup)** | `call_utility` (Correct) | `isolate_feeder` (Under-escalates danger) |
| **Transformer Temp with High Load** | `call_utility` (Correct) | `monitor` (Dangerous asset risk) |
| **Abnormal Voltage during Storm** | `call_utility` (Correct) | `monitor` (Grid surge ignored) |

> **Academic Limitations Note:** The evaluation uses 17 canonical operational scenarios. Because the expected test answers originate from the same domain operating logic as the rule base, this evaluation demonstrates **formal logical consistency and complete rule coverage**, rather than empirical statistical generalization on uncalibrated field telemetry.

---

## 🔌 REST API Specification

### 1. `GET /api/rules`
Returns the complete list of 12 production rules with antecedents, consequences, priority, and textual representation.
```json
[
  {
    "id": "R1",
    "conditions": { "alarm": ["overcurrent"], "load": ["low", "medium"] },
    "action": "monitor",
    "priority": 1,
    "specificity": 2,
    "text": "IF alarm=overcurrent AND load in {low, medium} THEN monitor (Priority 1)"
  }
]
```

### 2. `GET /api/events`
Returns the 17 canonical benchmark test events with facts, descriptions, and expected actions.

### 3. `POST /api/advise`
Executes forward chaining and conflict resolution for a reported event.
- **Request Body:**
  ```json
  {
    "feeder": "hostel",
    "alarm": "overcurrent",
    "load": "high",
    "weather": "clear",
    "backup": "available"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "action": "switch_to_backup",
    "alert_level": "WARNING",
    "fired_rules": ["R2", "R3"],
    "chosen_rule": {
      "id": "R3",
      "priority": 4,
      "specificity": 3,
      "text": "IF alarm=overcurrent AND load=high AND backup=available THEN switch_to_backup (Priority 4)"
    },
    "conflict": true,
    "reason": "Conflict resolved: R3 (Priority 4) overrode lower-priority matching rule(s) R2 (P3).",
    "safe_steps": [
      "Keep students and unauthorised persons away from the affected area.",
      "Do not touch, open, reset or attempt to repair electrical equipment.",
      "Inform the authorised campus electrical maintenance team immediately.",
      "Request the authorised team to transfer load to the backup supply."
    ]
  }
  ```
- **Validation Error (422 Unprocessable Entity):**
  Returns descriptive error details when attributes or values fail schema validation.

### 4. `GET /api/evaluate`
Runs the benchmark engine on all 17 canonical events, returning per-event accuracy and aggregate comparative statistics.

---

## 🎨 Design System: "Playful Twilight"

The UI strictly adheres to a four-color palette with tints computed via `color-mix()`:

| Token | Hex | Role | Contrast Ratio |
| :--- | :---: | :--- | :---: |
| **Blush** | `#F6E8EA` | Page background, card surfaces, input fills | Base light |
| **Coral** | `#EF626C` | Primary buttons, CRITICAL alerts, active accents | 5.8:1 with Ink |
| **Ink** | `#22181C` | Text, header/sidebar background, crisp borders | Base dark |
| **Mint** | `#59C9A5` | ADVISORY alerts, pass badges, chart successes | 7.9:1 with Ink |

### WCAG AA Compliance
- **Text Contrast:** Ink text (`#22181C`) is used on Blush, Mint, and Coral fills (exceeding WCAG AA 4.5:1 requirement).
- **No Reliance on Color Alone:** All alert levels are rendered with an explicit textual name and dedicated SVG icon.
- **Motion Accessibility:** Respects `@media (prefers-reduced-motion: reduce)`.

---

## 📑 How this Prototype Maps to the Course Report

| Report Section | Corresponding Web App Screen / Code Module | Key Concepts Demonstrated |
| :--- | :--- | :--- |
| **1. Problem Formulation** | **About Tab (`aboutView.js`)** | PEAS framework, campus substation single-line diagram context, safety boundaries. |
| **2. Knowledge Representation** | **Rule Base Tab (`rulesView.js`), `fault_advisor.py`** | Propositional production rules, condition specificity, priority ranking. |
| **3. Inference & Problem Solving** | **Advisor Tab (`advisorView.js`), Direct & Sensor Modes** | Forward-chaining inference, conflict resolution, sensor threshold derivation. |
| **4. Experimental Evaluation** | **Evaluation Tab (`evaluateView.js`)** | 17 benchmark cases, 100% vs 52.9% baseline comparison, inline SVG chart, academic limitations. |
| **5. Audit & Feedback Loop** | **Event Log Tab (`logView.js`)** | LocalStorage audit trail, CSV export, human-in-the-loop verification simulation. |


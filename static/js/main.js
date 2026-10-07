/**
 * MedAI Clinical Decision Support Platform — Interactive Client JS
 */

document.addEventListener("DOMContentLoaded", () => {
  initLightbox();
  initScanUploader();
  initSampleCaseButtons();
  initProbabilityBars();
});

/* ==========================================================================
   Scan Lightbox Modal
   ========================================================================== */
function initLightbox() {
  let modal = document.getElementById("scan-lightbox-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "scan-lightbox-modal";
    modal.className = "lightbox-modal";
    modal.innerHTML = `
      <div class="lightbox-content">
        <button class="lightbox-close" aria-label="Close image">&times;</button>
        <img id="lightbox-img" src="" alt="Enlarged Medical Scan" />
      </div>
    `;
    document.body.appendChild(modal);

    const closeBtn = modal.querySelector(".lightbox-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        modal.classList.remove("active");
      });
    }

    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("active")) {
        modal.classList.remove("active");
      }
    });
  }
}

window.openLightbox = function(imageUrl) {
  const modal = document.getElementById("scan-lightbox-modal");
  const img = document.getElementById("lightbox-img");
  if (modal && img) {
    img.src = imageUrl;
    modal.classList.add("active");
  }
};

/* ==========================================================================
   Multi-Scan File Uploader & Preview
   ========================================================================== */
function initScanUploader() {
  const fileInput = document.getElementById("scan-file-input") || document.getElementById("scan-files-input");
  const uploadZone = document.getElementById("upload-zone") || document.getElementById("scan-dropzone");
  const scansList = document.getElementById("scans-list") || document.getElementById("scan-upload-preview-container");
  const template = document.getElementById("scan-meta-template");

  if (!fileInput || !scansList) return;

  if (uploadZone) {
    ["dragenter", "dragover"].forEach(name => {
      uploadZone.addEventListener(name, (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = "var(--blue-600)";
        uploadZone.style.background = "#E0F2FE";
      }, false);
    });

    ["dragleave", "drop"].forEach(name => {
      uploadZone.addEventListener(name, (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = "";
        uploadZone.style.background = "";
      }, false);
    });

    uploadZone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      if (dt.files && dt.files.length) {
        fileInput.files = dt.files;
        renderFiles(dt.files);
      }
    });

    uploadZone.addEventListener("click", (e) => {
      if (e.target.tagName !== "BUTTON" && e.target !== fileInput) {
        fileInput.click();
      }
    });
  }

  fileInput.addEventListener("change", () => {
    if (fileInput.files) {
      renderFiles(fileInput.files);
    }
  });

  function renderFiles(files) {
    scansList.innerHTML = "";
    Array.from(files).forEach((file, idx) => {
      if (!file.type.startsWith("image/")) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        if (template) {
          const clone = template.content.cloneNode(true);
          const thumb = clone.querySelector(".scan-thumb");
          const nameEl = clone.querySelector(".scan-filename");
          const removeBtn = clone.querySelector(".scan-remove-btn");
          const bodyInput = clone.querySelector('input[name="body_region"]');

          if (thumb) thumb.src = e.target.result;
          if (nameEl) nameEl.textContent = file.name;
          if (bodyInput) bodyInput.value = "Chest";

          if (removeBtn) {
            removeBtn.addEventListener("click", (ev) => {
              const row = ev.target.closest(".scan-meta-row");
              if (row) row.remove();
            });
          }
          scansList.appendChild(clone);
        } else {
          const item = document.createElement("div");
          item.className = "scan-meta-row";
          item.innerHTML = `
            <div class="scan-thumb-wrap">
              <img class="scan-thumb" src="${e.target.result}" alt="${file.name}" />
            </div>
            <div class="scan-meta-fields">
              <div class="scan-filename">${file.name}</div>
              <select name="scan_type" class="form-control form-select form-select-sm">
                <option value="xray" selected>X-Ray</option>
                <option value="ct">CT Scan</option>
                <option value="mri">MRI</option>
                <option value="ultrasound">Ultrasound</option>
              </select>
              <input type="text" name="body_region" value="Chest" class="form-control form-control-sm" placeholder="Body Region" />
              <input type="text" name="scan_notes" class="form-control form-control-sm" placeholder="Notes (optional)" />
            </div>
          `;
          scansList.appendChild(item);
        }
      };
      reader.readAsDataURL(file);
    });
  }
}

/* ==========================================================================
   Quick-Fill Clinical Samples
   ========================================================================== */
function initSampleCaseButtons() {
  const samples = {
    pneumonia: {
      patient_name: "Eleanor Vance",
      patient_id: "MED-2026-8941",
      age: "64",
      gender: "female",
      specialty_context: "Pulmonology",
      referring_doctor: "Dr. Marcus Chen",
      chief_complaint: "Productive cough with rust-colored sputum, high fevers, and pleuritic right-sided chest pain for 4 days.",
      clinical_history: "Patient reports worsening shortness of breath on exertion, shaking chills, and fatigue. Mild COPD history, former smoker (20 pack-years, quit 8 yrs ago). Denies orthopnea or lower extremity edema.",
      medications: "Albuterol MDI PRN, Atorvastatin 20mg daily, Lisinopril 10mg daily",
      allergies: "Penicillin (rash)",
      vital_signs: "BP: 128/78 mmHg\nHR: 98 bpm (regular)\nTemp: 38.8 °C (101.8 °F)\nRR: 24 breaths/min\nSpO2: 92% on room air",
      lab_results: "WBC: 16.4 x10^3/uL (86% neutrophils, 8% bands)\nCRP: 112 mg/L\nProcalcitonin: 1.45 ng/mL\nBUN: 22 mg/dL, Creatinine: 1.0 mg/dL"
    },
    stroke: {
      patient_name: "Robert Henderson",
      patient_id: "MED-2026-3392",
      age: "71",
      gender: "male",
      specialty_context: "Neurology",
      referring_doctor: "Dr. Sarah Al-Mansoor",
      chief_complaint: "Sudden onset right-sided facial weakness, arm drift, and slurred expressive speech.",
      clinical_history: "Onset 2 hours ago during breakfast. History of essential hypertension, type 2 diabetes mellitus, and chronic atrial fibrillation.",
      medications: "Metformin 1000mg BID, Amlodipine 10mg daily, Warfarin 5mg daily",
      allergies: "NKDA",
      vital_signs: "BP: 174/98 mmHg\nHR: 92 bpm (irregular)\nTemp: 37.0 °C\nRR: 18 breaths/min\nSpO2: 97% on room air",
      lab_results: "INR: 1.3 (subtherapeutic)\nBlood Glucose: 138 mg/dL\nPlatelets: 220 x10^3/uL\nTroponin: <0.01 ng/mL"
    },
    cardiac: {
      patient_name: "Arthur Davies",
      patient_id: "MED-2026-4410",
      age: "58",
      gender: "male",
      specialty_context: "Cardiology",
      referring_doctor: "Dr. Rachel Sterling",
      chief_complaint: "Substernal crushing chest pressure radiating to left jaw and shoulder for 2 hours.",
      clinical_history: "Symptoms began at rest, associated with cold diaphoresis and mild nausea. History of hyperlipidemia and family history of premature CAD.",
      medications: "Atorvastatin 40mg daily",
      allergies: "Aspirin (gastritis)",
      vital_signs: "BP: 156/92 mmHg\nHR: 104 bpm\nTemp: 36.9 °C\nRR: 22 breaths/min\nSpO2: 95% on room air",
      lab_results: "hs-cTnI: 0.84 ng/mL (elevated, ref <0.04)\nCK-MB: 28 U/L\nTotal Cholesterol: 242 mg/dL\nPotassium: 4.1 mEq/L"
    }
  };

  document.querySelectorAll("[data-sample-case]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const key = btn.getAttribute("data-sample-case");
      const data = samples[key];
      if (!data) return;

      Object.keys(data).forEach(field => {
        const input = document.getElementById(field) || document.querySelector(`[name="${field}"]`);
        if (input) {
          input.value = data[field];
          input.dispatchEvent(new Event("change"));
        }
      });
    });
  });
}

/* ==========================================================================
   Animated Probability Bars
   ========================================================================== */
function initProbabilityBars() {
  const bars = document.querySelectorAll(".prob-bar");
  bars.forEach(bar => {
    const width = bar.style.width;
    bar.style.width = "0%";
    setTimeout(() => {
      bar.style.width = width;
    }, 150);
  });
}

window.showAnalysisSpinner = function(btn) {
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="pulse-dot" style="display:inline-block; margin-right:8px;"></span> Analyzing with AI...`;
    btn.form.submit();
  }
};

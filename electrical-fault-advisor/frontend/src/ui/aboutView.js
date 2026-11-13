/**
 * About Screen View
 * PEAS Framework, 5-Stage Pipeline, CO Mapping, Academic Attribution & Safety Boundary
 */

import { icons } from '../icons.js';

export function createAboutView() {
  const container = document.createElement('div');
  container.className = 'about-container';

  const PEAS = [
    ['Performance (P)', 'Zero false-negatives on critical faults; 100% adherence to substation operating procedures; <50ms response latency; maximized power continuity without risking asset damage.'],
    ['Environment (E)', 'Campus 11kV/415V distribution substation; 3 feeder circuits (Hostel, Academic, Lab); weather states (Clear, Rain, Storm).'],
    ['Actuators (A)', 'Advisory screen output to human operators, alert level badges, safe operational checklists (strictly advisory; no automated switchgear actuation).'],
    ['Sensors (S)', 'Current transformers (Amps), core temperature thermistors (°C), breaker auxiliary trip contacts, ground leakage residual sensors, smoke/fire detectors, weather feed.']
  ];

  const STAGES = [
    ['1', 'Input', 'Ingests feeder facts or continuous analog ammeter/thermistor telemetry.', 'var(--color-coral)'],
    ['2', 'Analyse', 'Computes load ratio percentage, derives alarms, validates input against 422 schema.', 'var(--color-ink)'],
    ['3', 'Reason', 'Forward-chaining inference over the 12 production rules in the knowledge base.', 'var(--color-coral)'],
    ['4', 'Advise', 'Conflict resolution (Priority wins, Specificity breaks ties) selects single response.', 'var(--color-mint)'],
    ['5', 'Escalate', 'Assigns alert level (ADVISORY to CRITICAL), compiles safety checklist and audit trace.', 'var(--color-ink)']
  ];

  const CO_MAP = [
    ['CO1', 'Formulate intelligent agents and evaluate performance', 'Complete PEAS agent model, rule engine benchmark across 17 test events, quantitative comparison against baseline (100% vs 52.9%).', 'var(--color-mint)'],
    ['CO2', 'Solve problems using knowledge representation and heuristic search', 'Multi-attribute substation facts and dispatch problem solving using hierarchical priority and specificity conflict resolution.', 'var(--color-coral)'],
    ['CO3', 'Design knowledge bases and logical inference mechanisms', 'Deterministic propositional rule base (R1-R12) executing forward chaining, transparent audit traces, and conflict explanation.', 'var(--color-ink)']
  ];

  const TEAM = [
    ['Derrick J', 'URK26AI1060'],
    ['Mani Kandan A', 'URK26AI1108'],
    ['A Jayas Shiny', 'URK26AI1062'],
    ['S Vishnu Priya', 'URK26AI1057']
  ];

  container.innerHTML = `
    <div class="card" style="border:2px solid var(--color-coral);background-color:var(--coral-tint-15);margin-bottom:24px;">
      <h3 style="font-size:1.1rem;font-weight:800;color:var(--color-ink);display:flex;align-items:center;gap:8px;">
        ${icons.shield(20)} Substation Safety Boundary & Operational Disclaimer
      </h3>
      <p style="margin-top:8px;font-size:0.9rem;line-height:1.5;color:var(--color-ink);">
        <strong>Advisory System Only:</strong> The Electrical Fault First-Response Advisor is an educational decision-support tool. 
        It does <em>not</em> directly control switchgear, trip breakers, or actuate relays. It is <em>not</em> a substitute for certified 
        substation electricians or chartered electrical safety engineers. All physical thresholds, ratings, and procedures are illustrative 
        and must be approved by qualified electrical personnel before applying to live high-voltage infrastructure.
      </p>
    </div>

    <div class="card">
      <h3 class="card-title">${icons.about(20)} PEAS Intelligent Agent Framework</h3>
      <p class="card-description">Formal specification of the substation diagnostic agent under the AI agent paradigm.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:16px;">
        ${PEAS.map(([title, text]) => `
          <div style="background:var(--bg-page);padding:14px;border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
            <strong style="color:var(--color-coral);font-size:0.85rem;text-transform:uppercase;">${title}</strong>
            <p style="font-size:0.84rem;margin-top:6px;line-height:1.45;">${text}</p>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="card">
      <h3 class="card-title">${icons.rules(20)} 5-Stage Inference & Decision Pipeline</h3>
      <p class="card-description">End-to-end data processing workflow from telemetry acquisition to operator escalation.</p>
      <div style="display:flex;gap:10px;margin-top:16px;flex-wrap:wrap;justify-content:space-between;">
        ${STAGES.map(([num, title, text, col]) => `
          <div style="flex:1;min-width:160px;background:var(--bg-page);padding:12px;border-radius:var(--radius-md);border-top:3px solid ${col};">
            <div style="font-size:0.72rem;font-weight:800;color:${col};">STAGE ${num}</div>
            <strong style="font-size:0.88rem;">${title}</strong>
            <p style="font-size:0.78rem;color:var(--text-muted);margin-top:4px;">${text}</p>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="card">
      <h3 class="card-title">${icons.evaluate(20)} Course Outcome (CO) Curriculum Mapping</h3>
      <p class="card-description">Alignment with Course 25DC204 (Fundamentals of Artificial Intelligence).</p>
      <div style="display:flex;flex-direction:column;gap:10px;margin-top:14px;">
        ${CO_MAP.map(([co, title, text, col]) => `
          <div style="background:var(--bg-page);padding:12px;border-radius:var(--radius-md);border-left:4px solid ${col};">
            <strong>${co}: ${title}</strong>
            <p style="font-size:0.82rem;color:var(--text-muted);margin-top:2px;">${text}</p>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="card">
      <h3 class="card-title">${icons.about(20)} Project Attribution & Team Information</h3>
      <div style="margin-top:12px;font-size:0.88rem;line-height:1.6;">
        <p><strong>Course:</strong> 25DC204 — Fundamentals of Artificial Intelligence</p>
        <p><strong>Department:</strong> Division of Data Science and Cyber Security</p>
        <p><strong>Institution:</strong> Karunya Institute of Technology and Sciences</p>
      </div>
      <div style="margin-top:16px;">
        <h4 style="font-size:0.85rem;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:8px;">Project Team:</h4>
        <ul style="list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;font-size:0.85rem;">
          ${TEAM.map(([name, id]) => `
            <li style="padding:8px 12px;background:var(--bg-page);border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
              <strong>${name}</strong> <span style="font-family:var(--font-mono);color:var(--color-ink);">(${id})</span>
            </li>
          `).join('')}
        </ul>
      </div>
    </div>
  `;

  return container;
}

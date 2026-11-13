/**
 * Advisor Screen View
 * Direct Form, Sensor Mode Derivation, Recommendation Banner, Safe Steps & Reasoning Trace
 */

import { requestAdvice } from '../api.js';
import { icons } from '../icons.js';

export function createAdvisorView(appState) {
  const container = document.createElement('div');
  container.className = 'advisor-container';

  let currentFacts = { feeder: 'hostel', alarm: 'overcurrent', load: 'medium', weather: 'clear', backup: 'available' };
  let isSensorMode = false;
  let sensorInputs = { current: 125, rated: 100, temp: 78, breaker: 'TRIPPED', smokeDetected: false, earthLeakageDetected: false, voltageAbnormal: false };

  const OPTIONS = {
    feeder: [['hostel', 'Hostel Feeder'], ['academic', 'Academic Block'], ['lab', 'Research Lab']],
    alarm: [
      ['overcurrent', 'Overcurrent'], ['earth_fault', 'Earth Fault'],
      ['transformer_temp', 'Transformer Temp'], ['abnormal_voltage', 'Abnormal Voltage'],
      ['breaker_trip', 'Breaker Trip'], ['smoke_or_fire', 'Smoke / Fire']
    ],
    load: [['low', 'Low (<70%)'], ['medium', 'Medium (70-100%)'], ['high', 'High (>100%)']],
    weather: [['clear', 'Clear'], ['rain', 'Rain'], ['storm', 'Storm / Lightning']],
    backup: [['available', 'Backup Available'], ['unavailable', 'Backup Unavailable']]
  };

  const ATTR_LABELS = {
    feeder: 'Substation Feeder', alarm: 'Alarm Indicator', load: 'Electrical Load',
    weather: 'Weather Condition', backup: 'Backup Supply'
  };

  function deriveFactsFromSensors() {
    const { current, rated, temp, breaker, smokeDetected, earthLeakageDetected, voltageAbnormal } = sensorInputs;
    const ratio = rated > 0 ? (current / rated) * 100 : 0;
    const derivedLoad = ratio < 70 ? 'low' : ratio <= 100 ? 'medium' : 'high';

    let derivedAlarm = 'abnormal_voltage';
    if (smokeDetected) derivedAlarm = 'smoke_or_fire';
    else if (breaker === 'TRIPPED') derivedAlarm = 'breaker_trip';
    else if (earthLeakageDetected) derivedAlarm = 'earth_fault';
    else if (current > rated) derivedAlarm = 'overcurrent';
    else if (temp > 75) derivedAlarm = 'transformer_temp';
    else if (voltageAbnormal) derivedAlarm = 'abnormal_voltage';
    else if (current > rated * 0.95) derivedAlarm = 'overcurrent';

    return { feeder: currentFacts.feeder, alarm: derivedAlarm, load: derivedLoad, weather: currentFacts.weather, backup: currentFacts.backup, ratio: ratio.toFixed(1) };
  }

  function renderSensorPanel() {
    const derived = deriveFactsFromSensors();
    return `
      <div class="sensor-panel">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
          <div>
            <strong style="font-size:0.9rem;">Sensor-to-Fact Derivation Mode</strong>
            <p style="font-size:0.78rem;color:var(--text-muted);">Analog telemetry evaluated against illustrative thresholds.</p>
          </div>
          <button type="button" id="load-slide-demo-btn" class="btn btn-secondary btn-sm" title="Load slide example">
            ${icons.bolt(14)} <span>1-Click Lecture Slide Demo</span>
          </button>
        </div>
        <div class="sensor-grid">
          <div class="input-group"><label for="sensor-current">Measured Current (A)</label><input type="number" id="sensor-current" value="${sensorInputs.current}" min="0" max="600" step="5"></div>
          <div class="input-group"><label for="sensor-rated">Rated Current (A)</label><input type="number" id="sensor-rated" value="${sensorInputs.rated}" min="10" max="600" step="10"></div>
          <div class="input-group"><label for="sensor-temp">Transformer Temp (°C)</label><input type="number" id="sensor-temp" value="${sensorInputs.temp}" min="20" max="150" step="1"></div>
          <div class="input-group"><label for="sensor-breaker">Breaker Status</label>
            <select id="sensor-breaker">
              <option value="OK" ${sensorInputs.breaker === 'OK' ? 'selected' : ''}>OK (Closed)</option>
              <option value="TRIPPED" ${sensorInputs.breaker === 'TRIPPED' ? 'selected' : ''}>TRIPPED (Open)</option>
            </select>
          </div>
        </div>
        <div class="derived-facts-summary">
          <div><strong>Derived Facts:</strong> <span class="fact-chip">load=${derived.load} (${derived.ratio}%)</span> <span class="fact-chip">alarm=${derived.alarm}</span></div>
          <span style="font-size:0.75rem;color:var(--text-muted);">Thresholds: current > rated → overcurrent; temp > 75°C → transformer_temp; breaker TRIPPED → breaker_trip.</span>
        </div>
      </div>
    `;
  }

  function render() {
    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${icons.advisor(20)} Campus Substation Fault Advisor</h2>
            <p class="card-description">Select reported fault parameters to receive instant explainable first-response recommendations.</p>
          </div>
          <button id="toggle-sensor-btn" class="btn btn-secondary btn-sm" title="Toggle Sensor Simulation Mode">
            ${icons.sensor(16)} <span>${isSensorMode ? 'Switch to Direct Mode' : 'Sensor Derivation Mode'}</span>
          </button>
        </div>

        ${isSensorMode ? renderSensorPanel() : ''}

        <form id="advisor-form" onsubmit="return false;">
          ${Object.keys(OPTIONS).map(attr => {
            const isAuto = isSensorMode && (attr === 'alarm' || attr === 'load');
            return `
              <div class="form-section" ${isAuto ? 'style="opacity:0.6;pointer-events:none;"' : ''}>
                <label class="form-label">${ATTR_LABELS[attr]} ${isAuto ? '(Auto-derived)' : ''}</label>
                <div class="segmented-group" data-attr="${attr}">
                  ${OPTIONS[attr].map(([val, label]) => `
                    <button type="button" class="chip-btn ${currentFacts[attr] === val ? 'active' : ''}" data-val="${val}">${label}</button>
                  `).join('')}
                </div>
              </div>
            `;
          }).join('')}

          <div style="display:flex;gap:12px;margin-top:24px;flex-wrap:wrap;">
            <button type="button" id="advise-submit-btn" class="btn btn-primary">${icons.bolt(18)} <span>Get Recommendation</span></button>
            <button type="button" id="advise-reset-btn" class="btn btn-secondary">${icons.reset(16)} <span>Reset</span></button>
          </div>
        </form>
      </div>
      <div id="results-container" aria-live="polite"></div>
    `;
    bindEvents();
  }

  function bindEvents() {
    const toggleSensorBtn = container.querySelector('#toggle-sensor-btn');
    if (toggleSensorBtn) {
      toggleSensorBtn.onclick = () => {
        isSensorMode = !isSensorMode;
        if (isSensorMode) {
          const derived = deriveFactsFromSensors();
          currentFacts.alarm = derived.alarm;
          currentFacts.load = derived.load;
        }
        render();
      };
    }

    const slideDemoBtn = container.querySelector('#load-slide-demo-btn');
    if (slideDemoBtn) {
      slideDemoBtn.onclick = () => {
        sensorInputs = { current: 125, rated: 100, temp: 78, breaker: 'TRIPPED', smokeDetected: false, earthLeakageDetected: false, voltageAbnormal: false };
        const derived = deriveFactsFromSensors();
        currentFacts.alarm = derived.alarm;
        currentFacts.load = derived.load;
        render();
        executeAdvice();
      };
    }

    if (isSensorMode) {
      const cur = container.querySelector('#sensor-current');
      const rat = container.querySelector('#sensor-rated');
      const tmp = container.querySelector('#sensor-temp');
      const brk = container.querySelector('#sensor-breaker');
      const onChg = () => {
        sensorInputs.current = parseFloat(cur.value) || 0;
        sensorInputs.rated = parseFloat(rat.value) || 100;
        sensorInputs.temp = parseFloat(tmp.value) || 25;
        sensorInputs.breaker = brk.value;
        const derived = deriveFactsFromSensors();
        currentFacts.alarm = derived.alarm;
        currentFacts.load = derived.load;
        render();
      };
      if (cur) cur.oninput = onChg;
      if (rat) rat.oninput = onChg;
      if (tmp) tmp.oninput = onChg;
      if (brk) brk.onchange = onChg;
    }

    container.querySelectorAll('.segmented-group button').forEach(btn => {
      btn.onclick = () => {
        const group = btn.closest('.segmented-group');
        currentFacts[group.dataset.attr] = btn.dataset.val;
        group.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      };
    });

    const submitBtn = container.querySelector('#advise-submit-btn');
    if (submitBtn) submitBtn.onclick = executeAdvice;

    const resetBtn = container.querySelector('#advise-reset-btn');
    if (resetBtn) {
      resetBtn.onclick = () => {
        currentFacts = { feeder: 'hostel', alarm: 'overcurrent', load: 'medium', weather: 'clear', backup: 'available' };
        sensorInputs = { current: 125, rated: 100, temp: 78, breaker: 'TRIPPED', smokeDetected: false, earthLeakageDetected: false, voltageAbnormal: false };
        const resBox = container.querySelector('#results-container');
        if (resBox) resBox.innerHTML = '';
        render();
      };
    }
  }

  async function executeAdvice() {
    const resultsBox = container.querySelector('#results-container');
    if (!resultsBox) return;

    resultsBox.innerHTML = `
      <div class="card" style="text-align:center;padding:28px;">
        <p style="font-weight:600;color:var(--text-muted);">Evaluating rules through forward chaining...</p>
      </div>`;

    try {
      if (isSensorMode) {
        const derived = deriveFactsFromSensors();
        currentFacts.alarm = derived.alarm;
        currentFacts.load = derived.load;
      }
      const res = await requestAdvice(currentFacts);
      renderResults(res, currentFacts);

      if (appState && appState.addLogEntry) {
        appState.addLogEntry({
          timestamp: new Date().toLocaleTimeString(),
          facts: { ...currentFacts },
          action: res.action,
          alert_level: res.alert_level,
          rule_id: res.chosen_rule ? res.chosen_rule.id : 'NONE',
          verified: false
        });
      }
    } catch (err) {
      resultsBox.innerHTML = `
        <div class="card" style="border:2px solid var(--color-coral);background-color:var(--coral-tint-15);">
          <h3 style="font-size:1.1rem;font-weight:700;color:var(--color-ink);">Advice Evaluation Error</h3>
          <p style="margin-top:6px;font-size:0.9rem;">${err.message || 'Unable to connect to advisory engine.'}</p>
        </div>`;
    }
  }

  function getBadgeHtml(level) {
    if (level === 'ADVISORY') return `<span class="badge badge-advisory">${icons.check(14)} ADVISORY</span>`;
    if (level === 'WARNING') return `<span class="badge badge-warning">${icons.alertTriangle(14)} WARNING</span>`;
    if (level === 'CRITICAL') return `<span class="badge badge-critical">${icons.criticalOctagon(14)} CRITICAL</span>`;
    return `<span class="badge badge-uncertain">${icons.uncertainSearch(14)} UNCERTAIN</span>`;
  }

  function formatActionTitle(act) {
    switch (act) {
      case 'monitor': return 'MONITOR SYSTEM CAREFULLY';
      case 'isolate_feeder': return 'ISOLATE AFFECTED FEEDER';
      case 'switch_to_backup': return 'TRANSFER TO BACKUP SUPPLY';
      case 'call_utility': return 'ESCALATE / CALL UTILITY NOW';
      default: return act.toUpperCase().replace('_', ' ');
    }
  }

  function renderResults(res, facts) {
    const resultsBox = container.querySelector('#results-container');
    if (!resultsBox) return;

    const levelClass = res.alert_level.toLowerCase();
    const badgeHtml = getBadgeHtml(res.alert_level);
    const actionHeadline = formatActionTitle(res.action);

    resultsBox.innerHTML = `
      <div class="recommendation-panel">
        <div class="alert-banner ${levelClass}">
          <div class="alert-header-row">
            ${badgeHtml}
            <span style="font-size:0.8rem;font-family:var(--font-mono);font-weight:700;">
              ${res.chosen_rule ? `Rule ${res.chosen_rule.id} (Priority ${res.chosen_rule.priority})` : 'Unmatched Pattern'}
            </span>
          </div>
          <h3 class="action-headline">${actionHeadline}</h3>
          <p class="action-reason">${res.reason}</p>
        </div>

        <div class="safe-steps-card">
          <h4 class="safe-steps-title">${icons.shield(18)} Safe Next Steps (Operational Advisory)</h4>
          <ul class="safe-checklist">
            ${res.safe_steps.map((step, idx) => `
              <li class="check-item"><input type="checkbox" id="step-${idx}"><label for="step-${idx}">${step}</label></li>
            `).join('')}
          </ul>
        </div>

        <div class="reasoning-box">
          <div class="reasoning-title">${icons.rules(18)} Transparent Reasoning Trace</div>
          <div>
            <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;margin-bottom:6px;color:var(--text-muted);">Evaluated Input Facts:</div>
            <div class="fact-chips-row">
              ${Object.entries(facts).map(([k, v]) => `<span class="fact-chip">${k}: ${v}</span>`).join('')}
            </div>
          </div>

          <div>
            <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;margin-bottom:6px;color:var(--text-muted);">Candidate Rules Fired (${res.fired_rules.length}):</div>
            <div class="rules-fired-list">
              ${res.fired_rules.length === 0 ? `
                <div class="rule-trace-item">None of the 12 predefined substation rules matched this fact combination.</div>
              ` : res.fired_rules.map(rid => {
                const isSelected = res.chosen_rule && res.chosen_rule.id === rid;
                const rText = appState.rulesMap[rid] ? appState.rulesMap[rid].text : rid;
                return `
                  <div class="rule-trace-item ${isSelected ? 'chosen' : ''}">
                    <span><strong>${rid}</strong>: ${rText}</span>
                    <span>${isSelected ? '<span class="badge badge-advisory" style="font-size:0.65rem;">CHOSEN</span>' : '<span style="font-size:0.75rem;color:var(--text-muted);">Overridden</span>'}</span>
                  </div>
                `;
              }).join('')}
            </div>
          </div>

          ${res.conflict ? `
            <div class="conflict-resolution-callout">
              <strong>Conflict Resolution Applied:</strong> Multiple rules fired (${res.fired_rules.join(', ')}). 
              ${res.reason}
            </div>
          ` : ''}
        </div>
      </div>
    `;

    resultsBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  render();
  return container;
}

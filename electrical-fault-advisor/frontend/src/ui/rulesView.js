/**
 * Rule Base View
 * Searchable, filterable table of all 12 forward-chaining rules with modal inspector.
 */

import { getRules } from '../api.js';
import { icons } from '../icons.js';

const ACTIONS = ['all', 'monitor', 'isolate_feeder', 'switch_to_backup', 'call_utility'];
const ALARMS = ['all', 'overcurrent', 'earth_fault', 'transformer_temp', 'abnormal_voltage', 'breaker_trip', 'smoke_or_fire'];

export function createRulesView(appState) {
  const container = document.createElement('div');
  container.className = 'rules-container';

  let rulesList = [];
  let searchQuery = '';
  let selectedAction = 'all';
  let selectedAlarm = 'all';

  function formatConditions(conds) {
    return Object.entries(conds).map(([k, vals]) => `${k} ∈ {${vals.join(', ')}}`).join(' AND ');
  }

  function getPriorityBadge(p) {
    const cls = p <= 2 ? 'badge-advisory' : p <= 4 ? 'badge-warning' : 'badge-critical';
    const lbl = p <= 2 ? 'Advisory' : p <= 4 ? 'Warning' : 'Critical';
    return `<span class="badge ${cls}">P${p} (${lbl})</span>`;
  }

  function getFilteredRules() {
    const q = searchQuery.toLowerCase().trim();
    return rulesList.filter(r => {
      if (selectedAction !== 'all' && r.action !== selectedAction) return false;
      if (selectedAlarm !== 'all' && !(r.conditions.alarm || []).includes(selectedAlarm)) return false;
      if (q && !r.id.toLowerCase().includes(q) && !r.text.toLowerCase().includes(q) && !r.action.toLowerCase().includes(q)) return false;
      return true;
    });
  }

  function updateTable() {
    const filtered = getFilteredRules();
    const countEl = container.querySelector('#rule-count');
    if (countEl) countEl.textContent = `Showing ${filtered.length} of ${rulesList.length} rules`;

    const tbody = container.querySelector('#rules-table-body');
    if (!tbody) return;

    if (!filtered.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-muted);">No rules match criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(r => `
      <tr class="rule-row" data-id="${r.id}" style="cursor:pointer;" tabindex="0" role="button" aria-label="View Rule ${r.id}">
        <td><strong>${r.id}</strong></td>
        <td style="font-family:var(--font-mono);font-size:0.8rem;">${formatConditions(r.conditions)}</td>
        <td><span class="fact-chip" style="font-weight:700;">${r.action}</span></td>
        <td>${getPriorityBadge(r.priority)}</td>
        <td style="text-align:center;font-family:var(--font-mono);">${r.specificity}</td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.rule-row').forEach(row => {
      const show = () => showModal(row.dataset.id);
      row.onclick = show;
      row.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(); } };
    });
  }

  function showModal(ruleId) {
    const rule = rulesList.find(r => r.id === ruleId);
    if (!rule) return;
    const modal = container.querySelector('#rule-detail-modal');
    modal.innerHTML = `
      <div class="modal-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
          <h3 style="font-size:1.25rem;font-weight:800;display:flex;align-items:center;gap:8px;">${icons.rules(20)} Rule ${rule.id} Specification</h3>
          <button id="modal-close-btn" class="btn btn-ghost btn-sm" aria-label="Close">${icons.close(18)}</button>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px;font-size:0.9rem;">
          <div>
            <span style="font-size:0.75rem;text-transform:uppercase;font-weight:700;color:var(--text-muted);">Rule Formulation</span>
            <p style="font-family:var(--font-mono);font-size:0.88rem;background:var(--bg-page);padding:10px;border-radius:var(--radius-md);border:1px solid var(--border-subtle);margin-top:4px;">${rule.text}</p>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div style="background:var(--bg-page);padding:10px;border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
              <span style="font-size:0.72rem;text-transform:uppercase;font-weight:700;color:var(--text-muted);">Priority Score</span>
              <p style="font-size:1.1rem;font-weight:800;margin-top:2px;">Level ${rule.priority}</p>
            </div>
            <div style="background:var(--bg-page);padding:10px;border-radius:var(--radius-md);border:1px solid var(--border-subtle);">
              <span style="font-size:0.72rem;text-transform:uppercase;font-weight:700;color:var(--text-muted);">Specificity Count</span>
              <p style="font-size:1.1rem;font-weight:800;margin-top:2px;">${rule.specificity} condition(s)</p>
            </div>
          </div>
          <div>
            <span style="font-size:0.75rem;text-transform:uppercase;font-weight:700;color:var(--text-muted);">First-Response Action</span>
            <p style="margin-top:4px;font-weight:700;font-size:1rem;color:var(--color-ink);">${rule.action}</p>
          </div>
          <div style="border-top:1px solid var(--border-subtle);padding-top:10px;font-size:0.8rem;color:var(--text-muted);">
            Conflict Resolution: Priority resolves conflicting rules; specificity serves as secondary tie-breaker.
          </div>
        </div>
        <button id="modal-ok-btn" class="btn btn-primary" style="width:100%;margin-top:16px;">Close</button>
      </div>
    `;
    modal.classList.remove('hidden');
    const hide = () => modal.classList.add('hidden');
    modal.querySelector('#modal-close-btn').onclick = hide;
    modal.querySelector('#modal-ok-btn').onclick = hide;
    modal.onclick = e => { if (e.target === modal) hide(); };
  }

  function initLayout() {
    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${icons.rules(20)} Substation Knowledge Base (12 Rules)</h2>
            <p class="card-description">Deterministic forward-chaining rules prioritized by asset protection and life safety criticality.</p>
          </div>
          <div id="rule-count" style="font-size:0.8rem;font-family:var(--font-mono);font-weight:700;color:var(--text-muted);"></div>
        </div>
        <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;align-items:center;">
          <input type="text" id="rule-search-input" class="search-input" placeholder="Search rules by ID, text, action...">
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <label style="font-size:0.78rem;font-weight:700;">Action:</label>
            <select id="action-filter-select" style="padding:6px 12px;border-radius:var(--radius-full);border:1px solid var(--border-medium);background:var(--bg-page);font-size:0.8rem;">
              ${ACTIONS.map(a => `<option value="${a}">${a === 'all' ? 'All Actions' : a}</option>`).join('')}
            </select>
            <label style="font-size:0.78rem;font-weight:700;margin-left:6px;">Alarm:</label>
            <select id="alarm-filter-select" style="padding:6px 12px;border-radius:var(--radius-full);border:1px solid var(--border-medium);background:var(--bg-page);font-size:0.8rem;">
              ${ALARMS.map(al => `<option value="${al}">${al === 'all' ? 'All Alarms' : al}</option>`).join('')}
            </select>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:60px;">ID</th>
                <th>IF (Antecedent Conditions)</th>
                <th>THEN (Action)</th>
                <th style="width:140px;">Priority</th>
                <th style="width:90px;text-align:center;">Specificity</th>
              </tr>
            </thead>
            <tbody id="rules-table-body"></tbody>
          </table>
        </div>
      </div>
      <div id="rule-detail-modal" class="modal-backdrop hidden"></div>
    `;

    container.querySelector('#rule-search-input').oninput = e => { searchQuery = e.target.value; updateTable(); };
    container.querySelector('#action-filter-select').onchange = e => { selectedAction = e.target.value; updateTable(); };
    container.querySelector('#alarm-filter-select').onchange = e => { selectedAlarm = e.target.value; updateTable(); };
  }

  async function loadData() {
    try {
      rulesList = await getRules();
      rulesList.forEach(r => { appState.rulesMap[r.id] = r; });
      initLayout();
      updateTable();
    } catch (err) {
      container.innerHTML = `
        <div class="card" style="border:2px solid var(--color-coral);background-color:var(--coral-tint-15);">
          <h3>Error Loading Rule Base</h3>
          <p>${err.message}</p>
        </div>`;
    }
  }

  loadData();
  return container;
}

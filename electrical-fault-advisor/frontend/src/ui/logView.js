/**
 * Event Log View
 * Session History, LocalStorage Persistence, CSV Export & Verification Feedback Loop
 */

import { icons } from '../icons.js';

export function createLogView(appState) {
  const container = document.createElement('div');
  container.className = 'log-container';

  function exportCsv() {
    const logs = appState.eventLogs;
    if (!logs || !logs.length) { alert('Event log is empty.'); return; }
    const headers = ['Timestamp', 'Feeder', 'Alarm', 'Load', 'Weather', 'Backup', 'Action', 'Alert Level', 'Rule ID', 'Verified'];
    const rows = logs.map(e => [
      `"${e.timestamp}"`, `"${e.facts.feeder}"`, `"${e.facts.alarm}"`, `"${e.facts.load}"`,
      `"${e.facts.weather}"`, `"${e.facts.backup}"`, `"${e.action}"`, `"${e.alert_level}"`,
      `"${e.rule_id}"`, `"${e.verified ? 'YES' : 'NO'}"`
    ]);
    const link = document.createElement('a');
    link.href = encodeURI('data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n'));
    link.download = `substation_fault_log_${Date.now()}.csv`;
    link.click();
  }

  function render() {
    const logs = appState.eventLogs || [];
    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${icons.log(20)} Session Operational Event Log</h2>
            <p class="card-description">Chronological history of evaluated queries with human verification feedback loop.</p>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button id="export-csv-btn" class="btn btn-secondary btn-sm" title="Download CSV">${icons.download(16)} <span>Export CSV</span></button>
            <button id="clear-log-btn" class="btn btn-ghost btn-sm" style="color:var(--color-coral);" title="Clear Entries">${icons.trash(16)} <span>Clear Log</span></button>
          </div>
        </div>

        <div style="padding:10px 14px;background:var(--ink-tint-8);border:1px solid var(--border-subtle);border-radius:var(--radius-md);margin-bottom:14px;font-size:0.8rem;color:var(--text-muted);">
          <strong>Prototype Feedback Loop:</strong> The "Mark Verified" switch simulates operator audit validation (prototype feature demonstrating human-in-the-loop review).
        </div>

        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:100px;">Time</th>
                <th>Substation Facts</th>
                <th>Action</th>
                <th>Alert Level</th>
                <th style="width:75px;">Rule</th>
                <th style="width:160px;text-align:center;">Verified by Team</th>
              </tr>
            </thead>
            <tbody>
              ${!logs.length ? `<tr><td colspan="6" style="text-align:center;padding:36px;color:var(--text-muted);">No queries logged yet. Generate advice on the Advisor tab.</td></tr>` : logs.map((e, idx) => `
                <tr>
                  <td style="font-family:var(--font-mono);font-size:0.78rem;">${e.timestamp}</td>
                  <td style="font-family:var(--font-mono);font-size:0.78rem;">${e.facts.feeder} | ${e.facts.alarm} | ${e.facts.load} | ${e.facts.weather} | ${e.facts.backup}</td>
                  <td><strong>${e.action}</strong></td>
                  <td><span class="badge badge-${e.alert_level.toLowerCase()}" style="font-size:0.68rem;">${e.alert_level}</span></td>
                  <td style="font-family:var(--font-mono);font-weight:700;">${e.rule_id}</td>
                  <td style="text-align:center;">
                    <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-size:0.78rem;">
                      <input type="checkbox" class="verify-toggle" data-idx="${idx}" ${e.verified ? 'checked' : ''} style="accent-color:var(--color-mint);cursor:pointer;">
                      <span style="font-weight:${e.verified ? '700' : '400'};color:${e.verified ? 'var(--color-ink)' : 'var(--text-muted)'};">${e.verified ? 'Verified ✓' : 'Pending'}</span>
                    </label>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    const exportBtn = container.querySelector('#export-csv-btn');
    if (exportBtn) exportBtn.onclick = exportCsv;

    const clearBtn = container.querySelector('#clear-log-btn');
    if (clearBtn) {
      clearBtn.onclick = () => {
        if (confirm('Clear session log history?')) {
          appState.eventLogs = [];
          localStorage.removeItem('fault_advisor_event_logs');
          render();
        }
      };
    }

    container.querySelectorAll('.verify-toggle').forEach(chk => {
      chk.onchange = e => {
        const idx = parseInt(e.target.dataset.idx, 10);
        if (appState.eventLogs[idx]) {
          appState.eventLogs[idx].verified = e.target.checked;
          try { localStorage.setItem('fault_advisor_event_logs', JSON.stringify(appState.eventLogs)); } catch (_) {}
          render();
        }
      };
    });
  }

  render();
  container.onTabOpen = render;
  return container;
}

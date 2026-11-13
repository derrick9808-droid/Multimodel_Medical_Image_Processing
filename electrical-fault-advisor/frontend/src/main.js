/**
 * Application Entry Point
 * Routing, State Management, Navigation & Accessibility
 */

import { setOfflineListener } from './api.js';
import { icons } from './icons.js';
import { createAdvisorView } from './ui/advisorView.js';
import { createRulesView } from './ui/rulesView.js';
import { createEvaluateView } from './ui/evaluateView.js';
import { createLogView } from './ui/logView.js';
import { createAboutView } from './ui/aboutView.js';

const TABS = [
  ['advisor', 'Advisor', icons.advisor],
  ['rules', 'Rule Base', icons.rules],
  ['evaluate', 'Evaluation', icons.evaluate],
  ['log', 'Event Log', icons.log],
  ['about', 'About', icons.about]
];

const appState = {
  rulesMap: {},
  eventLogs: [],
  addLogEntry(entry) {
    this.eventLogs.unshift(entry);
    if (this.eventLogs.length > 100) this.eventLogs.pop();
    try { localStorage.setItem('fault_advisor_event_logs', JSON.stringify(this.eventLogs)); } catch (_) {}
  }
};

try {
  const saved = localStorage.getItem('fault_advisor_event_logs');
  if (saved) appState.eventLogs = JSON.parse(saved);
} catch (_) {}

function initApp() {
  const root = document.getElementById('app');
  if (!root) return;

  root.innerHTML = `
    <header class="app-header">
      <div class="header-container">
        <div class="brand-wrapper">
          <div class="brand-icon">${icons.bolt(20)}</div>
          <div>
            <h1 class="brand-title">Electrical Fault First-Response Advisor</h1>
            <p class="brand-subtitle">Campus Substation Expert System • 25DC204 AI Project</p>
          </div>
        </div>

        <nav class="app-nav" role="tablist" aria-label="Main Navigation">
          ${TABS.map(([id, label, icon], idx) => `
            <button class="nav-tab ${idx === 0 ? 'active' : ''}" data-tab="${id}" role="tab" aria-selected="${idx === 0 ? 'true' : 'false'}" aria-controls="pane-${id}">
              ${icon(16)} <span>${label}</span>
            </button>
          `).join('')}
        </nav>
      </div>
    </header>

    <main class="app-main">
      <div id="offline-alert" class="offline-banner hidden" role="alert">
        <div style="display:flex;align-items:center;gap:8px;">
          ${icons.alertTriangle(18)}
          <span id="offline-alert-text">Standalone Web Mode: Running in-browser client rule engine.</span>
        </div>
        <button id="retry-server-btn" class="btn btn-secondary btn-sm" style="background:var(--color-blush);">Retry API</button>
      </div>

      ${TABS.map(([id], idx) => `<section id="pane-${id}" class="tab-pane ${idx === 0 ? 'active' : ''}" role="tabpanel"></section>`).join('')}
    </main>

    <footer class="app-footer">
      <div class="footer-container">
        <div class="footer-safety-notice">
          <span>${icons.shield(16)}</span>
          <div>
            <strong>SAFETY BOUNDARY NOTICE:</strong> 
            The Electrical Fault First-Response Advisor is an educational decision-support aid. 
            It only recommends and does <em>not</em> directly operate physical switchgear or replace licensed electrical maintenance personnel. 
            Thresholds and ratings shown are illustrative and must be verified and approved by qualified electrical engineers before field adoption.
          </div>
        </div>
        <div class="footer-team-note">
          Micro-Project for Course 25DC204 (Fundamentals of AI, CO1/CO2/CO3) • Karunya Institute of Technology and Sciences, Division of Data Science and Cyber Security • Team: Derrick J, Mani Kandan A, A Jayas Shiny, S Vishnu Priya
        </div>
      </div>
    </footer>
  `;

  const views = {
    advisor: createAdvisorView(appState),
    rules: createRulesView(appState),
    evaluate: createEvaluateView(appState),
    log: createLogView(appState),
    about: createAboutView()
  };

  Object.entries(views).forEach(([id, el]) => {
    const pane = document.getElementById(`pane-${id}`);
    if (pane) pane.appendChild(el);
  });

  const tabButtons = root.querySelectorAll('.nav-tab');
  const tabPanes = root.querySelectorAll('.tab-pane');

  function switchTab(tabId) {
    tabButtons.forEach(btn => {
      const isCur = btn.dataset.tab === tabId;
      btn.classList.toggle('active', isCur);
      btn.setAttribute('aria-selected', isCur ? 'true' : 'false');
    });

    tabPanes.forEach(pane => {
      const isTarget = pane.id === `pane-${tabId}`;
      pane.classList.toggle('active', isTarget);
      if (isTarget && pane.firstElementChild && typeof pane.firstElementChild.onTabOpen === 'function') {
        pane.firstElementChild.onTabOpen();
      }
    });

    window.location.hash = tabId;
  }

  tabButtons.forEach(btn => {
    btn.onclick = () => switchTab(btn.dataset.tab);
  });

  const initialHash = window.location.hash.replace('#', '');
  if (['advisor', 'rules', 'evaluate', 'log', 'about'].includes(initialHash)) {
    switchTab(initialHash);
  }

  const offlineAlert = document.getElementById('offline-alert');
  const offlineText = document.getElementById('offline-alert-text');
  const retryBtn = document.getElementById('retry-server-btn');

  setOfflineListener((isOnline, message) => {
    if (isOnline) {
      offlineAlert.classList.add('hidden');
    } else {
      offlineAlert.classList.remove('hidden');
      if (message) offlineText.textContent = message;
    }
  });

  if (retryBtn) {
    retryBtn.onclick = async () => {
      retryBtn.textContent = 'Connecting...';
      try {
        const res = await fetch('http://127.0.0.1:8000/api/rules');
        if (res.ok) {
          window.location.reload();
        } else {
          retryBtn.textContent = 'Retry API';
        }
      } catch (_) {
        retryBtn.textContent = 'Retry API';
      }
    };
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

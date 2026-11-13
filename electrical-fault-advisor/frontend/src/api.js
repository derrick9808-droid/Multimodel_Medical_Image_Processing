/**
 * API Client Layer with Standalone Engine Fallback
 */

import * as clientEngine from './clientEngine.js';

function getApiBase() {
  if (typeof window === 'undefined') return '';
  // When opened via file:// or another local dev port (e.g. Vite 5173 or LiveServer 5500)
  if (window.location.protocol === 'file:' || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '8000')) {
    return 'http://127.0.0.1:8000';
  }
  return '';
}

const API_BASE = getApiBase();
let rulesCache = null;
let eventsCache = null;
let isBackendOnline = true;
let onOfflineStatusChange = null;

export function setOfflineListener(cb) {
  onOfflineStatusChange = cb;
}

function updateOnlineStatus(online, msg = '') {
  if (isBackendOnline !== online) {
    isBackendOnline = online;
    if (onOfflineStatusChange) onOfflineStatusChange(online, msg);
  }
}

async function handleResponse(res) {
  if (!res.ok) {
    let err = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const j = await res.json();
      if (j.detail) err = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch (_) {}
    throw new Error(err);
  }
  return res.json();
}

export async function getRules() {
  if (rulesCache) return rulesCache;
  try {
    const res = await fetch(`${API_BASE}/api/rules`);
    rulesCache = await handleResponse(res);
    updateOnlineStatus(true);
    return rulesCache;
  } catch (_) {
    rulesCache = clientEngine.RULES;
    updateOnlineStatus(false, 'Standalone Web Mode: In-browser inference active (Python API offline).');
    return rulesCache;
  }
}

export async function getEvents() {
  if (eventsCache) return eventsCache;
  try {
    const res = await fetch(`${API_BASE}/api/events`);
    eventsCache = await handleResponse(res);
    updateOnlineStatus(true);
    return eventsCache;
  } catch (_) {
    eventsCache = clientEngine.EVENTS;
    return eventsCache;
  }
}

export async function requestAdvice(facts) {
  try {
    const res = await fetch(`${API_BASE}/api/advise`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(facts),
    });
    const data = await handleResponse(res);
    updateOnlineStatus(true);
    return data;
  } catch (_) {
    updateOnlineStatus(false, 'Standalone Web Mode: In-browser inference active.');
    return clientEngine.advise(facts);
  }
}

export async function runEvaluation() {
  try {
    const res = await fetch(`${API_BASE}/api/evaluate`);
    const data = await handleResponse(res);
    updateOnlineStatus(true);
    return data;
  } catch (_) {
    return clientEngine.evaluate();
  }
}

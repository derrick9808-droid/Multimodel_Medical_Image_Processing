/**
 * EduExaminer — Client-Side Scripts
 * ===================================
 * CO4 — small, clearly named functions.
 * CO2 — loops for clock tick, countdown iteration.
 * CO3 — arrays of question PKs kept stable in sessionStorage.
 *
 * NOTE (prototype): timer persistence uses sessionStorage so the countdown
 * survives a page refresh within the same browser tab.
 * Production must validate remaining time server-side on every request.
 */

"use strict";

/* =========================================================================
   Live Clock  (HH:MM:SS wall clock — shown on confirmation dialog)
   ========================================================================= */

/**
 * formatTime — convert total seconds to "HH:MM:SS" string.
 * CO4: small named function; CO2: arithmetic loop-equivalent.
 * @param {number} totalSeconds
 * @returns {string}
 */
function formatTime(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return [h, m, s].map(v => String(v).padStart(2, "0")).join(":");
}

/**
 * startLiveClock — update #edu-live-clock every second with the current time.
 * CO2: setInterval loop.
 */
function startLiveClock() {
  const el = document.getElementById("edu-live-clock");
  if (!el) return;

  function tick() {
    const now = new Date();
    el.textContent = [
      now.getHours(),
      now.getMinutes(),
      now.getSeconds(),
    ].map(v => String(v).padStart(2, "0")).join(":");
  }

  tick();
  setInterval(tick, 1000);
}


/* =========================================================================
   Exam Countdown Timer
   =========================================================================
   The countdown start epoch is stored in sessionStorage under the key
   "edu_attempt_start_<attemptId>" so it survives a refresh.

   Data attributes read from #edu-countdown:
     data-attempt-id   — Attempt PK
     data-duration-min — exam duration in minutes
     data-finish-url   — URL to redirect to when timer hits zero
   ========================================================================= */

/**
 * getRemainingSeconds — calculate how many seconds are left.
 * CO4: focused function; CO3: key lookup in sessionStorage (associative array).
 * @param {string} attemptKey  sessionStorage key
 * @param {number} durationSec total seconds for the exam
 * @returns {number}
 */
function getRemainingSeconds(attemptKey, durationSec) {
  const startEpoch = parseInt(sessionStorage.getItem(attemptKey) || "0", 10);
  if (!startEpoch) return durationSec;          // first load: full duration
  const elapsed = Math.floor(Date.now() / 1000) - startEpoch;
  return Math.max(0, durationSec - elapsed);
}

/**
 * startCountdownTimer — initialise and tick the exam countdown.
 * CO2: setInterval loop ticking every second.
 * CO4: delegates to getRemainingSeconds(), formatTime(), submitAttempt().
 */
function startCountdownTimer() {
  const el = document.getElementById("edu-countdown");
  if (!el) return;

  const attemptId   = el.dataset.attemptId;
  const durationSec = parseInt(el.dataset.durationMin, 10) * 60;
  const finishUrl   = el.dataset.finishUrl;
  const storageKey  = "edu_attempt_start_" + attemptId;

  // Record start epoch only once (CO3: insert into sessionStorage array)
  if (!sessionStorage.getItem(storageKey)) {
    sessionStorage.setItem(storageKey, String(Math.floor(Date.now() / 1000)));
  }

  function tick() {
    const remaining = getRemainingSeconds(storageKey, durationSec);
    el.textContent = formatTime(remaining);

    // Visual urgency when < 60 s remain
    el.classList.toggle("edu-countdown--urgent", remaining <= 60);

    if (remaining <= 0) {
      clearInterval(timerId);
      submitAttempt(finishUrl);
    }
  }

  tick();
  const timerId = setInterval(tick, 1000);
}

/**
 * submitAttempt — navigate to the finish URL to auto-submit when time is up.
 * CO4: focused function; side-effect is navigation only.
 * @param {string} finishUrl
 */
function submitAttempt(finishUrl) {
  if (finishUrl) {
    window.location.href = finishUrl;
  }
}


/* =========================================================================
   Confirmation Dialog — keyboard focus trap
   ========================================================================= */

/**
 * trapFocus — keep Tab/Shift-Tab cycling within the dialog.
 * CO4: focused function.
 * @param {HTMLElement} dialog
 */
function trapFocus(dialog) {
  const focusable = Array.from(
    dialog.querySelectorAll("a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])")
  ).filter(el => !el.disabled);

  if (!focusable.length) return;

  const first = focusable[0];
  const last  = focusable[focusable.length - 1];

  dialog.addEventListener("keydown", function (e) {
    if (e.key !== "Tab") return;
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last)  { e.preventDefault(); first.focus(); }
    }
  });

  first.focus();
}


/* =========================================================================
   Exam question page — enable Continue only after an option is chosen
   ========================================================================= */

/**
 * initAnswerSelection — watch radio buttons; enable Continue when one is chosen.
 * CO2: iterate over radio inputs (loop over collection).
 * CO4: small named function.
 */
function initAnswerSelection() {
  const form   = document.getElementById("edu-answer-form");
  const btn    = document.getElementById("edu-continue-btn");
  const radios = form ? Array.from(form.querySelectorAll("input[type='radio']")) : [];

  if (!form || !btn || !radios.length) return;

  // If page reloaded with a pre-selected answer (already_answered), enable immediately
  const anyChecked = radios.some(r => r.checked);
  if (anyChecked) btn.disabled = false;

  // CO2 — iterate over all radio inputs and attach listeners
  radios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      btn.disabled = false;
    });
  });
}


/* =========================================================================
   Navigation guard — warn before leaving an in-progress exam
   ========================================================================= */

/**
 * initExamNavigationGuard — confirm before unloading an active exam page.
 * CO4: focused function.
 */
function initExamNavigationGuard() {
  const guard = document.getElementById("edu-answer-form");
  if (!guard) return;

  window.addEventListener("beforeunload", function (e) {
    // Only warn if the student hasn't submitted (form hasn't posted)
    e.preventDefault();
    e.returnValue = ""; // Chrome requires returnValue to be set
  });

  // Remove guard on intentional form submit so it doesn't re-prompt
  guard.addEventListener("submit", function () {
    window.onbeforeunload = null;
  });
}


/* =========================================================================
   Boot — run initializers after DOM is ready
   ========================================================================= */

document.addEventListener("DOMContentLoaded", function () {
  startLiveClock();
  startCountdownTimer();
  initAnswerSelection();
  initExamNavigationGuard();

  // Auto-focus first focusable element in confirmation dialog
  const dialog = document.querySelector(".edu-confirm-dialog");
  if (dialog) trapFocus(dialog);
});


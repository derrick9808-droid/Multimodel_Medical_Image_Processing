/**
 * Client-Side Knowledge Base & Inference Engine
 * Allows the website to run standalone in any browser without Python.
 */

export const RULES = [
  ['R1', { alarm: ['overcurrent'], load: ['low', 'medium'] }, 'monitor', 1, 2],
  ['R2', { alarm: ['overcurrent'], load: ['high'] }, 'isolate_feeder', 3, 2],
  ['R3', { alarm: ['overcurrent'], load: ['high'], backup: ['available'] }, 'switch_to_backup', 4, 3],
  ['R4', { alarm: ['earth_fault'] }, 'isolate_feeder', 4, 1],
  ['R5', { alarm: ['earth_fault'], weather: ['storm'], backup: ['unavailable'] }, 'call_utility', 5, 3],
  ['R6', { alarm: ['transformer_temp'], load: ['low', 'medium'] }, 'monitor', 2, 2],
  ['R7', { alarm: ['transformer_temp'], load: ['high'] }, 'call_utility', 5, 2],
  ['R8', { alarm: ['breaker_trip'], backup: ['available'] }, 'switch_to_backup', 4, 2],
  ['R9', { alarm: ['breaker_trip'], backup: ['unavailable'] }, 'call_utility', 5, 2],
  ['R10', { alarm: ['abnormal_voltage'] }, 'monitor', 2, 1],
  ['R11', { alarm: ['abnormal_voltage'], weather: ['storm'] }, 'call_utility', 5, 2],
  ['R12', { alarm: ['smoke_or_fire'] }, 'call_utility', 6, 1]
].map(([id, conditions, action, priority, specificity]) => ({
  id, conditions, action, priority, specificity,
  text: `IF ${Object.entries(conditions).map(([k, v]) => `${k} in {${v.join(', ')}}`).join(' AND ')} THEN ${action} (Priority ${priority})`
}));

export const BASELINE = {
  overcurrent: 'isolate_feeder', earth_fault: 'isolate_feeder',
  transformer_temp: 'monitor', abnormal_voltage: 'monitor',
  breaker_trip: 'switch_to_backup', smoke_or_fire: 'call_utility'
};

const E_STR = '1,hostel,overcurrent,low,clear,available,monitor;2,academic,overcurrent,medium,rain,unavailable,monitor;3,lab,overcurrent,high,clear,available,switch_to_backup;4,hostel,overcurrent,high,clear,unavailable,isolate_feeder;5,academic,earth_fault,high,clear,available,isolate_feeder;6,lab,earth_fault,low,storm,unavailable,call_utility;7,hostel,earth_fault,medium,rain,available,isolate_feeder;8,academic,transformer_temp,low,clear,available,monitor;9,lab,transformer_temp,high,rain,available,call_utility;10,hostel,breaker_trip,medium,clear,available,switch_to_backup;11,academic,breaker_trip,high,clear,unavailable,call_utility;12,lab,breaker_trip,low,storm,unavailable,call_utility;13,hostel,abnormal_voltage,low,clear,available,monitor;14,academic,abnormal_voltage,high,storm,available,call_utility;15,lab,abnormal_voltage,medium,storm,unavailable,call_utility;16,hostel,smoke_or_fire,low,clear,available,call_utility;17,academic,smoke_or_fire,high,storm,unavailable,call_utility';

export const EVENTS = E_STR.split(';').map(s => {
  const [id, feeder, alarm, load, weather, backup, expected] = s.split(',');
  return { id: Number(id), facts: { feeder, alarm, load, weather, backup }, expected };
});

export function forwardChain(facts) {
  return RULES.filter(rule => Object.entries(rule.conditions).every(([a, vals]) => vals.includes(facts[a]))).map(r => r.id);
}

export function resolve(firedIds) {
  if (!firedIds.length) return null;
  const c = firedIds.map(id => RULES.find(r => r.id === id)).filter(Boolean);
  c.sort((a, b) => b.priority - a.priority || b.specificity - a.specificity || b.id.localeCompare(a.id));
  return c[0];
}

export function alertLevel(priority) {
  if (priority == null) return 'UNCERTAIN';
  if (priority <= 2) return 'ADVISORY';
  if (priority <= 4) return 'WARNING';
  if (priority <= 6) return 'CRITICAL';
  return 'UNCERTAIN';
}

export function compileSafeSteps(action, alert, alarm) {
  const s = [];
  if (['CRITICAL', 'WARNING', 'UNCERTAIN'].includes(alert)) {
    s.push('Keep students and unauthorised persons away from the affected area.');
    s.push('Do not touch, open, reset or attempt to repair electrical equipment.');
    s.push('Inform the authorised campus electrical maintenance team immediately.');
  }
  if (alert === 'UNCERTAIN') s.push('Request an immediate on-site safety and diagnostic inspection.');
  if (alarm === 'smoke_or_fire') s.push('Follow the campus emergency plan and contact emergency services.');
  if (action === 'monitor') s.push('Keep observing readings; log the event; escalate if the alarm repeats or load rises.');
  else if (action === 'isolate_feeder') s.push('Request the authorised team to isolate the affected feeder.');
  else if (action === 'switch_to_backup') s.push('Request the authorised team to transfer load to the backup supply.');
  else if (action === 'call_utility') s.push('Contact the utility / authorised electrical team now.');
  return s;
}

export function advise(facts) {
  const fired = forwardChain(facts);
  const chosen = resolve(fired);
  const conflict = fired.length > 1;
  const alarm = facts.alarm || '';

  if (chosen) {
    let reason = `Rule ${chosen.id} matched condition pattern: recommended action is ${chosen.action}.`;
    if (conflict) {
      const others = fired.filter(id => id !== chosen.id).map(id => RULES.find(r => r.id === id));
      const sameP = others.filter(r => r.priority === chosen.priority);
      if (sameP.length) {
        reason = `Conflict resolved: ${chosen.id} selected over ${sameP.map(r=>r.id).join(', ')} due to specificity (${chosen.specificity} vs ${sameP[0].specificity}) at Priority ${chosen.priority}.`;
      } else {
        reason = `Conflict resolved: ${chosen.id} (P${chosen.priority}) overrode lower-priority matching rule(s) ${others.map(r=>`${r.id} (P${r.priority})`).join(', ')}.`;
      }
    }
    return {
      action: chosen.action,
      alert_level: alertLevel(chosen.priority),
      fired_rules: fired,
      chosen_rule: { id: chosen.id, priority: chosen.priority, specificity: chosen.specificity, text: chosen.text },
      conflict,
      reason,
      safe_steps: compileSafeSteps(chosen.action, alertLevel(chosen.priority), alarm)
    };
  }

  return {
    action: 'call_utility',
    alert_level: 'UNCERTAIN',
    fired_rules: [],
    chosen_rule: null,
    conflict: false,
    reason: 'No predefined rule matched the reported condition pattern. Request immediate qualified inspection.',
    safe_steps: compileSafeSteps('call_utility', 'UNCERTAIN', alarm)
  };
}

export function evaluate() {
  const results = EVENTS.map(ev => {
    const adv = advise(ev.facts);
    const advAction = adv.action;
    const baseAction = BASELINE[ev.facts.alarm] || 'monitor';
    return {
      id: ev.id,
      facts: ev.facts,
      expected: ev.expected,
      advisor_action: advAction,
      rule_id: adv.chosen_rule ? adv.chosen_rule.id : null,
      correct: advAction === ev.expected,
      baseline_action: baseAction,
      baseline_correct: baseAction === ev.expected
    };
  });

  const advCorrect = results.filter(r => r.correct).length;
  const baseCorrect = results.filter(r => r.baseline_correct).length;
  const n = results.length;

  return {
    events: results,
    totals: {
      n,
      advisor_correct: advCorrect,
      baseline_correct: baseCorrect,
      advisor_pct: Number(((advCorrect / n) * 100).toFixed(1)),
      baseline_pct: Number(((baseCorrect / n) * 100).toFixed(1))
    }
  };
}

"""
Electrical Fault First-Response Advisor Engine
Course: 25DC204 - Fundamentals of Artificial Intelligence (CO1, CO2, CO3)
Institution: Karunya Institute of Technology and Sciences
"""

from typing import Dict, List, Any, Optional

# Valid attribute values
VALID_ATTRIBUTES = {
    "feeder": {"hostel", "academic", "lab"},
    "alarm": {
        "overcurrent",
        "earth_fault",
        "transformer_temp",
        "abnormal_voltage",
        "breaker_trip",
        "smoke_or_fire",
    },
    "load": {"low", "medium", "high"},
    "weather": {"clear", "rain", "storm"},
    "backup": {"available", "unavailable"},
}

VALID_RESPONSES = {"monitor", "isolate_feeder", "switch_to_backup", "call_utility"}

# Rule Base (R1 - R12)
RULES: Dict[str, Dict[str, Any]] = {
    "R1": {
        "id": "R1",
        "conditions": {
            "alarm": ["overcurrent"],
            "load": ["low", "medium"],
        },
        "action": "monitor",
        "priority": 1,
        "specificity": 2,
        "text": "IF alarm=overcurrent AND load in {low, medium} THEN monitor (Priority 1)",
    },
    "R2": {
        "id": "R2",
        "conditions": {
            "alarm": ["overcurrent"],
            "load": ["high"],
        },
        "action": "isolate_feeder",
        "priority": 3,
        "specificity": 2,
        "text": "IF alarm=overcurrent AND load=high THEN isolate_feeder (Priority 3)",
    },
    "R3": {
        "id": "R3",
        "conditions": {
            "alarm": ["overcurrent"],
            "load": ["high"],
            "backup": ["available"],
        },
        "action": "switch_to_backup",
        "priority": 4,
        "specificity": 3,
        "text": "IF alarm=overcurrent AND load=high AND backup=available THEN switch_to_backup (Priority 4)",
    },
    "R4": {
        "id": "R4",
        "conditions": {
            "alarm": ["earth_fault"],
        },
        "action": "isolate_feeder",
        "priority": 4,
        "specificity": 1,
        "text": "IF alarm=earth_fault THEN isolate_feeder (Priority 4)",
    },
    "R5": {
        "id": "R5",
        "conditions": {
            "alarm": ["earth_fault"],
            "weather": ["storm"],
            "backup": ["unavailable"],
        },
        "action": "call_utility",
        "priority": 5,
        "specificity": 3,
        "text": "IF alarm=earth_fault AND weather=storm AND backup=unavailable THEN call_utility (Priority 5)",
    },
    "R6": {
        "id": "R6",
        "conditions": {
            "alarm": ["transformer_temp"],
            "load": ["low", "medium"],
        },
        "action": "monitor",
        "priority": 2,
        "specificity": 2,
        "text": "IF alarm=transformer_temp AND load in {low, medium} THEN monitor (Priority 2)",
    },
    "R7": {
        "id": "R7",
        "conditions": {
            "alarm": ["transformer_temp"],
            "load": ["high"],
        },
        "action": "call_utility",
        "priority": 5,
        "specificity": 2,
        "text": "IF alarm=transformer_temp AND load=high THEN call_utility (Priority 5)",
    },
    "R8": {
        "id": "R8",
        "conditions": {
            "alarm": ["breaker_trip"],
            "backup": ["available"],
        },
        "action": "switch_to_backup",
        "priority": 4,
        "specificity": 2,
        "text": "IF alarm=breaker_trip AND backup=available THEN switch_to_backup (Priority 4)",
    },
    "R9": {
        "id": "R9",
        "conditions": {
            "alarm": ["breaker_trip"],
            "backup": ["unavailable"],
        },
        "action": "call_utility",
        "priority": 5,
        "specificity": 2,
        "text": "IF alarm=breaker_trip AND backup=unavailable THEN call_utility (Priority 5)",
    },
    "R10": {
        "id": "R10",
        "conditions": {
            "alarm": ["abnormal_voltage"],
        },
        "action": "monitor",
        "priority": 2,
        "specificity": 1,
        "text": "IF alarm=abnormal_voltage THEN monitor (Priority 2)",
    },
    "R11": {
        "id": "R11",
        "conditions": {
            "alarm": ["abnormal_voltage"],
            "weather": ["storm"],
        },
        "action": "call_utility",
        "priority": 5,
        "specificity": 2,
        "text": "IF alarm=abnormal_voltage AND weather=storm THEN call_utility (Priority 5)",
    },
    "R12": {
        "id": "R12",
        "conditions": {
            "alarm": ["smoke_or_fire"],
        },
        "action": "call_utility",
        "priority": 6,
        "specificity": 1,
        "text": "IF alarm=smoke_or_fire THEN call_utility (Priority 6)",
    },
}

# Baseline Mapping (Alarm type only)
BASELINE: Dict[str, str] = {
    "overcurrent": "isolate_feeder",
    "earth_fault": "isolate_feeder",
    "transformer_temp": "monitor",
    "abnormal_voltage": "monitor",
    "breaker_trip": "switch_to_backup",
    "smoke_or_fire": "call_utility",
}

# Canonical 17 Benchmark Test Events
EVENTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "facts": {
            "feeder": "hostel",
            "alarm": "overcurrent",
            "load": "low",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "monitor",
        "description": "Hostel light load transient overcurrent - safe to monitor readings",
    },
    {
        "id": 2,
        "facts": {
            "feeder": "academic",
            "alarm": "overcurrent",
            "load": "medium",
            "weather": "rain",
            "backup": "unavailable",
        },
        "expected": "monitor",
        "description": "Academic block moderate load transient - monitor for recurring trip",
    },
    {
        "id": 3,
        "facts": {
            "feeder": "lab",
            "alarm": "overcurrent",
            "load": "high",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "switch_to_backup",
        "description": "Research lab heavy overcurrent with active backup generator available",
    },
    {
        "id": 4,
        "facts": {
            "feeder": "hostel",
            "alarm": "overcurrent",
            "load": "high",
            "weather": "clear",
            "backup": "unavailable",
        },
        "expected": "isolate_feeder",
        "description": "Hostel sustained peak overload with no alternative supply line",
    },
    {
        "id": 5,
        "facts": {
            "feeder": "academic",
            "alarm": "earth_fault",
            "load": "high",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "isolate_feeder",
        "description": "Academic feeder insulation breakdown / earth fault",
    },
    {
        "id": 6,
        "facts": {
            "feeder": "lab",
            "alarm": "earth_fault",
            "load": "low",
            "weather": "storm",
            "backup": "unavailable",
        },
        "expected": "call_utility",
        "description": "Severe storm lightning surge causing ground fault without backup",
    },
    {
        "id": 7,
        "facts": {
            "feeder": "hostel",
            "alarm": "earth_fault",
            "load": "medium",
            "weather": "rain",
            "backup": "available",
        },
        "expected": "isolate_feeder",
        "description": "Moisture-induced ground fault on hostel feeder cabling",
    },
    {
        "id": 8,
        "facts": {
            "feeder": "academic",
            "alarm": "transformer_temp",
            "load": "low",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "monitor",
        "description": "Minor daytime transformer thermal rise under low load",
    },
    {
        "id": 9,
        "facts": {
            "feeder": "lab",
            "alarm": "transformer_temp",
            "load": "high",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "call_utility",
        "description": "Dangerous transformer core overheating under heavy lab load",
    },
    {
        "id": 10,
        "facts": {
            "feeder": "hostel",
            "alarm": "transformer_temp",
            "load": "medium",
            "weather": "rain",
            "backup": "unavailable",
        },
        "expected": "monitor",
        "description": "Transformer temperature alert with natural rain cooling and moderate load",
    },
    {
        "id": 11,
        "facts": {
            "feeder": "academic",
            "alarm": "breaker_trip",
            "load": "medium",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "switch_to_backup",
        "description": "Main feeder breaker trip with campus backup generator ready",
    },
    {
        "id": 12,
        "facts": {
            "feeder": "lab",
            "alarm": "breaker_trip",
            "load": "high",
            "weather": "clear",
            "backup": "unavailable",
        },
        "expected": "call_utility",
        "description": "Critical lab feeder breaker lockout with zero backup capacity",
    },
    {
        "id": 13,
        "facts": {
            "feeder": "hostel",
            "alarm": "abnormal_voltage",
            "load": "low",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "monitor",
        "description": "Transient grid voltage dip during low hostel demand",
    },
    {
        "id": 14,
        "facts": {
            "feeder": "academic",
            "alarm": "abnormal_voltage",
            "load": "high",
            "weather": "storm",
            "backup": "available",
        },
        "expected": "call_utility",
        "description": "Severe storm-induced phase voltage imbalance affecting academic block",
    },
    {
        "id": 15,
        "facts": {
            "feeder": "lab",
            "alarm": "abnormal_voltage",
            "load": "medium",
            "weather": "storm",
            "backup": "unavailable",
        },
        "expected": "call_utility",
        "description": "Thunderstorm power surge creating sustained dangerous voltage swings",
    },
    {
        "id": 16,
        "facts": {
            "feeder": "hostel",
            "alarm": "smoke_or_fire",
            "load": "low",
            "weather": "clear",
            "backup": "available",
        },
        "expected": "call_utility",
        "description": "Substation switchgear cabinet smoke detected - immediate emergency",
    },
    {
        "id": 17,
        "facts": {
            "feeder": "academic",
            "alarm": "smoke_or_fire",
            "load": "high",
            "weather": "storm",
            "backup": "unavailable",
        },
        "expected": "call_utility",
        "description": "Catastrophic storm lightning strike leading to switchboard fire",
    },
]


def forward_chain(facts: Dict[str, str]) -> List[str]:
    """
    Evaluates all rules against current facts and returns list of rule IDs that fired.
    """
    fired = []
    for rule_id, rule in RULES.items():
        conditions_met = True
        for attr, allowed_values in rule["conditions"].items():
            fact_val = facts.get(attr)
            if fact_val not in allowed_values:
                conditions_met = False
                break
        if conditions_met:
            fired.append(rule_id)
    return fired


def resolve(fired_rule_ids: List[str]) -> Optional[Dict[str, Any]]:
    """
    Resolves conflict among multiple fired rules:
    1. Highest priority wins (priority 1 to 6).
    2. Tie-breaker: Highest specificity (count of conditions) wins.
    3. Deterministic order if still tied.
    """
    if not fired_rule_ids:
        return None

    candidate_rules = [RULES[rid] for rid in fired_rule_ids if rid in RULES]
    if not candidate_rules:
        return None

    # Sort descending by priority, then descending by specificity, then by rule ID
    candidate_rules.sort(
        key=lambda r: (r["priority"], r["specificity"], -int(r["id"][1:])),
        reverse=True,
    )
    return candidate_rules[0]


def alert_level(priority: Optional[int]) -> str:
    """
    Maps chosen rule priority to operational alert level:
    1-2: ADVISORY
    3-4: WARNING
    5-6: CRITICAL
    None / Unmatched: UNCERTAIN
    """
    if priority is None:
        return "UNCERTAIN"
    if priority in (1, 2):
        return "ADVISORY"
    if priority in (3, 4):
        return "WARNING"
    if priority in (5, 6):
        return "CRITICAL"
    return "UNCERTAIN"


def compile_safe_steps(action: str, alert: str, alarm: str) -> List[str]:
    """
    Builds the safe-step advice checklist based on alert level, action, and alarm.
    """
    steps = []

    # Common mandatory safety boundary advice for WARNING and CRITICAL
    if alert in ("CRITICAL", "WARNING", "UNCERTAIN"):
        steps.append("Keep students and unauthorised persons away from the affected area.")
        steps.append("Do not touch, open, reset or attempt to repair electrical equipment.")
        steps.append("Inform the authorised campus electrical maintenance team immediately.")

    # Uncertain condition advice
    if alert == "UNCERTAIN":
        steps.append("Request an immediate on-site safety and diagnostic inspection.")

    # Emergency plan step if smoke or fire
    if alarm == "smoke_or_fire":
        steps.append("Follow the campus emergency plan and contact emergency services.")

    # Action-specific safe operational steps
    if action == "monitor":
        steps.append("Keep observing readings; log the event; escalate if the alarm repeats or load rises.")
    elif action == "isolate_feeder":
        steps.append("Request the authorised team to isolate the affected feeder.")
    elif action == "switch_to_backup":
        steps.append("Request the authorised team to transfer load to the backup supply.")
    elif action == "call_utility":
        steps.append("Contact the utility / authorised electrical team now.")
    elif action == "inspect":
        steps.append("Request an immediate on-site safety and diagnostic inspection.")

    return steps


def advise(facts: Dict[str, str]) -> Dict[str, Any]:
    """
    Main expert advisor reasoning pipeline:
    Forward chaining -> Conflict resolution -> Alert level -> Safe steps -> Explanation
    """
    fired_ids = forward_chain(facts)
    chosen = resolve(fired_ids)
    conflict = len(fired_ids) > 1

    alarm = facts.get("alarm", "")

    if chosen:
        action = chosen["action"]
        level = alert_level(chosen["priority"])
        chosen_rule_data = {
            "id": chosen["id"],
            "priority": chosen["priority"],
            "specificity": chosen["specificity"],
            "text": chosen["text"],
        }

        # Build clear explanation of reasoning and conflict resolution
        if conflict:
            other_ids = [rid for rid in fired_ids if rid != chosen["id"]]
            other_rules = [RULES[rid] for rid in other_ids]
            
            # Check if priority decided it or specificity
            same_priority_competitors = [r for r in other_rules if r["priority"] == chosen["priority"]]
            if same_priority_competitors:
                comp_ids = ", ".join(r["id"] for r in same_priority_competitors)
                reason = (
                    f"Conflict resolved: {chosen['id']} was selected over {comp_ids} because it has higher specificity "
                    f"({chosen['specificity']} conditions vs {same_priority_competitors[0]['specificity']} conditions) "
                    f"at Priority {chosen['priority']}."
                )
            else:
                other_priorities = ", ".join(f"{r['id']} (P{r['priority']})" for r in other_rules)
                reason = (
                    f"Conflict resolved: {chosen['id']} (Priority {chosen['priority']}) overrode lower-priority "
                    f"matching rule(s) {other_priorities}."
                )
        else:
            reason = f"Rule {chosen['id']} matched condition pattern: recommended action is {action}."

    else:
        # No rule matched
        action = "call_utility"
        level = "UNCERTAIN"
        chosen_rule_data = None
        reason = "No predefined rule matched the reported condition pattern. Request immediate qualified inspection."

    safe_steps = compile_safe_steps(action, level, alarm)

    return {
        "action": action,
        "alert_level": level,
        "fired_rules": fired_ids,
        "chosen_rule": chosen_rule_data,
        "conflict": conflict,
        "reason": reason,
        "safe_steps": safe_steps,
    }

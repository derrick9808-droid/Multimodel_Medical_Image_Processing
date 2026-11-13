"""
Unit Test Suite for Electrical Fault First-Response Advisor Engine
Course: 25DC204 - Fundamentals of AI
"""

import sys
import os

# Add parent and current dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fault_advisor import (
    RULES,
    BASELINE,
    EVENTS,
    forward_chain,
    resolve,
    alert_level,
    advise,
)


def test_rules_structure():
    assert len(RULES) == 12
    for r_id, rule in RULES.items():
        assert rule["id"] == r_id
        assert 1 <= rule["priority"] <= 6
        assert rule["specificity"] >= 1
        assert "text" in rule
        assert rule["action"] in {"monitor", "isolate_feeder", "switch_to_backup", "call_utility"}


def test_acceptance_criteria_1_conflict_resolution():
    """
    AC 1: Overcurrent + high load + backup available ->
    SWITCH TO BACKUP, WARNING, fired rules R2 and R3, chosen R3, conflict resolved.
    """
    facts = {
        "feeder": "lab",
        "alarm": "overcurrent",
        "load": "high",
        "weather": "clear",
        "backup": "available",
    }
    result = advise(facts)
    assert result["action"] == "switch_to_backup"
    assert result["alert_level"] == "WARNING"
    assert "R2" in result["fired_rules"]
    assert "R3" in result["fired_rules"]
    assert result["chosen_rule"]["id"] == "R3"
    assert result["conflict"] is True
    assert "Conflict resolved" in result["reason"]


def test_acceptance_criteria_2_smoke_or_fire():
    """
    AC 2: smoke_or_fire (any facts) ->
    CALL UTILITY, CRITICAL, rule R12, emergency-plan step shown.
    """
    facts = {
        "feeder": "hostel",
        "alarm": "smoke_or_fire",
        "load": "low",
        "weather": "clear",
        "backup": "available",
    }
    result = advise(facts)
    assert result["action"] == "call_utility"
    assert result["alert_level"] == "CRITICAL"
    assert result["chosen_rule"]["id"] == "R12"
    assert any("emergency plan" in step.lower() for step in result["safe_steps"])


def test_acceptance_criteria_3_earth_fault_storm():
    """
    AC 3: Earth fault + storm + backup unavailable ->
    CALL UTILITY, CRITICAL, rule R5 (R4 also fired and is overridden).
    """
    facts = {
        "feeder": "academic",
        "alarm": "earth_fault",
        "load": "medium",
        "weather": "storm",
        "backup": "unavailable",
    }
    result = advise(facts)
    assert result["action"] == "call_utility"
    assert result["alert_level"] == "CRITICAL"
    assert "R4" in result["fired_rules"]
    assert "R5" in result["fired_rules"]
    assert result["chosen_rule"]["id"] == "R5"
    assert result["conflict"] is True


def test_acceptance_criteria_4_unmatched_facts():
    """
    AC 4: A combination matching no rule shows UNCERTAIN with a request for inspection.
    """
    facts = {
        "feeder": "hostel",
        "alarm": "unknown_alarm",
        "load": "low",
        "weather": "clear",
        "backup": "available",
    }
    result = advise(facts)
    assert result["alert_level"] == "UNCERTAIN"
    assert result["action"] == "call_utility"
    assert result["chosen_rule"] is None
    assert "inspection" in result["reason"].lower()


def test_acceptance_criteria_5_all_17_events():
    """
    AC 5: Evaluate tab shows advisor 17/17 (100%) vs baseline 9/17 (52.9%),
    baseline failures highlighted on events 1, 2, 3, 6, 9, 12, 14, 15.
    """
    assert len(EVENTS) == 17
    advisor_correct = 0
    baseline_correct = 0
    failed_baseline_events = []

    for ev in EVENTS:
        ev_id = ev["id"]
        facts = ev["facts"]
        expected = ev["expected"]

        adv_res = advise(facts)
        if adv_res["action"] == expected:
            advisor_correct += 1

        alarm = facts["alarm"]
        base_act = BASELINE.get(alarm)
        if base_act == expected:
            baseline_correct += 1
        else:
            failed_baseline_events.append(ev_id)

    # Advisor must be 17/17 (100%)
    assert advisor_correct == 17, f"Advisor got {advisor_correct}/17"

    # Baseline must be 9/17 (52.9%)
    assert baseline_correct == 9, f"Baseline got {baseline_correct}/17"

    # Baseline failures must be exactly events 1, 2, 3, 6, 9, 12, 14, 15
    expected_failures = [1, 2, 3, 6, 9, 12, 14, 15]
    assert failed_baseline_events == expected_failures, (
        f"Failed baseline events: {failed_baseline_events} vs expected {expected_failures}"
    )


def test_alert_levels():
    assert alert_level(1) == "ADVISORY"
    assert alert_level(2) == "ADVISORY"
    assert alert_level(3) == "WARNING"
    assert alert_level(4) == "WARNING"
    assert alert_level(5) == "CRITICAL"
    assert alert_level(6) == "CRITICAL"
    assert alert_level(None) == "UNCERTAIN"


def run_all_tests():
    print("=" * 60)
    print("Running Electrical Fault Advisor Test Suite...")
    print("=" * 60)
    tests = [
        test_rules_structure,
        test_acceptance_criteria_1_conflict_resolution,
        test_acceptance_criteria_2_smoke_or_fire,
        test_acceptance_criteria_3_earth_fault_storm,
        test_acceptance_criteria_4_unmatched_facts,
        test_acceptance_criteria_5_all_17_events,
        test_alert_levels,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} - {e}")
            raise e
    print("=" * 60)
    print(f"All {passed}/{len(tests)} tests PASSED successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()


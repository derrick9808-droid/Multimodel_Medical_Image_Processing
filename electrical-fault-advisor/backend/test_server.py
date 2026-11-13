"""
In-process and mock integration tests for Electrical Fault Advisor backend.
Tests request validation, endpoints logic, evaluation calculation, and error handlers.
"""

import io
import json
import os
import sys

# Ensure backend directory is in path
backend_dir = os.path.dirname(__file__)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import fault_advisor
import main

class MockSocket:
    def __init__(self, request_bytes):
        self._rfile = io.BytesIO(request_bytes)
        self._wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "b" in mode:
            if "r" in mode:
                return self._rfile
            elif "w" in mode:
                return self._wfile
        return self._rfile

    def get_response(self):
        self._wfile.seek(0)
        return self._wfile.read()

def test_backend_direct_endpoints():
    print("Testing backend logic directly...")
    
    # 1. Rules endpoint data
    rules = list(fault_advisor.RULES.values())
    assert len(rules) == 12, f"Expected 12 rules, got {len(rules)}"
    print(f"PASS: Rules count = {len(rules)}")

    # 2. Events endpoint data
    events = fault_advisor.EVENTS
    assert len(events) == 17, f"Expected 17 events, got {len(events)}"
    print(f"PASS: Events count = {len(events)}")

    # 3. Evaluation calculation
    eval_res = main.compute_evaluation()
    totals = eval_res["totals"]
    assert totals["n"] == 17
    assert totals["advisor_correct"] == 17
    assert totals["baseline_correct"] == 9
    assert totals["advisor_pct"] == 100.0
    assert totals["baseline_pct"] == 52.9
    print(f"PASS: Evaluation totals match 17/17 (100%) vs 9/17 (52.9%)")

    # 4. Input validation (422 cases)
    errs = main.validate_facts_dict({"feeder": "space_station", "alarm": "overcurrent", "load": "high", "weather": "clear", "backup": "available"})
    assert any("feeder" in e for e in errs), f"Expected feeder error, got: {errs}"
    print("PASS: Feeder validation caught invalid value")

    errs = main.validate_facts_dict({"feeder": "hostel", "alarm": "explosion", "load": "high", "weather": "clear", "backup": "available"})
    assert any("alarm" in e for e in errs)
    print("PASS: Alarm validation caught invalid value")

    errs = main.validate_facts_dict({"feeder": "hostel", "alarm": "overcurrent", "load": "extreme", "weather": "clear", "backup": "available"})
    assert any("load" in e for e in errs)
    print("PASS: Load validation caught invalid value")

    errs = main.validate_facts_dict({"feeder": "hostel", "alarm": "overcurrent", "load": "high", "weather": "tsunami", "backup": "available"})
    assert any("weather" in e for e in errs)
    print("PASS: Weather validation caught invalid value")

    errs = main.validate_facts_dict({"feeder": "hostel", "alarm": "overcurrent", "load": "high", "weather": "clear", "backup": "maybe"})
    assert any("backup" in e for e in errs)
    print("PASS: Backup validation caught invalid value")

    # Valid dictionary
    no_errs = main.validate_facts_dict({"feeder": "hostel", "alarm": "overcurrent", "load": "high", "weather": "clear", "backup": "available"})
    assert len(no_errs) == 0, f"Expected no errors for valid facts, got {no_errs}"
    print("PASS: Valid facts pass validation cleanly")

    # 5. Acceptance Criteria 1: Conflict resolution
    res1 = fault_advisor.advise({
        "feeder": "hostel",
        "alarm": "overcurrent",
        "load": "high",
        "weather": "clear",
        "backup": "available"
    })
    assert res1["action"] == "switch_to_backup"
    assert res1["alert_level"] == "WARNING"
    assert res1["chosen_rule"]["id"] == "R3"
    assert res1["conflict"] is True
    assert set(res1["fired_rules"]) == {"R2", "R3"}
    assert any("isolate the affected feeder" in s for s in res1["safe_steps"]) or any("transfer load to the backup" in s for s in res1["safe_steps"])
    print("PASS: Acceptance Criteria 1 (Overcurrent high load backup available -> switch_to_backup R3)")

    # 6. Acceptance Criteria 2: smoke_or_fire
    res2 = fault_advisor.advise({
        "feeder": "academic",
        "alarm": "smoke_or_fire",
        "load": "low",
        "weather": "clear",
        "backup": "unavailable"
    })
    assert res2["action"] == "call_utility"
    assert res2["alert_level"] == "CRITICAL"
    assert res2["chosen_rule"]["id"] == "R12"
    assert any("emergency plan" in s for s in res2["safe_steps"])
    print("PASS: Acceptance Criteria 2 (Smoke or fire -> call_utility R12 with emergency plan step)")

    # 7. Acceptance Criteria 3: earth_fault + storm + unavailable
    res3 = fault_advisor.advise({
        "feeder": "lab",
        "alarm": "earth_fault",
        "load": "medium",
        "weather": "storm",
        "backup": "unavailable"
    })
    assert res3["action"] == "call_utility"
    assert res3["alert_level"] == "CRITICAL"
    assert res3["chosen_rule"]["id"] == "R5"
    assert "R4" in res3["fired_rules"] and "R5" in res3["fired_rules"]
    assert res3["conflict"] is True
    print("PASS: Acceptance Criteria 3 (Earth fault storm unavailable -> call_utility R5 over R4)")

    # 8. Acceptance Criteria 4: Unmatched facts -> UNCERTAIN
    res4 = fault_advisor.advise({
        "feeder": "lab",
        "alarm": "nonexistent_alarm",
        "load": "medium",
        "weather": "clear",
        "backup": "available"
    })
    assert res4["action"] == "call_utility"
    assert res4["alert_level"] == "UNCERTAIN"
    assert res4["chosen_rule"] is None
    assert any("qualified personnel" in s.lower() or "inspect" in s.lower() for s in res4["safe_steps"])
    print("PASS: Acceptance Criteria 4 (Unmatched facts -> UNCERTAIN + inspection safe step)")

    print("\n============================================================")
    print("ALL BACKEND & CRITERIA VERIFICATIONS PASSED!")
    print("============================================================")

if __name__ == "__main__":
    test_backend_direct_endpoints()

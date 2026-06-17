"""Unit tests for roadmap_validator.validate_roadmap.

Run with pytest (`python -m pytest test_roadmap_validator.py`) or directly
(`python test_roadmap_validator.py`) — a tiny runner at the bottom executes every
test function without requiring pytest to be installed.
"""

from roadmap_validator import validate_roadmap

EARLIEST = "Fall 2026"


def test_clean_plan_passes():
    """Valid order, valid terms, no dups, plus an unknown elective -> no violations."""
    roadmap = {
        "terms": [
            {"term": "Fall 2026", "courses": ["CSC 1001", "ELECT 1000"]},
            {"term": "Spring 2027", "courses": ["CSC 2001", "MATH 1261"]},
        ]
    }
    assert validate_roadmap(roadmap, earliest_term=EARLIEST) == []


def test_prereq_out_of_order_is_flagged():
    """CSC 2001 before its prereq CSC 1001 must be caught."""
    roadmap = {
        "terms": [
            {"term": "Fall 2026", "courses": ["CSC 2001"]},
            {"term": "Spring 2027", "courses": ["CSC 1001"]},
        ]
    }
    violations = validate_roadmap(roadmap, earliest_term=EARLIEST)
    assert any("CSC 1001" in v and "strictly earlier" in v for v in violations), violations


def test_off_term_course_is_flagged():
    """CSC 1001 is offered F/SP only — scheduling it in Summer must be flagged."""
    roadmap = {"terms": [{"term": "Summer 2027", "courses": ["CSC 1001"]}]}
    violations = validate_roadmap(roadmap, earliest_term=EARLIEST)
    assert any("not offered" in v and "CSC 1001" in v for v in violations), violations


def test_cap_breach_with_cap_set_is_flagged():
    """Three prereq-free major courses in one term breach a cap of 2."""
    roadmap = {
        "terms": [
            {"term": "Fall 2026", "courses": ["CSC 1000", "CSC 1001", "CSC 1024"]},
        ]
    }
    violations = validate_roadmap(roadmap, cs_cap=2, earliest_term=EARLIEST)
    assert any("cap" in v for v in violations), violations


def test_no_cap_passes_when_cs_cap_is_none():
    """The same overloaded term passes when no cap is supplied (cap check skipped)."""
    roadmap = {
        "terms": [
            {"term": "Fall 2026", "courses": ["CSC 1000", "CSC 1001", "CSC 1024"]},
        ]
    }
    assert validate_roadmap(roadmap, cs_cap=None, earliest_term=EARLIEST) == []


def test_unknown_elective_is_skipped_not_flagged():
    """A course in no dict, even in an off-season term, is skipped for offering/prereq."""
    roadmap = {"terms": [{"term": "Summer 2027", "courses": ["MU 101"]}]}
    assert validate_roadmap(roadmap, earliest_term=EARLIEST) == []


def test_term_floor_is_flagged():
    """A term earlier than the earliest allowed term is caught."""
    roadmap = {"terms": [{"term": "Spring 2026", "courses": ["CSC 1001"]}]}
    violations = validate_roadmap(roadmap, earliest_term=EARLIEST)
    assert any("earlier than the earliest" in v for v in violations), violations


def test_duplicate_course_is_flagged():
    """The same course in two terms is caught."""
    roadmap = {
        "terms": [
            {"term": "Fall 2026", "courses": ["CSC 1001"]},
            {"term": "Spring 2027", "courses": ["CSC 1001"]},
        ]
    }
    violations = validate_roadmap(roadmap, earliest_term=EARLIEST)
    assert any("more than one term" in v for v in violations), violations


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)

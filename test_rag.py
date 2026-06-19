"""Focused tests for rag.py's public retrieval logic.

Uses a small fixed professor fixture (passed straight into retrieve_rag_context) so the
tests are deterministic and need no network — get_professors() is never called here.

Run with pytest (`python -m pytest test_rag.py`) or directly (`python test_rag.py`).
"""

from rag import _extract_course_codes, retrieve_rag_context, retrieve_relevant_professors

# Shaped like real PolyRatings entries (firstName/lastName/courses/tags).
PROFESSORS = [
    {"firstName": "Foaad", "lastName": "Khosmood",
     "courses": ["CSC 480", "CSC 481", "CSC 466"], "tags": {}},
    {"firstName": "John", "lastName": "Bellardo",
     "courses": ["CSC 357", "CSC 453"], "tags": {}},
    {"firstName": "Julie", "lastName": "Workman",
     "courses": ["CSC 101", "CSC 202"], "tags": {}},
]


def test_bare_last_name_surfaces_that_professor_as_top_result():
    # README claim: a query that is just a professor's last name surfaces that professor.
    result = retrieve_rag_context("Khosmood", professors=PROFESSORS)
    assert result.documents, "expected at least one retrieved document"
    top = result.documents[0]
    assert top.kind == "professor"
    assert top.metadata["professor"]["lastName"] == "Khosmood"


def test_retrieve_relevant_professors_returns_named_professor_first():
    profs = retrieve_relevant_professors("Bellardo", PROFESSORS)
    assert profs, "expected a professor match"
    assert profs[0]["lastName"] == "Bellardo"


def test_course_code_is_extracted_from_query():
    codes = _extract_course_codes("who should I take for CSC 2050?")
    assert "CSC 2050" in codes


def test_course_code_extraction_tolerates_missing_space():
    assert "CSC 2050" in _extract_course_codes("any info on CSC2050 please")


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

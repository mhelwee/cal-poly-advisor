"""Pure, deterministic validation for LLM-produced course roadmaps.

No Flask, no network, no Anthropic — just data checks against requirements.py so
the app can stop trusting the model's roadmap blindly: emit it as structured
data, validate here, and regenerate on failure.

Expected roadmap shape:
    {"terms": [{"term": "Fall 2026", "courses": ["CSC 1001", "MATH 1261"]}, ...]}

DESIGN NOTE — sparse dicts, skip don't flag:
PREREQUISITE_CHAIN (9 entries) and TERM_OFFERED (21 entries) only cover core
major/support courses. The vast majority of GE/elective courses appear in
neither. For any course missing from the relevant dict, the corresponding check
is SKIPPED for that course rather than failed. A validator that false-flags
every elective is worse than no validator at all.
"""

import re

from advising_data import CS_REQUIREMENTS, PREREQUISITE_CHAIN, TERM_OFFERED

# Season string -> TERM_OFFERED code, and -> a month used purely for ordering
# (Fall after Summer after Spring within a year), so Fall 2026 < Spring 2027.
SEASON_CODE = {"fall": "F", "spring": "SP", "summer": "SU"}
SEASON_MONTH = {"fall": 9, "spring": 1, "summer": 6}

# Major CSC/CPE courses — the only ones that count toward the optional per-term cap.
MAJOR_COURSES = set(CS_REQUIREMENTS["major_courses"])

_CODE_RE = re.compile(r"^([A-Za-z]{2,4})\s*-?\s*(\d{3,4})$")


def _normalize(course):
    """Canonicalize a course code to '<SUBJ> <NUMBER>' (e.g. 'csc1001' -> 'CSC 1001').

    Non-course strings pass through with whitespace collapsed.
    """
    text = " ".join(str(course).split())
    match = _CODE_RE.match(text)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}"
    return text


def _parse_term(term):
    """Parse '<Season> <Year>' into (year, month, code). Return None if unparseable."""
    parts = str(term).split()
    if len(parts) != 2:
        return None
    season, year = parts[0].lower(), parts[1]
    if season not in SEASON_MONTH or not year.isdigit():
        return None
    return (int(year), SEASON_MONTH[season], SEASON_CODE[season])


def _sort_key(parsed):
    """Sortable (year, month) key from a parsed term tuple."""
    return (parsed[0], parsed[1])


def validate_roadmap(roadmap, *, cs_cap=None, earliest_term):
    """Validate a roadmap dict; return a list of human-readable violations.

    An empty list means the roadmap passed every applicable check.

    Args:
        roadmap: {"terms": [{"term": str, "courses": [str, ...]}, ...]}.
        cs_cap: max major CSC/CPE courses allowed per term. None disables the
            cap check entirely (there is NO default cap).
        earliest_term: '<Season> <Year>'; no term may precede it.
    """
    violations = []
    terms = roadmap.get("terms", []) if isinstance(roadmap, dict) else []

    earliest = _parse_term(earliest_term)

    # First pass: parse each term entry and record where every course is placed.
    parsed_terms = []  # (term_str, parsed_or_None, [normalized course codes])
    placements = {}    # normalized course -> [(sort_key_or_None, term_str), ...]

    for entry in terms:
        if not isinstance(entry, dict):
            continue
        term_str = entry.get("term", "")
        parsed = _parse_term(term_str)
        courses = [_normalize(c) for c in entry.get("courses", []) or []]
        parsed_terms.append((term_str, parsed, courses))

        if parsed is None:
            violations.append(
                f'Term "{term_str}" is not a valid "<Season> <Year>" term string.'
            )

        key = _sort_key(parsed) if parsed else None
        for course in courses:
            placements.setdefault(course, []).append((key, term_str))

    # Earliest valid (parseable) placement for each course — used for prereq ordering.
    course_min_key = {}
    for course, places in placements.items():
        keys = [key for key, _ in places if key is not None]
        if keys:
            course_min_key[course] = min(keys)

    # 5. NO DUPLICATES — a course code may appear in only one term.
    for course, places in placements.items():
        if len(places) > 1:
            where = ", ".join(term for _, term in places)
            violations.append(f"{course} appears in more than one term: {where}.")

    # 4. TERM FLOOR — no term earlier than earliest_term.
    if earliest is not None:
        earliest_key = _sort_key(earliest)
        for term_str, parsed, _courses in parsed_terms:
            if parsed is not None and _sort_key(parsed) < earliest_key:
                violations.append(
                    f'Term "{term_str}" is earlier than the earliest allowed '
                    f'term "{earliest_term}".'
                )

    for term_str, parsed, courses in parsed_terms:
        if parsed is None:
            continue  # already flagged; can't run term-dependent checks on it
        season_code = parsed[2]
        course_key = _sort_key(parsed)

        # 2. TERM OFFERING — season must be one this course is offered in.
        for course in courses:
            offered = TERM_OFFERED.get(course)
            if offered is None:
                continue  # unknown course: skip, do not flag
            if season_code not in offered:
                violations.append(
                    f"{course} is not offered in {term_str} "
                    f"(offered: {', '.join(offered)})."
                )

        # 1. PREREQ ORDER — each known prereq present in the plan must be strictly
        #    earlier. A prereq absent from the plan is assumed already completed
        #    (the roadmap only lists remaining terms) and is skipped, not flagged.
        #    Transitive chains resolve themselves: each prereq, if scheduled, is
        #    itself a course here and gets its own prereqs checked.
        for course in courses:
            for prereq in PREREQUISITE_CHAIN.get(course, []):
                prereq_key = course_min_key.get(_normalize(prereq))
                if prereq_key is None:
                    continue
                if prereq_key >= course_key:
                    violations.append(
                        f"{course} in {term_str} requires {prereq} in a "
                        f"strictly earlier term."
                    )

        # 3. CS-COURSE CAP — only when a cap is supplied.
        if cs_cap is not None:
            majors = [c for c in courses if c in MAJOR_COURSES]
            if len(majors) > cs_cap:
                violations.append(
                    f"{term_str} schedules {len(majors)} major CS courses "
                    f"({', '.join(majors)}), exceeding the cap of {cs_cap}."
                )

    # Preserve order while removing any accidental duplicate messages.
    seen = set()
    unique = []
    for violation in violations:
        if violation not in seen:
            seen.add(violation)
            unique.append(violation)
    return unique

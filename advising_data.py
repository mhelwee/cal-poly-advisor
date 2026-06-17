CS_REQUIREMENTS = {
    "major_courses": [
        "CSC 1000",   # Computing Majors Orientation
        "CSC 1001",   # Fundamentals of Computer Science
        "CSC 1024",   # Introduction to Computing
        "CSC 2001",   # Data Structures
        "CSC 2050",   # System Software Mechanics
        "CPE 2300",   # Introduction to Computer Systems
        "CSC 3001",   # Modern Application Development
        "CSC 3100",   # Software Engineering
        "CSC 3201",   # Introduction to Computer Security
        "CSC 3300",   # Programming Languages
        "CSC 3449",   # Algorithms and Complexity
        "CSC 4553",   # Introduction to Operating Systems
    ],
    "support_courses": [
        "MATH 1151",  # Linear Algebra
        "MATH 1261",  # Calculus I
        "MATH 1262",  # Calculus II
        "MATH 2031",  # Transition to Advanced Mathematics
        "STAT 3210",  # Engineering Statistics
        "PHIL 3323",  # Ethics, Science, and Technology
        "WGQS 3350",  # Gender, Race, Culture, Science, and Technology
    ],
    "senior_project": [
        "CSC 4460 or CSC 4461 (or approved alternative)"
    ],
    "technical_electives": "23 units required from approved elective list",
    "total_units": 120
}

PREREQUISITE_CHAIN = {
    "CSC 2001": ["CSC 1001"],
    "CSC 2050": ["CSC 1001"],
    "CPE 2300": ["CSC 1024"],
    "CSC 3001": ["CSC 2001"],
    "CSC 3100": ["CSC 3001"],
    "CSC 3201": ["CSC 2001"],
    "CSC 3300": ["CSC 2001"],
    "CSC 3449": ["CSC 2001", "MATH 2031"],
    "CSC 4553": ["CSC 2050", "CPE 2300"],
}

# Natural-language course aliases → canonical quarter course codes.
# Students say "Calc 1/2/3" to mean the quarter calculus sequence MATH 141/142/143.
COURSE_ALIASES = {
    "calc 1": "MATH 141",
    "calc i": "MATH 141",
    "calculus 1": "MATH 141",
    "calculus i": "MATH 141",
    "calc 2": "MATH 142",
    "calc ii": "MATH 142",
    "calculus 2": "MATH 142",
    "calculus ii": "MATH 142",
    "calc 3": "MATH 143",
    "calc iii": "MATH 143",
    "calculus 3": "MATH 143",
    "calculus iii": "MATH 143",
}

# Semester requirements satisfied JOINTLY by a set of quarter courses, where each
# member may be earned by class OR by AP credit. The full member set must be present
# (from any mix of sources) to satisfy the listed semester requirements.
SEQUENCE_REQUIREMENTS = [
    {
        "name": "Calculus sequence",
        "members": ["MATH 141", "MATH 142", "MATH 143"],
        "satisfies": ["MATH 1261", "MATH 1262"],
        # AP exam → which member it can supply (i.e. "test out of" that course)
        "ap_sources": {"MATH 141": "Calculus AB"},
    },
]

QUARTER_TO_SEMESTER = [
    # Each entry: old (all must be taken for combined; one of them for alternatives),
    # new (empty for non-satisfying mappings), kind, optional note.
    # kind: "major" | "support" | "tech_elective" | "free_elective" | "external_elective"

    # Major courses
    {"old": ["CSC 101"],              "new": ["CSC 1001"],              "kind": "major"},
    {"old": ["CSC 123"],              "new": ["CSC 1000", "CSC 1024"],  "kind": "major"},
    {"old": ["CSC 202"],              "new": ["CSC 2001"],              "kind": "major"},
    {"old": ["CSC 203"],              "new": [],                        "kind": "free_elective",    "note": "Free Electives"},
    {"old": ["CSC 357"],              "new": ["CSC 2050"],              "kind": "major"},
    {"old": ["CSC 225"],              "new": ["CPE 2300"],              "kind": "major"},
    {"old": ["CSC 364"],              "new": ["CSC 3001"],              "kind": "major"},
    {"old": ["CSC 464"],              "new": ["CSC 3001"],              "kind": "major"},
    {"old": ["CSC 307"],              "new": ["CSC 3100"],              "kind": "major"},
    {"old": ["CSC 308", "CSC 309"],   "new": ["CSC 3100"],              "kind": "major",            "note": "Both required"},
    {"old": ["CSC 321"],              "new": ["CSC 3201"],              "kind": "major"},
    {"old": ["CSC 323"],              "new": ["CSC 3201"],              "kind": "major"},
    {"old": ["CSC 325"],              "new": ["CSC 3201"],              "kind": "major"},
    {"old": ["CSC 430"],              "new": ["CSC 3300"],              "kind": "major"},
    {"old": ["CSC 349"],              "new": ["CSC 3449"],              "kind": "major"},
    {"old": ["CSC 453"],              "new": ["CSC 4553"],              "kind": "major"},
    {"old": ["CSC 491", "CSC 492"],   "new": ["CSC 4460"],              "kind": "major",            "note": "Both required"},
    {"old": ["CSC 469"],              "new": ["CSC 4669"],              "kind": "tech_elective"},
    {"old": ["CSC 365"],              "new": ["CSC 3665"],              "kind": "tech_elective"},
    {"old": ["CSC 445"],              "new": ["CSC 3445"],              "kind": "tech_elective"},

    # Support courses
    {"old": ["CSC 248"],                            "new": ["MATH 2031"],              "kind": "support"},
    {"old": ["CSC 300"],                            "new": ["PHIL 3323"],              "kind": "support"},
    {"old": ["PHIL 323"],                           "new": ["PHIL 3323"],              "kind": "support"},
    {"old": ["MATH 206"],                           "new": ["MATH 1151"],              "kind": "support"},
    {"old": ["MATH 244"],                           "new": ["MATH 1151"],              "kind": "support"},
    {"old": ["MATH 141", "MATH 142", "MATH 143"],   "new": ["MATH 1261", "MATH 1262"], "kind": "support", "note": "All three required (any member may come from class or AP credit); together they satisfy BOTH MATH 1261 and MATH 1262. See SEQUENCE_REQUIREMENTS."},
    {"old": ["STAT 312"],                           "new": ["STAT 3210"],              "kind": "support"},
    {"old": ["ES 350"],                             "new": ["WGQS 3350"],              "kind": "support"},
    {"old": ["WGQS 350"],                           "new": ["WGQS 3350"],              "kind": "support"},
    {"old": ["ES 351"],                             "new": ["WGQS 3351"],              "kind": "support"},
    {"old": ["WGQS 351"],                           "new": ["WGQS 3351"],              "kind": "support"},
    {"old": ["PHYS 141"],                           "new": ["PHYS 1141"],              "kind": "support"},
    {"old": ["CHEM 124"],                           "new": ["CHEM 1120"],              "kind": "support"},

    # Life Science Elective options (do NOT satisfy a named support requirement)
    {"old": ["BIO 111"],                "new": [], "kind": "external_elective", "note": "Life Science Elective"},
    {"old": ["BIO 213", "BMED 213"],    "new": [], "kind": "external_elective", "note": "Life Science Elective (both required)"},
    {"old": ["BIO 161"],                "new": [], "kind": "external_elective", "note": "Life Science Elective"},
    {"old": ["BOT 121"],                "new": [], "kind": "external_elective", "note": "Life Science Elective"},
    {"old": ["MCRO 221"],               "new": [], "kind": "external_elective", "note": "Life Science Elective"},

    # Approved External Electives (do NOT satisfy a named CS requirement)
    {"old": ["PHYS 142"], "new": [], "kind": "external_elective", "note": "Approved External Elective"},
    {"old": ["PHYS 143"], "new": [], "kind": "external_elective", "note": "Approved External Elective"},
    {"old": ["CHEM 125"], "new": [], "kind": "external_elective", "note": "Approved External Elective"},
    {"old": ["CHEM 126"], "new": [], "kind": "external_elective", "note": "Approved External Elective"},
]

COURSE_NAMES = {
    "CSC 1000": "Computing Majors Orientation",
    "CSC 1001": "Fundamentals of Computer Science",
    "CSC 1024": "Introduction to Computing",
    "CSC 2001": "Data Structures",
    "CSC 2050": "System Software Mechanics",
    "CPE 2300": "Introduction to Computer Systems",
    "CSC 3001": "Modern Application Development",
    "CSC 3100": "Software Engineering",
    "CSC 3201": "Introduction to Computer Security",
    "CSC 3300": "Programming Languages",
    "CSC 3449": "Algorithms and Complexity",
    "CSC 4553": "Introduction to Operating Systems",
    "MATH 1151": "Linear Algebra",
    "MATH 1261": "Calculus I",
    "MATH 1262": "Calculus II",
    "MATH 2031": "Transition to Advanced Mathematics",
    "STAT 3210": "Engineering Statistics",
    "PHIL 3323": "Ethics, Science, and Technology",
    "WGQS 3350": "Gender, Race, Culture, Science, and Technology",
}

# ---- General Education (quarter → 2026-28 semester catalog) ----

# Authoritative crosswalk: old quarter GE area → new semester GE area.
# A course earns GE credit for the area it was approved for WHEN TAKEN, then converts here.
GE_AREA_CROSSWALK = {
    "A1": "1C",
    "A2": "1A",
    "A3": "1B",
    "B4": "Area 2",
    "C1": "3A",
    "C2": "3B",
    "D1": "4A",
    "D2": "4B",
    "B1": "5A",
    "B2": "5B",
    "B3": "5C",
    "Area F": "Area 6",
    "Upper-Div B": "Upper-Div 2/5",
    "Upper-Div C": "Upper-Div 3",
    "Upper-Div D": "Upper-Div 4",
}

# Old quarter GE buckets that are DISCONTINUED in the 2026-28 semester catalog.
# A course that ONLY satisfied one of these now counts as free elective units —
# it is NOT a GE requirement and must NOT be listed as an unmet GE area.
DISCONTINUED_GE_AREAS = {
    "Lower-Division Area C elective": "Now free elective units (Lower-Div Area C elective discontinued).",
    "Area E": "Now free elective units (Area E discontinued).",
    "GE Electives": "Now free elective units (GE Electives discontinued).",
}

# Per-course GE crediting for this student, using the area each course was approved for
# WHEN TAKEN, then converted via GE_AREA_CROSSWALK.
# Fields:
#   old_area    – quarter GE area the course was approved for when taken
#   new_area    – semester area after crosswalk (list if more than one / ambiguous);
#                 None if the old area is discontinued (free elective only)
#   confirmed   – True if the area is verified; False → advisor must say "unverified, confirm"
#   discontinued– True if old_area is a discontinued bucket (free elective units only)
COURSE_GE_AREA = {
    "COMS 101": {"old_area": "A1",       "new_area": "1C",          "confirmed": True},
    "PHIL 126": {"old_area": "A3",       "new_area": "1B",          "confirmed": True},
    "ARCH 217": {"old_area": "C1",       "new_area": "3A",          "confirmed": True},
    "ES 252":   {"old_area": "Area F",   "new_area": "Area 6",      "confirmed": True},
    "POLS 112": {"old_area": "D1",       "new_area": "4A",          "confirmed": True},
    "SOC 218":  {"old_area": "D2",       "new_area": "4B",          "confirmed": True},
    "HLTH 255": {"old_area": "Area E",   "new_area": None,          "confirmed": True, "discontinued": True},
    "PHIL 323": {"old_area": "C2",       "new_area": "3B",          "confirmed": True},
}

# Terms each course is typically offered (F=Fall, SP=Spring, SU=Summer).
# Source: Cal Poly SLO catalog "Term Typically Offered" field.
TERM_OFFERED = {
    # Major courses
    "CSC 1000":  ["F", "SP"],
    "CSC 1001":  ["F", "SP"],
    "CSC 1024":  ["F", "SP"],
    "CSC 2001":  ["F", "SP"],
    "CSC 2050":  ["F", "SP"],
    "CPE 2300":  ["F", "SP"],
    "CSC 3001":  ["F", "SP"],
    "CSC 3100":  ["F", "SP"],
    "CSC 3201":  ["F", "SP"],
    "CSC 3300":  ["F", "SP"],
    "CSC 3449":  ["F", "SP"],
    "CSC 4553":  ["F", "SP"],
    # Senior project
    "CSC 4460":  ["F", "SP"],
    "CSC 4461":  ["F", "SP"],
    # Support courses
    "MATH 1151": ["F", "SP"],
    "MATH 1261": ["F", "SP", "SU"],
    "MATH 1262": ["F", "SP", "SU"],
    "MATH 2031": ["F", "SP"],
    "STAT 3210": ["F", "SP"],
    "PHIL 3323": ["F", "SP"],
    "WGQS 3350": ["F", "SP"],
}

# AP credit, keyed by year: AP_CREDIT[year][exam_name][min_score] → credit dict.
# Lookup: find the highest score key ≤ student's score; score < 3 → no credit.
# Fields:
#   courses          – course codes granted. Quarter-era codes (2023) run through
#                      QUARTER_TO_SEMESTER; semester codes (2024+) are used directly.
#                      If a code is not in CS_REQUIREMENTS (after any conversion), it
#                      does NOT satisfy any CS major or support requirement.
#   ge_areas         – CSU GE areas satisfied (A2, B3, B4, C2 notation from AP matrix)
#   title5           – Title 5 requirements (e.g. "US-1", "US-2"), not standard GE areas
#   elective_units   – additional elective units beyond named courses
#   duplicate_warning– course that triggers a duplication flag if also taken in class
#   notes            – advisory notes to surface verbatim to the student
#
# To add a new year: add a new top-level key with the full exam dict for that matrix.
# Year-specific entries override the shared defaults (see _AP_SHARED below).

_AP_PHYSICS_1_2023 = {
    3: {
        "courses": ["PHYS 141"],
        "ge_areas": ["B3"],
        "title5": [],
        "elective_units": 4,
        "duplicate_warning": "PHYS 141",
    },
}

_AP_PHYSICS_1_2024_2025 = {
    3: {
        "courses": ["PHYS 104"],
        "ge_areas": ["B3"],
        "title5": [],
        "elective_units": 4,
        "duplicate_warning": "PHYS 104",
        "notes": (
            "PHYS 104 satisfies GE Area B3 but is NOT a CS major or support requirement "
            "and does not appear in the CS degree requirements."
        ),
    },
}

_AP_SHARED = {
    "US History": {
        3: {"courses": [], "ge_areas": [], "title5": ["US-1"], "elective_units": 9},
    },
    "US Government and Politics": {
        3: {"courses": [], "ge_areas": [], "title5": ["US-2"], "elective_units": 9},
    },
    "Calculus AB": {
        3: {
            "courses": ["MATH 141"],
            "ge_areas": ["B4"],
            "title5": [],
            "elective_units": 1,
            "notes": (
                "Grants MATH 141 (student has 'tested out' of it). MATH 141 alone does NOT "
                "satisfy MATH 1261/1262 — but it COMBINES with MATH 142 and MATH 143 (from "
                "class or otherwise) to complete the sequence. A student with AP Calc AB + "
                "MATH 142 + MATH 143 has the full MATH 141+142+143 set and satisfies BOTH "
                "MATH 1261 and MATH 1262. This is a combination, NOT a duplication."
            ),
        },
    },
    "English Literature and Composition": {
        3: {"courses": ["ENGL 134"], "ge_areas": ["A2"], "title5": [], "elective_units": 3},
        5: {"courses": ["ENGL 134"], "ge_areas": ["A2", "C2"], "title5": [], "elective_units": 3},
    },
    "English Language and Composition": {
        3: {"courses": ["ENGL 134"], "ge_areas": ["A2"], "title5": [], "elective_units": 3},
    },
    "Computer Science Principles": {
        3: {"courses": ["CSC 123"], "ge_areas": [], "title5": [], "elective_units": 4},
    },
    "Statistics": {
        3: {
            "courses": ["STAT 130"],
            "ge_areas": ["B4"],
            "title5": [],
            "elective_units": 0,
            "notes": "STAT 130 does NOT satisfy STAT 3210 (Engineering Statistics).",
        },
    },
    "Environmental Science": {
        3: {"courses": [], "ge_areas": [], "title5": [], "elective_units": 9},
    },
}

AP_CREDIT = {
    2023: {**_AP_SHARED, "Physics 1": _AP_PHYSICS_1_2023},
    2024: {**_AP_SHARED, "Physics 1": _AP_PHYSICS_1_2024_2025},
    2025: {**_AP_SHARED, "Physics 1": _AP_PHYSICS_1_2024_2025},
}
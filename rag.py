import json
import re
from dataclasses import dataclass, field
from typing import Any

import requests

from advising_data import (
    COURSE_ALIASES,
    COURSE_NAMES,
    CS_REQUIREMENTS,
    DISCONTINUED_GE_AREAS,
    PREREQUISITE_CHAIN,
    QUARTER_TO_SEMESTER,
)

# Derived lookup: old course code → set of new semester course codes it satisfies.
# Non-satisfying kinds (free_elective, external_elective) map to an empty set.
_OLD_TO_NEW: dict[str, set[str]] = {}
for _entry in QUARTER_TO_SEMESTER:
    for _old in _entry["old"]:
        _OLD_TO_NEW.setdefault(_old, set()).update(_entry["new"])


def get_professors():
    """Fetch ALL professors from PolyRatings.

    No department filter — retrieval narrows by relevance, so professors in any
    department (WGQS, MATH, etc.) are available for last-name and course lookups.
    """
    url = "https://raw.githubusercontent.com/Polyratings/polyratings-data/refs/heads/data/professor-list.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return json.loads(response.text)


# 2026-28 semester GE sub-areas. A student is "done" with GE when every sub-area is
# complete — there is NO separate unit-total or upper-division-unit requirement to pad.
GE_REQUIREMENTS = {
    "1A": "Written Communication",
    "1B": "Critical Thinking",
    "1C": "Oral Communication",
    "Area 2": "Mathematics/Quantitative Reasoning",
    "3A": "Arts",
    "3B": "Humanities",
    "4A": "American Institutions",
    "4B": "Social and Behavioral Sciences",
    "5A": "Physical Science",
    "5B": "Life Science",
    "5C": "Laboratory / Additional Science",
    "Area 6": "Ethnic Studies",
    "Upper-Div 2/5": "Upper-Division Quantitative/Science",
    "Upper-Div 3": "Upper-Division Arts/Humanities",
    "Upper-Div 4": "Upper-Division Social Sciences",
}

# Sub-areas typically satisfied by CS major/support courses rather than standalone GE.
MAJOR_SATISFIED_GE_AREAS = [
    "Area 2",
    "5A",
    "5B",
    "5C",
    "Upper-Div 2/5",
    "Upper-Div 3",
]

COURSE_RE = re.compile(r"\b(CSC|CPE|MATH|STAT|PHIL|WGQS)\s*-?\s*(\d{3,4})\b", re.IGNORECASE)

STOP_WORDS = {
    "about",
    "after",
    "and",
    "are",
    "can",
    "class",
    "classes",
    "course",
    "courses",
    "did",
    "for",
    "from",
    "have",
    "help",
    "into",
    "next",
    "not",
    "now",
    "one",
    "plan",
    "quarter",
    "semester",
    "should",
    "take",
    "taken",
    "tell",
    "that",
    "the",
    "this",
    "what",
    "when",
    "which",
    "with",
}


@dataclass
class RagDocument:
    id: str
    kind: str
    title: str
    text: str
    keywords: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RagResult:
    context: str
    sources: list[str]
    documents: list[RagDocument]

    def __bool__(self):
        return bool(self.context.strip())


def retrieve_rag_context(query, professors=None, top_k=8):
    """Return compact advising context relevant to the user's query."""
    documents = _build_static_documents()
    if professors:
        documents.extend(_build_professor_documents(professors))

    tokens = _tokenize(query)
    course_codes = _extract_course_codes(query)
    query_lower = query.lower()
    query_departments = _query_departments(query, course_codes)

    scored = []
    for doc in documents:
        score = _score_document(doc, query_lower, tokens, course_codes, query_departments)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = []
    seen = set()

    for _, doc in scored:
        if doc.id in seen:
            continue
        selected.append(doc)
        seen.add(doc.id)
        if len(selected) >= top_k:
            break

    if not selected:
        return RagResult(context="", sources=[], documents=[])

    context = "\n".join(f"- [{doc.kind}] {doc.title}: {doc.text}" for doc in selected)
    sources = [doc.id for doc in selected]
    return RagResult(context=context, sources=sources, documents=selected)


def add_rag_context_to_message(message, rag_result):
    """Inject retrieved context while keeping stored chat history clean."""
    if not rag_result:
        return message

    return (
        f"{message}\n\n"
        "[Retrieved advising context]\n"
        f"{rag_result.context}\n"
        "[/Retrieved advising context]"
    )


def retrieve_relevant_professors(query, professors, top_k=5):
    """Compatibility helper for older professor-only RAG call sites."""
    rag_result = retrieve_rag_context(query, professors=professors, top_k=max(top_k, 8))
    relevant = [
        doc.metadata["professor"]
        for doc in rag_result.documents
        if doc.kind == "professor" and "professor" in doc.metadata
    ]
    return relevant[:top_k]


def _build_static_documents():
    documents = [
        RagDocument(
            id="degree-requirements",
            kind="requirement",
            title="CS degree requirements overview",
            text=(
                "The CS degree requires major courses, support courses, a senior project, "
                f"{CS_REQUIREMENTS['technical_electives']}, and "
                f"{CS_REQUIREMENTS['total_units']} total units."
            ),
            keywords={"degree", "requirements", "graduation", "graduate", "roadmap", "plan"},
        ),
        RagDocument(
            id="ge-requirements",
            kind="ge",
            title="GE requirements",
            text=(
                "2026-28 semester GE is satisfied by completing every sub-AREA below; "
                "there is NO unit-total or upper-division-unit padding requirement. "
                "Sub-areas (new codes): "
                + "; ".join(f"{area}: {name}" for area, name in GE_REQUIREMENTS.items())
                + ". Typically satisfied by major/support courses: "
                + ", ".join(MAJOR_SATISFIED_GE_AREAS)
                + ". Discontinued buckets (now free elective units, never list as unmet): "
                + ", ".join(DISCONTINUED_GE_AREAS.keys())
                + "."
            ),
            keywords={"ge", "ges", "general", "education", "area", "areas"},
        ),
    ]

    for category, courses in CS_REQUIREMENTS.items():
        if not isinstance(courses, list):
            continue

        for course in courses:
            code = _extract_first_course_code(course)
            name = COURSE_NAMES.get(code, course)
            prereqs = PREREQUISITE_CHAIN.get(code, [])
            prereq_text = f" Prerequisites: {', '.join(prereqs)}." if prereqs else ""
            documents.append(
                RagDocument(
                    id=f"requirement-{_slug(category)}-{_slug(course)}",
                    kind="requirement",
                    title=f"{course} requirement",
                    text=f"{course} ({name}) is in {category.replace('_', ' ')}.{prereq_text}",
                    keywords=_tokenize(f"{course} {name} {category} requirement required"),
                )
            )

    for course, prereqs in PREREQUISITE_CHAIN.items():
        name = COURSE_NAMES.get(course, course)
        documents.append(
            RagDocument(
                id=f"prereq-{_slug(course)}",
                kind="prerequisite",
                title=f"{course} prerequisites",
                text=f"{course} ({name}) requires {', '.join(prereqs)}.",
                keywords=_tokenize(f"{course} {name} prerequisites prereqs requires {' '.join(prereqs)}"),
            )
        )

    for entry in QUARTER_TO_SEMESTER:
        old_courses = entry["old"]
        new_courses = entry["new"]
        kind = entry["kind"]
        note = entry.get("note", "")
        old_str = " + ".join(old_courses)
        old_slug = "-".join(_slug(c) for c in old_courses)

        if kind in ("free_elective", "external_elective"):
            label = note or ("Free Electives" if kind == "free_elective" else "Approved External Elective")
            title = f"{old_str} → {label}"
            text = (
                f"Old quarter course {old_str} does NOT satisfy any specific CS major or support "
                f"requirement; it counts as {label}."
            )
        else:
            new_str = " + ".join(new_courses)
            title = f"{old_str} → {new_str}"
            if len(old_courses) > 1:
                text = f"Old quarter courses {old_str} (all required together) map to semester course {new_str}."
            else:
                text = f"Old quarter course {old_str} maps to semester course {new_str}."
            if note:
                text += f" Note: {note}."

        documents.append(
            RagDocument(
                id=f"mapping-{old_slug}",
                kind="course-mapping",
                title=title,
                text=text,
                keywords=_tokenize(
                    f"{old_str} {' '.join(new_courses)} {note} old quarter semester mapping"
                ),
            )
        )

    for area, name in GE_REQUIREMENTS.items():
        documents.append(
            RagDocument(
                id=f"ge-{_slug(area)}",
                kind="ge",
                title=f"GE Area {area}",
                text=f"GE Area {area} is {name}.",
                keywords=_tokenize(f"GE Area {area} {name} general education"),
            )
        )

    return documents


# Department-context aliases: a department mentioned in the query (key) is considered
# equivalent to the set of subject prefixes professors actually teach under (values).
# Used only as a light scoring tiebreaker, never as a filter.
DEPARTMENT_ALIASES = {
    "WGQS": {"WGQS", "WGS", "WS", "WGSS"},
}


def _course_departments(courses):
    """Subject prefixes (e.g. 'WS', 'CSC') from a professor's course list."""
    departments = set()
    for course in courses or []:
        match = re.match(r"\s*([A-Za-z]+)", str(course))
        if match:
            departments.add(match.group(1).upper())
    return departments


def _query_departments(query, course_codes):
    """Department context from the query: subjects in explicit course codes plus any
    bare department mentions, each expanded through DEPARTMENT_ALIASES."""
    departments = set()
    for code in course_codes:
        departments.add(code.split()[0].upper())

    query_lower = query.lower()
    for dept in DEPARTMENT_ALIASES:
        if re.search(rf"\b{re.escape(dept.lower())}\b", query_lower):
            departments.add(dept)

    expanded = set(departments)
    for dept in departments:
        expanded |= DEPARTMENT_ALIASES.get(dept, set())
    return expanded


def _build_professor_documents(professors):
    documents = []

    for professor in professors:
        first = str(professor.get("firstName", "")).strip()
        last = str(professor.get("lastName", "")).strip()
        name = " ".join(part for part in [first, last] if part) or "Unknown professor"
        courses = professor.get("courses", []) or []
        course_text = ", ".join(courses[:12]) if courses else "No listed courses"
        tag_text = _format_tags(professor.get("tags"))
        detail_text = _format_professor_details(professor)

        parts = [f"Courses taught: {course_text}."]
        if detail_text:
            parts.append(detail_text)
        if tag_text:
            parts.append(f"Tags: {tag_text}.")

        # Individual name words (handles multi-word names like "Del Rio"), lowercased,
        # so a query mentioning any single first/last name word matches reliably.
        name_tokens = {
            word.lower()
            for word in re.findall(r"[a-zA-Z]+", f"{first} {last}")
            if len(word) >= 2
        }
        documents.append(
            RagDocument(
                id=f"professor-{_slug(name)}",
                kind="professor",
                title=name,
                text=" ".join(parts),
                keywords=_tokenize(f"{name} {' '.join(courses)} {tag_text}"),
                metadata={
                    "professor": professor,
                    "name_tokens": name_tokens,
                    "departments": _course_departments(courses),
                },
            )
        )

    return documents


def _score_document(doc, query_lower, tokens, course_codes, query_departments=frozenset()):
    haystack = f"{doc.title} {doc.text}".lower()
    score = 0

    for course_code in course_codes:
        if course_code.lower() in haystack:
            score += 12

    for token in tokens:
        if token in doc.keywords:
            score += 4
        elif token in doc.title.lower():
            score += 3
        elif token in haystack:
            score += 1

    # A direct first/last name token match is the strongest possible signal — a query
    # that names a professor (even just a bare last name) must surface that professor.
    name_match = False
    if doc.kind == "professor":
        name_tokens = doc.metadata.get("name_tokens", set())
        if name_tokens & tokens:
            name_match = True
            score += 40

    professor_intent = name_match or _has_any(
        query_lower,
        (
            "professor",
            "prof",
            "teacher",
            "instructor",
            "rating",
            "polyratings",
            "teach",
            "teaches",
            "taught",
            "take with",
        ),
    ) or ("who" in query_lower and bool(course_codes))

    if professor_intent:
        if doc.kind == "professor" and score > 0:
            score += 10

    # Light department-context tiebreaker: when the query references a department/course,
    # nudge already-relevant professors who teach in that department higher. Gated on
    # score > 0 so it re-ranks real matches rather than introducing unrelated professors.
    if doc.kind == "professor" and query_departments and score > 0:
        if doc.metadata.get("departments", set()) & query_departments:
            score += 8

    if _has_any(query_lower, ("prereq", "prerequisite", "requires", "before")):
        if doc.kind == "prerequisite":
            score += 5

    if _has_any(query_lower, ("ge", "general education", "area")):
        if doc.kind == "ge":
            score += 5

    if _has_any(query_lower, ("roadmap", "graduate", "graduation", "degree", "requirements")):
        if doc.kind == "requirement":
            score += 4

    if _has_any(query_lower, ("old", "quarter", "semester", "map", "mapping")):
        if doc.kind == "course-mapping":
            score += 4

    return score


def _extract_course_codes(query):
    codes = set()
    for subject, number in COURSE_RE.findall(query):
        code = f"{subject.upper()} {number}"
        codes.add(code)
        codes.update(_OLD_TO_NEW.get(code, set()))

    # Resolve natural-language aliases like "Calc 1" -> MATH 141 -> semester equivalents.
    query_lower = query.lower()
    for alias, code in COURSE_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", query_lower):
            codes.add(code)
            codes.update(_OLD_TO_NEW.get(code, set()))
    return codes


def _extract_first_course_code(value):
    match = COURSE_RE.search(str(value))
    if not match:
        return str(value)
    return f"{match.group(1).upper()} {match.group(2)}"


def _tokenize(value):
    tokens = set()
    for token in re.findall(r"[a-zA-Z0-9]+", str(value).lower()):
        if token in STOP_WORDS:
            continue
        if len(token) >= 3 or token in {"cs", "ge"}:
            tokens.add(token)
    return tokens


def _format_tags(tags):
    if not tags:
        return ""

    if isinstance(tags, dict):
        sorted_tags = sorted(tags.items(), key=lambda item: _tag_sort_value(item[1]), reverse=True)
        return ", ".join(
            f"{tag} ({count})" if count not in (None, "") else str(tag)
            for tag, count in sorted_tags[:8]
        )

    if isinstance(tags, list):
        return ", ".join(str(tag) for tag in tags[:8])

    return str(tags)


def _format_professor_details(professor):
    ignored = {"firstName", "lastName", "courses", "tags", "id", "slug"}
    details = []

    for key, value in professor.items():
        if key in ignored or value in (None, "", [], {}):
            continue
        if isinstance(value, (str, int, float, bool)):
            details.append(f"{_humanize_key(key)}: {value}")

    return " ".join(f"{detail}." for detail in details[:8])


def _tag_sort_value(value):
    if isinstance(value, (int, float)):
        return value
    return 0


def _humanize_key(key):
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(key)).replace("_", " ")
    return words.lower()


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def _has_any(value, needles):
    return any(needle in value for needle in needles)

import json
import os
import re
from datetime import date

import requests
from flask import Flask, render_template, request, jsonify, session
from anthropic import Anthropic
from dotenv import load_dotenv
from requirements import (
    CS_REQUIREMENTS, PREREQUISITE_CHAIN, COURSE_NAMES, TERM_OFFERED, AP_CREDIT,
    COURSE_ALIASES, SEQUENCE_REQUIREMENTS,
    GE_AREA_CROSSWALK, DISCONTINUED_GE_AREAS, COURSE_GE_AREA,
)
from rag import add_rag_context_to_message, get_professors, retrieve_rag_context
from roadmap_validator import validate_roadmap

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def _next_term():
    today = date.today()
    return f"Fall {today.year}" if today.month <= 8 else f"Spring {today.year + 1}"


def build_system_prompt():
    today = date.today()
    next_term = _next_term()
    return f"""You are a Cal Poly SLO academic advisor chatbot.
You help CS students plan courses, check prerequisites, and choose professors.

Today's date: {today.strftime("%B %d, %Y")}. Earliest plannable term: {next_term}.
NEVER include any term before {next_term} in a roadmap. If asked about past terms, note they have already passed.

Official CS degree requirements: {json.dumps(CS_REQUIREMENTS)}
Prerequisite chains: {json.dumps(PREREQUISITE_CHAIN)}
Course names: {json.dumps(COURSE_NAMES)}
Terms each course is offered (F=Fall, SP=Spring, SU=Summer): {json.dumps(TERM_OFFERED)}
Only place a course in a term listed for it above. If a course isn't offered in a requested term, move it to the next term where it is.

Roadmap course-load balancing (CRITICAL — do not just pack terms because prerequisites allow it):
- Major CS courses (CSC/CPE) are demanding. Do NOT stack more than ~2-3 of them in one term. Default to a soft cap of 3 major CS courses per term, and prefer 2 when the term's courses are especially heavy.
- Spread demanding courses across the plan rather than front-loading. A lighter term, or pairing fewer CS courses with a support/GE/elective course, is better than a term with 3-4 major CS courses at once.
- If the student states a preferred maximum number of CS courses per semester, treat it as a HARD cap and honor it exactly (even if it lengthens the plan), overriding the default soft cap.
- Still respect prerequisite chains and term offerings. Balancing load and hitting the graduation target can genuinely conflict for a tight timeline: when they do, NEVER resolve it silently. Do NOT silently overload a term past the cap, and do NOT silently push graduation later than the target. Instead, explicitly flag the tradeoff and present the options (e.g. add a summer term, extend graduation by a term, or accept one heavier-than-preferred semester) and let the student choose.
- When building a roadmap, ask the student's preferred CS-courses-per-term cap (offer the 2-3 default) before finalizing.

AP credit table (structure: AP_CREDIT[year][exam][min_score], covers years {sorted(AP_CREDIT.keys())}): {json.dumps(AP_CREDIT)}

AP credit rules:
- Score < 3: no credit awarded for that exam.
- Per-exam year: each exam the student lists may have its own matrix year. Ask for the year if not provided; default to 2024 if unclear.
- Tier lookup: within AP_CREDIT[year][exam_name], find the highest score key ≤ student's score.
- courses in each entry: if the code appears in QUARTER_TO_SEMESTER (e.g. CSC 123, MATH 141, PHYS 141), apply that mapping to get the semester equivalent. Otherwise use the code directly (e.g. PHYS 104 stays as PHYS 104). Then check CS_REQUIREMENTS — if the resulting course is NOT listed there, it does NOT satisfy any CS major or support requirement.
- ge_areas use CSU GE notation (A2, B3, B4, C2 etc.) — distinct from Cal Poly's numbered GE areas.
- title5 entries (US-1, US-2) satisfy Title 5 U.S. history/government requirements, not standard GE areas.
- DUPLICATION: If a student also took a course from "courses" IN CLASS, that AP course credit converts to elective units only — do NOT double-count.
- COMBINATION: For paired exams (English Lang + English Lit; Calc AB + Calc BC; CS A + CS Principles; Physics 1 + Physics 2), use the matrix year of the later-dated exam for the lookup; only one set of course credits applies; the second exam's course credits convert to additional elective units.
- Surface any "notes" field from the entry verbatim to the student.
- DISCLAIMER: This table covers Cal Poly SLO AP matrices for years {sorted(AP_CREDIT.keys())}. For other exam years, direct students to verify with the Registrar.

Quarter-to-semester course mappings (CRITICAL — use these exactly):
Major: CSC 101→CSC 1001 | CSC 123→CSC 1000+CSC 1024 | CSC 202→CSC 2001
CSC 203→FREE ELECTIVE (does NOT satisfy any major requirement)
CSC 357→CSC 2050 | CSC 225→CPE 2300 | CSC 364 or 464→CSC 3001
CSC 307→CSC 3100 | CSC 308+309→CSC 3100 | CSC 321/323/325→CSC 3201
CSC 430→CSC 3300 | CSC 349→CSC 3449 | CSC 453→CSC 4553
CSC 491+492→CSC 4460 (senior project)
Tech electives: CSC 469→CSC 4669 | CSC 365→CSC 3665 | CSC 445→CSC 3445
Support: CSC 248→MATH 2031 | CSC 300/PHIL 323→PHIL 3323
MATH 206/244→MATH 1151 | MATH 141+142+143→MATH 1261+MATH 1262
STAT 312→STAT 3210 | ES/WGQS 350→WGQS 3350 | ES/WGQS 351→WGQS 3351
PHYS 141→PHYS 1141 | CHEM 124→CHEM 1120
Non-satisfying: PHYS 142/143, CHEM 125/126, BIO 111/161, BOT 121, MCRO 221 → Approved External Electives (do NOT count toward named CS requirements)

Course aliases (natural language → quarter course): {json.dumps(COURSE_ALIASES)}
When a student says "Calc 1/2/3" they mean the quarter courses MATH 141/142/143 respectively.

Sequence requirements (jointly satisfied sets): {json.dumps(SEQUENCE_REQUIREMENTS)}
Calculus sequence rule (CRITICAL):
- MATH 141 + MATH 142 + MATH 143 together satisfy BOTH semester MATH 1261 AND MATH 1262.
- Each member of the sequence may be earned by an in-class course OR by AP credit.
- AP Calculus AB grants MATH 141 (the student has "tested out" of 141). This COMBINES with in-class MATH 142 and MATH 143 to complete the full sequence.
- Therefore a student with AP Calc AB + MATH 142 + MATH 143 has satisfied BOTH MATH 1261 and MATH 1262. Do NOT flag the AP Calc AB MATH 141 as a duplication of the in-class 142/143 — those are different courses that combine. Do NOT leave MATH 1261 unmet in this case.
- Only flag duplication if the SAME member is earned twice (e.g. AP Calc AB MATH 141 AND an in-class MATH 141); then the AP credit becomes elective units only.
- A partial sequence (e.g. only MATH 141 from AP) does NOT yet satisfy MATH 1261/1262 — the student still needs the remaining members.

GENERAL EDUCATION (2026-28 semester catalog) — use this authoritative logic, not guesses:

Official GE area crosswalk (old quarter area → new semester area): {json.dumps(GE_AREA_CROSSWALK)}
This student's per-course GE crediting (area approved WHEN TAKEN → crosswalk → new area): {json.dumps(COURSE_GE_AREA)}
Discontinued quarter GE buckets (course → FREE ELECTIVE UNITS only, NOT a GE area): {json.dumps(DISCONTINUED_GE_AREAS)}

Critical GE rules:
- A course earns GE credit for the area it was approved for WHEN TAKEN, then converts via the crosswalk. Report GE status in NEW SEMESTER AREA CODES ONLY (e.g. "1A", "Area 2", "5C", "Area 6", "Upper-Div 4").
- DISCONTINUED: Lower-Division Area C elective, Area E, and GE Electives no longer exist. A course that only satisfied one of those now counts as FREE ELECTIVE UNITS. NEVER list these as unmet GE areas.
- NO UNIT DEFICITS: Per official policy, students are NOT required to take extra courses to reach 43 GE units or 9 upper-division GE units once all sub-areas are complete. NEVER warn about a GE unit shortfall — flag only unmet sub-AREAS.
- TABLE-ONLY SATISFACTION: Mark a sub-area satisfied ONLY when a course/AP in the data above maps to it. If a course's area is "confirmed": false (or otherwise unknown), say it is "unverified, confirm" — do NOT assert it as satisfied.
- AP GE areas also convert via the crosswalk (e.g. AP Calc AB B4 → Area 2; AP Physics 1 B3 → 5C; AP English Lit score 5 A2+C2 → 1A+3B). Run AP ge_areas through GE_AREA_CROSSWALK before reporting.
- DOUBLE-COUNTING: A single course can satisfy multiple requirements at once (e.g. PHIL 323 counts as BOTH the PHIL 3323 support course AND GE 3B). This is allowed — do not treat one use as cancelling the other.

DPR (Degree Progress Report) authority:
- If a student provides DPR statuses (what their official report already shows as satisfied), TRUST those as authoritative. They already account for double-counting and institutional exceptions. Report from them directly — do NOT recompute, second-guess, or "correct" a satisfied status based on your own mapping.
- Only fall back to the crosswalk/credit tables for items the DPR does not cover, or when no DPR is provided.

PolyRatings links (CRITICAL — never fabricate URLs):
- NEVER invent or construct a professor-specific PolyRatings URL (e.g. polyratings.dev/professor/<name>, /prof/<id>, etc.). These do not exist as you'd guess and will 404.
- Present the actual ratings data you retrieved (overall rating, evaluation count, tags, courses) directly in your answer. That retrieved data IS the deliverable — do not redirect the student to a link to find it.
- If you reference PolyRatings as a site, use ONLY the base search URL https://polyratings.dev and tell the student they can search the name there. Otherwise omit links entirely.
- NO MATCH: If a professor name returns no retrieved PolyRatings data, do NOT just say "no data." Note that the name may be a spelling variation or different spelling, and ask the student to double-check/confirm the spelling (e.g. accents, hyphens, first vs. last name). Do NOT guess at, approximate, or substitute a similarly-spelled professor — only report data for an exact match, and otherwise prompt the student to verify the name.

Conversation guidelines:
1. Ask for major and completed courses (including GEs) upfront
2. Identify which GE sub-areas are satisfied using the GE crosswalk and per-course GE table; report new semester area codes only, never warn about GE unit deficits, and mark unverified areas as "confirm"
3. Recommend next quarter options based on prerequisites
4. When professors are mentioned, look them up by last name in PolyRatings data
5. Ask about preferences before recommending professors
6. For roadmap requests: ask graduation year, courses per semester, and preferred max CS courses per term, then plan all the way to graduation respecting prerequisite chains, term offerings, and course-load balancing — flagging any tradeoff between spreading hard courses and the graduation target
7. When a student reports AP scores, apply the AP credit table systematically: state each exam's result, flag any duplications or combination conflicts, show the semester equivalent of each quarter course granted, and always include the matrix-year disclaimer.
8. When a student provides DPR (Degree Progress Report) statuses, treat them as the authoritative source of what is satisfied — they already reflect double-counting — and report from them rather than recomputing.

You may receive a [Retrieved advising context] block after the user's message.
Use that context as the grounded source for course, prerequisite, GE, course mapping,
and professor questions. If the retrieved context is not enough, ask a concise
follow-up question instead of inventing details.
Always be concise and conversational. Never respond in JSON."""

# Load professor data once at startup. If PolyRatings is unavailable, course RAG still works.
try:
    all_professors = get_professors()
except (requests.RequestException, json.JSONDecodeError) as exc:
    print(f"Could not load PolyRatings data: {exc}")
    all_professors = []
system_prompt = build_system_prompt()

# ---- Roadmap validation loop ----
#
# We don't trust the model's roadmap blindly. The model is asked (per-message, so
# the shared system prompt in advisor.py/app.py stays untouched) to append a
# machine-readable <roadmap-json> block whenever it produces a multi-term plan. We
# parse that block, run validate_roadmap on it, and if it has violations we feed
# them back and ask the model to fix the plan — capped at MAX_ROADMAP_RETRIES so a
# stubborn model can't loop or run up cost. The block is stripped before display.

ROADMAP_OPEN = "<roadmap-json>"
ROADMAP_CLOSE = "</roadmap-json>"
MAX_ROADMAP_RETRIES = 2

ROADMAP_INSTRUCTION = (
    "\n\n[System note] If your reply contains a concrete multi-term course plan (a "
    "roadmap), append ONE machine-readable block at the very end, in EXACTLY this "
    "form and nothing after it:\n"
    f'{ROADMAP_OPEN}{{"terms": [{{"term": "Fall 2026", "courses": ["CSC 1001"]}}]}}{ROADMAP_CLOSE}\n'
    "Use new semester course codes and \"<Season> <Year>\" term labels that match "
    "the plan you described. If your reply is not a multi-term plan, do NOT include "
    "the block."
)


def _extract_roadmap(text):
    """Return the parsed roadmap dict from a <roadmap-json> block, or None."""
    start = text.find(ROADMAP_OPEN)
    end = text.find(ROADMAP_CLOSE)
    if start == -1 or end == -1 or end < start:
        return None
    raw = text[start + len(ROADMAP_OPEN):end].strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and isinstance(data.get("terms"), list):
        return data
    return None


def _strip_roadmap_block(text):
    """Remove the machine-readable block so the student only sees prose."""
    pattern = re.escape(ROADMAP_OPEN) + r".*?" + re.escape(ROADMAP_CLOSE)
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _validation_feedback(violations):
    return (
        "The structured roadmap you provided failed automated validation. Fix every "
        "issue below, keeping the student's stated constraints and respecting "
        "prerequisite order, term offerings, and the earliest plannable term:\n"
        + "\n".join(f"- {v}" for v in violations)
        + "\n\nResend BOTH your conversational reply and a corrected "
        f"{ROADMAP_OPEN}...{ROADMAP_CLOSE} block."
    )


def _generate_validated_reply(messages, earliest_term):
    """Call the model and, if it emits a roadmap with violations, ask it to fix the
    plan (up to MAX_ROADMAP_RETRIES). Return the final raw reply (block included)."""
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4096,
        system=system_prompt, messages=messages,
    )
    reply = response.content[0].text
    convo = list(messages)

    for _ in range(MAX_ROADMAP_RETRIES):
        roadmap = _extract_roadmap(reply)
        if roadmap is None:
            break
        violations = validate_roadmap(roadmap, cs_cap=None, earliest_term=earliest_term)
        if not violations:
            break
        print(f"Roadmap violations, asking model to fix: {violations}")
        convo = convo + [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": _validation_feedback(violations)},
        ]
        response = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=4096,
            system=system_prompt, messages=convo,
        )
        reply = response.content[0].text

    return reply


@app.route("/")
def index():
    session["history"] = []
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"response": "Send me a course planning question and I can help."}), 400

    history = session.get("history", [])

    rag_result = retrieve_rag_context(user_message, professors=all_professors)
    print(f"RAG sources: {rag_result.sources}")
    message_with_context = add_rag_context_to_message(user_message, rag_result)
    message_with_context += ROADMAP_INSTRUCTION

    messages = history + [{"role": "user", "content": message_with_context}]

    raw_reply = _generate_validated_reply(messages, earliest_term=_next_term())
    assistant_message = _strip_roadmap_block(raw_reply)

    # Store the clean user message and the student-facing (block-stripped) reply.
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_message})

    session["history"] = history

    return jsonify({"response": assistant_message})

if __name__ == "__main__":
    app.run(debug=True)

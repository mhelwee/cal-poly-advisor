# Cal Poly AI Academic Advisor

**Live demo:** <URL>  (replace after deploy)

An AI academic advisor for Cal Poly SLO Computer Science students. It plans courses,
applies transfer and AP credit, tracks General Education progress, and recommends
professors from live ratings data - all through a natural, multi-turn conversation.

Built with **Python**, **Flask**, and the **Anthropic API** (Claude). It ships as both a
web app and a terminal app sharing one retrieval and advising core.

## What it does

- **Quarter → semester course mapping.** Translates legacy quarter courses to the new
  semester catalog, including one-to-one, combination (e.g. `CSC 308 + CSC 309 → CSC 3100`),
  and "free elective only" cases.
- **AP credit.** Applies year-specific AP matrices (2023 / 2024 / 2025), each exam scored
  against its minimum-passing tier, with **duplication** rules (no double credit for a
  course already taken) and **combination** rules (e.g. AP Calc AB supplies one course in
  the MATH sequence and combines with in-class courses rather than conflicting).
- **GE crosswalk.** Converts old quarter GE areas to the 2026-28 semester areas using the
  official crosswalk, recognizes **discontinued** buckets as free electives (never flagged
  as unmet), and reports status in new semester area codes. Trusts a student's Degree
  Progress Report (DPR) statuses as authoritative when provided.
- **Prerequisites and term offerings.** Checks prerequisite chains and only schedules a
  course in a term it is actually offered.
- **Roadmap planning with code-verified output.** Builds a multi-semester plan toward
  graduation, respecting prerequisites, term availability, and a target graduation date.
  The generated plan is then **validated in code** — prerequisite order, term offerings, a
  per-term CS-course cap when the student states one, no past terms, and no duplicate
  courses — and regenerated if it fails any check, so the plan the student sees has been
  verified rather than taken on the model's word.
- **Professor recommendations.** Pulls live **PolyRatings** data and recommends instructors
  matched by the courses they actually teach — not by home department, so cross-listed
  instructors still surface — then ranked against the student's stated preferences (e.g.
  recorded lectures, workload, grading).

## Architecture

The advising knowledge lives in structured Python data ([requirements.py](requirements.py))
and a retrieval layer ([rag.py](rag.py)) that grounds the model on only the relevant facts
per question.

**RAG retrieval layer ([rag.py](rag.py)):**

1. **Knowledge base.** At query time the system assembles a set of documents: degree
   requirements, prerequisite chains, course mappings, GE areas, and one document per
   professor (built from live PolyRatings data, all departments).
2. **Per-query relevance scoring.** Each document is scored lexically against the query:
   course-code matches, keyword/title overlap, professor name-token matches (a dominant
   signal so a bare last name reliably surfaces that professor), and intent boosts for
   prerequisite / GE / roadmap / professor questions.
3. **Top matches into the prompt.** The highest-scoring documents (top 8) are injected into
   the message as a compact `[Retrieved advising context]` block, so the model answers from
   grounded data instead of the entire dataset.

This is **lexical retrieval, not vector embeddings**, a deliberate scope choice. The
dataset is bounded and largely keyed by course codes and proper names, where exact lexical
matching is precise, transparent, and dependency-free. Embeddings would add infrastructure
and opacity without meaningfully improving recall on this corpus.

**Roadmap validation loop ([roadmap_validator.py](roadmap_validator.py)):**

Correctness-critical output is **verified in code, not trusted from the model**. The model
emits the plan as structured JSON — including the per-term CS-course cap it understood the
student to want — and [roadmap_validator.py](roadmap_validator.py), a pure, dependency-free
module, checks it against the *same* prerequisite and term-offering data used everywhere
else: prerequisite ordering, term offerings, the CS cap, no terms in the past, and no
duplicate courses. Any violations are fed back to the model to fix, and the plan is
re-validated, with retries capped to avoid loops or runaway cost. The cap is the pattern in
miniature: the model extracts the constraint from natural language ("max 2 CS courses a
term"), and code enforces it deterministically — catching the model if it contradicts its
own stated understanding. Courses outside the bounded requirement data are skipped rather
than false-flagged, and the checks are covered by unit tests in
[test_roadmap_validator.py](test_roadmap_validator.py).

**Conversation:** Both entry points keep multi-turn context (the Flask app per session,
the terminal app per process), so follow-up questions work naturally.

## Skills demonstrated

- **Prompt engineering:** structured system prompts that encode advising rules and control behavior
- **Structured outputs:** the model emits roadmaps as structured JSON that drives a code-based validation step, not just free text
- **Output verification / guardrails:** correctness-critical LLM output is constrained to a schema and checked in code (the roadmap validator), with invalid plans regenerated rather than shown
- **Agent design:** multi-turn conversation with persistent context, plus a generate → validate → regenerate loop for roadmaps
- **API economics:** the large, static advising knowledge base is sent with a prompt-cache marker so it is cached across turns — a deliberate choice that cuts per-message cost and latency
- **Retrieval-augmented generation:** per-query lexical retrieval that grounds responses
- **REST API integration:** the Anthropic API for the conversational core
- **External data integration:** live professor ratings from PolyRatings

## How to run

1. Clone the repo.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```
4. **Web app:** `python app.py`, then open `http://localhost:5000`.
5. **Terminal app:** `python advisor.py`.

## Deployment

The web app runs under **gunicorn** via the included `Procfile` (`web: gunicorn app:app`) and
needs `ANTHROPIC_API_KEY` and `SECRET_KEY` set in the host environment. Sessions are stored
**server-side (filesystem)**, so long multi-turn histories aren't lost to the ~4KB browser
cookie limit, and transient Anthropic API errors degrade gracefully — the student is asked to
resend rather than hitting a failed page.

## How to use

Talk to the advisor in plain language. Describe your completed courses, your AP scores
(include each exam's year so the correct matrix applies), and any GE areas your DPR already
confirms; then ask for a multi-semester roadmap or next-term recommendations. For professor
recommendations, tell it which professors are offered for the course and what matters to you
(workload, grading, recorded lectures); it ranks the real PolyRatings options against your
preferences rather than guessing who is teaching.

Example exchange:

> **You:** I've finished CSC 2001 and CSC 2050, got a 4 on AP Calc AB (2024), and my DPR shows
> GE 1A and 1B done. Plan a roadmap to graduate Spring 2028, max 2 CS courses per term.
>
> **Advisor:** Got it. AP Calc AB (2024) credits MATH 141 toward the calculus sequence, and
> 1A/1B are set per your DPR. Here's a balanced term-by-term plan that stays at 2 CS courses
> per semester, respects prerequisites and term offerings, and still reaches Spring 2028...

## Project structure

- [app.py](app.py): Flask web app (session-based conversation)
- [advisor.py](advisor.py): terminal chatbot
- [rag.py](rag.py): retrieval layer (PolyRatings fetch, document building, relevance scoring)
- [requirements.py](requirements.py): advising knowledge base (degree requirements,
  prerequisites, quarter→semester mappings, AP credit matrices, GE crosswalk, term offerings)
- [roadmap_validator.py](roadmap_validator.py): pure roadmap validation (prerequisite order,
  term offerings, per-term CS-course cap, past terms, duplicates) used to verify generated plans
- [test_roadmap_validator.py](test_roadmap_validator.py): unit tests for the roadmap validator
- [templates/index.html](templates/index.html): chat UI with Markdown rendering (tables, lists)
- [requirements.txt](requirements.txt): Python dependencies
- [Procfile](Procfile): process definition for gunicorn-based deployment

## Limitations

- Does **not** compute full 120-unit degree totals or unit-by-unit completion accounting;
  it tracks requirements and sub-areas, not running unit sums.
- Covers the **general CS curriculum only** (no concentrations or specialized tracks).
- AP and GE results are only as accurate as the matrices and DPR statuses provided; the
  bundled AP matrices cover specific years, and other years should be verified with the
  registrar.
- PolyRatings reflects whatever ratings exist on the source; instructors with no ratings
  return no data rather than fabricated results.

## Built by

Marc Helwee, Cal Poly SLO Computer Science

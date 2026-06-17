# Cal Poly AI Academic Advisor

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
- **Roadmap planning.** Builds a multi-semester plan toward graduation, respecting
  prerequisites, term availability, and a target graduation date, never scheduling a term
  in the past.
- **Professor recommendations.** Pulls live **PolyRatings** data and recommends instructors
  filtered by the student's stated course and preferences (e.g. recorded lectures,
  workload, grading), with a light department-context tiebreaker for ambiguous names.

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

**Conversation:** Both entry points keep multi-turn context (the Flask app per session,
the terminal app per process), so follow-up questions work naturally.

## Skills demonstrated

- **Prompt engineering:** structured system prompts that encode advising rules and control behavior
- **Structured outputs:** machine-usable structured data driving the advising logic
- **Agent design:** multi-turn conversation with persistent context
- **Retrieval-augmented generation:** per-query lexical retrieval that grounds responses
- **REST API integration:** the Anthropic API for the conversational core
- **External data integration:** live professor ratings from PolyRatings

## How to run

1. Clone the repo.
2. Install dependencies:
   ```
   pip install anthropic python-dotenv requests flask
   ```
3. Create a `.env` file in the project root with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```
4. **Web app:** `python app.py`, then open `http://localhost:5000`.
5. **Terminal app:** `python advisor.py`.

## Project structure

- [app.py](app.py): Flask web app (session-based conversation)
- [advisor.py](advisor.py): terminal chatbot
- [rag.py](rag.py): retrieval layer (PolyRatings fetch, document building, relevance scoring)
- [requirements.py](requirements.py): advising knowledge base (degree requirements,
  prerequisites, quarter→semester mappings, AP credit matrices, GE crosswalk, term offerings)
- [templates/index.html](templates/index.html): chat UI with Markdown rendering (tables, lists)

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

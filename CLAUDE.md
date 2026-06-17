# CLAUDE.md

Guidance for Claude when working in this repo.

## Project

AI academic advisor for Cal Poly SLO **Computer Science** students (general curriculum,
no concentrations). Plans courses, applies transfer/AP credit, tracks GE progress, and
recommends professors from live PolyRatings data — via a multi-turn chat.

Stack: **Python + Flask + Anthropic API** (model `claude-sonnet-4-6`).

## Architecture

- **`requirements.py`** — single source of truth for all advising data (plain Python
  structures). Includes: `CS_REQUIREMENTS`, `PREREQUISITE_CHAIN`, `COURSE_NAMES`,
  `QUARTER_TO_SEMESTER` (legacy→semester course mapping, incl. combination & free-elective
  cases), `COURSE_ALIASES` + `SEQUENCE_REQUIREMENTS` (e.g. Calc 1/2/3 → MATH 141/142/143),
  `TERM_OFFERED`, `AP_CREDIT` (keyed by matrix year 2023/2024/2025, with duplication &
  combination rules), and GE data: `GE_AREA_CROSSWALK`, `DISCONTINUED_GE_AREAS`,
  `COURSE_GE_AREA`.
- **`rag.py`** — retrieval layer. `get_professors()` fetches **all** PolyRatings professors
  (no department filter). `retrieve_rag_context()` builds requirement/prerequisite/mapping/
  GE/professor documents, scores them **lexically** per query (`_score_document`, `top_k=8`),
  and returns a compact context block injected into the prompt. Name-token matches are a
  dominant signal; there's a light department-context tiebreaker. **Lexical retrieval is a
  deliberate choice — do NOT introduce vector embeddings** (bounded, code/name-keyed dataset).
- **`app.py`** — Flask web app (session-based history). **`advisor.py`** — terminal app.
  Both build a large system prompt from `requirements.py` data and call the API.
- **`templates/index.html`** — chat UI; renders advisor Markdown via marked.js (user
  messages stay escaped).
- **`professors.py`** — legacy keyword matcher, superseded by `rag.py`; not imported.

## Critical conventions

- **The system prompt is DUPLICATED in `advisor.py` and `app.py`.** Any prompt change must
  be applied to **both** files, kept in sync. (Same for the `get_professors` import, etc.)
- **PolyRatings URL is `https://polyratings.dev`** — never `.com` (parked domain). Never
  fabricate professor-specific URLs; present retrieved ratings directly.
- Advising data changes go in `requirements.py`, then are referenced from both prompts —
  don't hardcode advising facts inline in the prompts.
- When a professor name returns no data, prompt the user to verify spelling; **never** add
  fuzzy/approximate name matching.

## Git / workflow

- **No AI attribution in commits.** Do NOT add `Co-Authored-By: Claude` or any AI trailer.
  A local `commit-msg` hook strips these as a backstop; commit as the user only.
- Author identity: `Marc Helwee <marc@helwee.com>` (global git config).
- `.env` holds `ANTHROPIC_API_KEY` and is gitignored — never stage or commit it.
- Two remote branches exist: `main` (active) and `master` (older parallel history).

## Running & testing

- Web: `python app.py` → `http://localhost:5000`. Terminal: `python advisor.py`.
- Verify changes by restarting Flask and POSTing to `/chat`, or via direct `rag.py` calls.
- **This Windows machine intermittently throws Git Bash fork errors** — if the Bash tool
  fails with a `fork`/`add_item` error, re-run the command via PowerShell (works reliably).
  `python` is also more reliable via PowerShell than the Bash tool here.

## Limitations (by design)

No full 120-unit total computation; general CS curriculum only; AP/GE accuracy depends on
the bundled matrices and any DPR statuses the student provides.

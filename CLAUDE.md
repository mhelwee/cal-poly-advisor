# CLAUDE.md

Guidance for Claude when working in this repo.

## Project

AI academic advisor for Cal Poly SLO **Computer Science** students (general curriculum,
no concentrations). Plans courses, applies transfer/AP credit, tracks GE progress, and
recommends professors from live PolyRatings data, via a multi-turn chat.

Stack: **Python + Flask + Anthropic API** (model `claude-sonnet-4-6`).

## Architecture

- **`advising_data.py`:** single source of truth for all advising data (plain Python
  structures). Includes: `CS_REQUIREMENTS`, `PREREQUISITE_CHAIN`, `COURSE_NAMES`,
  `QUARTER_TO_SEMESTER` (legacy→semester course mapping, incl. combination & free-elective
  cases), `COURSE_ALIASES` + `SEQUENCE_REQUIREMENTS` (e.g. Calc 1/2/3 → MATH 141/142/143),
  `TERM_OFFERED`, `AP_CREDIT` (keyed by matrix year 2023/2024/2025, with duplication &
  combination rules), and GE data: `GE_AREA_CROSSWALK`, `DISCONTINUED_GE_AREAS`,
  `COURSE_GE_AREA`.
- **`rag.py`:** retrieval layer. `get_professors()` fetches **all** PolyRatings professors
  (no department filter). `retrieve_rag_context()` builds requirement/prerequisite/mapping/
  GE/professor documents, scores them **lexically** per query (`_score_document`, `top_k=8`),
  and returns a compact context block injected into the prompt. Name-token matches are a
  dominant signal; there's a light department-context tiebreaker. **Lexical retrieval is a
  deliberate choice; do NOT introduce vector embeddings** (bounded, code/name-keyed dataset).
- **`advisor_core.py`:** shared advising core — the SINGLE canonical copy of the system
  prompt (`build_system_prompt`) and the roadmap generate→validate→regenerate loop
  (`generate_validated_reply`). No Flask and no Anthropic client at import; the caller passes
  its own `client`. Built from `advising_data.py`.
- **`roadmap_validator.py`:** pure, dependency-free validation of a generated roadmap
  (prerequisite order, term offerings, optional per-term CS cap, no past terms, no
  duplicates); courses outside the bounded data are skipped, not flagged. Tested by
  `test_roadmap_validator.py`; `advisor_core` helpers tested by `test_advisor_core.py`.
- **`app.py`:** Flask web app (session-based history). **`advisor.py`:** terminal app.
  Both import the prompt and validation loop from `advisor_core.py`; each owns only its own
  I/O (RAG context assembly, session/CLI handling) and its own Anthropic `client`.
- **`templates/index.html`:** chat UI; renders advisor Markdown via marked.js (user
  messages stay escaped).

## Critical conventions

- **The system prompt and roadmap validation loop live ONCE in `advisor_core.py`**, imported
  by both `app.py` and `advisor.py` — they are NOT duplicated. Change the prompt or the loop
  in `advisor_core.py` and both interfaces pick it up; never copy this logic back into the
  entry points.
- **PolyRatings URL is `https://polyratings.dev`**, never `.com` (parked domain). Never
  fabricate professor-specific URLs; present retrieved ratings directly.
- Advising data changes go in `advising_data.py`, surfaced through the shared prompt in
  `advisor_core.py`; don't hardcode advising facts inline in the prompt.
- When a professor name returns no data, prompt the user to verify spelling; **never** add
  fuzzy/approximate name matching.

## Git / workflow

- **No AI attribution in commits.** Do NOT add `Co-Authored-By: Claude` or any AI trailer;
  commit as the user only. (A `commit-msg` hook was tried as a backstop but removed: Git runs
  hooks through `sh`, which crashes on this machine's fork bug and blocked every commit.)
- Author identity: `Marc Helwee <marc@helwee.com>` (global git config).
- `.env` holds `ANTHROPIC_API_KEY` and is gitignored; never stage or commit it.
- Remote has a single branch: `main`. (An older `master` branch was deleted.)

## Running & testing

- Web: `python app.py` → `http://localhost:5000`. Terminal: `python advisor.py`.
- Verify changes by restarting Flask and POSTing to `/chat`, or via direct `rag.py` calls.
- **This Windows machine intermittently throws Git Bash fork errors;** if the Bash tool
  fails with a `fork`/`add_item` error, re-run the command via PowerShell (works reliably).
  `python` is also more reliable via PowerShell than the Bash tool here. For pushes, prepend
  `C:\Program Files\Git\mingw64\libexec\git-core` to PATH so git finds the credential manager.

## Gotchas / environment

- **Intermittent Git Bash fork bug.** This machine intermittently fails to fork msys
  processes (`fatal error: add_item ... fork`), which blocks any git operation that spawns a
  helper through `sh`/`bash`: notably `push` (credential helper) and `rebase --continue` (the
  editor spawn). It is intermittent, so the same command may succeed on a later try.
- **Reliable push workaround when it flares:** `git -c credential.helper=wincred push`. The
  native `wincred` binary reads the credential from Windows Credential Manager directly
  instead of spawning the GCM (`manager-core`) helper through `sh`.
- **If a rebase hangs on the editor spawn:** it can leave hung `git` processes. Kill them
  (`Get-Process git,sh,bash | Stop-Process -Force`) and clear any stale `.git/index.lock`
  before retrying `git rebase --continue`. Using a no-op editor (`GIT_EDITOR=true`) lets the
  continue reuse the existing commit message.

## Limitations (by design)

No full 120-unit total computation; general CS curriculum only; AP/GE accuracy depends on
the bundled matrices and any DPR statuses the student provides.

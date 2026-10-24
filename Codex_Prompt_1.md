# Codex instructions — Phase 1: foundation + "Plan" flow working end to end

You are building **Saathi**, an AI teacher copilot for **primary school teachers (Grades 1–5) in India**, who follow either the **NCERT** curriculum or the **Telangana state (SCERT Telangana)** curriculum. This is a solo final project for a Yale SOM course ("AI Foundations for Managers"). The deadline is tight: this phase must be working and deployable by **tonight (Saturday Oct 24)**, and the whole project finishes Sunday, so favor simple, working code over clever code.

Before you start, read these two files in this folder:
- `Product_Design.md`: the full product concept (it was written for Grades 6–8 with Indian-language output; **this file overrides it**: Grades 1–5, two boards, English only)
- `Project_Plan.md`: the scoped MVP, agent design, and grading requirements

This phase builds the foundation and the **Plan** flow (lesson plan + exit check, reviewed). Later phases will add Check (answer entry), Next steps (diagnosis + interventions), safety hardening, deployment, and the report. **Design the data model for the whole loop now** so later phases don't need rework, but only build the UI for Plan in this phase.

---

## Hard requirements (from the course; do not deviate)

1. **Model:** only `gpt-6-luna`, through Portkey, using the env var `PORTKEY_API_KEY`. Use PydanticAI exactly like this:
   ```python
   from pydantic_ai.models.openai import OpenAIChatModel
   from pydantic_ai.providers.openai import OpenAIProvider

   def get_model() -> OpenAIChatModel:
       return OpenAIChatModel(
           "gpt-6-luna",
           provider=OpenAIProvider(
               base_url="https://api.portkey.ai/v1",
               api_key=os.getenv("PORTKEY_API_KEY"),
           ),
       )
   ```
   Put this in one place (`app/llm.py`) so every agent uses it.
2. **`.env` lookup:** load `.env` from the repo folder first, then from the folder **one level above** the repo (the graders put their `.env` there). Use `python-dotenv`. On this machine the real `.env` already sits one level above the repo (`AI Foundations/.env`), which matches the graders' layout, so do not copy it into the repo. If no key is found, the app must still start and show a clear message ("PORTKEY_API_KEY not found") instead of crashing.
3. **Secrets:** create `.gitignore` (ignore `.env`, `*.db`, `__pycache__/`, `.venv/`) and `.env.example` containing `PORTKEY_API_KEY=` with no value. Never write a real key anywhere.
4. **Easy to run:** must run from a fresh clone in under 10 minutes using only `pip install -r requirements.txt` and `python run.py`. **No Node/npm build step.** The frontend is plain HTML/CSS/JS served by FastAPI.
5. **Real token counts:** every LLM call must record input tokens, cached input tokens, output tokens, and cost (see "Token logging" below). This is graded evidence.
6. **Do not invent curriculum facts.** Chapter names, textbook titles, and learning-outcome codes must come from official sources (NCERT: ncert.nic.in textbooks and the NCERT *Learning Outcomes at the Elementary Stage* document; Telangana: scert.telangana.gov.in textbooks). If you cannot verify something, leave it out and let the teacher type it instead (see "Curriculum coverage" below). Wrong chapter names would destroy teachers' trust.

## Tech stack

- Python 3.11+ (developer machine has 3.13), FastAPI, Uvicorn, PydanticAI, Pydantic v2, python-dotenv, SQLite via the standard `sqlite3` module (no ORM needed), pytest.
- Frontend: a single-page app in `static/` (`index.html`, `app.css`, `app.js`), vanilla JS with `fetch`. No frameworks, no CDN dependencies for the app itself.

## Folder structure

```
Saathi/
├── run.py                  # starts uvicorn on 0.0.0.0, port from $PORT or 8000
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md               # what it is + step-by-step run instructions
├── app/
│   ├── main.py             # FastAPI app, routes, serves static/
│   ├── config.py           # .env loading, model name, prices, budgets
│   ├── llm.py              # get_model()
│   ├── db.py               # SQLite setup + helper functions
│   ├── models.py           # Pydantic schemas (inputs + structured outputs)
│   ├── curriculum.py       # loads data/*.json; tool functions
│   ├── pipeline.py         # deterministic orchestration of agents
│   ├── usage.py            # token + cost logging
│   ├── agents/
│   │   ├── planner.py      # Lesson Planner agent
│   │   ├── exit_check.py   # Exit-Check Builder agent
│   │   └── reviewer.py     # Reviewer agent
│   └── prompts/            # system prompts as .md files, loaded at startup
├── data/
│   ├── boards.json         # boards → grades → subjects → chapters
│   ├── concepts.json       # curated concept library (board-agnostic)
│   ├── misconceptions.json # curated misconception library
│   └── demo_classes.json
├── static/
│   ├── index.html
│   ├── app.css
│   └── app.js
└── tests/
    ├── test_config.py
    ├── test_curriculum.py
    └── test_pipeline.py    # uses PydanticAI TestModel / FunctionModel, no real API calls
```

## Curriculum coverage: broad everywhere, deep where curated

We cannot hand-curate 5 grades × 2 boards × every subject by Sunday, so the app works in two modes:

- **Curated mode** (deep): the lesson's concepts exist in `concepts.json` with verified misconceptions. Exit-check options are tagged with misconception IDs from the library. This is the showcase.
- **Open mode** (broad): any board, grade, subject, and chapter/topic the teacher picks or types. The agents generate the plan from the board, grade, subject, and topic, and the exit check's misconception tags are **AI-suggested**, clearly labeled as such in the data and the UI (e.g. "Suggested common error" with a small "AI-suggested" tag).

The pipeline picks the mode automatically: if the topic matches curated concepts, use curated mode; otherwise open mode.

## Data files (create these)

**`data/boards.json`**: two boards:
- `NCERT` (name "NCERT / CBSE")
- `TS_SCERT` (name "Telangana State (SCERT)")

For each board, Grades 1–5, each grade with its subjects. Use this subject list (configurable in the file):
- Grades 1–2: English, Mathematics
- Grades 3–5: English, Mathematics, Environmental Studies (EVS). NCERT's newer textbooks call EVS "The World Around Us"; use the official name if you can verify it.

Do **not** include Telugu or Hindi as subjects; the pilot teachers don't teach them.

For each subject, a `chapters` list. **Only fill in chapters you can verify** from the official textbooks, each with `{title, verified_source}`. It is fine, and expected, for many lists to be empty. The UI always offers "Type a chapter or topic" as well.

**`data/concepts.json`**: a board-agnostic library of **primary Mathematics** concepts for Grades 1–5, about 20 concepts covering the core strands: counting and number sense (1–100), place value (2- and 3-digit, then larger), addition and subtraction (without and with regrouping), multiplication as repeated addition and tables, division as sharing and grouping, simple fractions (half, quarter, parts of a whole), money, measurement (length, weight, capacity), time, and basic shapes and patterns. Each concept: `id`, `name`, `subject` ("Mathematics"), `grades` (list), `description`, `learning_outcome` (a plain statement; add an official NCERT learning-outcome code **only** if verified), `prerequisite_ids`, and `keywords` (used to match a teacher's topic text to concepts).

**`data/misconceptions.json`**: for each concept, 2–4 well-known misconceptions from primary maths education research. Each has `id` (e.g. `M-PV-01`), `concept_id`, `description` (e.g. "Writes 'forty-three' as 403: writes the tens and ones parts separately"), and `example_wrong_answer`. These must be accurate.

**`data/demo_classes.json`**: two seeded demo classes:
- `3A-TS`: Grade 3, board `TS_SCERT`, Telangana government primary school, 38 students
- `1B-NCERT`: Grade 1, board `NCERT`, government school, 32 students

Each class also has `period_minutes` 40 and `resources` ["chalkboard", "textbook", "local objects (stones, sticks, bottle caps)"]. Students have `roll_no` and a common first name (Telugu names for the Telangana class, since the children are local). Teachers can also **create their own class** in the UI (board, grade, section, class size, period length, resources); students are then auto-created as roll numbers 1..N with no names.

## Assessment format depends on the grade

Many Grade 1–2 children cannot yet read a written multiple-choice question, so:

- **Grades 1–2 → "Observation check":** 3–5 short **oral or hands-on tasks** the teacher does with the class or small groups (e.g. "Show me 7 using sticks", "Which group has more?"). For each task: `concept_id`, `task` (what the teacher says/does), `materials`, `what_success_looks_like`, and `common_errors` (each with a misconception ID or an AI-suggested description). The teacher later marks each child **Got it / Partly / Not yet** and can tick which common error they saw.
- **Grades 3–5 → "Exit check":** 5 short multiple-choice questions that fit on a chalkboard (no diagrams needed), options A–D, each wrong option tagged with one misconception.

Both formats feed the same diagnosis in Phase 2 (mastery per concept, most common errors, Ready / Practice / Re-teach groups).

## Database (SQLite, `saathi.db`, auto-created on startup)

Create tables for the whole loop now:
- `classes` (id, name, board, grade, section, class_size, period_minutes, resources_json), `students` (class_id, roll_no, first_name nullable): seeded from `demo_classes.json` on first run
- `lesson_plans`: id, class_id, board, grade, subject, chapter_or_topic, mode ("curated"|"open"), plan_json, created_at
- `checks`: id, lesson_plan_id, check_type ("observation"|"mcq"), items_json
- `responses`: check_id, roll_no, item_index, chosen_option (mcq) or rating ("got_it"|"partly"|"not_yet") plus error_id (observation) (used in Phase 2)
- `insights`: check_id, insight_json, created_at (used in Phase 2)
- `llm_calls`: id, run_id, agent_name, input_tokens, cached_input_tokens, output_tokens, cost_usd, duration_ms, created_at
- `runs`: id, kind ("plan", later "next_steps"), class_id, status, total_cost_usd, created_at

## Structured outputs (Pydantic models in `app/models.py`)

- **`LessonPlan`**: `title`, `learning_objectives` (list), `concept_ids` (curated IDs, may be empty in open mode), `materials` (list; prefer free local objects), `sections` (list of `{name, minutes, teacher_actions, student_actions}`, covering warm-up, explanation/demonstration, activity, practice, wrap-up; minutes must add up to the period length), `local_examples` (list), `differentiation_tips` (`{support, on_level, challenge}`), `large_class_tips` (list: how to run this with 35–50 children), `homework_or_home_activity`.
- **`ObservationCheck`** (Grades 1–2): 3–5 `ObservationTask`s as described above.
- **`McqCheck`** (Grades 3–5): exactly 5 `Question`s. Each `Question` has `concept_id` (nullable in open mode), `stem`, `options` (exactly 4: A–D), `correct_option`, and `option_errors` (dict mapping each **wrong** option letter to `{misconception_id | null, description, ai_suggested: bool}`).
- **`ReviewResult`**: `passed` (bool), `issues` (list of `{target: "plan"|"item N", problem, fix}`).

Add Pydantic validators: item counts, exactly 4 options, `correct_option` in A–D, every wrong option has an error description, plan section minutes add up to the period length, and `ai_suggested` is false only when `misconception_id` is set.

## Tools (plain Python functions in `app/curriculum.py`, registered as PydanticAI tools)

- `get_curriculum_context(board, grade, subject, chapter_or_topic)` → board name, grade, subject, the chapter if found in `boards.json`, any matched curated concepts (with learning outcomes and prerequisites), and the mode ("curated" or "open")
- `get_class_profile(class_id)` → board, grade, class size, resources, period length (**never student names**)
- `get_latest_insights(class_id)` → latest insight for this class, or "no data yet" (Phase 2 fills this in)
- `get_misconceptions(concept_id)` → list of curated misconceptions for that concept

## Agents

Each agent: its own file, system prompt loaded from `app/prompts/<name>.md`, typed `output_type`, and only the tools it needs.

1. **Lesson Planner**: tools `get_curriculum_context`, `get_class_profile`, `get_latest_insights`. Writes a practical 40-minute plan for a large Indian government primary classroom with a chalkboard, textbook, and free local objects. Age-appropriate for the grade: for Grades 1–2, short segments, songs/rhymes, movement, concrete objects, lots of oral work; for Grades 3–5, more pair and group work and written practice. Uses familiar local examples; for Telangana classes, use Telangana context (local foods, festivals like Bathukamma and Bonalu, markets, rupees, village and town life). Follows the class's board. If the latest insights show a weak concept, adds a short review in the warm-up.
2. **Check Builder**: tool `get_misconceptions`. Builds an `ObservationCheck` for Grades 1–2 or an `McqCheck` for Grades 3–5. In curated mode it must use only misconception IDs returned by the tool; in open mode it writes AI-suggested errors with `ai_suggested: true`.
3. **Reviewer**: tool `get_curriculum_context`. Checks the plan and the check for factual or math errors, wrong answer keys, wrong error tags, timing that doesn't add up, age fit for the grade, fit to the board and topic, and whether the English is simple enough for the grade. Returns `ReviewResult`.

### Language

**English only**, for both the app and all generated content. No language selector. Many of these children are learning English as a second language, so anything the teacher says or writes for children (instructions, questions, chalkboard text) must use short sentences and simple, common words suitable for the grade.

## Pipeline (`app/pipeline.py`): plain Python, not an LLM router

`generate_plan(class_id, subject, chapter_or_topic, teacher_note: str | None)`:
1. Create a `runs` row. Board and grade come from the class.
2. Decide the mode (curated or open) in code, via keyword matching against `concepts.json`.
3. Run Lesson Planner → `LessonPlan`.
4. Run Check Builder → `ObservationCheck` or `McqCheck` (by grade, decided in code).
5. **Code check:** in curated mode, every misconception ID exists in `misconceptions.json` and belongs to the item's concept; record failures as review issues.
6. Run Reviewer. If `passed` is false, re-run **only** the failing part (planner or check) **once** with the issues as feedback, then review again. **Never more than one revision.**
7. Save to DB; return plan, check, mode, final review result, and the run's token/cost summary.
8. Use PydanticAI `UsageLimits` on every agent run (e.g. `request_limit=6`, a total token cap) so nothing can loop forever.

`chapter_or_topic` (when typed) and `teacher_note` (optional, e.g. "many children still confuse 6 and 9") are **untrusted teacher text**. Cap them (topic 120 characters, note 500 characters) and pass them to the agents **wrapped as data**, e.g. inside `<teacher_note>…</teacher_note>`, with an instruction that this is context only and never instructions. (Phase 2 adds full prompt-injection defenses and tests.)

## Token logging (`app/usage.py`)

- After every agent run, read `result.usage()` and record input tokens, cached input tokens (from PydanticAI usage details if available, else 0), output tokens, and duration in `llm_calls`, linked to the `run_id`.
- Cost: prices per 1M tokens live in `app/config.py` as `PRICE_INPUT_PER_M`, `PRICE_CACHED_INPUT_PER_M`, `PRICE_OUTPUT_PER_M`. I don't know gpt-6-luna's prices yet, so use clearly marked placeholder values with a `# TODO: confirm gpt-6-luna pricing` comment.
- **Prompt caching:** structure every agent prompt so the long, unchanging content (system prompt, then grade-band guidance and curated reference text) comes **first**, and the variable request comes **last**, so the provider's automatic prompt caching can apply.

## API routes

- `GET /api/health` → `{ok, key_found}`
- `GET /api/boards` → boards, grades, subjects, chapters
- `GET /api/classes`, `POST /api/classes`, `GET /api/classes/{id}`
- `POST /api/plans` → body `{class_id, subject, chapter_or_topic, teacher_note?}` → runs the pipeline
- `GET /api/plans/{id}`
- `GET /api/usage` → per-run and total tokens and cost, plus a breakdown per agent

## Frontend (`static/`)

Mobile-first, clean, friendly, large tap targets, works well on a phone screen and also looks good on a laptop. Plain language ("children who need help", not jargon).

- **Top bar:** "Saathi" + class selector (shows e.g. "Grade 3A · Telangana") + "Add class" + a small key status dot.
- **Bottom tab bar:** **Plan** · **Check** · **Next steps** · **Usage**. Check and Next steps show a friendly "Coming soon" card in this phase.
- **Add class form:** board (NCERT / Telangana), grade (1–5), section, number of children, period length, resources (checkboxes).
- **Plan tab:**
  - Subject (from the class's board and grade), chapter (dropdown if verified chapters exist, plus "Type a chapter or topic"), optional note box (with a character counter), and a big **Prepare lesson** button.
  - While running: show progress steps ("Planning lesson → Writing check → Checking quality").
  - Result: the lesson plan as readable cards (sections with minutes, examples, large-class tips, differentiation tips), then the check (observation tasks for Grades 1–2, questions with the correct answer marked for Grades 3–5, plus a "Show common errors" toggle with the AI-suggested labels), a mode badge ("Curated" or "Open"), and a review badge ("Checked ✓" or the issues found).
  - **Token/cost strip** under every result: input, cached input, and output tokens, plus cost for this run.
  - A **Print** button that prints just the plan and check cleanly (print CSS), plus a "Chalkboard version" (Grades 3–5: the 5 questions in large text; Grades 1–2: the task list in large text for the teacher).
- **Usage tab:** table of recent runs with tokens and cost, totals, and a breakdown per agent.
- Use a calm palette (e.g. deep teal primary, warm saffron accent, off-white background) and a system font stack (don't load fonts from a CDN).

## Tests (pytest, no real API calls)

- `.env` lookup: finds a key in the repo folder; falls back to the parent folder; starts without a key.
- Curriculum: all JSON loads; every concept's prerequisites exist; every misconception's concept exists; every listed chapter has a `verified_source`.
- Mode selection: a Grade 3 topic like "place value" → curated; a Grade 4 EVS topic → open.
- Check type: Grade 1–2 class → observation check; Grade 3–5 → MCQ.
- Validators: reject an MCQ check with 4 questions, a wrong option with no error, an `ai_suggested: false` error with no ID, or plan minutes that don't add up.
- Pipeline: with PydanticAI `TestModel`/`FunctionModel`, a run completes, logs `llm_calls` rows, and does at most one revision when the reviewer fails it.

## README.md

Title, one-sentence description, "Run locally" steps (clone → `python -m venv .venv` → activate → `pip install -r requirements.txt` → put `.env` with `PORTKEY_API_KEY` in this folder or the folder above → `python run.py` → open http://localhost:8000), and how to run tests. Leave a placeholder line at the top for the online link.

## Done means

1. `pip install -r requirements.txt && python run.py` starts the app with no errors.
2. With a real `PORTKEY_API_KEY`, all of these work and show real token counts and cost on screen and on the Usage tab:
   - Grade 3 Telangana class, Mathematics, "place value" → curated plan + 5-question MCQ check
   - Grade 1 NCERT class, Mathematics, "numbers 1 to 20" → plan + observation check
   - Grade 4 Telangana class (create it), EVS, a typed topic → open-mode plan + MCQ check with AI-suggested error labels
3. `pytest` passes.
4. `git init` done, with `.env` ignored; nothing secret committed.
5. At the end, tell me: what you built, which chapter lists you could verify (and from where) and which you left empty, the token counts and cost of one real run, and anything I should check by hand.

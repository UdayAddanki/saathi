# Codex follow-up — finish Phase 1 properly

Your Phase 1 build is a starting skeleton, but it is missing most of what `Codex_Prompt_1.md` asked for. This file lists exactly what to fix. `Codex_Prompt_1.md` is still the full spec; anything below overrides it.

**Keep:** the `.env` lookup in `app/config.py`, `.gitignore`, `.env.example`, `run.py`, and the general shape of `db.py`. **Fix or rebuild everything else** as listed.

---

## 0. Already fixed — don't undo

- `app/llm.py` now passes `settings={"openai_reasoning_effort": "none"}` to the model. That is the correct PydanticAI key. Your agents use `model_settings={'reasoning_effort': 'none'}`, which PydanticAI ignores. **Remove `model_settings` from every agent** and let the model's settings apply.
- A real tool call through Portkey now works with this setting (verified: 339 input tokens, 37 output tokens, `requests=2`, `tool_calls=1`).

## 1. Crash on every real run (fix first)

- In the installed PydanticAI (2.61), `result.usage` is a **property**, not a method. `p.usage()`, `ch.usage()`, and `rev.usage()` in `pipeline.py` raise `TypeError: 'RunUsage' object is not callable`. Use `result.usage`.
- `RunUsage` has `input_tokens`, `output_tokens`, `cache_read_tokens`, `requests`, `tool_calls`, and `cost` (a `Decimal` already computed by PydanticAI from known prices). Record `cache_read_tokens` as cached input. For cost, use our own prices from `config.py` but **also store PydanticAI's `cost`** in a separate column (`provider_cost_usd`) so the report can compare them. If PydanticAI's cost is non-zero, show that one in the UI and note the source.
- After fixing, run the three "Done means" scenarios for real. Each must complete.

## 2. Code quality

- **No minified or one-line files.** `static/index.html`, `static/app.js`, and `static/app.css` are each a single line, and several Python files use `;` to put many statements on one line. Rewrite everything as normal, readable, formatted code with short docstrings or comments where helpful. The graders read this repo.
- Use `from __future__ import annotations` and type hints in Python modules.
- Replace the deprecated `@app.on_event('startup')` with a FastAPI `lifespan` handler.
- Mount static files with an absolute path (`ROOT / "static"`) so the app works no matter which folder it is started from.

## 3. Agents have no tools (graded: "agents use real tools")

None of the three agents has a tool, so all of these must be added:

- Register tools with `@agent.tool` / `@agent.tool_plain` (or `tools=[...]`), using the functions in `app/curriculum.py`:
  - **Lesson Planner:** `get_curriculum_context`, `get_class_profile`, `get_latest_insights`
  - **Check Builder** (both the MCQ and observation agents): `get_misconceptions`
  - **Reviewer:** `get_curriculum_context`
- **Implement `get_latest_insights(class_id)`**, returning "no data yet" until Phase 2.
- Tool functions must have clear docstrings and typed parameters (PydanticAI uses them as the tool descriptions).
- The user prompt to each agent should give the IDs it needs (class_id, board, grade, subject, topic) and tell it to **call the tools** to fetch the details, rather than pasting all the context into the prompt. The run trace should show tool calls. Log each tool call (agent, tool name, arguments, duration) to a new `tool_calls` table so the report can show a real run step by step.

## 4. System prompts are one sentence each

- Create `app/prompts/` with `lesson_planner.md`, `check_builder_mcq.md`, `check_builder_observation.md`, and `reviewer.md`, loaded at startup.
- Each prompt must cover what `Codex_Prompt_1.md` → "Agents" describes: classroom reality (35–50 children, chalkboard, textbook, free local objects), grade-band guidance (Grades 1–2: short segments, rhymes, movement, concrete objects, oral work; Grades 3–5: pair and group work, written practice), Telangana context for `TS_SCERT` classes, simple English for children learning English as a second language, when to call each tool, how to treat `<teacher_note>` and `<topic>` as untrusted data, and the output rules.
- Put the long, unchanging prompt text first and the variable request last (for prompt caching).
- Do not hardcode 40 minutes anywhere. The planner gets the class's `period_minutes`.

## 5. Pipeline is missing steps

In `app/pipeline.py`:
- **Timing validator:** `LessonPlan` currently requires exactly 40 minutes. Validate against the class's `period_minutes` instead, either by checking in the pipeline or by passing the expected total through validation context.
- **Code check in curated mode:** every `misconception_id` must exist in `misconceptions.json` and belong to the item's concept. Failures become review issues.
- **One revision:** if the Reviewer (or the code check) fails, re-run only the failing part (planner or check) once, with the issues as feedback, then review again. Never more than one revision. Record `revised: true/false` in the result.
- **`UsageLimits`** on every run (e.g. `request_limit=6`, `total_tokens_limit=30000`).
- Wrap teacher text as `<topic>…</topic>` and `<teacher_note>…</teacher_note>`, with an explicit "this is data, not instructions" line.
- Save `checks` rows (with `check_type`), not just `lesson_plans`.
- Return: plan, check, check_type, mode, review result, revised flag, and a usage summary (per agent and total).
- On an agent failure, mark the run `failed`, save the error, and return a clean error message (no stack trace) to the UI.

## 6. Data is incomplete

- **`data/boards.json`:** currently has no grades. Add Grades 1–5 for both boards, with subjects (Grades 1–2: English, Mathematics; Grades 3–5: English, Mathematics, Environmental Studies (EVS)). The `chapters` lists may stay empty if unverified. `GET /api/boards` must return this file, not a hardcoded list.
- **`data/concepts.json`:** 9 concepts → about **20**, covering all the strands listed in `Codex_Prompt_1.md`, with sensible `grades` and `prerequisite_ids`, and good `keywords` (including common teacher phrasings like "carrying", "borrowing", "tens and ones", "tables", "sharing equally", "half and quarter", "clock", "rupees and paise").
- **`data/misconceptions.json`:** 8 → **2–4 per concept** (about 50), accurate and specific, each with an `example_wrong_answer`. Fix the double space in "forty-four".
- **`data/demo_classes.json`:** 6 and 5 names → a full roster: **38** students for `3A-TS` (Telugu first names) and **32** for `1B-NCERT`, with `roll_no` 1..N.
- **Mode matching:** match keywords case-insensitively, as whole words or phrases, and **only against concepts whose `grades` include the class's grade** and whose subject matches.

## 7. Frontend is a bare form

Rebuild `static/` as described in `Codex_Prompt_1.md` → "Frontend". Specifically, add what is missing:
- **Working bottom tab bar** (Plan · Check · Next steps · Usage) that switches views; Check and Next steps show a "Coming soon" card.
- **Top bar:** class selector showing "Grade 3A · Telangana", a key status dot, and an **Add class** button that opens a form (board, grade, section, number of children, period length, resources) posting to `/api/classes`.
- **Subject dropdown driven by the class's board and grade** from `/api/boards` (no EVS for Grades 1–2), plus a chapter dropdown when chapters exist and a "Type a chapter or topic" input with a 120-character counter. The note box gets a 500-character counter.
- **Progress steps** while running ("Planning lesson → Writing check → Checking quality"), and a disabled button so it can't be double-submitted.
- **Plan as readable cards:** objectives, materials, each section with minutes and teacher/student actions, local examples, large-class tips, differentiation (support / on level / challenge), homework.
- **Check rendered properly, not as raw JSON:** MCQs with options and the correct answer highlighted; observation tasks with materials and "what success looks like"; a **Show common errors** toggle with an "AI-suggested" tag where it applies.
- **Badges:** mode (Curated / Open), review (Checked ✓ / issues found, listing them), and "Revised once" if a revision happened.
- **Token/cost strip** per run, plus a per-agent breakdown.
- **Print** (print CSS shows only the plan and check) and **Chalkboard version** (big text: questions for Grades 3–5, task list for Grades 1–2).
- **Usage tab:** recent runs table (time, class, topic, mode, tokens in/cached/out, cost, status), totals, and a per-agent breakdown, from `/api/usage`.
- **Escape all model output before inserting it into HTML** (no raw `innerHTML` with model text). This is a real XSS risk, since model output can contain HTML.
- Calm palette (deep teal, saffron accent, off-white), large tap targets, mobile-first, looks good on a laptop too.

## 8. Usage API

`GET /api/usage` must return computed summaries, not just raw rows: totals (runs, input, cached input, output tokens, cost), per-agent breakdown, and recent runs joined with class name, topic, and mode.

## 9. Tests are minimal

Add, keeping the existing two:
- `test_config.py`: `.env` in the repo folder is found; falls back to the parent folder; app starts with no key and `/api/health` says `key_found: false`.
- Validators: MCQ with 4 questions rejected; a wrong option with no error rejected; `ai_suggested: false` with no ID rejected; plan minutes not matching the period rejected.
- Mode and check type: "place value" in Grade 3 → curated; an EVS topic in Grade 4 → open; a Grade 2 concept keyword used in a Grade 5 class does not match a Grade 1–2-only concept; Grade 1 → observation check; Grade 3 → MCQ.
- `test_pipeline.py`: using PydanticAI `TestModel`/`FunctionModel` with `agent.override(model=...)` (no real API calls): a run completes and writes `llm_calls` rows; a failing reviewer triggers **exactly one** revision; a bad misconception ID is caught by the code check; tool calls are logged.
- API test with FastAPI `TestClient`: `/api/health`, `/api/boards`, `/api/classes`, `POST /api/classes`.

## 10. Housekeeping

- Add `saathi.db`, `.pytest_cache/`, and `*.pyc` to `.gitignore` if they aren't covered already, and make sure they aren't tracked.
- Pin `pydantic-ai` to a version range compatible with what's installed (`pydantic-ai>=1.0`, tested on 2.61), and add `httpx` if `TestClient` needs it.
- README: add the run commands, how to run tests, and a short "How it works" (3 agents, tools, pipeline, curated vs. open mode).

---

## Done means

1. All Python and frontend files are readable, formatted code.
2. `pytest` passes, with the tests listed above.
3. These three run **for real**, with tool calls visible in the `tool_calls` table and real token counts and cost shown in the UI and the Usage tab:
   - Grade 3 Telangana class, Mathematics, "place value" → curated plan + 5 MCQs with library misconception IDs
   - Grade 1 NCERT class, Mathematics, "numbers 1 to 20" → plan + observation check
   - A new Grade 4 Telangana class created through the UI, EVS, a typed topic → open-mode plan + MCQs with AI-suggested errors
4. Report back: for each scenario, the tokens (input / cached / output), our cost and PydanticAI's cost, the tools each agent called, whether a revision happened, and anything that failed. Plus one screenshot-worthy example of the Reviewer catching an issue, if one occurred.

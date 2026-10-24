# Codex instructions — Phase 2: Check → Diagnose → Next steps (close the loop)

Phase 1 (Plan) is done and committed. This phase builds the rest of the loop that makes Saathi more than a lesson-plan generator:

**Plan → teach → Check (teacher enters results) → Diagnose (code) → Next steps (agent) → the next Plan uses the results.**

`Codex_Prompt_1.md` and `Codex_Prompt_1b.md` still apply (code style, model, safety, token logging). Keep all existing tests passing.

---

## 0. Leftover from Phase 1

Add `tests/test_pipeline.py` using PydanticAI `TestModel` / `FunctionModel` with `agent.override(model=...)` and no real API calls:
- a run completes and writes `llm_calls` and `tool_calls` rows;
- a reviewer that returns a `must_fix` issue triggers **exactly one** revision;
- a reviewer that returns only `suggestion` issues triggers **no** revision;
- a bad misconception ID in curated mode is caught by the code check.

## 1. Check tab: entering results (fast, phone-friendly)

The teacher picks one of their saved lessons ("Grade 3A · Place value · today"), then enters what the children did. Add a "Recent lessons" list at the top of the Check tab.

**Grades 3–5 (MCQ check), "Each child" mode:**
- A grid with one row per child (roll number + first name if present) and one column per question (Q1–Q5).
- **Everything starts as correct.** Tapping a cell cycles through the wrong options (B → C → D → blank/absent → correct). Show the chosen letter in the cell, with red for wrong and grey for absent.
- An "Absent" toggle per child.
- Sticky header row, large cells, works on a 375px-wide phone without horizontal scrolling for 5 questions.

**Grades 1–2 (observation check), "Each child" mode:**
- One row per child, one column per task. Tapping a cell cycles **Got it ✓ → Partly ~ → Not yet ✗**, starting at Got it.
- For a "Partly" or "Not yet" cell, an optional small picker of that task's `common_errors` lets the teacher tick the error they saw.

**"Class count" mode (both grade bands)**, for very large classes or when the teacher has no time:
- Per question, the number of children who chose A / B / C / D (MCQ); or per task, the number who were Got it / Partly / Not yet (observation).
- This gives class-level diagnosis only, with no per-child groups. Say so in the UI.

**Also:**
- **Save** button, with a confirmation. Results can be edited and re-saved (overwrite).
- A **"Fill sample results"** button, shown only when `DEMO_MODE=true` (env var; default true locally, false on Render unless set). It fills realistic results for demos and screenshots: about 55–70% correct overall, with one misconception clearly more common than the others, and a few absent children.
- Validate on the server: roll numbers exist in the class, options are A–D, counts don't exceed class size.

**Data:** use the existing `responses` table. Add a `check_mode` ("each_child" | "class_count") and a `class_counts_json` column, or a separate table for counts.

## 2. Diagnose: plain Python, no LLM (`app/diagnosis.py`)

`analyze_results(check_id) -> Insight` (a Pydantic model), computed only from saved results, the check items, and the curated library:

- **Per concept:** children assessed, % correct (MCQ), or % Got it / Partly / Not yet (observation). Status: **Secure** (≥ 80%), **Developing** (50–79%), **Needs re-teaching** (< 50%).
- **Top errors:** for each wrong option or ticked error, how many children chose it, mapped to its misconception (description, ID, or "AI-suggested"). Sorted by count. Include which question it came from.
- **Groups** (each-child mode only):
  - **Ready to move on:** ≥ 4/5 correct (MCQ), or all tasks Got it (observation)
  - **Needs practice:** 2–3/5, or a mix
  - **Needs re-teaching:** ≤ 1/5, or mostly Not yet
  - Absent children are listed separately as **Missed this lesson**.
- **Prerequisite flag:** if a concept is "Needs re-teaching" and it has prerequisites in `concepts.json`, list them as "check these first".
- **Recommended action type** (rules, not LLM):
  - class ≥ 80% → `move_on` (with a short warm-up for the practice group)
  - 50–79% → `group_practice`
  - < 50% → `whole_class_reteach`
  - prerequisite flag present → also `review_prerequisite`
- Save to the `insights` table. Re-running replaces the old insight for that check.

Unit-test this module thoroughly with hand-made results (it is pure code, so it must be exactly right): group boundaries, absent handling, class-count mode, top-error sorting, the AI-suggested label, and prerequisite flags.

## 3. Next-Step Coach agent (`app/agents/coach.py`)

A fourth agent. It **never computes numbers**. It reads the computed insight through a tool and writes the teaching content.

- **Tools:**
  - `get_insight(check_id)`: the computed Insight from step 2
  - `get_misconceptions(concept_id)`
  - `get_prerequisites(concept_id)`
  - `get_class_profile(class_id)`
- **Output: `NextSteps`**
  - `summary`: 2–3 plain sentences for the teacher (e.g. "Most children can read 2-digit numbers. 14 children wrote 43 as 403, so they are writing tens and ones separately.") The numbers must come from the insight.
  - `reteach`: `{minutes, target_misconception, steps}`, a 10–15 minute whole-class segment that directly targets the top error with a concrete chalkboard or object demonstration. Empty if the action type is `move_on`.
  - `group_activities`: one activity per group (Ready / Practice / Re-teach), **the same topic at three levels**, runnable at the same time in one classroom, plus a peer-helper suggestion (pair Ready children with Re-teach children).
  - `practice_sheet`: 3 levels × 4 short items each, printable on one page, with answers.
  - `missed_lesson_catchup`: a 5-minute catch-up for absent children.
  - `next_lesson_warmup`: a 5–7 minute warm-up to add to the next lesson.
- **Code check after the agent runs:** every number in `summary` must appear in the insight (extract integers with a regex and compare). Any mismatch is a `must_fix` issue → **one** revision. This defends against invented statistics, and it's a strong safety example for the report, so log it.
- Reuse the Reviewer (with `must_fix` / `suggestion`) on the coach output, in a "next steps" review mode.
- `UsageLimits` and token logging exactly as in Phase 1; `runs.kind = "next_steps"`.

## 4. Next steps tab

After results are saved, a **"See what to do next"** button runs diagnosis (instant) and then the coach.

Layout, top to bottom:
1. **Class Insight card** (shown instantly from the code diagnosis, before the coach finishes): per-concept bars with % and status color; the top 3 errors with counts ("14 children: wrote 43 as 403"); "AI-suggested" tags where relevant.
2. **Groups:** three colored cards (🟢 Ready · 🟡 Practice · 🔴 Re-teach) with counts; tap to expand the roll numbers and names. Plus "Missed this lesson". Hidden in class-count mode, with a note.
3. **Coach output:** summary, reteach segment, three-level group activities, peer helpers, catch-up, warm-up.
4. Buttons: **Print practice sheet** (one page, three levels, answers on a separate teacher section) and **Use in next lesson**.
5. Token/cost strip for this run.

## 5. Close the loop

- `get_latest_insights(class_id)` (already a planner tool) now returns the latest real insight for that class and subject: weak concepts, top errors, and the `next_lesson_warmup`.
- **"Use in next lesson"** stores the warm-up as the class's pending warm-up. The next Plan run for that class includes it, and the plan shows a banner: *"Includes a 6-minute review of place value. 14 children found it hard last time."*
- On the Plan tab, show a small "Last check" card for the selected class when insights exist (concept statuses + one line).

## 6. Progress (simple, inside the Next steps tab)

A **Class progress** section: a table of concepts assessed so far (rows) × checks over time (columns), with % correct colored by status, and a list of "children in Re-teach 2+ times in a row". Plain code from the `insights` and `responses` tables; no LLM.

## 7. Usage tab

Include `next_steps` runs. Show per-kind totals (plan vs. next steps) and the **average cost per full loop** (one plan + one next-steps run). The report needs this number.

## 8. Tests

- Diagnosis unit tests (section 2): the most important ones.
- Results API: save each-child MCQ, each-child observation, class counts; reject a bad roll number, a bad option, counts over class size; access code required.
- Coach code check: a summary with a number not in the insight → `must_fix` → exactly one revision (FunctionModel, no real API).
- Loop: after "Use in next lesson", the planner's `get_latest_insights` returns the warm-up.

## Done means

1. `pytest` passes (all old and new tests).
2. Real end-to-end loop, run **twice** for real with **"Fill sample results"**:
   - Grade 3 Telangana, place value: Plan → Check (each child) → Next steps → Use in next lesson → a new Plan that shows the review banner.
   - Grade 1 NCERT, numbers 1–20: Plan → observation Check (each child) → Next steps.
3. Commit (not push) with `.env`, db, caches excluded; show `git status` first.
4. Report back: for each loop, the tokens (input / cached / output) and cost per step and for the full loop; the tools the coach called; whether the number check or the Reviewer forced a revision (and why); and anything that failed or is still missing.

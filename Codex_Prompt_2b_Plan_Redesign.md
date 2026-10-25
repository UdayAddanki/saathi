# Codex instructions — Redesign the Plan flow (do this before Codex_Prompt_3.md)

The teachers' lesson-planning practice is built on two ideas this app must follow:
1. **A lesson starts from the class's context.** Plan from where the children are now and what the unit is aiming for, not just from a topic.
2. **Double planning.** Every step shows what the **teacher** does or says alongside what the **students** do or say in response.

This file changes the Plan inputs, the `LessonPlan` structure, the planner and reviewer prompts, and the Plan screen. The Check, Next steps, and loop features from Phase 2 must keep working. `Codex_Prompt_1.md`, `1b`, and `2` still apply for code style, model, safety, and token logging.

---

## 1. New Plan form (in this order)

1. **Class** (already exists; shows the grade prominently, e.g. "Grade 3 · Section A · Telangana"). The grade comes from the class.
2. **Classroom context** (a collapsible card; filled once, then saved):
   - **Current learning level:** quick choice *Most children below grade level / Mixed levels / Most at grade level*, plus an optional text box: "What can most children already do? Who is struggling, and with what?" (300 characters)
   - **Unit goal:** "What do you want children to achieve by the end of this unit?" (300 characters)
   - Saved **once per class** (one context for the whole class, used for every subject) and pre-filled for every lesson in that class, with an **Edit** link. Show "Last updated <date>". Ask for it the first time a class is used. The Add class form can also collect it, as an optional last step.
3. **Subject:** as now (English, Mathematics; EVS for Grades 3–5).
4. **Chapter name:** a text input (120 characters). If verified chapters exist in `boards.json` for this board, grade, and subject, show them as suggestions (a `<datalist>`), but always allow typing.
5. **Topic:** a text input (120 characters), e.g. "Reading 3-digit numbers using place value".
6. **Lesson type:** four large tap cards, each with a one-line description:
   - **5-step lesson (I do · We do · You do):** teacher models, class practises together, children practise alone
   - **5E lesson:** Engage · Explore · Explain · Elaborate · Evaluate
   - **Project-based learning:** children work on a real project over several days
   - **Experiential learning:** children learn by doing something, then reflect on it
   - For **Project-based** and **Experiential**, show two extra fields: "Day __ of __" (default 1 of 1) and, for projects, an optional "Project idea or driving question" (200 characters).
7. **Differentiated lesson?** A toggle, off by default. When it's on, the teacher picks **one or more** ways to differentiate (tap chips, with a one-line explanation each):
   - **Content:** *what* children learn: the same objective at different levels of difficulty, or different materials for each level (e.g. 2-digit numbers for the support group, 3-digit for on level, 4-digit for challenge)
   - **Process:** *how* children learn it: different activities, support, grouping, or amount of help for each level (e.g. objects and teacher help for support, pair work for on level, a puzzle for challenge)
   - **Product:** *how* children show what they learned: different ways to show the objective (e.g. show with sticks, draw it, or write and explain it)
   If the class has a saved insight from Phase 2, show "Use groups from your last check" (pre-selected), so the levels match the real Ready / Practice / Re-teach groups and their sizes.
8. **Note for Saathi** (optional, as now).
9. **Prepare lesson.**

Remove the old empty "Chapter or topic" dropdown. All typed fields are untrusted teacher text: keep the length caps, pass them wrapped in tags (`<learning_level>`, `<unit_goal>`, `<chapter>`, `<topic>`, `<project_idea>`, `<teacher_note>`), and run them through the existing prompt-injection check.

## 2. The plan has two halves

### Half 1 — Lesson Vision

- **Objective:** one clear, measurable sentence starting "Students will be able to …", for this one lesson.
- **Why this objective:** 2–4 sentences linking it to the unit goal, the children's current level (from the classroom context), what comes before and after, and why it matters in children's lives.
- **Assessment:** how the teacher will know the objective was met, meaning the end-of-lesson check (5 MCQs for Grades 3–5, observation tasks for Grades 1–2, as now), plus 1–2 quick checks during the lesson.
- **Expected student response:** what a correct answer looks like (an example of what a child would say, write, or show), and the 2–3 most likely wrong responses with what each one tells the teacher. In curated mode, link these to misconception IDs.
- **Key words:** 3–6 words, each with a child-friendly meaning and a way to introduce it (an example, object, or gesture).

### Half 2 — Lesson Method (follows the chosen lesson type)

Every step has: `name`, `minutes`, `purpose` (one line), `materials`, and a list of **exchanges**, where each exchange is a pair `{teacher: what the teacher does/says, students: what students do/say in response}`. Write key teacher questions word for word. Every teacher action has a matching student response. Optionally a `check_for_understanding` line.

Required steps per lesson type (names and order must match):

| Lesson type | Steps |
|---|---|
| 5-step (I do · We do · You do) | 1. Opening (hook, connect to what they know, share the objective) → 2. I do (teacher models with think-aloud) → 3. We do (guided practice together, with checks for understanding) → 4. You do (independent practice) → 5. Closing (assessment + recap) |
| 5E | Engage → Explore → Explain → Elaborate → Evaluate |
| Project-based learning | Launch or recap (driving question, where we are in the project) → Work time (children investigate, build, or create in groups) → Check-in (teacher circulates; quick critique) → Share (groups show progress) → Reflect + assess |
| Experiential learning | Do (concrete experience) → Reflect (what happened? what did you notice?) → Think (what does it mean? the idea or rule) → Apply (try it in a new situation) → Assess |

For project-based learning, also return a short **project outline**: the driving question, the final product, and one line per day for all the days, with today highlighted. For both project-based and experiential lessons, today's plan covers **only one period**.

### Differentiated lessons (only when the toggle is on)

Use three levels: **Support**, **On level**, **Challenge** (named after the Phase 2 groups, with their sizes, when "Use groups from your last check" is on).

- **Vision:** add a **Differentiation plan** box: which types were chosen (content / process / product), and for each, one line per level saying what differs. The objective stays the **same for everyone**. Differentiation changes the route, not the destination.
- **Method:** the step where children practise (We do / You do, Explore / Elaborate, Work time, Do / Apply) gets **tiered exchanges**: separate teacher/student pairs for each level, shown side by side. Other steps stay whole-class. Include how the teacher moves between groups in a 35–50 child classroom (who starts first, who gets the teacher's time, what the others do meanwhile).
  - **Content** → each level gets different numbers, texts, or examples.
  - **Process** → each level gets a different activity, amount of support, or grouping.
  - **Product** → each level shows its learning a different way. Also give the **expected student response for each product**, so the teacher knows what success looks like at each level.
- **Assessment:** the end-of-lesson check stays the same for everyone (so the results stay comparable for diagnosis). For product differentiation, add a short "what to look for" per product.
- When the toggle is off, keep the brief differentiation tips in "Make it work in your class" as below.

After the steps, a short **"Make it work in your class"** section: differentiation (support / on level / challenge), large-class tips (35–50 children), local examples (Telangana context for `TS_SCERT`), and a home activity.

## 3. Data model changes

- `LessonPlan` becomes `{lesson_type, vision: LessonVision, method: LessonMethod, make_it_work: MakeItWork, project_outline?: ProjectOutline}` with Pydantic models for each.
- Validators:
  - step names and order match the lesson type exactly (table above);
  - step minutes add up to the class's `period_minutes`;
  - every step has at least one exchange, and each exchange has both `teacher` and `students`;
  - the objective starts with "Students will be able to";
  - 3–6 key words;
  - `project_outline` is required for project-based lessons, and today's day is within the total days;
  - when differentiation is on: the chosen types are a non-empty subset of {content, process, product}; the differentiation plan covers exactly the chosen types with all three levels; at least one practice step has tiered exchanges for all three levels; with product differentiation, every level has an expected response.
- `lesson_plans` also stores `differentiated` (bool) and `differentiation_types` (list).
- New table `class_contexts` (class_id as the primary key, learning_level_choice, learning_level_text, unit_goal, updated_at): one row per class. Routes: `GET` and `PUT /api/classes/{id}/context`.
- `lesson_plans` gets `lesson_type`, `chapter`, `topic`, `day_number`, `total_days`, and a snapshot of the context used.
- **Old saved plans** (the old structure) must still open in the Check and Next steps tabs without crashing. Show them in a simple "older plan" layout.
- Anything in Phase 2 that reads `plan.sections` or `plan.learning_objectives` (the coach, the next-lesson warm-up, the review banner, print) must be updated to the new structure. The warm-up from "Use in next lesson" should go into the **first step** of the new plan, and be mentioned in "Why this objective".

## 4. Agents

- **Lesson Planner prompt:** rewrite for the two halves and the four lesson models. Include a short description of each model and what makes a good step in it; how to use the classroom context (pitch the objective to the current level, and point it at the unit goal); double-planning rules (teacher and student actions side by side, key questions word for word, children active in every step, no step that's just "teacher explains"); grade-band guidance and simple English as before. Add one short example exchange per lesson type.
- **Tools:** add `get_class_context(class_id)`. The planner calls it, along with the existing tools.
- **Check Builder:** gets the plan's objective, key words, and expected student responses, so the end-of-lesson check measures exactly the objective. In curated mode, the wrong answers should match the expected wrong responses where possible.
- **Reviewer:** add `must_fix` checks for: steps not matching the lesson type; a teacher action with no student response; an objective that isn't measurable or doesn't fit the grade; an assessment that doesn't measure the objective; a plan that ignores the stated learning level (e.g. far too hard for "most below grade level"); and, for differentiated lessons, levels that differ in the wrong way (e.g. "process" chosen but only the numbers change), different objectives per level, or a challenge level that's just "more of the same". Wording problems stay `suggestion`.
- Revision policy unchanged: only `must_fix`, and at most one revision.

## 5. Plan screen

- **Lesson Vision** first, as a highlighted card: Objective (large), Why this objective, Assessment, Expected student response (correct response in green, likely wrong responses in amber with what each tells you), Key words as chips (tap to see the meaning and how to introduce it).
- **Lesson Method** next: a header with the lesson type and a strip of step names with minutes, like a timeline. Each step is a collapsible card (first one open), with purpose and materials, then the **double plan**:
  - on a laptop: a two-column table, **Teacher does / says** | **Students do / say**, one row per exchange;
  - on a phone (under 600px): each exchange stacked as a "Teacher" line followed by an indented "Students" line, clearly colored differently.
- Project outline (project-based only): a small day-by-day list with today highlighted.
- For differentiated lessons: a **Differentiation plan** box in Vision with chips showing the chosen types; in the tiered step, three colored columns on a laptop (Support · On level · Challenge, with group sizes), or three tabs on a phone.
- "Make it work in your class" as a collapsible card.
- The end-of-lesson check as now, under Assessment or at the end.
- **Print:** prints Vision on top, then the double-plan table for every step (two columns on paper), then the check. **Chalkboard version:** unchanged.

## 6. Tests

- Validators: wrong step order for each lesson type; missing student response; minutes not matching the period; objective not starting with "Students will be able to"; project lesson without an outline; day 5 of 4.
- Class context: save, fetch, and pre-fill once per class (the same context appears for every subject in that class); injection text in the context is blocked.
- Old-format plans still load in Check and Next steps.
- Pipeline (FunctionModel, no real API): the planner receives the context; the reviewer flags a lesson-type mismatch as `must_fix` → exactly one revision.
- The loop: a warm-up from "Use in next lesson" appears in the new plan's first step.
- Differentiation: an empty or invalid type list is rejected; a plan missing a level, or missing tiered exchanges, is rejected; with "Use groups from your last check", the group sizes in the plan come from the saved insight.

## Done means

1. `pytest` passes (all old and new tests).
2. Real runs, one per lesson type, all with a classroom context filled in:
   - Grade 3 Telangana, Mathematics, chapter "Numbers up to 999" (or similar), topic "place value of 3-digit numbers", **5-step**, level "Mixed levels"
   - Grade 1 NCERT, Mathematics, topic "numbers 1 to 20", **Experiential**, level "Most below grade level"
   - Grade 4 Telangana (create it), EVS, topic "Plants around us", **Project-based**, day 1 of 4
   - Grade 3 Telangana, English, topic "action words (verbs)", **5E**
   - Grade 3 Telangana, Mathematics, place value, **5-step, differentiated by process + product**, using groups from the last check (run this after the loop in item 3, so a saved insight exists)
3. A full loop still works on the 5-step Grade 3 plan: Plan → Check → Next steps → Use in next lesson → new Plan with the warm-up in step 1.
4. Commit (don't push); show `git status` first.
5. Report back: for each real run, whether it passed review the first time (and if not, why), tokens and cost, and anything you weren't sure about. Also note how the new, longer plan changed tokens per run compared with before.

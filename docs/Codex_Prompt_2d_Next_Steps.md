# Codex instructions — Redesign the Next steps tab

Class progress now lives in the Check tab (step ④), so **remove the "Class progress" card from Next steps**. The Next steps tab gets two inner tabs:

**[ Next steps ] [ Additional resources ]**

Both work from **confirmed** results only (from an uploaded check, or the quick tap grid). `Codex_Prompt_1.md`, `1b`, `2`, `2b`, and `2c` still apply: readiness levels are Low / Mid / High everywhere, code does all the numbers, children's names never go to the model, and the same token logging, usage limits, Reviewer, and budget rules apply.

---

## 1. Top of the tab (shared by both inner tabs)

- A **check picker**: "Results from: Sun 25 Oct · 5-step · place value · 21 of 38 children", newest first, for the selected class.
- A one-line summary from the code diagnosis, plus a link: "Class average 62% · Low 38% · Mid 64% · High 85% · **See full progress in Check →**". No charts here; they're in Check ④.
- If there are no confirmed results yet: "Confirm results in the Check tab first", with a button that goes there.

## 2. Inner tab: Next steps (what we already decided)

The existing Next-Step Coach output, reorganised by readiness level:
- **Summary:** 2–3 plain sentences (numbers from the insight only; the existing number check stays).
- **Re-teach** (10–15 minutes, whole class, aimed at the most common error), if the action type calls for it.
- **Group activities for tomorrow:** three cards, **Low · Mid · High readiness** (with counts and the level colors), the same topic at three levels, runnable at the same time, plus how the teacher moves between groups in a 35–50 child class.
- **Peer helpers:** suggested pairs of a High child with a Low child. The pairing is done in code from results; names are added in code after generation.
- **Catch-up** for children who were absent or not checked.
- **Next lesson warm-up** and the **Use in next lesson** button (unchanged).
- Token/cost strip.

## 3. Inner tab: Additional resources

Two resource types. Each is generated **only when the teacher taps its button** (not automatically), to keep cost down; record this as a cost-saving measure for the report.

### 3a. Home practice worksheets

- **Generate worksheets** creates **three printable worksheets, one per readiness level** (Low / Mid / High), on the topic of the check, aimed at that level's weakest questions and concepts (from the code diagnosis).
- Each worksheet:
  - a title, the child's name and roll number lines (blank; names are filled in by code only when printing per child, see below), and a short "For parents" box: 2–3 simple sentences on how to help, written so a parent with little schooling can follow (e.g. "Ask your child to show you 34 using spoons. Praise them for trying.")
  - 6–8 short items, starting easy; at least two use **things found at home** (spoons, stones, rotis, coins, steps)
  - a "Fun at home" activity the family can do together (5 minutes, no materials to buy)
  - an **answer key on a separate page** for the teacher or parent
- Simple English, big text, one page each, black and white printable. Print shows one level per page.
- **Per-child copies:** a "Print for each child" button prints one copy per child, with their name and roll number filled in by code, grouped by readiness level (Low children get the Low sheet, and so on).
- **Children who need extra support** (see 3b) can also get a personal sheet: 6 items aimed at the specific questions they got wrong. Generated in a small batch, at most 10 children per tap.
- **Share:** "Copy as message" produces a short text version (the parent tips + 3 questions) that the teacher can paste into WhatsApp.
- The **Reviewer** checks every worksheet (`must_fix`: wrong answers in the key, wrong level, unsafe or costly home activity, too hard for the grade). For Mathematics, code also re-checks simple arithmetic answers in the key (e.g. `34 + 25 = 59`) and flags any mismatch as `must_fix`.

### 3b. Parent–teacher meeting plan for children who need support

- **Who needs support** is decided by code, and the teacher can change it. A child is suggested if any of these are true:
  - Low readiness and scored under 50% on this check;
  - scored under 40% on this check, at any level;
  - scored under 50% on 2 or more checks in a row;
  - was marked absent on 2 or more of the last 3 checks.
  Show the list with each child's reason (e.g. "Low readiness · 30% on place value · 2 checks in a row under 50%"). The teacher can tick or untick children, or add any child.
- **Generate meeting plans** creates one plan per selected child (at most 10 per tap). The model gets **roll numbers and results only, never names**; code inserts names afterwards. Each plan is one page:
  1. **Start with strengths:** 1–2 real things the child does well (from questions they got right, or the teacher's note)
  2. **What they find hard right now:** in plain words, from their wrong answers (e.g. "mixing up tens and ones, writing forty-three as 403"), with no labels like "weak" or "slow"
  3. **What we are doing in school:** the group and support they'll get (from the Next steps plan)
  4. **What you can do at home:** 3 simple, free, everyday activities (10 minutes a day), suitable for parents who may not read
  5. **Questions to ask the parent:** 2–3 open questions (e.g. "When does your child seem most interested in numbers?", "Is anything at home making study hard right now?")
  6. **What we agree:** a short checklist and a follow-up date (default: two weeks), to be filled in at the meeting
  7. **A short opening script** for the teacher (3–4 sentences, warm and respectful)
- The teacher can add a private note per child **before** generating (e.g. "parents are daily-wage workers, available only after 6 pm"). It's untrusted text: capped at 300 characters, checked for injection, and passed in tags.
- **Print all** (one child per page) and **Print one**.
- The **Reviewer** checks each plan (`must_fix`: blaming or labeling language, advice that costs money, invented facts not in the child's results, missing strengths). A code check confirms every score or count mentioned is in that child's results.

### Privacy (state this in the UI)

"Names and notes stay in Saathi. The AI only sees roll numbers and results." Meeting plans and personal worksheets are saved per child, and only visible to someone with the access code.

## 4. Agents and tools

- **Next-Step Coach:** unchanged, except output is organised by Low / Mid / High.
- **New: Resource Builder** agent with two output types, `HomeWorksheetSet` and `ParentMeetingPlan`. Tools:
  - `get_insight(check_id)`: class and level results
  - `get_child_results(check_id, roll_no)`: one child's per-question results and history, roll number only
  - `get_misconceptions(concept_id)`
  - `get_class_profile(class_id)`
- Plain code: choosing who needs support, peer-helper pairs, inserting names, arithmetic re-checks, number checks.
- Same token logging (`runs.kind` = `worksheets` / `meeting_plans`), `UsageLimits`, the daily budget, and at most one revision per item on `must_fix`.

## 5. Data

- `resources` table: id, check_id, kind (`worksheet_level` | `worksheet_child` | `meeting_plan`), readiness_level or roll_no, content_json, review_json, created_at.
- `support_selections`: check_id, roll_no, reason, selected_by_teacher, teacher_note.
- Regenerating replaces the old resource for the same check and child or level.

## 6. Tests

- The Class progress card is gone from Next steps; the link to Check ④ works.
- Support suggestions: each of the four rules, with hand-made results; the teacher can add or remove children.
- Names: prompts sent to the Resource Builder never contain a roster name; names appear in the printed output.
- Worksheets: three levels generated; the arithmetic re-check catches a wrong key (FunctionModel); per-child printing gives one sheet per child at the right level.
- Meeting plans: the number check catches an invented score; blaming language flagged by the Reviewer triggers exactly one revision (FunctionModel); the max-10 batch limit.
- Resources are generated only on a button tap (no automatic runs).

## Done means

1. `pytest` passes.
2. One real run on the Grade 3 class (from confirmed results): Next steps, then Generate worksheets, then Generate meeting plans for the suggested children (up to 5).
3. Commit, don't push; show `git status` first.
4. Report back: tokens and cost for each of the three runs; how many children were suggested for meetings and why; any Reviewer or code-check revisions; and screenshots or a description of each screen.

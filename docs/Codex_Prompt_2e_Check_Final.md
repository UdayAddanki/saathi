# Codex instructions — Final Check flow (wire it up for real)

This file is the **final word on the Check tab and how it connects to Next steps**. Where it differs from `Codex_Prompt_2c_Check_Redesign.md` (including its "Teacher-approved simplified Check flow" addendum) or `Codex_Prompt_2d_Next_Steps.md`, **this file wins**. Everything else in the earlier files still applies (Low / Mid / High readiness everywhere, code does all marking and numbers, the teacher confirms, names never go to the model, token logging, usage limits, budget, Reviewer).

## Decisions from the teacher

- **The answer key comes from the Plan tab.** Every Check starts by picking a lesson generated in Plan; that lesson's end-of-lesson check (the 5 MCQs for Grades 3–5, or the observation tasks for Grades 1–2) is the question paper and answer key. **There is no separate question-paper upload.** Remove the Paper Reader from the plan; don't build it.
- **No "choose children" step and no 50% rule.** Every child who has a submission is included. Results say "based on X of Y children".
- **Next steps keeps both inner tabs** (Next steps + Additional resources), as in `Codex_Prompt_2d_Next_Steps.md`. Ignore the 2c addendum line saying Next steps contains only diagnosis, coaching, and "Use in next lesson".

## The problem to fix first

`buildSimpleCheckFlow()` in `static/app.js` currently **replaces the whole Check tab with a mock-up** whose uploads go nowhere. It deleted the working Excel/CSV roll import, the Recent lesson picker, the quick tap grid, and Save results, so **no results can be entered and Next steps has no data**. Rebuild the Check tab so every step is wired to the backend. Never use `replaceChildren()` on the whole view; render each step into its own container.

## The Check tab: four steps, each a card

### ① Class roll
- Collapsed to one line once saved: "38 children · 10 Low · 16 Mid · 12 High · **Edit**".
- **Upload options:**
  1. **PDF** with three labelled sections (High readiness, Mid readiness, Low readiness). Read it with **code only** (`pypdf` text extraction plus heading detection, case-insensitive: "High readiness", "Mid readiness", "Low readiness", also "High / Mid / Low"). Keep roll numbers when present ("1. Anitha" or "1 Anitha"); otherwise number in order. **Never send a roll to the model.** If the PDF has no extractable text (a scan or photo), show: "This PDF looks scanned. Please upload a typed PDF, Excel, or CSV."
  2. **Excel or CSV**, the existing working import (roll number, name, readiness level).
- Preview in three colored columns before **Save roll**. All the earlier save fixes still apply (keep the file's roll numbers; clear errors; persists after refresh).
- Add a fixture `tests/fixtures/class_roll/class_roll_3A_buckets.pdf` (the same 38 children as the valid xlsx, in three labelled sections) and test that it imports to exactly 10 / 16 / 12 with the same roll numbers.

### ② Choose the lesson (this is the answer key)
- "Which lesson's check did children answer?" A list of this class's lessons from Plan, newest first: "Sun 25 Oct, 10:15 · 5-step · place value · 5 questions".
- Show the questions with the correct answers (read-only), and a **Print answer sheet** button: a one-page printable sheet with the roll number box at the top, question numbers, and A / B / C / D bubbles or answer lines. Children answer on this, which makes photos far easier to read.
- If the class has no lessons yet: "Create a lesson in Plan first", with a button to go there.

### ③ Upload submissions
"How are your submissions organized?" with two cards:

**Each student is one file**
- Multi-file upload (drag and drop or browse; `capture` on phones).
- **Matching files to children:** first by roll number in the file name (e.g. `12.jpg`, `roll_12.pdf`, `12_Ravi.jpg`); otherwise by the roll number the Answer Sheet Reader reads from the sheet's roll-number box; anything still unmatched shows a dropdown so the teacher assigns it. Show a matching table: file thumbnail → child (roll, name, level) → status.
- Teachers can add more files to the same check later.

**All students in one file**
- One PDF (or several photos) with everyone's sheets. The reader detects where each child's sheet starts, from the roll-number box on each page, and splits the pages. The teacher confirms the split in the same matching table (page range → child).
- **Import from Google Drive:** show the button disabled with "Coming soon". Don't build it (it needs Google sign-in and a key the course doesn't allow).

**File types:** PDF, JPG, PNG, HEIC. For Word (.docx) and PowerPoint (.pptx), show a friendly "Please save it as PDF and upload again" for now. All earlier upload limits, image resizing, and injection defenses apply.

**Reading and review:**
- The **Answer Sheet Reader** transcribes each child's answer per question with a confidence score. It does not mark. Code marks against the key from ②.
- **Review grid:** children × questions, showing what was read, the mark (✓ / ✗ / ?), and confidence, with low-confidence cells highlighted. Tap a cell to see the page and correct it. **Confirm results** saves them. Only confirmed results count.
- If section 0 of `Codex_Prompt_2c_Check_Redesign.md` showed that gpt-6-luna **can't** read images, say so on this card and send the teacher to the quick grid instead. **You still haven't reported the section 0 result; run it first.**

**Quick grid (always available):** a clear link under ③, "No answer sheets? Enter results quickly", opening the existing tap grid and class-count mode for the lesson chosen in ②. It saves confirmed results the same way, so everything downstream works. Grades 1–2 observation checks use the quick grid by default.

### ④ Class analysis (visual, Low / Mid / High colors)
From confirmed results only, for children with submissions, "based on X of Y children":
1. Class average mastery (ring)
2. Mastery by readiness level (three bars)
3. Student-wise mastery (dot or strip chart by level; tap for a child's answers)
4. Question-wise mastery (questions × levels heatmap; tap for the most common wrong answers, linked to misconceptions)
5. Concept bars by level
6. Over time (one line per level)
Then a **"See what to do next →"** button that opens Next steps for this check.

## Next steps tab: connect it

Wire up everything in `Codex_Prompt_2d_Next_Steps.md` to confirmed results from ③ or the quick grid:
- The "Results from" picker lists confirmed checks.
- **Next steps** inner tab: the Coach runs (summary, re-teach, Low / Mid / High group activities, peer helpers, catch-up, warm-up, "Use in next lesson").
- **Additional resources** inner tab: **Generate worksheets** and **Generate meeting plans** make real calls (the Resource Builder agent), with the support-suggestion rules, name insertion in code, the Reviewer, and the arithmetic and number checks.
- Remove every "not connected" message.

## Build order (commit and report after each)

1. Run the section 0 image/PDF test and report it. Confirm the roll save fix (10 / 16 / 12, roll 2 = Bhavya, Mid).
2. Rebuild the Check tab without wiping the view: ① roll (PDF + Excel/CSV), ② choose lesson + print answer sheet, the quick-grid link, ④ analysis. Test the whole loop with the quick grid: Plan → ② → quick grid (Fill sample results) → Confirm → ④ → Next steps.
3. Connect Next steps and Additional resources (real runs).
4. ③ uploads: each-student files with matching, then the all-in-one file with page splitting, the review grid, and Confirm results.

## Tests

- The Check tab keeps all four step containers after switching tabs (nothing is wiped).
- PDF roll: the buckets PDF imports correctly; a PDF with no text gives the "scanned" message; no model call is made for rolls.
- ② lists only this class's lessons; the key comes from the chosen lesson's check.
- File matching: by file name, by the roll-number box (FunctionModel), and teacher assignment for unmatched files.
- Single-file split: page ranges per child, teacher confirmation required.
- Word and PowerPoint get the "save as PDF" message.
- End to end with the quick grid: confirmed results → ④ charts data → Next steps Coach → worksheets → meeting plans (FunctionModel).

## Done means

1. `pytest` passes.
2. Real runs: the section 0 probe; one full loop with the quick grid (Plan → Check → Next steps → worksheets → meeting plans for up to 5 children); and, if images work, one upload run with 5 answer-sheet photos using the printed answer sheet from ②.
3. Commit after each build step; don't push; show `git status`.
4. Report back after each step: what works, tokens and cost of each real run, whether images worked, and what's still missing.

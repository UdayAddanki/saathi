# Final Project Plan — Saathi (Teacher Copilot)

**Due: Monday, October 26, 2026, 6:00 PM on Canvas.** Submit: GitHub repo link, `report.html`, `slides.html`, and an optional (but recommended) 2–3 minute demo video.

This plan cuts [Product_Design.md](Product_Design.md) down to what can be built well by Sunday night (one day before the deadline) and maps every piece to the grading rubric.

---

## 1. What we build (the MVP loop)

Scope: **Grades 1–5, NCERT or Telangana State (SCERT) curriculum**, chosen per class. Subjects: English and Maths (Grades 1–5), plus EVS (Grades 3–5). **English output only.**
- **Curated mode (deep):** primary Mathematics, with a vetted concept and misconception library. This is the showcase for diagnosis.
- **Open mode (broad):** any subject and chapter or topic. Plans are generated from board, grade, and topic, and suggested errors are labeled "AI-suggested".
- **Checks fit the age:** Grades 1–2 get oral or hands-on observation tasks marked Got it / Partly / Not yet. Grades 3–5 get 5 multiple-choice questions for the chalkboard.
- Chapter lists include only chapters verified from official textbooks. Teachers can always type a chapter or topic.

```
Teacher ──► [1. Plan]  Lesson Planner agent  ──► Check Builder agent ──► Reviewer agent
                                                                                 │
            printable plan + 5-question exit check  ◄────────────────────────────┘
                 │
                 ▼ (teacher teaches, students answer on paper)
            [2. Check]  teacher taps answers into roster grid
                 │
                 ▼
            [3. Diagnose]  analyze_results()  ← plain Python, no LLM
                 │          mastery %, top misconceptions, Ready/Practice/Re-teach groups
                 ▼
            [4. Next steps]  Next-Step Coach agent ──► Reviewer agent
                             reteach segment + 3-level group activity + worksheet
                 │
                 └──► feeds the next lesson plan (loop)
```

## 2. Agents and tools (rubric: Agent design, 10 pts)

All agents: **PydanticAI + gpt-6-luna via Portkey** (course key), with typed structured outputs.

| Agent | Job | Tools |
|---|---|---|
| **Lesson Planner** | Writes the 40-minute plan for the class's context; adds a review segment if past results show a gap | `get_curriculum_context(board, grade, subject, topic)`, `get_class_profile(class_id)`, `get_latest_insights(class_id)` |
| **Check Builder** | Grades 1–2: 3–5 observation tasks; Grades 3–5: 5 multiple-choice questions. Every wrong answer or common error is tagged with a misconception (from the library, or labeled AI-suggested) | `get_misconceptions(concept_id)` |
| **Next-Step Coach** | Turns the diagnosis into tomorrow's actions | `analyze_results(check_id)`, `get_prerequisites(concept_id)`, `get_misconceptions(concept_id)` |
| **Reviewer** | Checks output for math errors, wrong answer keys, age fit, and curriculum fit; returns pass or a fix list (one revision max) | `get_curriculum_context(...)` |

**Orchestration is plain Python, not an LLM router.** The steps are always the same, so a fixed pipeline is cheaper, faster, and cannot be hijacked into calling the wrong agent. The report argues this choice explicitly.

**Diagnosis is plain Python.** Mastery %, misconception counts, and groups are computed by code so the numbers teachers see are never invented.

## 3. App and tech (rubric: It works 15, Can run it 5, Look + feel 10)

- **Backend:** FastAPI + PydanticAI + SQLite (one file, created automatically).
- **Frontend:** plain HTML/CSS/JS served by FastAPI. **No npm build step**, so `pip install` + one command runs it. Mobile-first, three tabs: **Plan · Check · Next steps**, plus **Usage**.
- **Data:** `data/boards.json` (boards → grades → subjects → verified chapters), `data/concepts.json` and `data/misconceptions.json` (primary maths library), plus two demo classes (Grade 3 Telangana, Grade 1 NCERT). Teachers can add their own classes.
- **.env lookup:** repo folder first, then one folder up (as required). `.env.example` lists `PORTKEY_API_KEY`.
- **Hosting:** deployed online (e.g. Render free tier) so pilot teachers can open a link on their phones; link goes at the top of the README and report. Also runs locally from a fresh clone.
- **Run locally:** `pip install -r requirements.txt` → `python run.py` → open `http://localhost:8000`.
- **Online safety:** a simple access code for pilot teachers plus the daily token budget, so a public link cannot burn through the course key.

## 4. Tokenomics (rubric: 8 pts — needs real counts)

- Every agent call logs **input, cached input, output tokens, and cost** to SQLite.
- The app shows tokens and cost **after each run** and on a **Usage** page (this is the screenshot evidence).
- Cost cutting to build and measure:
  1. **Prompt caching:** long, stable content (system prompt + curriculum + misconception library) goes first so repeat calls hit the cache.
  2. **Diagnosis in code**, not in an LLM.
  3. **Plan reuse:** the same lesson for a similar class reuses the cached plan and only regenerates the adapted parts.
  4. **Short structured outputs** with limits.
- **Evidence for "did cost cutting hurt quality?":** run the same lessons with and without the cuts; compare Reviewer pass rate and a quick quality rubric.
- Model scale-up: cost per run → per teacher per month (~22 school days × planned runs) → 100 and 10,000 teachers.

## 5. Safety (rubric: 8 pts — needs a defense shown working)

| Risk | Defense built | Evidence |
|---|---|---|
| **Prompt injection** in teacher notes ("ignore your instructions…") | Input guard (pattern check + length cap), notes wrapped as untrusted data, structured output only | Test + screenshot of the blocked attempt |
| **Wrong math / wrong answer key** | Reviewer agent; code checks every misconception ID exists; answer key checked against option list | Test where a bad question is caught and fixed |
| **Runaway loops** | Max 1 revision; PydanticAI `UsageLimits` (request and token caps per run) | Test |
| **Overspending** | Daily token budget per teacher in SQLite; request refused when exceeded | Test + screenshot of the refusal |
| **Student privacy** | Only roll numbers and first names; names never sent to the model | Shown in the code and the logs |

Tests go in `tests/` (pytest), and their output is screenshotted for the report.

## 6. Impact (rubric: 5 pts + Tier 3 — needs a real user)

**This is the most time-sensitive item.** By Sunday we need at least 1–3 real teachers to try it:
- Time to a ready lesson plan with Saathi vs. their normal time.
- Their rating of plan quality (1–5) and whether they would teach from it.
- One quote and a screenshot or photo.
- Even better: one teacher runs a real exit check in class, and we enter the results.

Supporting numbers: published data on Indian teacher workload and class sizes, with sources.

## 7. Schedule (target: everything done Sunday night, Oct 25)

Monday is buffer only. India is 9.5 hours ahead of New Haven, so the teachers' Sunday daytime is Saturday night through Sunday morning here. That's why the Plan flow has to be online by Saturday night.

| When (New Haven time) | Work |
|---|---|
| **Sat Oct 24, afternoon** | Phase 1 (Codex): data files, agents, pipeline, token logging, Plan screen, tests |
| **Sat Oct 24, night** | Deploy online (Render) behind an access code; push to GitHub. **Send the link to teachers** to try lesson planning during their Sunday |
| **Sun Oct 25, morning** | Phase 2: Check + Next steps screens, diagnosis, Next-Step Coach; safety guards + tests; budget cap. Collect teacher feedback on Plan (time taken, rating, quote) |
| **Sun Oct 25, early afternoon** | Redeploy; one full loop on a real or realistic class; screenshots of a full run, Usage page, and blocked attacks; cost-cutting comparison runs |
| **Sun Oct 25, late afternoon** | Fresh-clone dry run with `.env` one folder up; README final; optional demo video |
| **Sun Oct 25, evening** | `report.html` and `slides.html` (reveal.js, images embedded); final check; **submit on Canvas** |
| **Mon Oct 26** | Buffer only: fix anything broken; late teacher feedback can be added to the report before 6 PM |

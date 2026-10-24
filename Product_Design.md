# Teacher Copilot for Indian Classrooms — Product Design

*Working name: **Saathi** (companion). Placeholder; easy to change.*

---

## 1. Product concept

### The problem with "just a lesson-plan generator"

A lesson-plan generator answers one question: *What should I teach?* It saves the teacher time, but it is blind to what happens after the lesson. It does not know whether students understood, so tomorrow's plan is generated exactly as if today never happened. In an Indian classroom of 40–60 students spanning three or four grade levels of actual ability, that is the core failure: teachers move on with the syllabus while a large share of the class falls further behind.

### The concept

Saathi is a **teacher copilot built around a single loop**:

```
        ┌──────────────┐
        │  1. PLAN     │  What should I teach?
        │  lesson +    │
        │  exit check  │
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  2. TEACH    │  (in class, offline, on paper)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  3. CHECK    │  Are my students learning?
        │  5-question  │
        │  exit check  │
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  4. DIAGNOSE │  Which concepts, which students,
        │  gaps +      │  which misconceptions?
        │  groups      │
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  5. ACT      │  What should I do next?
        │  reteach +   │  → feeds the next PLAN
        │  grouped work│
        └──────────────┘
          (loop back to 1)
```

Every lesson plan comes with a **short diagnostic check built in**. The answers to that check drive the **next** lesson plan. The product's value comes from the loop, not from any single feature.

### Three design principles

1. **Paper-first, phone-second.** Students do not need devices. Everything students see can be printed or written on a chalkboard. Only the teacher uses a phone (or occasionally a laptop).
2. **Every wrong answer carries information.** Assessment questions are built so that each wrong option maps to a specific, named misconception ("adds numerators and denominators: 1/2 + 1/3 = 2/5"). One tap per student gives a diagnosis, not just a score.
3. **Teach at the right level, inside the timetable.** Recommendations use 2–3 ability groups (the *Teaching at the Right Level* approach, which has strong evidence in India from Pratham and J-PAL) rather than 50 individual learning paths that no teacher can run.

### The AI's job vs. the system's job

| Task | Who does it | Why |
|---|---|---|
| Write lesson plans, activities, worksheets, local examples, translations | LLM, grounded in curriculum content | Language generation is what LLMs are good at |
| Write diagnostic questions with misconception-tagged distractors | LLM drafts → validated against a curated misconception library → teacher can edit | Needs accuracy; LLMs alone make subtle errors |
| Score answers, compute mastery, form groups | Plain code (rules + simple statistics) | Must be correct, explainable, and consistent. No LLM needed |
| Turn the diagnosis into next steps in plain language | LLM, given the computed results | Explanation and content generation |

Keeping the diagnosis deterministic is important. Teachers need to trust "14 students don't understand equivalent fractions," and that number should never be hallucinated.

---

## 2. Core teacher journey

**Persona: Meena**, Grade 6 Maths and Science teacher at a government school in Karnataka. 52 students. Teaches in Kannada with English terms. Has an Android phone with patchy 4G. Not a heavy app user, but uses WhatsApp and YouTube daily.

### Monday evening — Plan (≈10 minutes)

1. Opens Saathi. The home screen shows **"Tomorrow: Grade 6-B Maths, Fractions — Chapter 7, Lesson 3"**, already suggested from her syllabus pace and last week's results.
2. Taps **Prepare lesson**. Sees a one-page plan (40 min): learning objective (tied to the official NCERT learning outcome code), a 5-minute warm-up, explanation with a local example (dividing rotis or a cricket score), a pair activity that needs no materials, and a **5-question exit check**.
3. A note at the top: *"Last week, 18 students struggled with comparing fractions. A 7-minute review is added to the warm-up."*
4. Taps **Simpler language** on one section and **Kannada** for the whole plan. Saves.
5. Taps **Print / Share**. Gets a one-page PDF and a chalkboard version of the exit check. Everything is cached for offline use.

### Tuesday in class — Teach (no phone required)

6. Teaches from the printed or cached plan.
7. The last 5 minutes: copies the 5 exit-check questions on the board. Students write answers (A/B/C/D) in their notebooks or on a slip.

### Tuesday after class — Check (≈5–8 minutes)

8. Opens **Check** for 6-B. Sees her roster as a grid: one row per student, one column per question.
9. Enters answers quickly. Three options, from simplest to most advanced:
   - **Tap grid** (MVP): taps the letter each student chose. Correct answers are one tap via "mark all correct, then fix the wrong ones."
   - **Count mode** (fallback for very large classes): enters only how many students chose each option per question, using a show of hands. This gives a class-level diagnosis without per-student data.
   - **Scan** (later version): students hold up printed QR answer cards (like Plickers) or the teacher photographs answer slips.
10. Works offline. Syncs when she next has a signal.

### Tuesday evening — Diagnose (≈2 minutes, just reading)

11. The **Class Insight** card:
    - *"Equivalent fractions: 71% got it ✅"*
    - *"Comparing unlike fractions: 38% got it ⚠️. Most common error: thinks a bigger denominator means a bigger fraction (19 students)."*
    - Students grouped automatically: **Ready to move on (21)**, **Needs practice (19)**, **Needs re-teaching from basics (12)**.
12. Taps a group to see names. She can drag a student to a different group if she knows better.

### Wednesday — Act

13. Wednesday's lesson plan already includes:
    - a 10-minute whole-class reteach of "comparing fractions" that directly targets the misconception (using a fraction strip drawing on the board);
    - a **3-level group activity**: the same topic at three difficulty levels, printable on one sheet cut into three parts;
    - a peer-tutor suggestion: pair a "Ready" student with a "Re-teach" student.
14. Optional: taps **Send home practice** to send a short voice note plus 3 practice questions in Kannada to parents via WhatsApp.
15. The loop repeats. After 2–3 cycles, Meena's **Progress** view shows how each concept and each student has moved.

**Total teacher time per day: about 15–20 minutes**, with most of it replacing work she already does (planning and correcting).

---

## 3. MVP vs. future capabilities

### Prioritization logic

Each feature is scored on three questions:
- **Learning impact:** Does it directly change what happens in the classroom for struggling students?
- **Loop necessity:** Is the loop broken without it?
- **Feasibility:** Can a small team build it well in a few months, and can teachers use it on a basic phone with poor internet?

### MVP: the smallest version where the loop works

Scope it narrowly: **one board (e.g. NCERT/CBSE), Grades 6–8, Maths and Science, English + one Indian language.**

| # | Feature | Why it is in the MVP |
|---|---|---|
| 1 | **Curriculum map** (chapters → concepts → learning outcomes → prerequisites) | Everything else depends on it. Tags every plan, question, and result to a concept |
| 2 | **Lesson plan generator with built-in exit check** | Answers "What should I teach?" and creates the assessment for free |
| 3 | **Misconception-tagged question bank** (LLM-drafted, curated, teacher-editable) | Turns a score into a diagnosis |
| 4 | **Class roster + quick answer entry** (tap grid + count mode), offline | Captures the data the loop needs, in a few minutes |
| 5 | **Class Insight report** (concept mastery, top misconceptions, 3 groups) | Answers "Are my students learning?" |
| 6 | **Next-step recommendations** (reteach segment, 3-level activity, printable differentiated worksheet) automatically added to the next plan | Answers "What should I do next?" and closes the loop |
| 7 | **Print / PDF / chalkboard export, offline caching, simple language switching** | Makes it usable in a real classroom |

Not in the MVP: parent messaging, attendance, admin dashboards, scanning, student logins.

### Version 2: deepen the loop (after the pilot proves teachers complete it)

| Feature | Learning value |
|---|---|
| **Student progress over time** (per-student concept history) | Spot students who are persistently behind, not just behind today |
| **QR answer cards / photo scan** | Cuts entry time to under 1 minute and makes per-student data effortless |
| **Parent home practice via WhatsApp** (voice + text, regional language) | Extends practice time for "Needs practice" students; parents in India are reachable on WhatsApp far more than on any app |
| **Lightweight attendance** (one-tap, from the same roster) | Only as context: *"6 students were absent for Lesson 3. Here is a 5-minute catch-up."* |
| **Unit tests and periodic assessments** | A broader check than daily exit tickets; feeds the same mastery model |
| **More boards, grades, subjects, languages** | Expansion once quality is proven |
| **Voice input** (dictate a request like "make this easier for weak students") | Helps teachers with lower digital literacy |

### Version 3: scale and system-level

| Feature | Note |
|---|---|
| **Head-teacher / cluster view** | Which concepts are weak across a school or cluster, so training and support can be targeted |
| **Administrative reporting** | Needed for government partnerships, but kept separate so the teacher's tool does not become a compliance burden |
| **Teacher community library** | Share and rate plans and activities that worked |
| **Adaptive practice for students with device access** | Only where devices actually exist |

### Ranking the complementary features by learning impact

| Feature | Learning impact | Recommendation |
|---|---|---|
| Progress dashboards | **High.** Core to "Are my students learning?" | MVP (class level), V2 (student history) |
| Parent communication | **Medium–High.** More practice time and family involvement | V2, focused on practice, not just notices |
| Attendance tracking | **Medium.** Useful only when linked to missed concepts | V2, one tap, as context for catch-up |
| Administrative reporting | **Low for learning** directly; high for adoption | V3, opt-in, never adds teacher work |
| Engagement monitoring | **Low and risky.** Hard to measure without cameras or devices; feels like surveillance | Skip. Use the exit-check results as the engagement signal |

---

## 4. How each feature works and what data it needs

### 4.1 Curriculum map

- **How it works:** A structured database of the syllabus. Each chapter is broken into concepts, each concept is linked to official learning outcomes (NCERT learning outcome codes, NCF 2023 competencies) and to prerequisite concepts (e.g. *comparing fractions* depends on *equivalent fractions*).
- **Data needed:** NCERT/state textbooks and syllabi (publicly available), learning outcome documents, prerequisite links (LLM-drafted, then reviewed by subject experts).
- **Effort note:** This is the most important piece of groundwork. For the MVP, build it by hand plus LLM help for a narrow scope.

### 4.2 Lesson plan generator

- **How it works:** The teacher picks class, chapter, and lesson (or accepts the suggestion). The system retrieves the relevant textbook section and concept data (retrieval-augmented generation), adds class context, and asks the LLM for a fixed-format plan: objective, warm-up, explanation, activity, exit check, homework. Quick edit buttons regenerate one section: *Simpler*, *More activity-based*, *No materials*, *Translate*.
- **Data needed:**
  - *Class profile* (entered once): grade, subject, board, language, class size, available resources (chalkboard only / projector / lab), period length.
  - *Curriculum content* from 4.1.
  - *Latest class results* from 4.5, so the plan can include review.
- **Quality safeguards:** Plans are tied to the textbook text; a second automatic check verifies facts and age fit; teachers can flag errors with one tap.

### 4.3 Misconception-tagged question bank

- **How it works:** Each concept has a list of known misconceptions (from research literature and teacher input). Exit-check questions are multiple choice, and each wrong option is written to reveal one misconception. Example:

  > Which is bigger: 1/3 or 1/5?
  > A) 1/3 ✅ B) 1/5 ← *"bigger denominator = bigger fraction"* C) They are equal ← *"compares numerators only"* D) Cannot tell

- **Data needed:** Misconception library per concept (seeded from research and resources such as Ei's diagnostic studies and NCERT materials, then expanded by LLM drafting with expert review); question metadata (concept, difficulty, misconception per option).
- **Why it matters:** A score of 2/5 says little. "Chose B on question 3" tells the teacher exactly what to reteach.

### 4.4 Quick answer entry (offline)

- **How it works:** A roster grid on the phone. Default all answers to correct; the teacher taps only the exceptions and picks the wrong option chosen. Count mode records class totals per option when per-student entry is not practical. All data is stored on the phone and synced later.
- **Data needed:** Student roster (name or roll number only; no other personal data needed in the MVP) and answers per student per question.
- **Target:** Under 5 minutes for a class of 50 in tap mode, under 2 minutes in count mode.

### 4.5 Class Insight report

- **How it works (plain code, no LLM):**
  - *Concept mastery* = % of students who answered that concept's questions correctly.
  - *Top misconceptions* = the wrong options chosen most often, with counts.
  - *Groups*: each student is placed in **Ready / Practice / Re-teach** based on their score on the current concept and whether they have missed the prerequisite.
  - The LLM then writes a 2–3 line plain-language summary from these numbers only.
- **Data needed:** Answers (4.4), question metadata (4.3), prerequisite links (4.1), and past results where available.

### 4.6 Next-step recommendations

- **How it works:** Simple rules decide *what kind* of action is needed; the LLM generates *the content*.

  | Situation | Recommended action |
  |---|---|
  | Over 80% mastery | Move on; give "Practice" students a 5-minute warm-up next lesson |
  | 50–80% | Grouped activity at 3 levels + targeted practice sheet |
  | Under 50% | 10–15 minute whole-class reteach targeting the top misconception |
  | Prerequisite gap found | Short review of the prerequisite concept before continuing |
  | Same student in "Re-teach" 3 times in a row | Flag for individual attention, peer tutor, or parent practice |

- **Output:** Changes are automatically added to the next lesson plan (teacher can accept, edit, or skip), plus a printable 3-level worksheet.
- **Data needed:** Insight results (4.5), curriculum map (4.1), teacher's class profile, and whether past recommendations were used (to learn what works).

### 4.7 Progress view

- **How it works:** A grid of concepts (columns) by students (rows), colored green / amber / red over time; a class-level line of concept mastery across the term.
- **Data needed:** Accumulated results from 4.5.

### 4.8 Parent home practice (V2)

- **How it works:** The teacher taps *Send home practice*. Each group gets a different, short message on WhatsApp: a voice note in the home language plus 2–3 questions a parent can check even without knowing the subject.
- **Data needed:** Parent phone numbers and language, explicit parental consent.

### 4.9 Attendance (V2)

- **How it works:** One-tap present/absent on the same roster. Used only to flag students who missed a concept and suggest a catch-up.
- **Data needed:** Daily attendance per student.

### Data privacy

India's Digital Personal Data Protection Act (2023) requires verifiable parental consent to process children's data. The MVP keeps student data to the minimum (roll number and first name, answers), stores it encrypted, never uses it to train models, and gives schools a clear consent form before parent phone numbers are collected in V2.

---

## 5. Website interface and dashboard

### Principles

- **Mobile-first web app** (a Progressive Web App that installs to the home screen, works offline, no app store needed). It also works on a laptop.
- **Three tabs only**, matching the three questions: **Plan**, **Check**, **Next steps**. Plus **Classes** for setup.
- **Large tap targets, icons + words, local language throughout**, no jargon (say "students who need help," not "remediation cohort").
- **One primary action per screen.** Never a blank prompt box. The teacher picks from options; free text is optional.
- **Light pages** that load fast on 3G; images optional.

### Home screen — "Today"

```
┌─────────────────────────────────────┐
│  Namaste, Meena 👋        ☁ Synced  │
│                                     │
│  TODAY                              │
│  ┌───────────────────────────────┐  │
│  │ 📘 6-B Maths · 10:30          │  │
│  │ Fractions – Lesson 3          │  │
│  │ + 7 min review (18 students)  │  │
│  │ [ Open plan ]  [ Print ]      │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ ✏️ 6-A Science · Exit check    │  │
│  │ not entered yet               │  │
│  │ [ Enter answers ]             │  │
│  └───────────────────────────────┘  │
│                                     │
│  THIS WEEK IN 6-B                   │
│  Comparing fractions   ▓▓▓▓░░ 38% ⚠ │
│  Equivalent fractions  ▓▓▓▓▓░ 71% ✅ │
│                                     │
│ ─────────────────────────────────── │
│  📝 Plan   ✅ Check   ➡️ Next   👥 Class │
└─────────────────────────────────────┘
```

### Check — answer entry grid

```
┌─────────────────────────────────────┐
│  ← 6-B · Fractions L3 · Exit check  │
│  Mode: [Each student] [Class count] │
│                                     │
│  All marked ✅. Tap to change.       │
│         Q1  Q2  Q3  Q4  Q5          │
│  1 Aarav ✅  ✅  B   ✅  ✅          │
│  2 Bhavya✅  C   B   ✅  ✅          │
│  3 Chetan✅  ✅  ✅  ✅  D           │
│  ...                                │
│                                     │
│        [ Save — works offline ]     │
└─────────────────────────────────────┘
```

### Next steps — Class Insight

```
┌─────────────────────────────────────┐
│  6-B · After Fractions L3           │
│                                     │
│  ⚠ Comparing fractions: 38% got it   │
│  19 students think a bigger         │
│  denominator means a bigger fraction│
│                                     │
│  GROUPS                             │
│  🟢 Ready to move on      21  ›      │
│  🟡 Needs practice        19  ›      │
│  🔴 Re-teach basics       12  ›      │
│                                     │
│  SUGGESTED FOR TOMORROW             │
│  • 10-min reteach with fraction     │
│    strips (board drawing)           │
│  • 3-level group worksheet          │
│  • Pair 🟢 with 🔴 students          │
│                                     │
│  [ Add to tomorrow's plan ]         │
│  [ Send home practice 📱 ]  (V2)    │
└─────────────────────────────────────┘
```

### Progress dashboard (laptop or phone)

```
┌───────────────────────────────────────────────────────┐
│  6-B Maths · Term 1 progress                          │
│                                                       │
│  Class mastery by concept                             │
│  Fractions basics    ████████████████░░  84%  ↑ +22   │
│  Equivalent          ██████████████░░░░  71%  ↑ +15   │
│  Comparing           ████████░░░░░░░░░░  38%  new     │
│                                                       │
│  Students needing attention (3+ weeks in 🔴)           │
│  Chetan, Divya, Farhan, Gauri               [ View ]  │
│                                                       │
│  Student × concept grid                               │
│             Basics  Equiv  Compare  Add               │
│  Aarav        🟢     🟢      🟢       ·                │
│  Bhavya       🟢     🟡      🔴       ·                │
│  Chetan       🔴     🔴      🔴       ·                │
└───────────────────────────────────────────────────────┘
```

---

## 6. Metrics: is it actually improving learning?

The platform's own exit checks are useful for teachers but biased as evidence: the same tool writes the questions and the lessons. The real test of impact must use an **independent assessment**.

### North-star outcome

**Learning gain on an independent test**: improvement from baseline to endline on a standard assessment (e.g. items from the state's learning assessment survey, NAS/PARAKH items, or an ASER-style tool), compared with similar classrooms not using Saathi.

### Metric tree

| Level | Metric | What it tells you |
|---|---|---|
| **Learning outcomes** (lagging) | Baseline → endline gain, Saathi vs. comparison classes | Does it work? |
| | Gain for the bottom third of students | Does it help those who need it most? (equity) |
| | Misconception rate after reteach vs. before | Does the reteach step actually fix the gap? |
| | % of "Re-teach" students who reach "Ready" within 2 weeks | Gap closure speed |
| **Teacher practice** (leading) | **Loop completion rate**: % of lessons where the exit check is entered *and* a next step is used | The single most important product metric. No loop, no impact |
| | % of recommendations accepted, edited, or skipped (and why) | Are recommendations useful? |
| | Time from opening the app to a ready plan; time to enter answers | Is it fast enough? |
| **Adoption** | Weekly active teachers; 4-week and 8-week retention | Will teachers keep using it? |
| **Teacher experience** | Self-reported preparedness and confidence (short monthly pulse) | The "small wins" goal from the original idea |
| **Quality** | Teacher-flagged errors per 100 plans; expert review score on a sample | Is the content trustworthy? |

### Pilot evaluation design (suggested)

- 8–15 teachers, ideally across 2–3 schools, with a similar set of comparison classrooms.
- 8–10 weeks covering 2–3 chapters.
- Baseline and endline independent test on those chapters.
- Weekly short calls or WhatsApp check-ins with teachers; usage logs for the loop metrics.
- Be explicit that a small pilot gives **directional** evidence, not proof. It is mainly for learning whether teachers complete the loop and which recommendations they find useful.

---

## 7. Differentiation from existing AI teaching tools

| Tool type | Examples | What they do | Gap Saathi fills |
|---|---|---|---|
| General chatbots | ChatGPT, Gemini | Anything on request | No curriculum structure, no memory of the class, starts blank every time |
| Teacher AI toolkits (global) | MagicSchool, Brisk, Eduaide | Many content generators | Content tools, not a loop; built for US classrooms with devices |
| Indian lesson-plan copilots | e.g. Shiksha Copilot (Microsoft Research + Sikshana Foundation) and state initiatives | Curriculum-aligned plans in local languages | Mostly stop at planning; Saathi adds diagnosis and next steps |
| Adaptive learning for students | Mindspark (Ei), Khan Academy / Khanmigo, BYJU'S | Personalized practice on student devices | Need one device per student; Saathi works with zero student devices |
| Assessment tools | Google Forms, Plickers, OMR apps | Collect answers | Give scores, not misconception diagnosis or a next-lesson plan |

### Saathi's differentiators

1. **The closed loop.** Tomorrow's plan is shaped by today's results. Few tools connect planning, assessment, and intervention in one flow.
2. **Diagnosis, not scores.** Misconception-tagged questions tell the teacher *why* students are wrong.
3. **Zero student devices.** Paper and chalkboard on the student side; one phone for the teacher; offline by default.
4. **Teach at the right level, in practice.** 3 groups the teacher can actually run in a 40-minute period with 50 students, based on an approach with strong evidence in India.
5. **Built for Indian classrooms.** NCERT and state board alignment, local-language and code-mixed output, local examples, chalkboard-only activities, large-class defaults.
6. **Trustworthy numbers.** Diagnosis is computed by plain code; the AI explains and creates content but never invents the results.

---

## 8. Risks and how to handle them

| Risk | Mitigation |
|---|---|
| Teachers skip the exit check, so the loop breaks | Make it 5 questions and under 5 minutes; count mode as a fallback; the plan improves visibly when they do it |
| AI content errors (wrong facts, poor translations) | Ground in textbook text; automatic checks; one-tap flagging; native-speaker review for each language |
| Weak misconception library at launch | Start narrow (one subject, a few chapters); seed from research; let teachers add misconceptions they see |
| Poor connectivity | Offline-first design; small downloads; print-ready outputs |
| Becomes another reporting burden | Admin features are opt-in and read-only; the teacher view never asks for data that does not help the teacher |
| Children's data privacy | Minimal data, consent, encryption, no model training on student data (DPDP Act 2023) |

---

## 9. Suggested build plan for the final project

Given the course scope, a realistic project deliverable:

1. **Curriculum slice:** 1 subject, 1 grade, 2–3 chapters (e.g. NCERT Grade 6 Maths, Fractions and Decimals), with concepts, prerequisites, and misconceptions.
2. **Working prototype** (Python + Streamlit or a simple web app, LLM via API):
   - Plan: generate lesson plan + exit check
   - Check: roster grid answer entry
   - Next steps: Class Insight report + generated next-lesson changes and 3-level worksheet
3. **Pilot with a few teachers in India:** have them run 2–3 loops; collect timing, usage, and feedback.
4. **Write-up:** the problem, the loop design, what teachers did and said, metrics, and what to build next.

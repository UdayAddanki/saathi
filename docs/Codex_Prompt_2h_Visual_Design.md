# Codex instructions — Make Saathi look and feel like a primary school classroom

Give the app a warm, playful **elementary school** look with small creative touches that make it feel interactive and friendly, while staying **clear, fast, and professional for teachers**. This is a **look-and-feel change only**: don't change any features, routes, or data. All tests must keep passing.

Do this **after** the accounts work is merged, and **before** `Codex_Prompt_3.md`, so the report's screenshots show the final design.

---

## 1. The idea: "a classroom notebook"

The teacher should feel they're working in a cheerful classroom, not a spreadsheet.
- **Page background:** off-white notebook paper (`#FFFDF6`) with very faint ruled lines and a thin red margin line on the left, made with CSS gradients (no image files).
- **Top bar:** a **chalkboard** band (deep chalkboard green `#2F5D50`, with a subtle chalk-dust texture made in CSS or a tiny inline SVG noise) and a light wooden frame line at the bottom. "Saathi" written in a friendly rounded heading font in chalk-white, with 2–3 small chalk doodles (a star, a little sun, "ABC 123").
- **Cards:** paper cards with rounded corners, a soft shadow, and a strip of **washi tape** (a small translucent colored rectangle, slightly rotated) on the top corner of main cards. Keep form cards straight; only decorative elements tilt.
- **Doodles:** a small set of hand-drawn-style **inline SVG** doodles (pencil, crayon, paper plane, star, sun, leaf, kite, apple, abacus, ABC blocks, a Bathukamma-style flower for Telangana classes). Place them in page margins and empty spaces at low opacity (10–20%). **Never behind text, inputs, or buttons.** Hide most of them on small screens so the phone layout stays clean.

## 2. Colors (crayon box, kept accessible)

- Chalkboard green `#2F5D50` (primary, header, main buttons)
- Paper `#FFFDF6` (background), card white `#FFFFFF`
- Saffron `#F2A93B` (accent, highlights)
- Sky blue `#5DA9E9` (links, info)
- **Readiness levels keep their meaning and colors everywhere:** Low = coral `#EF6F5E`, Mid = amber `#F4B942`, High = teal `#2A9D8F`
- Text: near-black `#1F2A2E` on paper. **Every text and background pair must meet WCAG AA contrast** (4.5:1 for body text). Darken a color for text use if needed (e.g. a darker amber for amber text).

## 3. Type

- **Headings:** a rounded, friendly font. Self-host one open-licence font file (e.g. *Baloo 2* or *Nunito*, OFL) as `static/fonts/*.woff2` with its licence file. **No CDN.** Use it for headings and big numbers only.
- **Body:** the system font stack, at least 16px, line height 1.5. Form labels and plan text must stay very readable.

## 4. Friendly touches that feel interactive

- **Greeting:** "Good morning, Meena! ☀️" (or afternoon/evening by local time, using the username), with a rotating short teacher encouragement ("Small steps every day add up." / "Every child can grow.").
- **Tab bar:** four big crayon-colored tabs with simple icons: 📘 Plan, ✅ Check, 👣 Next steps, and Usage only where it's shown. The active tab looks like a crayon-highlighted label.
- **Readiness as growth, not labels:** show Low / Mid / High with small plant icons, 🌱 Low · 🌿 Mid · 🌳 High (inline SVG or emoji), everywhere levels appear: roll columns, charts legend, group cards. It's encouraging and avoids labelling children.
- **Waiting moments:** while a lesson is being prepared (30–60 seconds), show a friendly animation, e.g. a pencil drawing a wavy line across a notebook page, with the current step underneath ("Planning your lesson… → Writing the check… → Checking quality…") and "This takes about a minute". The same style while sheets are being read ("Reading sheet 3 of 5…").
- **Little celebrations:** a short burst of stars (under 1 second, a few CSS-animated SVG stars) when a lesson is ready, results are confirmed, or worksheets are generated. Plus a gentle message: "Lesson ready! ⭐", "Results confirmed. Great work!".
- **Buttons:** rounded, chunky, with a slight "press" effect (move down 1–2px, the shadow shrinks) and a clear focus ring.
- **Empty states with friendly illustrations:** e.g. no lessons yet → a small doodle of a book and pencil, "No lessons yet. Let's plan your first one!" with a button; no roll yet → "Add your class roll to get started."
- **Lesson type cards:** each gets its own small icon and color (5-step 🪜, 5E 🔍, Project-based 🛠️, Experiential 🌍, 5 Magic Questions ✨), and lifts slightly on hover or tap.
- **Charts** (Check ④): use the crayon colors, rounded bar ends, and the plant icons in the legend; labels stay plain and readable.
- **Welcome / log-in page:** a big chalkboard with "Saathi: plan, check, and know what to do next" in chalk, a few doodles around it, and the log-in card pinned with washi tape.

## 5. Rules (don't break these)

- **Usability first:** decoration never covers content, never moves while someone is typing, and never makes a page harder to scan. On a phone (375px), keep decoration minimal: the chalkboard header and plant icons, with almost no margin doodles.
- **Respect `prefers-reduced-motion`:** turn off the pencil animation, star bursts, and hover lifts, and use simple text progress instead.
- **Accessibility:** AA contrast; tap targets at least 44px; visible focus rings; decorative SVGs get `aria-hidden="true"`; icons that carry meaning (like the plant levels) also have text ("Low readiness").
- **Print stays plain:** print CSS removes backgrounds, doodles, tape, and colors so lesson plans, answer sheets, worksheets, and meeting plans print clean black-on-white. Answer sheets must stay exactly as readable for the Answer Sheet Reader as they are now; **don't restyle the printed answer sheet**.
- **Performance:** no external requests; all added assets (font plus SVGs) under about 150 KB total; doodles inline or in one SVG sprite.
- **Consistency:** put all colors, spacing, radius, and shadows in CSS variables at the top of `app.css`, and use them everywhere.
- Keep `app.css` and `app.js` readable and organised (sections with comments: tokens, layout, components, doodles, animations, print).

## 6. Done means

1. `pytest` passes; no feature changes.
2. Take **before and after screenshots** at 390×844 (phone) and 1280×800 (laptop) of: the welcome/log-in page, Plan (form and a finished plan), Check (roll, ③ review grid, ④ charts), Next steps, and Additional resources. Save them in `evidence/design/` (the report will use them).
3. Check the reduced-motion version and the print preview of a lesson plan and an answer sheet, and say whether they're clean.
4. Run a quick contrast check on the main text, button, and readiness colors, and list the ratios.
5. Commit, don't push, and report what changed, with the screenshot file names.

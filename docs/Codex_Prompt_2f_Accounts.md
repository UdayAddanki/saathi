# Codex instructions — Teacher accounts (sign up, log in, own data)

Teachers create an account and use it every time. Each teacher sees **only their own** classes, rolls, lessons, results, and resources. Build this **after** `Codex_Prompt_2e_Check_Final.md` build steps 1–3 are committed. All earlier rules still apply.

Keep it simple: teachers sign up with just a **username and password**, plus an email used **only** to send a password-reset link. No mobile numbers, no SMS, no Google sign-in.

---

## 1. Sign up

A clean welcome screen when nobody is logged in: "Saathi: plan, check, and know what to do next", with **Create account** and **Log in**.

**Create account** has only these fields:
- **Username**: the login ID. 3–30 characters: letters, numbers, `.`, `_`, `-`. Unique, case-insensitive (stored lower-case; "Meena" and "meena" are the same account).
- **Password** (at least 8 characters) and **Confirm password**, with a show/hide toggle
- **Email**, labelled "Used only to send you a password-reset link." Validate the format. Unique. Never shown to other teachers and never sent to the model.
- **Invite code:** required on the online pilot so a public link can't be used by strangers or burn the budget. It comes from the env var `INVITE_CODE`. If `INVITE_CODE` isn't set (local runs, graders), no invite code is needed and the field is hidden.
- A short consent line with a checkbox: "I'll use roll numbers on children's work. Children's names stay in Saathi and are never sent to the AI."

After sign-up, the teacher is logged in and goes to a short **first-time setup**: "Add your first class" (the existing Add class form), then their class roll, then Plan. Name, school, board, grades, and subjects are **optional** and live in My profile; don't ask for them at sign-up.

## 2. Log in, log out, sessions

- **Log in** with username and password. Show "Wrong username or password" for both cases (don't reveal which one was wrong).
- **Sessions:** a random session token (`secrets.token_urlsafe(32)`) stored server-side in a `sessions` table (hashed), sent as a cookie: `HttpOnly`, `SameSite=Lax`, `Secure` when served over HTTPS (Render), 30-day expiry, renewed on use. **Log out** deletes the session.
- **Passwords:** hash with `hashlib.scrypt` (standard library; a random 16-byte salt per user; store the salt and parameters) or `argon2-cffi`. Never store or log plain passwords. Use a constant-time comparison.
- **Login rate limit:** 5 failed attempts per username or IP in 15 minutes → "Too many attempts, try again in 15 minutes". Log the attempts.
- **Forgot password (email reset link):**
  - "Forgot password?" asks for the **username or email**. Always answer "If an account exists, we've emailed a reset link", whether or not it exists (so accounts can't be discovered).
  - Create a random token (`secrets.token_urlsafe(32)`). Store only its **hash**, with a **30-minute expiry**, **single use**. Email a link `{APP_URL}/reset?token=...`.
  - The reset page asks for a new password twice, then logs the teacher in, and **ends all their other sessions**.
  - Limit: 3 reset emails per account per hour.
  - **Sending email:** use standard-library `smtplib` with env vars `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`, `APP_URL` (e.g. a Gmail account with an app password). Keep it in one small `app/mailer.py`.
  - **If SMTP isn't configured** (local runs and graders), don't fail: print the reset link to the server log and show it on `/admin/pilot`, so the flow can still be tested.
  - Backup: on `/admin/pilot` (ADMIN_CODE), **Reset password** for a teacher generates a one-time temporary password they must change at next login, for teachers without email access.
  - Tell me in your report that email credentials are a new secret: they go only in Render's environment settings, never in the repo.
- **Account menu** (top right: the teacher's first name): My profile (username shown read-only; edit email, and optional name, school, default board, grades, and subjects), Change password, Log out.

## 3. Every piece of data belongs to a teacher

- Add `teacher_id` to `classes`. Everything else (students, class context, lesson plans, checks, results, insights, resources, feedback, runs, and llm_calls) is reached through its class, or gets `teacher_id` directly where that's simpler (runs, llm_calls, feedback).
- **Every `/api` route** (except health, sign-up, and log-in) requires a logged-in teacher and **checks ownership**: a teacher asking for another teacher's class, plan, check, file, or resource gets **404** (not 403, so IDs can't be probed). Put this in one helper (e.g. `require_teacher(request)` plus `owned_class(teacher, class_id)`) and use it everywhere. Don't repeat the logic per route.
- Uploaded files are stored per teacher (`uploads/<teacher_id>/...`) and served only to their owner.
- The Class dropdown, Recent lessons, Results pickers, and Usage tab show only the logged-in teacher's data.
- The old shared `ACCESS_CODE` is replaced by accounts. Remove the access-code prompt and use `INVITE_CODE` at sign-up instead. Keep `ADMIN_CODE` for `/admin/pilot`.

## 4. Budgets and usage per teacher

- A **per-teacher daily budget** (`TEACHER_DAILY_BUDGET_USD`, default 0.50) on top of the existing global `DAILY_BUDGET_USD`. Over the limit → a friendly "You've used today's limit. It resets at midnight."
- The rate limit becomes per teacher.
- The Usage tab shows the teacher's own usage. The `/admin/pilot` page shows **all teachers**: sign-up date, number of classes, lessons, checks, last active, tokens and cost, and their feedback. This gives the report "N teachers signed up, M active, average lessons per teacher, cost per teacher".

## 5. Existing data, local runs, and graders

- **Migration:** on startup, if there are classes with no `teacher_id`, create a **demo teacher** account and give it those classes (3A-TS, 1B-NCERT, and their data).
- **Graders must get in within 10 minutes.** When `DEMO_MODE=true` (the default locally), the welcome screen shows a **"Try the demo account"** button that logs in as the demo teacher, and the README lists the demo login (username `demo`, password from `DEMO_PASSWORD`, default `saathi-demo`). On Render, `DEMO_MODE` is off unless I set it.
- Add `INVITE_CODE`, `ADMIN_CODE`, `TEACHER_DAILY_BUDGET_USD`, `DEMO_MODE`, `DEMO_PASSWORD`, `APP_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `MAIL_FROM` to `.env.example`, all without real values, with a comment for each.

## 6. Hosting warning (tell me, don't solve it silently)

Accounts make Render's free plan a real problem: the SQLite file is wiped on every redeploy and can be lost on restarts, which **would delete every teacher's account and data**. Tell me the options with costs before deploying:
- a Render persistent disk mounted at the database folder (paid plan), set via `SAATHI_DB_PATH`;
- or a free hosted Postgres (e.g. Neon) via a `DATABASE_URL` env var, keeping SQLite for local runs and graders.
Make the database location configurable either way (`SAATHI_DB_PATH` already exists). Don't add Postgres unless I ask.

## 7. Safety tests (these are report evidence)

- Sign-up: a duplicate username (any case) is rejected; a duplicate email is rejected; an invalid username or email format is rejected; a weak password is rejected; a wrong or missing invite code is rejected when `INVITE_CODE` is set.
- Forgot password: the same message whether or not the account exists; the token is stored hashed; an expired token (over 30 minutes) and a reused token are rejected; a reset ends other sessions; the 4th reset email in an hour is refused; without SMTP settings, the link goes to the log and `/admin/pilot` instead of failing (mock `smtplib` in tests, so no real email is sent).
- Log-in: a wrong password gives the generic message; the 6th failed attempt is locked out; the session cookie has `HttpOnly` and `SameSite=Lax`; log-out invalidates the session.
- Passwords are stored hashed (the stored value never equals the password; two users with the same password have different hashes).
- **Ownership:** teacher B gets 404 for teacher A's class, roll, plan, check, results, resource, and uploaded file, for every route. Write this as one parametrised test over all routes, so new routes can't skip it.
- Every `/api` route except health, sign-up, and log-in returns 401 without a session.
- The per-teacher budget blocks a teacher over the limit, while another teacher can still run.
- Admin reset: the temporary password works once and forces a change.
- The demo account works when `DEMO_MODE=true` and is hidden when it's false.

## Done means

1. `pytest` passes, including the ownership test over every route.
2. Manual flow works: sign up with username, password, and email → add class → upload roll → Plan → Check (quick grid) → Next steps, then log out and log in again with everything still there; use Forgot password and reset it via the link (from the log if SMTP isn't set); a second teacher signs up and sees none of the first teacher's data.
3. README updated: how to sign up locally, the demo login, the env vars, how invite codes work online, and how to set up email for reset links (e.g. a Gmail app password).
4. Commit, don't push; show `git status`.
5. Report back: what you built, the test results, the hosting options with costs (section 6), and anything still missing.

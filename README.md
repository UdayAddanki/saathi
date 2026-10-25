# Saathi

Online link: _to be added_

Saathi is an AI teacher copilot for Grades 1–5 in NCERT and Telangana primary classrooms.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# put PORTKEY_API_KEY=... in this folder or its parent folder
python run.py
```

Open http://localhost:8000. Run tests with `pytest`.

Only `gpt-6-luna` through Portkey is configured. The SQLite database is created automatically. Chapter lists are empty unless a chapter can be verified from an official textbook source; teachers can type any topic.

## Try it with sample data

The roll-import fixtures are in `tests/fixtures/class_roll/`. Try either `class_roll_3A_valid.csv` or `class_roll_3A_valid.xlsx` for the 38-child class, then try the matching `class_roll_messy` files to see invalid rows highlighted for teacher review. Sample question-paper and answer-sheet fixtures will be added under `tests/fixtures/` when available.

## Deploy on Render

1. Push this repository to GitHub, without `.env`, `saathi.db`, `.venv`, or caches.
2. In Render, choose **New → Blueprint** and connect the GitHub repository.
3. Render reads `render.yaml`, installs the requirements, and starts `python run.py`.
4. In the service Environment settings, set `PORTKEY_API_KEY` to the Portkey key, choose a strong `ACCESS_CODE`, and leave `DAILY_BUDGET_USD` at `1.00` or choose a budget appropriate for the course.
5. Deploy and open the generated `onrender.com` URL. Enter the access code once in the browser when prompted.
6. Check `/api/health`, then create one small test lesson and inspect the Usage tab. SQLite is stored at the repository path, which works for a live demo; use persistent disk or an external database before production use because an ephemeral Render instance can lose local files on redeploy.

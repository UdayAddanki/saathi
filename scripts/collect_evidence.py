"""Create redacted evidence from pilot.db without changing application data."""
from __future__ import annotations
import csv, json, os, sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
DB_PATH = Path(os.environ.get("SAATHI_EVIDENCE_DB", ROOT / "pilot.db"))

def query(db, sql):
    db.row_factory = sqlite3.Row
    return [dict(r) for r in db.execute(sql)]

def tokenomics(db):
    calls = query(db, "select l.*, r.kind run_kind from llm_calls l left join runs r on r.id=l.run_id")
    groups = defaultdict(lambda: {"runs": set(), "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "cost_usd": 0, "provider_cost_usd": 0, "duration_ms": 0})
    agents = defaultdict(lambda: {"calls": 0, "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "cost_usd": 0, "duration_ms": 0})
    for row in calls:
        g = groups[row["run_kind"] or "unknown"]; g["runs"].add(row["run_id"])
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "cost_usd", "provider_cost_usd", "duration_ms"): g[key] += row[key] or 0
        a = agents[row["agent_name"] or "unknown"]; a["calls"] += 1
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "cost_usd", "duration_ms"): a[key] += row[key] or 0
    def finish(item, average):
        out = dict(item); divisor = len(out.pop("runs")) if "runs" in out else 1
        if average:
            for key in ("input_tokens", "cached_input_tokens", "output_tokens", "cost_usd", "provider_cost_usd", "duration_ms"): out[key] = round(out[key] / max(1, divisor), 8)
        for key, value in list(out.items()):
            if key != "calls" and isinstance(value, (int, float)): out[key] = round(value, 8)
        return out
    run_types = {k: finish(v, True) for k, v in groups.items()}
    agent_totals = {k: finish(v, False) for k, v in agents.items()}
    total = sum(v["cost_usd"] for v in agent_totals.values())
    for value in agent_totals.values(): value["cost_share"] = round(value["cost_usd"] / total, 8) if total else 0
    payload = {"source": "pilot.db (aggregate llm_calls and runs)", "run_types": run_types, "agents": agent_totals, "scale_assumptions": {"school_days_per_month": 22, "full_loops_per_day": [1, 2, 4], "note": "Scenarios are arithmetic, not observed usage."}, "not_measured": ["LLM-vs-code diagnosis experiment", "before/after severity-based revision comparison", "hosting price"]}
    (EVIDENCE / "tokenomics.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = ["# Tokenomics", "", "Source: aggregate records in `pilot.db`; no records are fabricated.", "", "## Measured averages by run type", ""]
    for kind, value in run_types.items(): lines += [f"### {kind}", "", "```json", json.dumps(value, indent=2), "```", ""]
    lines += ["## Agent totals", "", "```json", json.dumps(agent_totals, indent=2), "```", "", "## Projection assumptions", "", "Arithmetic scenarios use 22 school days/month and 1, 2, or 4 full loops/day. They are scenarios, not claims about teacher usage.", "", "## Not measured in the pilot database", "", "- LLM-vs-code diagnosis accuracy/cost experiment.", "- Before/after severity-based revision comparison.", "- Hosting price."]
    (EVIDENCE / "tokenomics.md").write_text("\n".join(lines) + "\n")

def pilot(db):
    feedback = query(db, "select rating, teach_decision, usual_time, saathi_minutes, opened_plan_tab_at, prepare_clicked_at, plan_ready_at, first_print_or_feedback_at, created_at from feedback order by created_at")
    fields = ["feedback_id"] + list(feedback[0].keys()) if feedback else ["feedback_id"]
    with (EVIDENCE / "pilot_feedback.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for index, row in enumerate(feedback, 1): writer.writerow({"feedback_id": f"feedback-{index}", **row})
    count_queries = {"classrooms": "select count(*) n from papers", "children": "select count(*) n from students", "sheets": "select count(*) n from sheet_files", "answers_read": "select count(*) n from sheet_readings", "results": "select count(*) n from results", "insights": "select count(*) n from insights", "feedback_entries": "select count(*) n from feedback"}
    counts = {key: query(db, sql)[0]["n"] for key, sql in count_queries.items()}
    lines = ["# Pilot summary", "", "Wording: piloted with real data from three classrooms.", "", "## Verified counts", ""]
    lines += [f"- {key.replace('_', ' ').title()}: {value}" for key, value in counts.items()]
    if feedback:
        ratings = [r["rating"] for r in feedback if r["rating"] is not None]; minutes = [r["saathi_minutes"] for r in feedback if r["saathi_minutes"] is not None]
        lines += ["", "## Recorded feedback (redacted)", "", f"- Ratings recorded: {len(ratings)}; mean: {sum(ratings) / len(ratings):.2f}.", f"- Saathi minutes recorded: {', '.join(map(str, minutes))}.", "- Teacher names and free-text comments are excluded from the committed export."]
    else: lines += ["", "PLACEHOLDER: no teacher feedback recorded yet. Do not infer satisfaction or time saved."]
    lines += ["", "## Caveats", "", "The pilot observations include an inverted Grade 2 readiness pattern, an English/Maths label mix-up, and a first Grade 5 plan failure. These remain limitations. Uploaded results were confirmed automatically; teacher review before confirmation remains a next step."]
    (EVIDENCE / "pilot_summary.md").write_text("\n".join(lines) + "\n")

def main():
    EVIDENCE.mkdir(exist_ok=True)
    if not DB_PATH.exists(): raise SystemExit(f"Evidence database not found: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as db: tokenomics(db); pilot(db)
    print(f"Wrote redacted evidence from {DB_PATH}")

if __name__ == "__main__": main()

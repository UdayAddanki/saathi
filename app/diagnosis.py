from __future__ import annotations

import json
from collections import Counter, defaultdict

from .curriculum import CONCEPTS, MISCONCEPTIONS
from .db import conn, one
from .models import Insight


def _status(percent: float) -> str:
    if percent >= 80:
        return "Secure"
    if percent >= 50:
        return "Developing"
    return "Needs re-teaching"


def analyze_results(check_id: str) -> Insight:
    """Compute mastery, errors, groups, and actions using only saved data."""
    database = conn()
    check = one("SELECT * FROM checks WHERE id=?", (check_id,))
    if not check:
        raise ValueError("Check not found")
    lesson = one("SELECT * FROM lesson_plans WHERE id=?", (check["lesson_plan_id"],))
    profile = one("SELECT * FROM classes WHERE id=?", (lesson["class_id"],))
    items = json.loads(check["items_json"])
    response_rows = [dict(row) for row in database.execute("SELECT * FROM responses WHERE check_id=?", (check_id,))]
    mode = response_rows[0].get("check_mode", "each_child") if response_rows else "each_child"
    if mode == "class_count" and response_rows:
        expanded = []
        for row in response_rows:
            for item_index, values in json.loads(row.get("class_counts_json") or "{}").items():
                for answer, amount in values.items():
                    for _ in range(int(amount)):
                        expanded.append({"item_index": int(item_index), "chosen_option": answer, "rating": answer, "check_mode": mode})
        response_rows = expanded
    counts = Counter()
    student_scores = defaultdict(list)
    absent = set()
    concept_stats = defaultdict(lambda: {"assessed": 0, "correct": 0, "got_it": 0, "partly": 0, "not_yet": 0})
    error_counts = Counter()
    error_meta = {}
    for row in response_rows:
        roll = row.get("roll_no")
        if row.get("rating") == "absent" or row.get("chosen_option") == "absent":
            absent.add(roll)
            continue
        index = row["item_index"]
        item = items[index]
        concept_id = item.get("concept_id") or "open"
        stats = concept_stats[concept_id]
        if check["check_type"] == "mcq":
            chosen = row.get("chosen_option")
            correct = chosen == item.get("correct_option")
            stats["assessed"] += 1
            stats["correct"] += int(correct)
            student_scores[roll].append(correct)
            if not correct and chosen:
                counts[(index, chosen)] += 1
                error = item.get("option_errors", {}).get(chosen, {})
                error_counts[(index, chosen)] += 1
                error_meta[(index, chosen)] = error
        else:
            rating = row.get("rating", "got_it")
            stats["assessed"] += 1
            stats[rating] += 1
            student_scores[roll].append(rating == "got_it")
            if rating != "got_it" and row.get("error_id"):
                error_counts[(index, row["error_id"])] += 1
                error_meta[(index, row["error_id"])] = next((e for e in item.get("common_errors", []) if e.get("misconception_id") == row["error_id"]), {"description": "AI-suggested error", "ai_suggested": True})
    concepts = []
    prerequisites = []
    concept_map = {concept["id"]: concept for concept in CONCEPTS}
    for concept_id, stats in concept_stats.items():
        denominator = stats["assessed"] or 1
        percent = round(100 * (stats["correct"] if check["check_type"] == "mcq" else stats["got_it"]) / denominator)
        status = _status(percent)
        concepts.append({"concept_id": concept_id, "assessed": stats["assessed"], "percent_correct": percent, "got_it": stats["got_it"], "partly": stats["partly"], "not_yet": stats["not_yet"], "status": status})
        if status == "Needs re-teaching" and concept_id in concept_map and concept_map[concept_id]["prerequisite_ids"]:
            prerequisites.append({"concept_id": concept_id, "check_these_first": concept_map[concept_id]["prerequisite_ids"]})
    top_errors = []
    library = {item["id"]: item for item in MISCONCEPTIONS}
    for (index, key), count in error_counts.most_common():
        error = error_meta[(index, key)]
        error_id = error.get("misconception_id") if isinstance(error, dict) else None
        top_errors.append({"item_index": index, "count": count, "misconception_id": error_id, "description": library.get(error_id, error).get("description", "AI-suggested error"), "ai_suggested": bool(error.get("ai_suggested", False))})
    actions = []
    for concept in concepts:
        actions.append("move_on" if concept["percent_correct"] >= 80 else "group_practice" if concept["percent_correct"] >= 50 else "whole_class_reteach")
    if prerequisites:
        actions.append("review_prerequisite")
    groups = {"ready": [], "practice": [], "reteach": []}
    if mode == "each_child":
        for roll, scores in student_scores.items():
            correct_count = sum(scores)
            if check["check_type"] == "mcq":
                target = "ready" if correct_count >= 4 else "practice" if correct_count >= 2 else "reteach"
            else:
                target = "ready" if all(scores) else "reteach" if scores.count(False) >= len(scores) / 2 else "practice"
            student = one("SELECT first_name FROM students WHERE class_id=? AND roll_no=?", (lesson["class_id"], roll))
            groups[target].append({"roll_no": roll, "first_name": student["first_name"] if student else None})
    insight = Insight(check_id=check_id, check_mode=mode, concepts=concepts, top_errors=top_errors, groups=groups, missed_lesson=[{"roll_no": roll} for roll in sorted(absent)], prerequisite_flags=prerequisites, recommended_actions=sorted(set(actions)))
    database.execute("DELETE FROM insights WHERE check_id=?", (check_id,))
    import datetime
    database.execute("INSERT INTO insights VALUES(?,?,?)", (check_id, insight.model_dump_json(), datetime.datetime.now(datetime.timezone.utc).isoformat()))
    database.commit()
    database.close()
    return insight

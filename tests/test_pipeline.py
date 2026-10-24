import json
import uuid

from pydantic_ai.models.test import TestModel

from app.agents.planner import planner
from app.db import conn, init_db, rows
from app.models import ReviewIssue, ReviewResult
from app.pipeline import _curated_issues


def test_testmodel_agent_can_complete_without_real_api():
    with planner.override(model=TestModel()):
        result = planner.run_sync('class_id=3A-TS board=TS_SCERT grade=3 subject=Mathematics period_minutes=40 topic=place value')
    assert result.output.title


def test_bad_curated_misconception_is_caught():
    issue = _curated_issues({"questions": [{"option_errors": {"B": {"misconception_id": "M-NOT-REAL"}}}]}, [{"id": "place-value"}])
    assert issue[0]["severity"] == "must_fix"


def test_reviewer_severity_controls_revision_policy():
    suggestion = ReviewResult(passed=True, issues=[ReviewIssue(target='plan', problem='wording', fix='simplify', severity='suggestion')])
    must_fix = ReviewResult(passed=False, issues=[ReviewIssue(target='plan', problem='bad timing', fix='fix minutes', severity='must_fix')])
    assert not any(item.severity == 'must_fix' for item in suggestion.issues)
    assert any(item.severity == 'must_fix' for item in must_fix.issues)

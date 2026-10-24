from __future__ import annotations

from ..config import ROOT
from ..curriculum import get_class_profile, get_misconceptions
from ..diagnosis import analyze_results
from ..llm import get_model
from ..models import NextSteps
from pydantic_ai import Agent


def get_insight(check_id: str) -> dict:
    """Return the code-computed insight for a check."""
    return analyze_results(check_id).model_dump()


def get_prerequisites(concept_id: str) -> list[str]:
    """Return prerequisite concept IDs from the curated library."""
    from ..curriculum import CONCEPTS
    return next((item["prerequisite_ids"] for item in CONCEPTS if item["id"] == concept_id), [])


coach = Agent(get_model(), output_type=NextSteps, system_prompt=(ROOT / "app/prompts/coach.md").read_text())
coach.tool_plain(get_insight)
coach.tool_plain(get_misconceptions)
coach.tool_plain(get_prerequisites)
coach.tool_plain(get_class_profile)

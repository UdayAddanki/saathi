from pydantic_ai import Agent
from ..config import ROOT
from ..curriculum import get_class_profile, get_curriculum_context, get_latest_insights
from ..llm import get_model
from ..models import LessonPlan
planner=Agent(get_model(), output_type=LessonPlan, system_prompt=(ROOT / 'app/prompts/lesson_planner.md').read_text())
planner.tool_plain(get_curriculum_context)
planner.tool_plain(get_class_profile)
planner.tool_plain(get_latest_insights)

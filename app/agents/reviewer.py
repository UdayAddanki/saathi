from pydantic_ai import Agent
from ..config import ROOT
from ..curriculum import get_curriculum_context
from ..llm import get_model
from ..models import ReviewResult
reviewer=Agent(get_model(), output_type=ReviewResult, system_prompt=(ROOT / 'app/prompts/reviewer.md').read_text())
reviewer.tool_plain(get_curriculum_context)

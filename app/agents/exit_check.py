from pydantic_ai import Agent
from ..config import ROOT
from ..curriculum import get_misconceptions
from ..llm import get_model
from ..models import McqCheck, ObservationCheck
check_agent=Agent(get_model(), output_type=McqCheck, system_prompt=(ROOT / 'app/prompts/check_builder_mcq.md').read_text())
observation_agent=Agent(get_model(), output_type=ObservationCheck, system_prompt=(ROOT / 'app/prompts/check_builder_observation.md').read_text())
check_agent.tool_plain(get_misconceptions)
observation_agent.tool_plain(get_misconceptions)

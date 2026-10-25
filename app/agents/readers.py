from __future__ import annotations

from pydantic_ai import Agent

from ..config import ROOT
from ..models import Paper, SheetReading
from ..llm import get_model

paper_reader = Agent(get_model(), output_type=list[dict], system_prompt=(ROOT / 'app/prompts/paper_reader.md').read_text())
answer_sheet_reader = Agent(get_model(), output_type=SheetReading, system_prompt=(ROOT / 'app/prompts/answer_sheet_reader.md').read_text())

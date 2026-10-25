from pydantic_ai import Agent
from ..config import ROOT
from ..curriculum import get_class_profile, get_misconceptions
from ..diagnosis import analyze_results
from ..llm import get_model
from ..models import ResourceSet

def get_insight(check_id: str) -> dict:
    return analyze_results(check_id).model_dump()

def get_child_results(check_id: str, roll_no: int) -> list[dict]:
    from ..db import rows, one
    check = one('select * from checks where id=?', (check_id,))
    if not check: return []
    return rows('select * from responses where check_id=? and roll_no=? order by item_index', (check_id, roll_no))

resource_builder = Agent(get_model(), output_type=ResourceSet, system_prompt=(ROOT / 'app/prompts/resource_builder.md').read_text())
resource_builder.tool_plain(get_insight)
resource_builder.tool_plain(get_child_results)
resource_builder.tool_plain(get_misconceptions)
resource_builder.tool_plain(get_class_profile)

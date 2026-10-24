from __future__ import annotations

import datetime
import time
import uuid
from decimal import Decimal

from .config import PRICE_CACHED_INPUT_PER_M, PRICE_INPUT_PER_M, PRICE_OUTPUT_PER_M
from .db import conn


def record(run_id: str, agent: str, usage: object, started: float) -> dict:
    """Persist provider usage and calculate the project's comparable cost."""
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    cached_tokens = int(getattr(usage, "cache_read_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    provider_cost = getattr(usage, "cost", Decimal("0")) or Decimal("0")
    our_cost = (input_tokens * PRICE_INPUT_PER_M + cached_tokens * PRICE_CACHED_INPUT_PER_M + output_tokens * PRICE_OUTPUT_PER_M) / 1_000_000
    database = conn()
    database.execute("INSERT INTO llm_calls VALUES(?,?,?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), run_id, agent, input_tokens, cached_tokens, output_tokens, our_cost, float(provider_cost), int((time.perf_counter() - started) * 1000), datetime.datetime.now(datetime.timezone.utc).isoformat()))
    database.commit()
    database.close()
    return {"input_tokens": input_tokens, "cached_input_tokens": cached_tokens, "output_tokens": output_tokens, "cost_usd": our_cost, "provider_cost_usd": float(provider_cost)}

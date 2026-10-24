import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# gpt-6-luna on Portkey rejects function tools unless reasoning is off.
# The setting name PydanticAI recognises is "openai_reasoning_effort".
MODEL_SETTINGS = {"openai_reasoning_effort": "none"}


def get_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        "gpt-6-luna",
        settings=MODEL_SETTINGS,
        provider=OpenAIProvider(
            base_url="https://api.portkey.ai/v1",
            api_key=os.getenv("PORTKEY_API_KEY"),
        ),
    )

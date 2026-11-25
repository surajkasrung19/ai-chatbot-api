import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.services.responders import (
    ChatResponder,
    RuleBasedResponder
)
from app.services.openai_responder import OpenAIResponder


load_dotenv()


@lru_cache(maxsize=1)
def get_responder() -> ChatResponder:

    provider = os.getenv(
        "CHATBOT_PROVIDER", "rule-based"
    ).lower()

    if provider == "rule-based":
        return RuleBasedResponder()

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        # Although the class is called OpenAIResponder, we're reusing it as an OpenAI-compatible API client.
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=20.0,
            max_retries=0
        )

        return OpenAIResponder(
            client=client,
            model=os.getenv(
                "GROQ_MODEL", "openai/gpt-oss-20b"
            )
        )

    raise ValueError(
        f"Unsupported chatbot provider: {provider}"
    )
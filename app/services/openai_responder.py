
from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    RateLimitError
)

from app.models import Message
from app.services.provider_errors import ChatProviderError

class OpenAIResponder:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str
    ) -> None:
        self.client = client
        self.model = model

    async def generate(
        self,
        message: str,
        history: list[Message]
    ) -> str:

        # Include up to 10 previous messages
        previous_messages = [
            {
                "role": item.role,
                "content": item.content
            }
            for item in history[-10:]
        ]

        # Append the current user message
        previous_messages.append({
            "role": "user",
            "content": message
        })

        try:
            response = await self.client.responses.create(
                model=self.model,
                instructions=(
                    "You are a helpful and concise "
                    "Python learninig assistant."
                ),
                input=previous_messages,
                store=False,
                max_output_tokens=400
            )

        except RateLimitError as exc:
            raise ChatProviderError(
                detail="AI service limit reached. Please try again later.",
                status_code=503,
                code="rate_limited"
            ) from exc

        except APITimeoutError as exc:
            raise ChatProviderError(
                detail="AI service timed out. Please try again.",
                status_code=504,
                code="provider_timeout"
            ) from exc

        except APIConnectionError as exc:
            raise ChatProviderError(
                detail="AI service is temporarily unavailable.",
                status_code=503,
                code="connection_error"
            ) from exc

        except APIStatusError as exc:
            raise ChatProviderError(
                detail="AI provider could not complete the request.",
                status_code=(
                    503 if exc.status_code >= 500 else 502
                ),
                code="Provider_http_error"
            ) from exc

        except APIError as exc:
            raise ChatProviderError(
                detail="An AI provider error occurred.",
                statusC_code=502,
                code="provider_error"
            ) from exc

        answer = (response.output_text or "").strip()

        if not answer:
            raise ChatProviderError(
                detail="AI provider returned an empty response.",
                status_code=502,
                code="empty_response"
            )

        return answer
from typing import Protocol

from app.models import Message

from app.utils.nlp_stub import generate_stub_response



class ChatResponder(Protocol):

    async def generate(
            self,
            message: str,
            history: list[Message]
    ) -> str:
        ...



class RuleBasedResponder:

    async def generate(
            self,
            message: str,
            history: list[Message]
    ) -> str:
        # TODO: Implement response generation
        return generate_stub_response(message)




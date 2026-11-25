import asyncio

from app.services.responders import RuleBasedResponder
from app.utils.nlp_stub import SAMPLE_RESPONSES


def test_rule_based_responder():

    responder = RuleBasedResponder()

    # generate() function is asynchronous. calling it without awaiting or running the coroutine doesn't execute its body.
    response = asyncio.run(
        responder.generate(
            message="Explain FastAPI",
            history=[]
        )
    )

    assert response in SAMPLE_RESPONSES["fastapi"]
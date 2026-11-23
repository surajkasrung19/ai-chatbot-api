import random


SAMPLE_RESPONSES = {
    "hello": [
        "Hello! How can I help you?",
        "Hi there! What can I assist you with?"
    ],
    "python": [
        "python is a versatile programming language",
        "Python is popular for backend development, AI and automation"
    ],
    "fastapi": [
        "FastAPI is a modern Python framework for building APIs",
        "FastAPI uses Python type hints and Pydantic for validation"
    ],
    "help": [
        "I'm here to help! Ask me about Python or FastAPI.",
        "Sure! What would you like to know?"
    ],
    "thanks": [
        "You're very welcome",
        "pleasure is mine",
        "Anytime",
        "Glad to help"
    ]
}

DEFAULT_RESPONSES = [
    "I'm still learning. Could you explain your question?",
    "Interesting! Can you provide more details?",
    "I'm a simple rule-based chatbot for now."
]

def generate_stub_response(user_message: str) -> str:
    normalized_message = user_message.lower()

    for keyword, responses in SAMPLE_RESPONSES.items():
        if keyword in normalized_message:
            return random.choice(responses)


    return random.choice(DEFAULT_RESPONSES)
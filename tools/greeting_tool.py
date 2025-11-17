from langchain.tools import tool

GREETINGS = ["hi", "hello", "kumusta", "good morning", "good afternoon"]

@tool
def greeting_handler(query: str) -> str:
    """Handle greetings and simple friendly messages."""
    q = query.lower()
    if any(g in q for g in GREETINGS):
        return "Hello! How can I assist you with your HR or onboarding questions today?"
    return ""

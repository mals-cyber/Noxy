from langchain.tools import tool

VAGUE = ["guide me", "help me", "assist me", "i need help", "what do i do"]

@tool
def vague_handler(query: str) -> str:
    """Respond to vague or unclear requests."""
    q = query.lower()
    if any(v in q for v in VAGUE):
        return "Can you tell me which part of onboarding or HR you need help with?"
    return ""

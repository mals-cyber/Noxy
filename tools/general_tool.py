from langchain.tools import tool

NAME_QUESTIONS = [
    "your name",
    "what is your name",
    "who are you",
    "who am i talking to",
    "may i know your name",
]

GREETINGS = ["hi", "hello", "kumusta", "good morning", "good afternoon"]
VAGUE = ["guide me", "help me", "assist me", "i need help", "what do i do"]

def is_pure_greeting(query: str) -> bool:
    """
    Returns True only if the message is JUST a greeting,
    and does NOT contain other intent like asking for name.
    """
    if any(q in query for q in ["name", "who", "what"]):
        return False
    
    return query.strip() in GREETINGS

@tool("general_filter_tool")
def general_filter_tool(data: dict) -> str:
    """
    Detects greetings or vague requests and returns a label.
    The LLM will produce the natural response.
    """
    query = data.get("query", "").lower()

    if any(n in query for n in NAME_QUESTIONS):
        return None

    if is_pure_greeting(query):
        return "greeting"

    if any(v in query for v in VAGUE):
        return "vague"

    return None

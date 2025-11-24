from langchain.tools import tool
HR_KEYWORDS = [
    "hr info",
    "hr information",
    "hr details",
    "hr contact",
    "contact hr",
    "how to contact hr",
    "hr email",
    "hr number",
    "human resources",
    "reach hr",
    "talk to hr",
    "hr hotline",
]

HR_INFO = (
    "HR Email: hr.department@n-pax.com "
    "Cebu HR: (032) 123-4567. "
    "Manila HR: (02) 987-6543. "
    "Office hours are Monday to Friday, 8AM to 6PM."
)

@tool("hr_lookup")
def hr_lookup(data: dict) -> str:
    """Returns HR contact information when user asks for HR details."""
    query = data.get("query", "").lower()

    if any(k in query for k in HR_KEYWORDS):
        return HR_INFO

    return None

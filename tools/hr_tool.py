from langchain.tools import tool

HR_INFO = (
    "HR Email: hrdepartment@n-pax.com. "
    "Cebu HR: (032) 123-4567. "
    "Manila HR: (02) 987-6543. "
    "Office hours are Monday to Friday, 8AM to 6PM."
)

@tool
def hr_lookup(_: str) -> str:
    """Provide HR contact details."""
    return HR_INFO

from typing import List, Dict
from langchain.tools import tool

@tool("pending_tasks_tool")
def pending_tasks_tool(data: dict) -> str:
    """Filter and return pending onboarding tasks in a friendly formatted list."""

    task_progress = data.get("task_progress", [])

    if not task_progress:
        return "You currently have no pending onboarding requirements."

    pending = [
        t for t in task_progress
        if t.get("status", "").lower() in ["pending", "in_progress"]
    ]

    if not pending:
        return "You currently have no pending onboarding requirements."

    items = "\n".join([f"- {t['taskTitle']}" for t in pending])

    return (
        "Here are your pending onboarding tasks:\n"
        f"{items}\n"
        "Please complete them as soon as possible."
    )

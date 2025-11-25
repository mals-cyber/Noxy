from langchain.tools import tool

@tool("pending_tasks_tool")
def pending_tasks_tool(data: dict) -> str:
    """Return onboarding status: pending, in progress, and completed onboarding tasks in a friendly formatted list."""

    pending = data.get("pending", [])
    in_progress = data.get("in_progress", [])
    completed = data.get("completed", [])

    def format_section(title, items):
        if not items:
            return f"{title}:\n- None\n"
        lines = [f"{title}:"]
        for t in items:
            lines.append(f"- {t.get('taskTitle', 'Untitled task')}")
        return "\n".join(lines) + "\n"

    message = (
        "Here is your onboarding task status:\n\n" +
        format_section("Pending", pending) +
        format_section("In Progress", in_progress) +
        format_section("Completed", completed)
    )

    if not pending and not in_progress:
        message += "\nGreat news! You have completed all your onboarding requirements."
    else:
        message += "\nPlease continue working on the remaining requirements."

    return message.strip()

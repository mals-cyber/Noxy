import requests

# Detect when user is asking about task status
PENDING_TASK_PHRASES = [
    "what are the tasks i need to comply",
    "what do i need",
    "what are my pending requirements",
    "what am i missing",
    "what do i still need to submit",
    "incomplete tasks",
    "lacking requirements",
    "pending requirements",
    "onboarding tasks status",
    "task status",
]

def fetch_task_status_groups(user_id: str):
    url = f"http://localhost:5164/api/onboarding/user-tasks/{user_id}"

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            print("TASK ERROR:", resp.status_code, resp.text)
            return {
                "pending": [],
                "in_progress": [],
                "completed": []
            }

        tasks = resp.json()

        grouped = {
            "pending":      [t for t in tasks if t.get("status", "").lower() == "pending"],
            "in_progress":  [t for t in tasks if t.get("status", "").lower() == "in_progress"],
            "completed":    [t for t in tasks if t.get("status", "").lower() == "completed"]
        }

        return grouped

    except Exception as e:
        print("TASK EXCEPTION:", str(e))
        return {
            "pending": [],
            "in_progress": [],
            "completed": []
        }

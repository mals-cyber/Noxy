import requests

def fetch_pending_tasks(user_id: str):
    url = f"http://localhost:5164/api/onboarding/user-tasks/{user_id}"

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            print("TASK ERROR:", resp.status_code, resp.text)
            return []

        tasks = resp.json()

        pending = [
            t for t in tasks
            if t.get("status", "").lower() in ["pending", "in progress"]
        ]

        return pending

    except Exception as e:
        print("TASK EXCEPTION:", str(e))
        return []

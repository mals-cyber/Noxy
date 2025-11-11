import json

def load_knowledge_base(path: str):
    with open(path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)
    
    all_items = []
    for category in kb_data["knowledgeBase"]["categories"]:
        for item in category["items"]:
            all_items.append(item)
    return all_items

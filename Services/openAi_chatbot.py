import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")   
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") 

client = AzureOpenAI(api_key=api_key, api_version="2024-02-15-preview", azure_endpoint=endpoint)

with open(r"C:\Users\TRAINEE-CAÑEDO\Downloads\NOXAPP\Noxy\KnowledgeBase.json", "r", encoding="utf-8") as f:
    kb_data = json.load(f)

all_items = []
for category in kb_data["knowledgeBase"]["categories"]:
    for item in category["items"]:
        all_items.append(item)


def find_relevant_entries(user_input, kb_items):
    relevant_texts = []
    for item in kb_items:
        title = item.get("title", "")
        content = item.get("content", "")
        text_to_search = f"{title} {content}"

        if any(word.lower() in text_to_search.lower() for word in user_input.split()):
            relevant_texts.append(text_to_search)
    return relevant_texts


def chat_with_azure(messages, user_input):
    for item in all_items:
        for faq in item.get("faqs", []):
            if user_input.lower() in faq["question"].lower():
                answer = faq["answer"]
                messages.append({"role": "assistant", "content": answer})
                return answer

    relevant_info = find_relevant_entries(user_input, all_items)
    if relevant_info:
        kb_text = "\n".join(relevant_info)
        messages.append({"role": "system", "content": f"Use this knowledge to answer: {kb_text}"})

    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages
    )

    bot_reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": bot_reply})
    return bot_reply

conversation = [
    {"role": "system", "content":
     "Your name is Noxy, an AI chatbot designed to assist new employees with onboarding. "
     "Your purpose is to guide new employees through onboarding and answer questions about government requirements, "
     "company policies, and related processes. "
     "Answer in a friendly and professional manner. "
     "Maximum of two sentences only."}
]

print("Noxy is ready! Type 'quit' to exit.")
while True:
    user_input = input("User: ")
    if user_input.lower() == "quit":
        break
    bot_response = chat_with_azure(conversation, user_input)
    print("Noxy:", bot_response)

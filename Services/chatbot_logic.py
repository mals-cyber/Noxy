from openai import AzureOpenAI
from .config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME

client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_ENDPOINT
)

def find_relevant_entries(user_input: str, kb_items: list):
    relevant_texts = []
    for item in kb_items:
        title = item.get("title", "")
        content = item.get("content", "")
        text_to_search = f"{title} {content}"

        if any(word.lower() in text_to_search.lower() for word in user_input.split()):
            relevant_texts.append(text_to_search)
    return relevant_texts


def chat_with_azure(user_input: str, conversation: list, kb_items: list):
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    if user_input.strip().lower() in greetings:
        reply = "Hello! I'm Noxy, your onboarding assistant. How can I help you today?"
        conversation.append({"role": "assistant", "content": reply})
        return reply

    for item in kb_items:
        for faq in item.get("faqs", []):
            if user_input.lower() in faq["question"].lower():
                answer = faq["answer"]
                conversation.append({"role": "assistant", "content": answer})
                return answer

    relevant_info = find_relevant_entries(user_input, kb_items)
    if relevant_info:
        kb_text = "\n".join(relevant_info)
        conversation.append({"role": "system", "content": f"Use this knowledge to answer: {kb_text}"})

    conversation.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=conversation
    )

    bot_reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": bot_reply})
    return bot_reply

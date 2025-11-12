from Services.vector_store import search_vectors
from openai import AzureOpenAI
from .config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME
import os

client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_ENDPOINT
)

PDF_FOLDER = "MockData"

def chat_with_azure(user_input: str, conversation: list):
    vector_hits = search_vectors(user_input)

    matched_file = None
    for file in os.listdir(PDF_FOLDER):
        if file.lower().endswith(".pdf") and any(word in file.lower() for word in user_input.lower().split()):
            matched_file = file
            break

    if matched_file:
        download_link = f"http://127.0.0.1:8000/download-pdf?filename={matched_file}"

        conversation.append({
            "role": "system",
            "content": (
                f"The user is requesting a document or form.\n"
                f"You found a matching PDF: {matched_file}.\n"
                f"Provide a natural response and include this download link: {download_link}.\n"
                f"Do NOT list file paths or code. Speak like a helpful HR assistant."
            )
        })

    if vector_hits:
        joined_hits = "\n".join(vector_hits)
        conversation.append({
            "role": "system",
            "content": f"Use this knowledge to answer:\n{joined_hits}"
        })

    conversation.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=conversation
    )

    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})
    return reply

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

PDF_TRIGGER_WORDS = ["pdf", "form", "file", "download", "template"]

PDF_KEYWORDS = {
    "pagibig": "HDMF.pdf",
    "pag-ibig": "HDMF.pdf",
    "hdmf": "HDMF.pdf",

    "philhealth": "PHILHEALTH.pdf",

    "sss": "SSS E1 FORM.pdf",
    "e1": "SSS E1 FORM.pdf",

    "bir 1904": "BIR FORM 1904.pdf",
    "1904": "BIR FORM 1904.pdf",

    "bir 1905": "BIR FORM 1905.pdf",
    "1905": "BIR FORM 1905.pdf",

    "bir 2316": "BIR FORM 2316.pdf",
    "2316": "BIR FORM 2316.pdf"}


def chat_with_azure(user_input: str, conversation: list):
    vector_hits = search_vectors(user_input)

    user_asked_for_pdf = any(word in user_input.lower() for word in PDF_TRIGGER_WORDS)

    matched_file = None
    lower_input = user_input.lower()

    for keyword, filename in PDF_KEYWORDS.items():
        if keyword in lower_input:
            matched_file = filename
            break

    if matched_file:
        download_link = f"http://127.0.0.1:8000/download-pdf?filename={matched_file}"
        conversation.append({
            "role": "system",
            "content": (
                f"The user is requesting a specific document.\n"
                f"The correct file is: {matched_file}.\n"
                f"Provide a natural HR-style answer with this link:\n"
                f"{download_link}"
            )})

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

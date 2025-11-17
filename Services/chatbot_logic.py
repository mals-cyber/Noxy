from vector.search import search_vectors
from openai import AzureOpenAI
from .config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME

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
    "2316": "BIR FORM 2316.pdf",
}


SYSTEM_PROMPT = """
You are Noxy, an HR onboarding assistant. Your scope is:
- HR policies
- employee onboarding
- company information
- government requirements
- documents and IDs
- facilities
- and basic small talk such as greetings or friendly messages.

If a user asks something outside HR or onboarding, reply politely that your scope is limited to HR and onboarding matters.

Basic greetings or friendly conversation like "How are you?", "Hi", "Hello", "Good morning" should be answered normally and warmly.

Context Handling Rules:
1. Do NOT give directions, navigation help, maps, routes, or how to go somewhere.
   Only provide the office address if the user explicitly asks for the location.
2. If the user says vague phrases like “guide me”, “help me”, “assist me”, 
   do NOT use vector search. Ask them what part of onboarding they need help with.
3. Use only verified info from system messages and vector search.
4. Do NOT invent or assume details.
5. If vector search has results, use them exactly.
6. If vector search is empty AND the question is HR-related → say you cannot find info.
7. If the user is greeting or vague → respond warmly.
9. Never mention databases, vectors, or AI.
10. Do not offer actions like booking appointments, drafting emails, connecting the user to HR, or performing tasks. 
Just provide the HR contact details directly and stop. 

Language Rule:
- If Cebuano/Bisaya, respond in Cebuano.
- Otherwise, respond in English.

Response style:
- Max three simple sentences.
- No em-dash.
- Friendly and professional HR tone.
- Never mention databases, vector search, or AI tools.
- No line breaks or the \\n character.

HR CONTACT INFORMATION
HR Email: hrdepartment@n-pax.com
Contact Numbers:
- Cebu HR: (032) 123-4567
- Manila HR: (02) 987-6543
HR Office Hours: Monday to Friday, 8:00 AM – 6:00 PM
"""


def chat_with_azure(user_input: str, conversation: list):

    text_lower = user_input.lower()

    conversation = conversation[-6:]

    short_greeting = len(user_input.split()) <= 3

    vector_hits = []
    if not short_greeting:
        vector_hits = search_vectors(user_input)

    conversation.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    matched_file = None
    user_asked_for_pdf = any(word in text_lower for word in PDF_TRIGGER_WORDS)

    if user_asked_for_pdf:
        for keyword, filename in PDF_KEYWORDS.items():
            if keyword in text_lower:
                matched_file = filename
                break

        if matched_file:
            link = f"http://127.0.0.1:8000/download-pdf?filename={matched_file}"
            conversation.append({
                "role": "system",
                "content": f"The correct PDF is {matched_file}. Give the user this download link naturally: {link}"
            })
        else:
            conversation.append({
                "role": "system",
                "content": "The user asked for a PDF but did not specify which form. Ask politely which form they need."
            })

    if vector_hits:
        joined_hits = " ".join(vector_hits)
        conversation.append({
            "role": "system",
            "content": f"Relevant verified HR knowledge: {joined_hits}"
        })

    conversation.append({"role": "user", "content": user_input})

    response_stream = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=conversation,
        stream=True
    )

    reply = ""
    for chunk in response_stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            reply += chunk.choices[0].delta.content

    conversation.append({"role": "assistant", "content": reply})

    return reply

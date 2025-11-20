from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from vector.search import search_vectors
from Services.config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME
from tools.pdf_tool import fetch_pdf_links
from tools.file_matcher import find_best_file_match
from tools.pending_tasks import fetch_pending_tasks


llm = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    model=AZURE_DEPLOYMENT_NAME,
    api_version="2024-02-15-preview",
    temperature=0.2
)

SYSTEM_PROMPT = """
You are Noxy, an HR onboarding assistant.

Your allowed scope:
- HR policies
- employee onboarding
- company information
- government requirements
- IDs and documents
- HR contact info
- basic greetings

Forbidden:
- Do NOT give directions, routes, navigation, or "how to go there".
- Do NOT book appointments or perform actions.
- Do NOT say you can connect to HR.
- Do NOT invent information.

Rules:
1. If query is vague (ex: "guide me", "help me"), ask what onboarding topic they need.
2. If greeting (hi, hello, good morning), answer warmly without search.
3. If query is HR-related, use vector search results.
4. If search is empty and query is HR-related → say you cannot find info.
5. Maximum 3 simple sentences. No line breaks.
6. If there is a link, provide a simple one sentence after.
7. Do not use Mdash or special formatting.

HR CONTACT INFORMATION:
Email: hrdepartment@n-pax.com
Cebu HR: (032) 123-4567
Manila HR: (02) 987-6543
Hours: Monday–Friday, 8:00 AM – 6:00 PM
"""


prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
User message: {question}

Relevant knowledge:
{context}

Answer as Noxy.
""")
])


def retrieve_context(input: dict):
    q = input["question"].lower()

    if q in ["hi", "hello", "hey", "good morning", "good afternoon"]:
        return ""

    if q in ["guide me", "help me", "assist me"]:
        return ""

    hits = search_vectors(q)
    return "\n".join(hits)


chain = (
    RunnableParallel({
        "question": RunnablePassthrough(),
        "context": retrieve_context
    })
    | prompt
    | llm
)

def ask_noxy(message: str, user_id: str = None):
    q = message.lower()
    responses = []  # collect partial responses

    requirements_keywords = ["lacking requirements", "pending", "incomplete", 
                             "what do i need", "missing"]

    if any(k in q for k in requirements_keywords) and user_id:
        pending = fetch_pending_tasks(user_id)
        if pending:
            items = "\n".join([f"- {t['taskTitle']}" for t in pending])
            natural = llm_pending_sentence()
            intro, outro = natural.split(". ", 1)
            responses.append(f"{intro}:\n{items}\n{outro}")
        else:
            responses.append("You currently have no pending onboarding requirements.")

    request_keywords = ["form", "pdf", "file", "document", "download", "copy"]

    if any(k in q for k in request_keywords):
        files = fetch_pdf_links()
        if files:
            best = find_best_file_match(q, files)
            if best:
                followup = llm_followup_sentence(best["name"])
                responses.append(
                    f"Here is the file you need: {best['url']}. {followup}"
                )
        else:
            responses.append("I’m having trouble retrieving the files right now.")

    llm_result = chain.invoke({"question": message}).content
    responses.append(llm_result)

    return "\n\n".join(responses)

def llm_followup_sentence(filename: str):
    prompt = (
        f"Write a simple one sentence after the link and make it friendly: {filename}. "
        f"Do not add a link, do not ask questions. Maximum 1 sentence."
    )
    result = llm.invoke(prompt)
    return result.content.strip()

def llm_pending_sentence():
    prompt = (
        "Write two short, friendly sentences for showing pending onboarding "
        "requirements to a user. The first sentence should introduce the list. "
        "The second sentence should come after the list and encourage the user "
        "to complete the requirements. Do NOT add bullets or formatting, only two sentences."
    )
    result = llm.invoke(prompt)
    return result.content.strip()


def retrieve_context(input: dict):
    q = input["question"].lower() 


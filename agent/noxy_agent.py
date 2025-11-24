from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from vector.search import search_vectors
from Services.config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME
from tools.pdf_tool import fetch_pdf_links
from tools.file_matcher import find_best_file_match
from tools.pendingtasks_tool import pending_tasks_tool
from tools.pending_tasks import PENDING_TASK_PHRASES
from tools.pending_tasks import fetch_task_status_groups


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
5. Maximum 3 simple sentences.
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

def ask_noxy(message: str, user_id: str = None, task_progress=None):
    q = message.lower()

    # Pending task handling
    if user_id and any(p in q for p in PENDING_TASK_PHRASES):
        task_groups = fetch_task_status_groups(user_id)
        return pending_tasks_tool.invoke({
            "data": {
                "pending": task_groups.get("pending", []),
                "in_progress": task_groups.get("in_progress", []),
                "completed": task_groups.get("completed", [])
            }
        })


    # Detect if user is asking for any file
    request_keywords = ["form", "pdf", "file", "document", "download", "copy"]

    if any(k in q for k in request_keywords):

        # Special handling for generic BIR queries
        generic_bir_cases = [
            "bir",
            "bir form",
            "bir file",
            "bir document",
            "bir pdf",
            "bureau of internal revenue"
        ]

        if q.strip() in generic_bir_cases:
            return "It looks like you are requesting a BIR form, but there are multiple types. May I know the specific form number you need?"

        # Fetch files
        files = fetch_pdf_links()
        if not files:
            return "I’m having trouble retrieving the files right now. Please try again later."

        # Attempt to match
        best = find_best_file_match(q, files)

        # If no specific file found, ask clarification
        if best is None:
            return "I could not find a matching file. Can you specify the exact form name or number?"

        # If found, return file with friendly follow-up
        followup = llm_followup_sentence(best["name"])
        return f"Here is the file you need: {best['url']}. {followup}"

    # Default LLM response flow
    result = chain.invoke({"question": message})
    return result.content


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



from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from vector.search import search_vectors
from Services.config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME
from tools.pdf_fetch import fetch_pdf_links
from tools.file_matcher import find_best_file_match
from tools.progresstask_tool import pending_tasks_tool
from tools.status_taskprogress import PENDING_TASK_PHRASES
from tools.status_taskprogress import fetch_task_status_groups
from tools.pdf_tool import pdf_file_tool

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

    #1 Pending task handling
    if user_id and any(p in q for p in PENDING_TASK_PHRASES):
        task_groups = fetch_task_status_groups(user_id)
        return pending_tasks_tool.invoke({
            "data": {
                "pending": task_groups.get("pending", []),
                "in_progress": task_groups.get("in_progress", []),
                "completed": task_groups.get("completed", [])
            }
        })

    #2 FILE REQUEST HANDLING USING TOOL
    if any(k in q for k in ["form", "pdf", "file", "document", "download", "copy"]):
        return pdf_file_tool.invoke({"data": {"query": message}})

    # Default LLM response flow
    result = chain.invoke({"question": message})
    return result.content

def retrieve_context(input: dict):
    q = input["question"].lower() 



from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from vector.search import search_vectors
from Services.config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME
from tools.progresstask_tool import pending_tasks_tool
from tools.status_taskprogress import PENDING_TASK_PHRASES
from tools.status_taskprogress import fetch_task_status_groups
from tools.pdf_tool import pdf_file_tool
from tools.general_tool import general_filter_tool
from tools.hr_tool import hr_lookup

llm = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    model=AZURE_DEPLOYMENT_NAME,
    api_version="2024-02-15-preview",
    temperature=0.2
)

SYSTEM_PROMPT = """
You are Noxy, an HR onboarding assistant.
Your purpose is to answer only about these scope.
Your allowed scope:
- HR policies
- employee onboarding
- company information
- government requirements
- IDs and documents
- HR contact info
- basic greetings
- pending requirements

Forbidden:
- Do NOT give directions, routes, navigation, or "how to go there".
- Do NOT book appointments or perform actions.
- Do NOT say you can connect to HR.
- Do NOT invent information.

Rules:
1. If search is empty and query is HR-related, say you cannot find info.
2. Maximum 3 simple sentences.
3. Do not use Mdash or special formatting.
4. You can't connect to HR. There is no supported live HR support. 
Tell that you are happy to assist them (refer to your scope).

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

    # 0. Run unified filter tool
    filter_result = general_filter_tool.invoke({"data": {"query": message}})
    if filter_result == "greeting":
        return llm.invoke("The user greeted you. Reply warmly, brief, friendly, "
        "and within HR onboarding scope.").content
    
    if filter_result == "vague":
        return llm.invoke("The user asked for help but was unclear. " \
        "Ask naturally which HR or onboarding topic they mean. Keep it short.").content
    
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
    
    #3 HR lookup
    hr_result = hr_lookup.invoke({"data": {"query": message}})
    if hr_result:
        return hr_result
    

    # Default LLM response flow
    result = chain.invoke({"question": message})
    return result.content



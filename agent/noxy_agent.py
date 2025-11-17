from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from vector.search import search_vectors
from Services.config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME


# ---- LLM MODEL ----
llm = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    model=AZURE_DEPLOYMENT_NAME,
    api_version="2024-02-15-preview",
    temperature=0.2
)


# ---- SYSTEM PROMPT ----
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

HR CONTACT INFORMATION:
Email: hrdepartment@n-pax.com
Cebu HR: (032) 123-4567
Manila HR: (02) 987-6543
Hours: Monday–Friday, 8:00 AM – 6:00 PM
"""


# ---- FORMAT INPUT TO LLM ----
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
User message: {question}

Relevant knowledge:
{context}

Answer as Noxy.
""")
])


# ---- PIPELINE ----
def retrieve_context(input: dict):
    q = input["question"].lower()

    # Greeting → no vector search
    if q in ["hi", "hello", "hey", "good morning", "good afternoon"]:
        return ""

    # Vague → no vector search
    if q in ["guide me", "help me", "assist me"]:
        return ""

    # Normal → use vector search
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

def ask_noxy(message: str):
    result = chain.invoke({"question": message})
    return result.content

def retrieve_context(input: dict):
    q = input["question"].lower()   # now this works


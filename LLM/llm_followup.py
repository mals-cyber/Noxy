from langchain_openai import AzureChatOpenAI
from Services.config import AZURE_API_KEY, AZURE_ENDPOINT, AZURE_DEPLOYMENT_NAME

llm = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    model=AZURE_DEPLOYMENT_NAME,
    api_version="2024-02-15-preview",
    temperature=0.2
)

def llm_followup_sentence(filename: str):
    prompt = (
        f"Write one sentence asking the user if they need anything else."
        f"Do not add a link, do not ask questions. Maximum 1 sentence."
    )
    result = llm.invoke(prompt)
    return result.content.strip()

import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv()

AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_API_VERSION = os.getenv("AZURE_EMBEDDING_API_VERSION", "2024-02-01")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")

embedding_model = AzureOpenAIEmbeddings(
    model=AZURE_EMBEDDING_DEPLOYMENT,        
    azure_endpoint=AZURE_EMBEDDING_ENDPOINT, 
    api_key=AZURE_EMBEDDING_API_KEY,         
    api_version=AZURE_EMBEDDING_API_VERSION  
)

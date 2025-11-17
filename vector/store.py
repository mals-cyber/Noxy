import os
from dotenv import load_dotenv

from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "ChromaDB")

AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_API_VERSION = os.getenv("AZURE_EMBEDDING_API_VERSION", "2024-02-01")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")

vector_db = None


def get_vector_db():
    global vector_db

    if vector_db is not None:
        return vector_db

    embeddings = AzureOpenAIEmbeddings(
        model=AZURE_EMBEDDING_DEPLOYMENT,
        api_key=AZURE_EMBEDDING_API_KEY,
        azure_endpoint=AZURE_EMBEDDING_ENDPOINT,
        api_version=AZURE_EMBEDDING_API_VERSION
    )

    vector_db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )

    return vector_db


def persist_db():
    try:
        get_vector_db().persist()
    except:
        pass


def add_documents_to_db(documents, metadatas=None):
    """
    Add documents to existing ChromaDB without rebuilding.

    Args:
        documents: List of LangChain Document objects to add
        metadatas: Optional list of metadata dicts (must match documents length)

    Returns:
        Number of documents added

    Raises:
        ValueError: If no documents or metadata mismatch
    """
    if not documents:
        raise ValueError("No documents to add")

    vector_db = get_vector_db()

    # If metadatas provided, ensure length matches
    if metadatas and len(metadatas) != len(documents):
        raise ValueError(
            f"Metadata count ({len(metadatas)}) must match document count ({len(documents)})"
        )

    try:
        vector_db.add_documents(documents=documents, metadatas=metadatas)
        return len(documents)
    except Exception as e:
        raise ValueError(f"Failed to add documents to ChromaDB: {str(e)}")


def delete_documents_by_url(url: str) -> int:
    """
    Delete all documents from ChromaDB that were injected from a specific URL.

    Args:
        url: The original URL of the document to delete

    Returns:
        Number of documents deleted

    Raises:
        ValueError: If URL is invalid or deletion fails
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    vector_db = get_vector_db()

    try:
        # Delete all chunks with matching source URL
        # The delete method returns None, so we need to count before and after
        # Get current count of matching documents
        results = vector_db.get(where={"source": url})
        documents_to_delete = len(results.get("ids", []))

        if documents_to_delete == 0:
            raise ValueError(f"No documents found with source URL: {url}")

        # Delete documents matching the source URL
        vector_db.delete(where={"source": url})
        return documents_to_delete

    except Exception as e:
        raise ValueError(f"Failed to delete documents from ChromaDB: {str(e)}")

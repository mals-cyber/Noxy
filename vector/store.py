from langchain_chroma import Chroma
from .embeddings import embedding_model

vector_db = None

def get_vector_db():
    global vector_db
    if vector_db is None:
        vector_db = Chroma(
            persist_directory="ChromaDB",
            embedding_function=embedding_model
        )
    return vector_db


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

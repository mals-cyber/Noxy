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
        print("ChromaDB loaded once.")
    return vector_db

from langchain.tools import tool
from vector.search import search_vectors

@tool
def vector_lookup(query: str) -> str:
    """Search HR knowledge base content."""
    results = search_vectors(query)
    return " ".join(results) if results else ""

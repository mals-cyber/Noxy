from .store import get_vector_db

def search_vectors(query: str, k=5):
    db = get_vector_db()
    results = db.similarity_search(query, k=k)
    return [r.page_content for r in results]

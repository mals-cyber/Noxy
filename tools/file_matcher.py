from openai import AzureOpenAI
from Services.config import EMBEDDING_API_KEY, EMBEDDING_ENDPOINT, EMBEDDING_DEPLOYMENT_NAME, EMBEDDING_API_VERSION

client = AzureOpenAI(
    api_key=EMBEDDING_API_KEY,
    azure_endpoint=EMBEDDING_ENDPOINT,
    api_version=EMBEDDING_API_VERSION
)

def embed(text: str):
    """Generate an embedding for text."""
    resp = client.embeddings.create(
        input=text,
        model=EMBEDDING_DEPLOYMENT_NAME
    )
    return resp.data[0].embedding


def find_best_file_match(user_query: str, files: list):
    """Return best file match using embeddings."""
    
    user_vec = embed(user_query)

    scored = []
    for f in files:
        file_vec = embed(f["name"])
        score = cosine_similarity(user_vec, file_vec)
        scored.append((score, f))

    scored.sort(reverse=True, key=lambda x: x[0])
    best_score, best_file = scored[0]

    # If similarity is low, do not guess
    if best_score < 0.55:
        return None

    return best_file


def cosine_similarity(a, b):
    import math
    return sum(x*y for x, y in zip(a, b)) / (
        math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    )

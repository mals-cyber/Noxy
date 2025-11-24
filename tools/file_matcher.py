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

QUERY_SYNONYMS = {
    "pag ibig": "hdmf", "pag-ibig": "hdmf", "hdmf": "hdmf", "mdf": "hdmf",
    "sss": "sss","social security": "sss",
    "tin": "bir","tax": "bir","bir": "bir",
    "philhealth": "philhealth","health insurance": "philhealth",
}

def normalize_query(q: str):
    q = q.lower()
    for key, value in QUERY_SYNONYMS.items():
        if key in q:
            return value
    return q


def cosine_similarity(a, b):
    import math
    return sum(x*y for x, y in zip(a, b)) / (
        math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    )


def find_best_file_match(user_query: str, files: list):
    """Return best file match using embeddings with synonym support."""

    # Normalize before embedding
    normalized_query = normalize_query(user_query)
    print("NORMALIZED QUERY:", normalized_query)

    user_vec = embed(normalized_query)

    scored = []
    for f in files:
        file_vec = embed(f["name"])
        score = cosine_similarity(user_vec, file_vec)
        scored.append((score, f))
        print(f"SCORE {score} → {f['name']}")

    scored.sort(reverse=True, key=lambda x: x[0])
    best_score, best_file = scored[0]

    if best_score < 0.55:
        print("NO CONFIDENT MATCH, SCORE BELOW THRESHOLD")
        return None

    print("BEST MATCH:", best_file["name"])
    return best_file

import re
from openai import AzureOpenAI
from Services.config import EMBEDDING_API_KEY, EMBEDDING_ENDPOINT, EMBEDDING_DEPLOYMENT_NAME, EMBEDDING_API_VERSION

client = AzureOpenAI(
    api_key=EMBEDDING_API_KEY,
    azure_endpoint=EMBEDDING_ENDPOINT,
    api_version=EMBEDDING_API_VERSION
)

QUERY_SYNONYMS = {
    "pagibig": "hdmf",
    "pag ibig": "hdmf",
    "pag-ibig": "hdmf",
    "hdmf": "hdmf",
    "mdf": "hdmf",

    "sss": "sss",
    "social security": "sss",
    "e1": "sss",

    "tin": "bir",
    "tax": "bir",
    "bir": "bir",

    "philhealth": "philhealth",
    "health insurance": "philhealth",
    "phil health": "philhealth"
}


generic_bir_cases = [
    "bir",
    "bir form",
    "bir forms",
    "bir file",
    "bir document",
    "bir pdf",
    "provide bir",
    "tin",
    "tax form",
    "bureau of internal revenue"
]

def embed(text: str):
    resp = client.embeddings.create(
        input=text,
        model=EMBEDDING_DEPLOYMENT_NAME
    )
    return resp.data[0].embedding

def normalize_query(q: str):
    q = q.lower().replace("-", " ").replace("_", " ").strip()

    # enhanced numeric form detection (BIR)
    form_num_match = re.search(r"\b(06\d{2}|19\d{2}|23\d{2}|25\d{2}q?)\b", q)
    if form_num_match:
        return form_num_match.group(0)

    # prioritize exact agency forms BEFORE embeddings
    for key, value in QUERY_SYNONYMS.items():
        if key in q:
            return value

    # special case: pagibig without space
    if "pagibig" in q:
        return "hdmf"
    
    return q


def cosine_similarity(a, b):
    import math
    return sum(x*y for x, y in zip(a, b)) / (
        math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    )

def find_best_file_match(user_query: str, files: list):
    normalized_query = normalize_query(user_query)
    print("NORMALIZED QUERY:", normalized_query)

    # direct match priority
    form_num_match = re.search(r"\b\d{3,4}\b", normalized_query)
    if form_num_match:
        form_num = form_num_match.group(0)
        for f in files:
            if form_num in f["name"]:
                print("DIRECT FORM NUMBER MATCH:", f["name"])
                return f

    user_vec = embed(normalized_query)

    scored = []
    for f in files:
        file_vec = embed(f["name"])
        score = cosine_similarity(user_vec, file_vec)
        scored.append((score, f))

    scored.sort(reverse=True, key=lambda x: x[0])
    best_score, best_file = scored[0]

    if best_score < 0.48:
        print("NO CONFIDENT MATCH, SCORE BELOW THRESHOLD")
        return None

    return best_file

import json
import fitz
import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

PDF_FOLDER = "MockData"

def extract_pdf_text(pdf_path: str):
    """Extract text from a PDF file safely."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except:
        return ""

def load_json_kb(path: str):
    docs = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            kb = json.load(f)

        categories = kb.get("knowledgeBase", {}).get("categories", [])

        for cat in categories:
            entries = cat.get("entries", [])
            for entry in entries:
                question = entry.get("question", "")
                answer = entry.get("answer", "")
                keywords = ", ".join(entry.get("keywords", []))

                text_block = (
                    f"QUESTION: {question}\n"
                    f"ANSWER: {answer}\n"
                    f"KEYWORDS: {keywords}"
                )

                docs.append(Document(page_content=text_block))

        return docs

    except Exception as e:
        return []

def expand_bullet_points(text: str):
    """Convert bullet points into readable sentences."""
    lines = text.split("\n")
    expanded = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("- "):
            bullet = stripped.replace("- ", "")
            expanded.append(f"{bullet} is required as part of the onboarding process.")
        else:
            expanded.append(stripped)

    return "\n".join(expanded)


def load_md_kb(path: str):
    docs = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_md = f.read()

        raw_md = expand_bullet_points(raw_md)

        sections = re.split(r"\n#+ ", raw_md)

        for sec in sections:
            cleaned = sec.strip()
            if len(cleaned) > 40:  
                docs.append(Document(page_content=cleaned))

        return docs

    except Exception as e:
        return []

def load_pdf_kb():
    docs = []
    for file in os.listdir(PDF_FOLDER):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file)
            pdf_text = extract_pdf_text(pdf_path)

            if pdf_text:
                docs.append(
                    Document(
                        page_content=f"PDF FILE: {file}\n{pdf_text}"
                    )
                )
    return docs

def setup_vector_db(kb_folder: str):

    all_docs = []

    for file in os.listdir(kb_folder):
        path = os.path.join(kb_folder, file)

        if file.endswith(".json"):
            all_docs.extend(load_json_kb(path))

        elif file.endswith(".md"):
            all_docs.extend(load_md_kb(path))

    all_docs.extend(load_pdf_kb())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split_docs = splitter.split_documents(all_docs)

    if os.path.exists("ChromaDB"):
        import shutil
        shutil.rmtree("ChromaDB")

    Chroma.from_documents(
        documents=split_docs,
        embedding=embedding_model,
        persist_directory="ChromaDB"
    )

def search_vectors(query: str):
    vector_db = Chroma(
        persist_directory="ChromaDB",
        embedding_function=embedding_model
    )

    results = vector_db.similarity_search(query, k=3)
    return [r.page_content for r in results]

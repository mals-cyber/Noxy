import json
import fitz
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

PDF_FOLDER = "MockData"

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def setup_vector_db(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    docs = []
    categories = kb_data["knowledgeBase"]["categories"]

    for cat in categories:
        for item in cat.get("items", []):
            docs.append(Document(page_content=f"{item.get('title','')}\n{item.get('content','')}"))

            for faq in item.get("faqs", []):
                docs.append(Document(
                    page_content=f"Q: {faq.get('question','')}\nA: {faq.get('answer','')}"
                ))

    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file)
            pdf_text = extract_pdf_text(pdf_path)
            docs.append(Document(page_content=f"PDF FILE: {file}\n{pdf_text}"))

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

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

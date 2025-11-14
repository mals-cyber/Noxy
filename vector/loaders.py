import json
import fitz
import os
import re
from langchain_core.documents import Document
from .chunker import expand_bullet_points


def load_json_kb(path: str):
    docs = []
    try:
        with open(path, encoding="utf-8") as f:
            kb = json.load(f)
        
        for cat in kb.get("knowledgeBase", {}).get("categories", []):
            for entry in cat.get("entries", []):
                q = entry.get("question", "")
                a = entry.get("answer", "")
                k = ", ".join(entry.get("keywords", []))

                docs.append(Document(page_content=f"QUESTION: {q}\nANSWER: {a}\nKEYWORDS: {k}"))
    except:
        pass
    return docs


def load_md_kb(path: str):
    docs = []
    try:
        with open(path, encoding="utf-8") as f:
            raw = expand_bullet_points(f.read())

        sections = re.split(r"\n#+ ", raw)

        for sec in sections:
            if len(sec.strip()) > 40:
                docs.append(Document(page_content=sec.strip()))
    except:
        pass

    return docs


def extract_pdf_text(path: str):
    try:
        doc = fitz.open(path)
        return "".join([p.get_text() for p in doc]).strip()
    except:
        return ""


def load_pdf_kb(pdf_folder="MockData"):
    docs = []
    for f in os.listdir(pdf_folder):
        if f.lower().endswith(".pdf"):
            text = extract_pdf_text(os.path.join(pdf_folder, f))
            if text:
                docs.append(Document(page_content=f"PDF FILE: {f}\n{text}"))
    return docs

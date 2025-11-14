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

        # Normalize categories path
        knowledge_base = kb.get("knowledgeBase", kb)
        categories = knowledge_base.get("categories", [])

        for cat in categories:

            # --- FORMAT 1: entries[] ---
            entries = cat.get("entries", [])
            for entry in entries:
                q = entry.get("question", "")
                a = entry.get("answer", "")
                k = ", ".join(entry.get("keywords", []))

                text = f"QUESTION: {q}\nANSWER: {a}\nKEYWORDS: {k}"
                docs.append(Document(page_content=text))

            # --- FORMAT 2: items[] (government requirements) ---
            items = cat.get("items", [])
            for item in items:
                title = item.get("title", "")
                content = item.get("content", "")

                # requirements list
                requirements = item.get("requirements", [])
                req_text = " | ".join(
                    f"{r.get('item', '')}: {r.get('description', '')}"
                    for r in requirements
                )

                # FAQs if present
                faqs = item.get("faqs", [])
                faq_text = " | ".join(
                    f"Q:{f.get('question')} A:{f.get('answer')}" 
                    for f in faqs
                )

                text = (
                    f"TITLE: {title}\n"
                    f"CONTENT: {content}\n"
                    f"REQUIREMENTS: {req_text}\n"
                    f"FAQS: {faq_text}"
                )

                docs.append(Document(page_content=text))

    except Exception as e:
        print(f"[ERROR] JSON Load Failed ({path}): {e}")

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

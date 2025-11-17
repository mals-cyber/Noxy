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
            data = json.load(f)

        dep_root = data.get("departmentKnowledgeBase")
        if dep_root:
            # ---- Departments + their FAQs ----
            for dept in dep_root.get("departments", []):
                dept_name = dept.get("departmentName", "")
                faqs = dept.get("faqs", [])

                for faq in faqs:
                    text = (
                        f"DEPARTMENT: {dept_name}\n"
                        f"ID: {faq.get('id', '')}\n"
                        f"CATEGORY: {faq.get('category', '')}\n"
                        f"QUESTION: {faq.get('question', '')}\n"
                        f"ANSWER: {faq.get('answer', '')}\n"
                        f"KEYWORDS: {', '.join(faq.get('keywords', []))}\n"
                    )
                    docs.append(Document(page_content=text))

            for faq in dep_root.get("crossDepartmentFAQs", []):
                text = (
                    f"CROSS-DEPARTMENT FAQ\n"
                    f"ID: {faq.get('id', '')}\n"
                    f"QUESTION: {faq.get('question', '')}\n"
                    f"ANSWER: {faq.get('answer', '')}\n"
                    f"RELATED: {', '.join(faq.get('relatedDepartments', []))}\n"
                )
                docs.append(Document(page_content=text))

            general = dep_root.get("generalDepartmentInfo")
            if general:
                text = "GENERAL DEPARTMENT INFO\n" + json.dumps(general, indent=2)
                docs.append(Document(page_content=text))

            return docs

        kb_root = data.get("knowledgeBase", data)
        categories = kb_root.get("categories", [])

        for cat in categories:

            # ---- entries[] format ----
            for entry in cat.get("entries", []):
                q = entry.get("question", "")
                a = entry.get("answer", "")
                k = ", ".join(entry.get("keywords", []))

                text = (
                    f"QUESTION: {q}\n"
                    f"ANSWER: {a}\n"
                    f"KEYWORDS: {k}"
                )
                docs.append(Document(page_content=text))

            # ---- items[] format (government requirements) ----
            for item in cat.get("items", []):
                title = item.get("title", "")
                content = item.get("content", "")

                # Requirements
                req_text = " | ".join(
                    f"{r.get('item', '')}: {r.get('description', '')}"
                    for r in item.get("requirements", [])
                )

                # FAQs inside items
                faq_text = " | ".join(
                    f"Q:{f.get('question')} A:{f.get('answer')}"
                    for f in item.get("faqs", [])
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

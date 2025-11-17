import json
import fitz
import os
import re
from langchain_core.documents import Document
from .chunker import expand_bullet_points


def _safe_meta(value):
    """Ensure metadata is always a str/int/bool/float/None."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value)
    return value


def load_json_kb(path: str):
    docs = []
    source = os.path.basename(path)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # ==========================
        # FORMAT 1: departmentKnowledgeBase
        # ==========================
        dep_root = data.get("departmentKnowledgeBase")
        if dep_root:

            # DEPARTMENT FAQs
            for dept in dep_root.get("departments", []):
                dept_name = dept.get("departmentName", "")
                for faq in dept.get("faqs", []):
                    text = (
                        f"QUESTION: {faq.get('question')}\n"
                        f"ANSWER: {faq.get('answer')}"
                    )
                    docs.append(Document(
                        page_content=text,
                        metadata={
                            "source": source,
                            "type": "department_faq",
                            "department": _safe_meta(dept_name),
                            "id": _safe_meta(faq.get("id"))
                        }
                    ))

            # CROSS-DEPARTMENT FAQs
            for faq in dep_root.get("crossDepartmentFAQs", []):
                text = f"{faq.get('question')}\n{faq.get('answer')}"
                docs.append(Document(
                    page_content=text,
                    metadata={
                        "source": source,
                        "type": "cross_department_faq",
                        "related": _safe_meta(faq.get("relatedDepartments", [])),
                        "id": _safe_meta(faq.get("id"))
                    }
                ))

            return docs

        # ==========================
        # FORMAT 2: knowledgeBase.categories
        # ==========================
        kb_root = data.get("knowledgeBase", data)
        categories = kb_root.get("categories", [])

        for cat in categories:

            # ---- entries[] format (Q&A)
            for entry in cat.get("entries", []):
                text = f"Q: {entry.get('question')}\nA: {entry.get('answer')}"
                docs.append(Document(
                    page_content=text,
                    metadata={
                        "source": source,
                        "type": "entry",
                        "category": _safe_meta(cat.get("categoryName")),
                        "id": _safe_meta(entry.get("id")),
                        "keywords": _safe_meta(entry.get("keywords", []))
                    }
                ))

            # ---- items[] format (Gov requirements)
            for item in cat.get("items", []):
                text = f"{item.get('title')}\n{item.get('content')}"
                docs.append(Document(
                    page_content=text,
                    metadata={
                        "source": source,
                        "type": "requirement_item",
                        "category": _safe_meta(cat.get("name")),
                        "id": _safe_meta(item.get("id"))
                    }
                ))

    except Exception as e:
        print(f"[ERROR] JSON Load Failed ({path}): {e}")

    return docs


def load_md_kb(path: str):
    source = os.path.basename(path)
    docs = []

    try:
        with open(path, encoding="utf-8") as f:
            raw = expand_bullet_points(f.read())

        sections = re.split(r"\n#+\s*", raw)

        for sec in sections:
            sec = sec.strip()
            if len(sec) > 40:
                docs.append(Document(
                    page_content=sec,
                    metadata={
                        "source": source,
                        "type": "markdown"
                    }
                ))
    except Exception as e:
        print(f"[ERROR] Markdown Load Failed {path}: {e}")

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
            path = os.path.join(pdf_folder, f)
            text = extract_pdf_text(path)

            if text:
                docs.append(Document(
                    page_content=text,
                    metadata={
                        "source": f,
                        "type": "pdf"
                    }
                ))
    return docs
